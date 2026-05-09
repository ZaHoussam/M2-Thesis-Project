# ================================================================
#  core/frame_aggregator.py — multi-frame embedding averager
#
#  Buffers N embeddings from FacePipeline and returns
#  a single stable averaged + L2-normalised vector.
# ================================================================
import numpy as np
from collections import deque


class FrameAggregator:
    """
    Buffers N embeddings and returns their L2-normalised average.

    Since InsightFace already returns L2-normalised embeddings,
    averaging then re-normalising gives a stable canonical vector
    that represents the face across N frames of natural movement.
    """

    def __init__(self, n_frames: int = 7):
        self.n_frames = n_frames
        self._buffer  = deque(maxlen=n_frames)

    def push(self, embedding: list[float]):
        self._buffer.append(embedding)

    def is_ready(self) -> bool:
        return len(self._buffer) == self.n_frames

    def get_aggregate(self) -> list[float]:
        if not self.is_ready():
            raise RuntimeError("Not enough frames buffered.")

        matrix   = np.array(self._buffer, dtype=np.float32)
        mean_vec = matrix.mean(axis=0)

        # Re-normalise after averaging
        norm = np.linalg.norm(mean_vec)
        if norm > 0:
            mean_vec = mean_vec / norm

        self._buffer.clear()
        return mean_vec.tolist()

    def clear(self):
        self._buffer.clear()

    @property
    def progress(self) -> int:
        return len(self._buffer)