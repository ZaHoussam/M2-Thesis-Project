# ================================================================
#  core/camera_process.py — Camera + InsightFace worker process
#  No display here — sends frames and embeddings to main process
# ================================================================
import cv2
import numpy as np
from multiprocessing import Queue

from core.camera           import Camera
from core.embedder         import FacePipeline
from core.detector         import is_sharp
from core.frame_aggregator import FrameAggregator

N_FRAMES = 3


def camera_worker(
    embedding_queue: Queue,   # OUT — stable embeddings → main
    frame_queue:     Queue,   # OUT — raw frames → main for display
    camera_index:    int = 0,
):
    """
    Runs in its own process.
    Tight synchronous loop — no asyncio, no display.
    """
    print("[CAM PROCESS] Loading models...")
    pipeline   = FacePipeline()
    camera     = Camera()
    aggregator = FrameAggregator(n_frames=N_FRAMES)
    print("[CAM PROCESS] Ready — reading frames.")

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        bbox      = None
        progress  = 0

        # Sharpness gate
        if is_sharp(frame):
            result = pipeline.process(frame)

            if result is not None:
                bbox = result["bbox"]
                aggregator.push(result["embedding"])
                progress = aggregator.progress

                if aggregator.is_ready():
                    if embedding_queue.empty():
                        try:
                            embedding_queue.put_nowait({
                                "embedding": aggregator.get_aggregate(),
                                "bbox":      bbox,
                            })
                        except Exception:
                            pass
            else:
                aggregator.clear()

        # Send frame + metadata to main process for display
        # Resize frame before sending to reduce Queue bandwidth
        small = cv2.resize(frame, (640, 480))
        try:
            if frame_queue.empty():
                frame_queue.put_nowait({
                    "frame":    small,
                    "bbox":     bbox,
                    "progress": progress,
                })
        except Exception:
            pass

    camera.release()