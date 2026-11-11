import cv2
import time
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Tuple

from app.services.camera_stream import camera_manager
from app.services.loitering_engine import loitering_engine

logger = logging.getLogger("stream_router")
router = APIRouter(prefix="/api/stream", tags=["Stream"])

class ROIPointsPayload(BaseModel):
    points: List[Tuple[float, float]]  # List of (x, y) in percentage (0.0 - 1.0)

def generate_video_frames():
    while True:
        frame = camera_manager.get_frame()
        if frame is None:
            time.sleep(0.03)
            continue

        # Run inference & overlay
        annotated_frame, _ = loitering_engine.process_frame(frame)

        # Encode to JPEG
        ret, buffer = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            time.sleep(0.03)
            continue

        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        
        # Limit to ~25-30 FPS
        time.sleep(0.03)

@router.get("/video_feed")
def video_feed():
    """Provides non-blocking MJPEG stream with YOLOv8 inference & loitering HUD."""
    return StreamingResponse(
        generate_video_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/roi")
def set_roi(payload: ROIPointsPayload):
    """Dynamically updates the polygon Region of Interest (ROI)."""
    if len(payload.points) < 3:
        raise HTTPException(status_code=400, detail="ROI polygon must contain at least 3 vertices.")
    
    loitering_engine.update_roi_from_percent(payload.points)
    return {"status": "success", "message": "ROI updated successfully", "points": payload.points}

