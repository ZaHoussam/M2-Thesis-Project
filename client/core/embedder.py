# ================================================================
#  core/embedder.py — InsightFace pipeline
#                     RetinaFace detection + ArcFace embedding
#
#  One class handles everything:
#    - Face detection (RetinaFace)
#    - 5-point geometric alignment (built-in)
#    - ArcFace embedding extraction
#    - Returns L2-normalised 512-d vector
#
#  Usage:
#    pipeline = FacePipeline()
#    result   = pipeline.process(frame_bgr)
#    if result:
#        embedding = result["embedding"]  # 512-d list
#        bbox      = result["bbox"]       # (x1,y1,x2,y2)
#        score     = result["det_score"]  # detection confidence
# ================================================================
import numpy as np
import cv2
# pyrefly: ignore [missing-import]
from insightface.app import FaceAnalysis
from config import settings


class FacePipeline:
    """
    Unified detection + alignment + embedding pipeline.
    One instance per client — created once, reused every frame.
    """

    def __init__(self):
        self._app = FaceAnalysis(
            name      = "buffalo_l",
            providers = ["CPUExecutionProvider"],
        )
        # det_size: resolution fed to RetinaFace detector
        # 640x640 is the recommended default — good balance of
        # speed vs accuracy for webcam distance
        self._app.prepare(ctx_id=0, det_size=(640, 640))
        print("[PIPELINE] InsightFace buffalo_l loaded.")
        print("[PIPELINE] RetinaFace + ArcFace ready.")

    def process(self, frame_bgr: np.ndarray) -> dict | None:
        """
        Run full pipeline on one BGR frame.

        Returns dict if a face is found:
            embedding  : list[float] — 512-d L2-normalised ArcFace vector
            bbox       : tuple(x1, y1, x2, y2)
            det_score  : float — RetinaFace detection confidence (0–1)
            landmarks  : np.ndarray shape (5, 2) — 5 facial keypoints

        Returns None if no face detected or face too small.
        """
        faces = self._app.get(frame_bgr)

        if not faces:
            return None

        # If multiple faces detected — take the largest one
        # (most likely the person standing at the door)
        face = max(faces, key=lambda f: self._face_area(f.bbox))

        # Reject faces that are too small — too far from camera
        area = self._face_area(face.bbox)
        min_area = settings.min_face_size ** 2
        if area < min_area:
            return None

        bbox = tuple(face.bbox.astype(int))   # (x1, y1, x2, y2)

        return {
            "embedding":  face.normed_embedding.tolist(),   # already L2-normalised
            "bbox":       bbox,
            "det_score":  float(face.det_score),
            "landmarks":  face.kps,                          # 5-point keypoints
        }

    def process_batch(self, frames: list[np.ndarray]) -> list[list[float]] | None:
        """
        Process a batch of frames and return list of embeddings.
        Used by FrameAggregator to collect N embeddings.
        Returns None if any frame has no face.
        """
        embeddings = []
        for frame in frames:
            result = self.process(frame)
            if result is None:
                return None
            embeddings.append(result["embedding"])
        return embeddings

    @staticmethod
    def _face_area(bbox) -> float:
        """Compute bounding box area."""
        return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])