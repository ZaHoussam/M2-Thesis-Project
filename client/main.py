# ================================================================
#  client/main.py — Entry point
#  Camera + InsightFace + AntiSpoof → separate process
#  Display + WebSocket              → main process
# ================================================================
import asyncio
import threading
import multiprocessing
from multiprocessing import Queue
import json
import os

import cv2
import numpy as np

from core.camera_process import camera_worker
from core.display        import draw_frame
from config              import settings


N_FRAMES = 3


class AppState:
    def __init__(self):
        self.state     = "SCANNING"
        self.score     = None
        self.user_name = None
        self.is_spoof  = False        # ← new


def show_loading_screen():
    cv2.namedWindow("Lab Access Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lab Access Control", 560, 260)
    canvas = np.zeros((260, 560, 3), dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (560, 4), (29, 158, 117), -1)
    cv2.putText(canvas, "Starting camera...",
                (40, 110), cv2.FONT_HERSHEY_DUPLEX,
                0.85, (29, 158, 117), 2, cv2.LINE_AA)
    cv2.putText(canvas, "Loading RetinaFace + ArcFace + AntiSpoof  |  Please wait",
                (40, 155), cv2.FONT_HERSHEY_SIMPLEX,
                0.45, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.imshow("Lab Access Control", canvas)
    cv2.waitKey(1)


def bridge_thread_fn(
    mp_queue:      Queue,
    asyncio_queue: asyncio.Queue,
    loop:          asyncio.AbstractEventLoop,
):
    while True:
        try:
            data = mp_queue.get(timeout=1)

            def safe_put(d=data):
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
    state:         AppState,
):
    cv2.namedWindow("Lab Access Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Lab Access Control", 640, 480)

    while True:
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
            is_spoof = frame_data.get("is_spoof", False)

            # Use SPOOF state if camera process detected spoof
            display_state = "DENY" if is_spoof else state.state
            display_score = (
                (progress / N_FRAMES)
                if state.state == "SCANNING" and not is_spoof
                else state.score
            )

            rendered = draw_frame(
                frame     = frame,
                bbox      = bbox,
                state     = display_state,
                score     = display_score,
                user_name = state.user_name,
                pin_len   = 0,
            )

            # Buffering counter
            if state.state == "SCANNING" and bbox and progress > 0 and not is_spoof:
                cv2.putText(rendered,
                            f"Buffering: {progress}/{N_FRAMES}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (29, 158, 117), 2, cv2.LINE_AA)

            # Spoof warning overlay
            if is_spoof:
                overlay = rendered.copy()
                cv2.rectangle(overlay, (0, 0), (rendered.shape[1], rendered.shape[0]),
                              (0, 0, 200), -1)
                cv2.addWeighted(overlay, 0.25, rendered, 0.75, 0, rendered)
                cv2.putText(rendered,
                            "⚠ SPOOF DETECTED",
                            (10, 40),
                            cv2.FONT_HERSHEY_DUPLEX,
                            0.9, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.putText(rendered,
                            "Presentation attack blocked",
                            (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (100, 100, 255), 1, cv2.LINE_AA)

            cv2.imshow("Lab Access Control", rendered)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        await asyncio.sleep(0.03)

    cv2.destroyAllWindows()


async def auth_task(
    asyncio_embed: asyncio.Queue,
    state:         AppState,
):
    while True:
        try:
            async with __import__('websockets').connect(
                settings.server_ws_url
            ) as ws:
                print("[CLIENT] Connected.")

                while True:
                    if state.state == "SCANNING":
                        data = await asyncio_embed.get()

                        # ── Spoof detected ────────────────────
                        if data.get("is_spoof"):
                            spoof_prob = data.get("spoof_prob", 0.0)
                            print(
                                f"[SPOOF] 🚨 Presentation attack detected! "
                                f"spoof_prob={spoof_prob:.3f}"
                            )
                            state.state    = "DENY"
                            state.is_spoof = True
                            state.score    = None

                            await ws.send(json.dumps({
                                "embedding":  None,
                                "lab_id":     settings.lab_id,
                                "is_spoof":   True,
                                "spoof_prob": spoof_prob,
                                "det_score":  data.get("det_score"),
                            }))

                            await ws.recv()   # consume server response
                            await asyncio.sleep(2.0)

                            state.state    = "SCANNING"
                            state.is_spoof = False
                            continue

                        # ── Real face — normal auth ───────────
                        embedding = data.get("embedding")
                        if embedding is None:
                            continue

                        await ws.send(json.dumps({
                            "embedding":  embedding,
                            "lab_id":     settings.lab_id,
                            "is_spoof":   False,
                            "det_score":  data.get("det_score"),
                            "spoof_prob": data.get("spoof_prob"),
                        }))

                        response = json.loads(await ws.recv())
                        decision = response.get("decision")
                        score    = response.get("similarity_score")

                        print(
                            f"[AUTH] {decision} "
                            f"score={score} "
                            f"margin={response.get('margin')}"
                        )

                        state.score    = score
                        state.is_spoof = False

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
            state.state    = "SCANNING"
            state.is_spoof = False
            await asyncio.sleep(3)


async def main_async(frame_queue: Queue, embedding_mp_queue: Queue):
    state         = AppState()
    asyncio_embed = asyncio.Queue(maxsize=1)

    loop = asyncio.get_event_loop()

    # Bridge thread — mp.Queue → asyncio.Queue
    threading.Thread(
        target = bridge_thread_fn,
        args   = (embedding_mp_queue, asyncio_embed, loop),
        daemon = True,
    ).start()

    # Run display + auth concurrently
    await asyncio.gather(
        display_loop(frame_queue, state),
        auth_task(asyncio_embed, state),
    )


def main():
    multiprocessing.freeze_support()

    embedding_queue = Queue(maxsize=2)
    frame_queue     = Queue(maxsize=2)

    show_loading_screen()

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