# ================================================================
#  client/enroll.py — Interactive face enrollment script
#  Updated for InsightFace (RetinaFace + ArcFace)
#
#  Run with: python enroll.py
# ================================================================
import asyncio
import cv2
import httpx

from core.camera   import Camera
from core.embedder import FacePipeline
from core.display  import draw_frame
from config        import settings

ANGLES = ["front", "left", "right", "up", "low_light"]


def prompt_user_info(angle: str) -> dict | None:
    """Ask for user details in the terminal."""
    print("\n" + "="*50)
    print(f"  Enrolling angle: [{angle}]")
    print("="*50)

    full_name = input("  Full name       : ").strip()
    if not full_name:
        print("  [ERROR] Name cannot be empty.")
        return None

    email = input("  Email           : ").strip()
    if not email:
        print("  [ERROR] Email cannot be empty.")
        return None

    role = input("  Role [researcher]: ").strip() or "researcher"

    return {
        "full_name":   full_name,
        "email":       email,
        "role":        role,
        "angle_label": angle,
    }


async def send_enrollment(user_info: dict, embedding: list[float]):
    payload = {**user_info, "embedding": embedding}
    async with httpx.AsyncClient(timeout=15) as client:
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


async def add_angle(user_id: int, user_info: dict, embedding: list[float]):
    payload = {**user_info, "embedding": embedding}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.server_rest_url}/enroll/{user_id}/add-angle",
            json=payload,
        )
        print(f"\n  [DEBUG] HTTP status : {resp.status_code}")
        print(f"  [DEBUG] Raw response: {resp.text[:300]}")
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"detail": resp.text or "Empty response"}


async def run_enrollment():
    camera   = Camera()
    pipeline = FacePipeline()     # single InsightFace instance

    print("\n" + "="*50)
    print("  LAB ACCESS — FACE ENROLLMENT (InsightFace)")
    print("="*50)
    print("  SPACE  → capture current frame")
    print("  R      → retake")
    print("  Q      → quit\n")

    # Choose angle
    print("  Available angles:")
    for i, a in enumerate(ANGLES):
        print(f"    [{i+1}] {a}")
    choice = input("\n  Select angle (1-5) [1=front]: ").strip() or "1"
    angle  = ANGLES[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= 5 else "front"

    cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Enrollment", 640, 520)

    captured_embedding = None

    print(f"\n  [CAMERA] Opened. Align your face and press SPACE to capture.")

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        # Run InsightFace pipeline on every frame for live preview
        result    = pipeline.process(frame)
        bbox      = result["bbox"]      if result else None
        det_score = result["det_score"] if result else None

        display_state = "ALLOW" if captured_embedding else "SCANNING"

        rendered = draw_frame(
            frame     = frame,
            bbox      = bbox,
            state     = display_state,
            score     = det_score,
            user_name = "Captured! — fill details below" if captured_embedding else "Press SPACE to capture",
        )

        # Detection confidence overlay
        if det_score is not None:
            cv2.putText(rendered,
                        f"det: {det_score:.2f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (29, 158, 117), 2, cv2.LINE_AA)

        hint = f"Angle: {angle}  |  SPACE=capture  R=retake  Q=quit"
        cv2.putText(rendered, hint,
                    (10, rendered.shape[0] - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                    (160, 160, 160), 1, cv2.LINE_AA)

        cv2.imshow("Enrollment", rendered)
        key = cv2.waitKey(1) & 0xFF

        # ── SPACE — capture ──────────────────────────────────────
        if key == ord(' '):
            if result is None:
                print("  [WARN] No face detected — move closer or improve lighting.")
                continue

            # InsightFace gives us the embedding directly
            # detection + alignment + embedding all in one call
            captured_embedding = result["embedding"]
            print(f"  [OK] Face captured. det_score={result['det_score']:.3f}")
            print("  Fill in details in the terminal below...")

            cv2.destroyWindow("Enrollment")

            user_info = prompt_user_info(angle)
            if user_info is None:
                print("  [ERROR] Invalid input — retrying.")
                captured_embedding = None
                cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Enrollment", 640, 520)
                continue

            print("\n  Is this a new user or adding an angle to existing?")
            print("  [1] New user (first enrollment)")
            print("  [2] Add angle to existing user")
            reg_choice = input("  Choice [1]: ").strip() or "1"

            if reg_choice == "2":
                user_id = input("  Enter existing user ID: ").strip()
                if not user_id.isdigit():
                    print("  [ERROR] Invalid user ID.")
                    captured_embedding = None
                    cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
                    cv2.resizeWindow("Enrollment", 640, 520)
                    continue
                print("\n  [SENDING] Adding angle to server...")
                code, res = await add_angle(int(user_id), user_info, captured_embedding)
            else:
                print("\n  [SENDING] Enrolling new user to server...")
                code, res = await send_enrollment(user_info, captured_embedding)

            print("\n" + "="*50)
            if code in (200, 201):
                print(f"  ✅ SUCCESS")
                print(f"     User ID   : {res.get('user_id')}")
                print(f"     Name      : {res.get('full_name')}")
                print(f"     Message   : {res.get('message')}")
            else:
                print(f"  ❌ FAILED  (HTTP {code})")
                print(f"     Detail    : {res.get('detail', res)}")
            print("="*50)

            another = input("\n  Enroll another angle? (y/n) [n]: ").strip().lower()
            if another == "y":
                captured_embedding = None
                print("\n  Available angles:")
                for i, a in enumerate(ANGLES):
                    print(f"    [{i+1}] {a}")
                choice = input("  Select angle (1-5): ").strip()
                angle  = ANGLES[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= 5 else "front"
                cv2.namedWindow("Enrollment", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Enrollment", 640, 520)
                print(f"\n  [CAMERA] Re-opened for [{angle}]. Press SPACE to capture.")
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
    print("\n  [ENROLLMENT] Done. Goodbye.")


if __name__ == "__main__":
    asyncio.run(run_enrollment())