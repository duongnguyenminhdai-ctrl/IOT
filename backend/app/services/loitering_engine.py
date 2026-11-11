import os
import cv2
import time
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO

from app.config import settings
from app.mqtt_client import mqtt_manager

logger = logging.getLogger("loitering_engine")

class TrackedPerson:
    def __init__(self, track_id: int, entry_time: float):
        self.track_id = track_id
        self.first_seen_roi: float = entry_time
        self.last_seen_roi: float = entry_time
        self.is_inside_roi: bool = True
        self.alert_triggered: bool = False
        self.consecutive_outside_frames: int = 0

class LoiteringEngine:
    def __init__(self):
        logger.info(f"Initializing YOLOv8 model from {settings.YOLO_MODEL_PATH}...")
        self.model = YOLO(settings.YOLO_MODEL_PATH)
        
        # Tracking dictionaries: track_id -> TrackedPerson
        self.tracked_persons: Dict[int, TrackedPerson] = {}
        
        # Region of Interest (ROI) polygon in pixel coordinates
        self.roi_polygon: Optional[np.ndarray] = None
        self.frame_width = settings.FRAME_WIDTH
        self.frame_height = settings.FRAME_HEIGHT
        self.update_roi_from_percent(settings.DEFAULT_ROI_PERCENT)
        
        # Cooldown management
        self.last_alarm_time: float = 0.0
        self.alarm_cooldown: float = settings.ALARM_COOLDOWN_SECONDS
        self.loitering_threshold: float = settings.LOITERING_THRESHOLD_SECONDS

    def update_roi_from_percent(self, points_pct: List[Tuple[float, float]]):
        """Converts normalized (0.0 to 1.0) points into integer pixel polygon."""
        pixel_points = [
            [int(pt[0] * self.frame_width), int(pt[1] * self.frame_height)]
            for pt in points_pct
        ]
        self.roi_polygon = np.array(pixel_points, dtype=np.int32)
        logger.info(f"ROI Polygon updated: {pixel_points}")

    def update_roi_pixels(self, points: List[List[int]]):
        """Directly sets ROI polygon using pixel coordinates."""
        self.roi_polygon = np.array(points, dtype=np.int32)

    def is_point_in_roi(self, x: float, y: float) -> bool:
        """Uses cv2.pointPolygonTest to evaluate if a point is inside ROI."""
        if self.roi_polygon is None:
            return False
        # distance > 0: inside, == 0: on edge, < 0: outside
        res = cv2.pointPolygonTest(self.roi_polygon, (float(x), float(y)), False)
        return res >= 0

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[dict]]:
        """
        Runs YOLOv8 tracking with ByteTrack, calculates dwell time inside ROI polygon,
        annotates the frame, and triggers alerts if loitering exceeds threshold.
        """
        if frame is None:
            return frame, []

        h, w, _ = frame.shape
        if (w != self.frame_width or h != self.frame_height) and self.roi_polygon is not None:
            # Dynamically recalculate if resolution changed
            self.frame_width, self.frame_height = w, h
            self.update_roi_from_percent(settings.DEFAULT_ROI_PERCENT)

        now = time.time()
        detections = []
        roi_has_person = False

        # Run ByteTrack on YOLOv8nano (class 0 = Person only)
        results = self.model.track(
            source=frame,
            classes=[0],
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
            conf=0.45
        )

        current_active_ids = set()

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                # If tracker hasn't assigned an ID yet, skip
                if box.id is None:
                    continue

                track_id = int(box.id[0].item())
                current_active_ids.add(track_id)
                
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                conf = float(box.conf[0].item())

                # Person anchor point: bottom-center (foot level standing position)
                anchor_x = (x1 + x2) / 2.0
                anchor_y = float(y2)

                inside = self.is_point_in_roi(anchor_x, anchor_y)

                if inside:
                    roi_has_person = True
                    if track_id not in self.tracked_persons:
                        self.tracked_persons[track_id] = TrackedPerson(track_id, now)
                    else:
                        person = self.tracked_persons[track_id]
                        person.last_seen_roi = now
                        person.is_inside_roi = True
                        person.consecutive_outside_frames = 0
                else:
                    if track_id in self.tracked_persons:
                        person = self.tracked_persons[track_id]
                        person.consecutive_outside_frames += 1
                        if person.consecutive_outside_frames > 30:  # ~1 second outside
                            person.is_inside_roi = False

                # Calculate dwell time
                dwell_time = 0.0
                if track_id in self.tracked_persons and self.tracked_persons[track_id].is_inside_roi:
                    dwell_time = now - self.tracked_persons[track_id].first_seen_roi

                is_loitering = (dwell_time >= self.loitering_threshold)

                # Check and trigger alarm
                if is_loitering and inside:
                    person = self.tracked_persons[track_id]
                    if not person.alert_triggered and (now - self.last_alarm_time > self.alarm_cooldown):
                        person.alert_triggered = True
                        self.last_alarm_time = now
                        self._trigger_loitering_alert(frame, track_id, dwell_time, (x1, y1, x2, y2))

                detections.append({
                    "id": track_id,
                    "bbox": [x1, y1, x2, y2],
                    "anchor": [int(anchor_x), int(anchor_y)],
                    "conf": conf,
                    "inside_roi": inside,
                    "dwell_time": round(dwell_time, 1),
                    "is_loitering": is_loitering
                })

        # Cleanup lost tracks
        all_ids = list(self.tracked_persons.keys())
        for tid in all_ids:
            if tid not in current_active_ids:
                if now - self.tracked_persons[tid].last_seen_roi > 5.0:
                    del self.tracked_persons[tid]

        # Draw overlays on the annotated frame
        annotated_frame = self._render_overlays(frame, detections, roi_has_person)
        return annotated_frame, detections

    def _trigger_loitering_alert(self, frame: np.ndarray, track_id: int, dwell_time: float, bbox: Tuple[int, int, int, int]):
        """Saves snapshot and dispatches alarm through MQTT & Telegram."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"loiter_id{track_id}_{timestamp_str}.jpg"
        snapshot_filepath = os.path.join(settings.SNAPSHOT_DIR, filename)

        # Draw warning highlight onto snapshot
        snap = frame.copy()
        x1, y1, x2, y2 = bbox
        cv2.rectangle(snap, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(
            snap,
            f"ALERT: ID {track_id} Loitering {dwell_time:.1f}s",
            (x1, max(y1 - 10, 25)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )
        # Add timestamp watermark
        cv2.putText(
            snap,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (20, snap.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )
        cv2.imwrite(snapshot_filepath, snap)

        # Dispatch via MQTT and Telegram
        description = f"Phát hiện đối tượng (ID: {track_id}) lảng vảng trước cửa trên {dwell_time:.1f} giây."
        logger.warning(f"LOITERING DETECTED! Track ID: {track_id}, Dwell: {dwell_time:.1f}s")
        mqtt_manager.trigger_alarm(
            event_type="LOITERING",
            description=description,
            snapshot_path=snapshot_filepath,
            person_id=track_id,
            dwell_time=dwell_time
        )

    def _render_overlays(self, frame: np.ndarray, detections: List[dict], roi_has_person: bool) -> np.ndarray:
        """Renders visual ROI boundaries, HUD statistics, and bounding boxes."""
        overlay = frame.copy()

        # 1. Draw ROI Polygon with alpha transparency
        if self.roi_polygon is not None:
            roi_color = (0, 0, 220) if roi_has_person else (0, 200, 0)
            cv2.polylines(overlay, [self.roi_polygon], isClosed=True, color=roi_color, thickness=2)
            
            mask = np.zeros_like(frame, dtype=np.uint8)
            cv2.fillPoly(mask, [self.roi_polygon], roi_color)
            cv2.addWeighted(mask, 0.15, overlay, 0.85, 0, overlay)

            # Label ROI
            cv2.putText(
                overlay,
                "DOOR ZONE (ROI)",
                (self.roi_polygon[0][0] + 10, self.roi_polygon[0][1] + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                roi_color,
                2
            )

        # 2. Draw Bounding Boxes and Tracking Badges
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            track_id = det["id"]
            dwell = det["dwell_time"]
            is_loiter = det["is_loitering"]
            inside = det["inside_roi"]

            if is_loiter:
                box_color = (0, 0, 255)      # Red for Loitering Alarm
            elif inside:
                box_color = (0, 165, 255)    # Orange for inside ROI
            else:
                box_color = (0, 255, 0)      # Green for normal tracking outside ROI

            # Bounding box
            cv2.rectangle(overlay, (x1, y1), (x2, y2), box_color, 2)

            # Foot anchor point
            ax, ay = det["anchor"]
            cv2.circle(overlay, (ax, ay), 5, box_color, -1)

            # Badge Label
            if inside:
                label = f"ID #{track_id} | {dwell:.1f}s / {self.loitering_threshold:.0f}s"
            else:
                label = f"ID #{track_id}"

            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(overlay, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), box_color, -1)
            cv2.putText(
                overlay,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            # Pulsing Loitering Warning Header
            if is_loiter:
                cv2.putText(
                    overlay,
                    "⚠️ LOITERING ALERT! ⚠️",
                    (x1, y2 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 0, 255),
                    2
                )

        # 3. Top Status Banner (HUD)
        banner_h = 35
        cv2.rectangle(overlay, (0, 0), (overlay.shape[1], banner_h), (25, 25, 25), -1)
        status_mode = "ARMED" if mqtt_manager.is_armed else "DISARMED"
        mode_color = (0, 255, 0) if mqtt_manager.is_armed else (180, 180, 180)
        
        cv2.putText(
            overlay,
            f"SYSTEM: {status_mode}",
            (15, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            mode_color,
            2
        )

        alarm_str = "ALARM: ACTIVE" if mqtt_manager.alarm_active else "ALARM: QUIET"
        alarm_col = (0, 0, 255) if mqtt_manager.alarm_active else (180, 180, 180)
        cv2.putText(
            overlay,
            alarm_str,
            (220, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            alarm_col,
            2
        )

        door_col = (0, 0, 255) if mqtt_manager.door_status == "OPEN" else (0, 255, 0)
        cv2.putText(
            overlay,
            f"DOOR: {mqtt_manager.door_status}",
            (420, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            door_col,
            2
        )

        pir_col = (0, 165, 255) if mqtt_manager.pir_status == "MOTION" else (180, 180, 180)
        cv2.putText(
            overlay,
            f"PIR: {mqtt_manager.pir_status}",
            (600, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            pir_col,
            2
        )

        # Clock
        time_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(
            overlay,
            time_str,
            (overlay.shape[1] - 110, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )

        return overlay

loitering_engine = LoiteringEngine()

