# ================================================================
#  client/main.py — Entry point (InsightFace version)
# ================================================================
import asyncio
import cv2

from core.camera          import Camera
from core.embedder        import FacePipeline
from core.detector        import is_sharp
from core.frame_aggregator import FrameAggregator
from core.ws_client       import AuthClient
from core.display         import draw_frame

N_FRAMES = 7   # frames to average per decision


class AppState:
    def __init__(self):
        self.state     = "SCANNING"
        self.score     = None
        self.user_name = None
        self.bbox      = None
        self.pin_len   = 0


async def camera_loop(queue: asyncio.Queue, state: AppState):
    camera      = Camera()
    pipeline    = FacePipeline()     # single InsightFace instance
    aggregator  = FrameAggregator(n_frames=N_FRAMES)

    print(f"[CAMERA] Started. Aggregating {N_FRAMES} frames. Press Q to quit.")
    cv2.namedWindow("Lab Access Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lab Access Control", 640, 520)

    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                await asyncio.sleep(0.03)
                continue

            # Sharpness gate — skip blurry frames entirely
            if not is_sharp(frame):
                state.bbox = None
                await asyncio.sleep(0.03)
                continue

            # Run detection + alignment + embedding
            result = pipeline.process(frame)

            if result is not None:
                state.bbox = result["bbox"]

                if state.state == "SCANNING":
                    aggregator.push(result["embedding"])

                    if aggregator.is_ready() and queue.empty():
                        stable = aggregator.get_aggregate()
                        await queue.put(stable)

            else:
                # No face — reset aggregator
                if state.state == "SCANNING":
                    aggregator.clear()
                state.bbox = None

            # Build display score
            if state.state == "SCANNING" and result:
                display_score = aggregator.progress / N_FRAMES
            else:
                display_score = state.score

            rendered = draw_frame(
                frame     = frame,
                bbox      = state.bbox,
                state     = state.state,
                score     = display_score,
                user_name = state.user_name,
                pin_len   = state.pin_len,
            )

            if state.state == "SCANNING" and result:
                cv2.putText(rendered,
                            f"Buffering: {aggregator.progress}/{N_FRAMES}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (29, 158, 117), 2, cv2.LINE_AA)

            cv2.imshow("Lab Access Control", rendered)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            await asyncio.sleep(0.03)

    finally:
        camera.release()
        cv2.destroyAllWindows()


async def main():
    queue  = asyncio.Queue(maxsize=1)
    state  = AppState()
    client = AuthClient(state)

    await asyncio.gather(
        camera_loop(queue, state),
        client.run(queue),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[CLIENT] Stopped.")