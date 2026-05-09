# ================================================================
#  core/camera.py — OpenCV camera frame capture
# ================================================================
import cv2
import numpy as np
from config import settings


class Camera:
    def __init__(self):
        idx = settings.camera_index
        # If it's a string that looks like an integer, convert it to int
        if isinstance(idx, str) and idx.isdigit():
            idx = int(idx)
            
        self._cap = cv2.VideoCapture(idx)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {idx}")

    def read_frame(self) -> np.ndarray | None:
        """Read one frame. Returns BGR numpy array or None on failure."""
        ok, frame = self._cap.read()
        return frame if ok else None

    def release(self):
        self._cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()
