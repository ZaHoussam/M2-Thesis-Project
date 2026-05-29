# ================================================================
#  core/camera_process.py — Camera + InsightFace + AntiSpoof
# ================================================================
import cv2
import numpy as np
from multiprocessing import Queue

from core.camera           import Camera
from core.embedder         import FacePipeline
from core.detector         import is_sharp
from core.frame_aggregator import FrameAggregator
from core.antispoof        import AntiSpoofDetector   # ← new

N_FRAMES = 3


def camera_worker(
    embedding_queue: Queue,
    frame_queue:     Queue,
    camera_index:    int = 0,
):
    print("[CAM PROCESS] Loading models...")
    pipeline    = FacePipeline()
    antispoof   = AntiSpoofDetector()                 # ← new
    camera      = Camera()
    aggregator  = FrameAggregator(n_frames=N_FRAMES)
    print("[CAM PROCESS] Ready.")

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        bbox      = None
        progress  = 0
        is_spoof  = False                             # ← new

        if is_sharp(frame):
            result = pipeline.process(frame)

            if result is not None:
                bbox = result["bbox"]
                crop = frame[
                    bbox[1]:bbox[3],
                    bbox[0]:bbox[2]
                ]

                # ── Anti-spoof check ──────────────────────────
                spoof_result = antispoof.predict(crop)
                is_spoof     = not spoof_result["is_real"]

                if is_spoof:
                    # Send spoof signal — do NOT embed
                    if embedding_queue.empty():
                        try:
                            embedding_queue.put_nowait({
                                "embedding":  None,
                                "bbox":       bbox,
                                "det_score":  float(result["det_score"]),
                                "is_spoof":   True,
                                "spoof_prob": spoof_result["spoof_prob"],
                                "real_prob":  spoof_result["real_prob"],
                            })
                        except Exception:
                            pass
                else:
                    # Real face — aggregate and embed
                    aggregator.push(result["embedding"])
                    progress = aggregator.progress

                    if aggregator.is_ready():
                        if embedding_queue.empty():
                            try:
                                embedding_queue.put_nowait({
                                    "embedding":  aggregator.get_aggregate(),
                                    "bbox":       bbox,
                                    "det_score":  float(result["det_score"]),
                                    "is_spoof":   False,
                                    "spoof_prob": spoof_result["spoof_prob"],
                                    "real_prob":  spoof_result["real_prob"],
                                })
                            except Exception:
                                pass
            else:
                aggregator.clear()

        # Send frame for display
        small = cv2.resize(frame, (640, 480))
        try:
            if frame_queue.empty():
                frame_queue.put_nowait({
                    "frame":    small,
                    "bbox":     bbox,
                    "progress": progress,
                    "is_spoof": is_spoof, 
                })
        except Exception:
            pass

    camera.release()