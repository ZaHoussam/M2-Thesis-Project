# ================================================================
#  core/detector.py — Sharpness check utility
#
#  Detection is now handled by FacePipeline in embedder.py.
#  This file only provides the sharpness gate — used to skip
#  blurry frames before they reach the aggregator.
# ================================================================
import cv2
import numpy as np


def is_sharp(frame_bgr: np.ndarray, threshold: float = 80.0) -> bool:
    """
    Returns True if the frame is sharp enough to embed.
    Uses Laplacian variance — blurry images have low variance.

    threshold: tune this value based on your camera:
        60.0  → permissive (accepts slightly blurry frames)
        80.0  → recommended default
        120.0 → strict (only very sharp frames pass)
    """
    gray     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance >= threshold