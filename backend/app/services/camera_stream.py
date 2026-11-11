import cv2
import threading
import time
import logging
import numpy as np
from app.config import settings

logger = logging.getLogger("camera_stream")

class VideoCamera:
    def __init__(self, camera_index=None):
        self.camera_index = camera_index if camera_index is not None else settings.CAMERA_INDEX
        self.cap = None
        self.frame = None
        self.is_running = False
        self.lock = threading.Lock()
        self.thread = None
        self._init_camera()

    def _init_camera(self):
        try:
            # On Windows, cv2.CAP_DSHOW provides fast non-lagging initialization
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default backend
                self.cap = cv2.VideoCapture(self.camera_index)
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                logger.info(f"USB Camera opened at index {self.camera_index}")
            else:
                logger.warning(f"Unable to open camera at index {self.camera_index}. Fallback dummy frames enabled.")
        except Exception as e:
            logger.error(f"Error opening camera: {e}")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Camera capture thread started.")

    def _capture_loop(self):
        while self.is_running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.frame = frame
                else:
                    time.sleep(0.02)
            else:
                # Generate synthetic test pattern if camera is absent
                dummy = np.zeros((settings.FRAME_HEIGHT, settings.FRAME_WIDTH, 3), dtype=np.uint8)
                cv2.putText(
                    dummy,
                    f"USB Camera #{self.camera_index} Disconnected",
                    (settings.FRAME_WIDTH // 4, settings.FRAME_HEIGHT // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                    2
                )
                with self.lock:
                    self.frame = dummy
                time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        logger.info("Camera released.")

camera_manager = VideoCamera()

