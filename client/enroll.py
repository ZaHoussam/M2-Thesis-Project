# ================================================================
#  client/enroll.py — Face enrollment script
#  One embedding per person — no multiple angles
# ================================================================
import asyncio
import cv2
import httpx

from core.camera   import Camera
from core.embedder import FacePipeline
from core.display  import draw_frame
from config        import settings


async def send_enrollment(user_info: dict, embedding: list[float]):
    payload = {**user_info, "embedding": embedding}
    # New — separate timeouts for connect vs read
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect = 10.0,   # max time to establish connection
            read    = 60.0,   # max time to wait for server response
            write   = 30.0,   # max time to send the request body
            pool    = 10.0,
        )
    ) as client:
            resp = await client.post(
                f"{settings.server_rest_url}/enroll",
                json=payload,
            )
            print(f"\n  [DEBUG] HTTP status : {resp.status_code}")
            print(f"  [DEBUG] Raw response: {resp.text[:300]}")
            try:
                return resp.status_code, resp.json()
            except Exception:
                return resp.status_code, {"detail": resp.text or "Empty response"}


def prompt_user_info() -> dict | None:
    print("\n" + "="*50)
    print("  NEW USER ENROLLMENT")
    print("="*50)

    full_name = input("  Full name : ").strip()
    if not full_name:
        print("  [ERROR] Name cannot be empty.")
        return None

    email = input("  Email     : ").strip()
    if not email:
        print("  [ERROR] Email cannot be empty.")
        return None

    role = input("  Role [researcher]: ").strip() or "researcher"

    return {
        "full_name": full_name,
        "email":     email,
        "role":      role,
    }


async def run_enrollment():
    camera   = Camera()
    pipeline = FacePipeline()

    print("\n" + "="*50)
    print("  LAB ACCESS — FACE ENROLLMENT")
    print("="*50)
    print("  SPACE → capture face")
    print("  R     → retake")
    print("  Q     → quit\n")

    cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Enrollment", 640, 520)

    captured_embedding = None

    print("  [CAMERA] Align your face and press SPACE to capture.")

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        result    = pipeline.process(frame)
        bbox      = result["bbox"]      if result else None
        det_score = result["det_score"] if result else None

        rendered = draw_frame(
            frame     = frame,
            bbox      = bbox,
            state     = "ALLOW" if captured_embedding else "SCANNING",
            score     = det_score,
            user_name = "Captured!" if captured_embedding else "Press SPACE to capture",
        )

        if det_score is not None:
            cv2.putText(rendered,
                        f"det: {det_score:.2f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (29, 158, 117), 2, cv2.LINE_AA)

        cv2.putText(rendered,
                    "SPACE=capture  R=retake  Q=quit",
                    (10, rendered.shape[0] - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.38, (160, 160, 160), 1, cv2.LINE_AA)

        cv2.imshow("Enrollment", rendered)
        key = cv2.waitKey(1) & 0xFF

        # ── SPACE — capture ──────────────────────────────────────
        if key == ord(' '):
            if result is None:
                print("  [WARN] No face detected — move closer.")
                continue

            captured_embedding = result["embedding"]
            print(f"  [OK] Face captured. det_score={result['det_score']:.3f}")
            print("  Fill in details below...")

            cv2.destroyWindow("Enrollment")

            user_info = prompt_user_info()
            if user_info is None:
                captured_embedding = None
                cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Enrollment", 640, 520)
                continue

            print("\n  [SENDING] Enrolling to server...")
            code, res = await send_enrollment(user_info, captured_embedding)

            print("\n" + "="*50)
            if code in (200, 201):
                print(f"  ✅ SUCCESS")
                print(f"     User ID : {res.get('user_id')}")
                print(f"     Name    : {res.get('full_name')}")
                print(f"     Message : {res.get('message')}")
            else:
                print(f"  ❌ FAILED (HTTP {code})")
                print(f"     Detail  : {res.get('detail', res)}")
            print("="*50)

            another = input("\n  Enroll another person? (y/n) [n]: ").strip().lower()
            if another == "y":
                captured_embedding = None
                cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Enrollment", 640, 520)
                print("\n  [CAMERA] Ready. Press SPACE to capture.")
            else:
                break

        # ── R — retake ───────────────────────────────────────────
        elif key == ord('r'):
            captured_embedding = None
            print("  [INFO] Retake — last capture discarded.")

        # ── Q — quit ─────────────────────────────────────────────
        elif key == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
    print("\n  [ENROLLMENT] Done.")


if __name__ == "__main__":
    asyncio.run(run_enrollment())