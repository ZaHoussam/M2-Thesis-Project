# ================================================================
#  client/main.py — Entry point
#  Camera + InsightFace → separate process
#  Display + WebSocket  → main process
# ================================================================
import asyncio
import threading
import multiprocessing
from multiprocessing import Queue

import cv2
import numpy as np

from core.camera_process import camera_worker
from core.ws_client      import AuthClient
from core.display        import draw_frame


N_FRAMES = 3


class AppState:
    def __init__(self):
        self.state     = "SCANNING"
        self.score     = None
        self.user_name = None


def show_loading_screen():
    """Show loading screen before camera process starts."""
    cv2.namedWindow("Lab Access Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lab Access Control", 560, 260)
    canvas = np.zeros((260, 560, 3), dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (560, 4), (29, 158, 117), -1)
    cv2.putText(canvas, "Starting camera...",
                (40, 110), cv2.FONT_HERSHEY_DUPLEX,
                0.85, (29, 158, 117), 2, cv2.LINE_AA)
    cv2.putText(canvas, "Loading RetinaFace + ArcFace  |  Please wait",
                (40, 155), cv2.FONT_HERSHEY_SIMPLEX,
                0.48, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.imshow("Lab Access Control", canvas)
    cv2.waitKey(1)


def bridge_thread_fn(
    mp_queue:      Queue,
    asyncio_queue: asyncio.Queue,
    loop:          asyncio.AbstractEventLoop,
):
    """
    Moves embeddings from multiprocessing.Queue to asyncio.Queue.
    If asyncio.Queue is full — drain it first then insert latest.
    We always want the newest embedding, never a stale one.
    """
    while True:
        try:
            data = mp_queue.get(timeout=1)

            def safe_put(d=data):
                # Drain queue if full — drop old, keep latest
                while asyncio_queue.full():
                    try:
                        asyncio_queue.get_nowait()
                    except Exception:
                        break
                try:
                    asyncio_queue.put_nowait(d)
                except Exception:
                    pass

            loop.call_soon_threadsafe(safe_put)

        except Exception:
            continue


async def display_loop(
    frame_queue:   Queue,
    asyncio_embed: asyncio.Queue,
    state:         AppState,
    client:        AuthClient,
):
    """
    Runs in main process asyncio loop.
    Pulls frames from camera process and shows them.
    Also drives the auth client.
    """
    cv2.namedWindow("Lab Access Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lab Access Control", 640, 480)

    while True:
        # ── Pull latest frame from camera process ─────────────
        frame_data = None
        while not frame_queue.empty():
            try:
                frame_data = frame_queue.get_nowait()
            except Exception:
                break

        if frame_data is not None:
            frame    = frame_data["frame"]
            bbox     = frame_data["bbox"]
            progress = frame_data["progress"]

            display_score = (progress / N_FRAMES) if state.state == "SCANNING" else state.score

            rendered = draw_frame(
                frame     = frame,
                bbox      = bbox,
                state     = state.state,
                score     = display_score,
                user_name = state.user_name,
                pin_len   = 0,
            )

            if state.state == "SCANNING" and bbox and progress > 0:
                cv2.putText(rendered,
                            f"Buffering: {progress}/{N_FRAMES}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (29, 158, 117), 2, cv2.LINE_AA)

            cv2.imshow("Lab Access Control", rendered)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        await asyncio.sleep(0.03)

    cv2.destroyAllWindows()


async def auth_task(asyncio_embed: asyncio.Queue, state: AppState, state_queue: Queue):
    """Handles WebSocket communication."""
    client = AuthClient(state_queue)

    while True:
        try:
            async with __import__('websockets').connect(
                __import__('os').environ.get('SERVER_WS_URL', 'ws://localhost:8000/ws/verify')
            ) as ws:
                print("[CLIENT] Connected.")
                import json
                while True:
                    if state.state == "SCANNING":
                        data = await asyncio_embed.get()
                        embedding = data["embedding"]

                        await ws.send(json.dumps({
                            "embedding": embedding,
                            "lab_id":    1,
                            "det_score": data.get("det_score"),
                        }))

                        response = json.loads(await ws.recv())
                        decision = response.get("decision")
                        score    = response.get("similarity_score")

                        print(f"[AUTH] {decision} score={score} margin={response.get('margin')}")

                        state.score = score

                        if decision == "ALLOW":
                            state.state     = "ALLOW"
                            state.user_name = response.get("user_name")
                            await asyncio.sleep(2.5)
                            state.state     = "SCANNING"
                            state.user_name = None
                            state.score     = None

                        elif decision == "DENY":
                            state.state = "DENY"
                            await asyncio.sleep(1.5)
                            state.state     = "SCANNING"
                            state.user_name = None
                            state.score     = None
                    else:
                        await asyncio.sleep(0.05)

        except Exception as e:
            print(f"[CLIENT] {e} — retrying in 3s...")
            state.state = "SCANNING"
            await asyncio.sleep(3)


async def main_async(frame_queue: Queue, embedding_mp_queue: Queue):
    state         = AppState()
    asyncio_embed = asyncio.Queue(maxsize=1)
    state_queue   = Queue(maxsize=2)

    loop = asyncio.get_event_loop()

    # Bridge thread — mp.Queue → asyncio.Queue
    t = threading.Thread(
        target = bridge_thread_fn,
        args   = (embedding_mp_queue, asyncio_embed, loop),
        daemon = True,
    )
    t.start()

    # Run display + auth concurrently
    await asyncio.gather(
        display_loop(frame_queue, asyncio_embed, state, None),
        auth_task(asyncio_embed, state, state_queue),
    )


def main():
    multiprocessing.freeze_support()

    # Queues
    embedding_queue = Queue(maxsize=2)
    frame_queue     = Queue(maxsize=2)

    # Show loading screen before spawning
    show_loading_screen()

    # Spawn camera process
    cam = multiprocessing.Process(
        target = camera_worker,
        args   = (embedding_queue, frame_queue, 0),
        daemon = True,
    )
    cam.start()
    print("[MAIN] Camera process started.")

    try:
        asyncio.run(main_async(frame_queue, embedding_queue))
    except KeyboardInterrupt:
        print("\n[MAIN] Stopping...")
    finally:
        cam.terminate()
        cam.join()
        print("[MAIN] Done.")


if __name__ == "__main__":
    main()