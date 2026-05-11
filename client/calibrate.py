# ================================================================
#  client/calibrate.py — Threshold calibration data collector
#
#  Run with: python calibrate.py
#
#  What it does:
#    1. Opens camera
#    2. Authenticates against the server N times
#    3. You tell it whether each person is genuine or impostor
#    4. Saves scores to calibration_data/scores.json
#    5. Runs analysis and recommends optimal threshold
# ================================================================
import asyncio
import json
import os
import cv2
import httpx
import numpy as np
import websockets

from core.camera           import Camera
from core.embedder         import FacePipeline
from core.detector         import is_sharp
from core.frame_aggregator import FrameAggregator
from config                import settings

OUTPUT_DIR  = "calibration_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scores.json")
N_FRAMES    = 3


def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_existing() -> dict:
    if os.path.isfile(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {"genuine": [], "impostor": []}


def save_scores(data: dict):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def capture_embedding(camera, pipeline, aggregator) -> list[float] | None:
    """
    Capture N frames from camera and return averaged embedding.
    Returns None if face not found.
    """
    aggregator.clear()
    print("  Look at the camera...")

    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        if not is_sharp(frame):
            continue

        result = pipeline.process(frame)

        if result is not None:
            aggregator.push(result["embedding"])
            progress = aggregator.progress

            # Draw progress on frame
            display = frame.copy()
            cv2.putText(display,
                        f"Buffering: {progress}/{N_FRAMES}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (29, 158, 117), 2)

            # Draw bbox
            bbox = result["bbox"]
            cv2.rectangle(display,
                          (bbox[0], bbox[1]),
                          (bbox[2], bbox[3]),
                          (29, 158, 117), 2)

            cv2.imshow("Calibration", display)

            if aggregator.is_ready():
                cv2.waitKey(1)
                return aggregator.get_aggregate()
        else:
            display = frame.copy()
            cv2.putText(display, "No face — move closer",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (100, 100, 255), 2)
            cv2.imshow("Calibration", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return None


async def get_score_from_server(embedding: list[float]) -> float | None:
    """Send embedding to server via WebSocket and get score back."""
    try:
        async with websockets.connect(
            settings.server_ws_url,
            open_timeout=5
        ) as ws:
            await ws.send(json.dumps({
                "embedding": embedding,
                "lab_id":    settings.lab_id,
            }))
            response = json.loads(await ws.recv())
            return response.get("similarity_score")
    except Exception as e:
        print(f"  [ERROR] Server connection failed: {e}")
        return None


def analyze_scores(data: dict) -> dict:
    """
    Compute FAR, FRR, accuracy at each threshold.
    Find optimal threshold at EER point.
    """
    genuine  = data["genuine"]
    impostor = data["impostor"]

    if not genuine or not impostor:
        return {}

    results = []

    # Test every threshold from 0.10 to 0.99
    for t in [x / 100 for x in range(10, 100)]:
        t = round(t, 2)

        # FAR — impostors that score ABOVE threshold (wrongly allowed)
        fa  = sum(1 for s in impostor if s > t)
        far = fa / len(impostor)

        # FRR — genuine users that score BELOW threshold (wrongly denied)
        fr  = sum(1 for s in genuine if s <= t)
        frr = fr / len(genuine)

        # Accuracy
        correct = sum(1 for s in genuine  if s > t) + \
                  sum(1 for s in impostor if s <= t)
        total   = len(genuine) + len(impostor)
        acc     = correct / total

        results.append({
            "threshold": t,
            "far":       round(far, 4),
            "frr":       round(frr, 4),
            "accuracy":  round(acc, 4),
            "eer_diff":  round(abs(far - frr), 4),
        })

    # Find EER — minimum difference between FAR and FRR
    eer_point = min(results, key=lambda x: x["eer_diff"])

    # Find best accuracy
    best_acc  = max(results, key=lambda x: x["accuracy"])

    return {
        "results":         results,
        "eer_threshold":   eer_point["threshold"],
        "eer_far":         eer_point["far"],
        "eer_frr":         eer_point["frr"],
        "best_acc_threshold": best_acc["threshold"],
        "best_accuracy":   best_acc["accuracy"],
        "genuine_mean":    round(float(np.mean(genuine)), 4),
        "genuine_std":     round(float(np.std(genuine)),  4),
        "impostor_mean":   round(float(np.mean(impostor)), 4),
        "impostor_std":    round(float(np.std(impostor)),  4),
    }


def print_report(analysis: dict, data: dict):
    """Print a clean calibration report to terminal."""
    print("\n" + "="*60)
    print("  THRESHOLD CALIBRATION REPORT")
    print("="*60)

    print(f"\n  Dataset:")
    print(f"    Genuine  samples : {len(data['genuine'])}")
    print(f"    Impostor samples : {len(data['impostor'])}")

    print(f"\n  Score distributions:")
    print(f"    Genuine  mean ± std : {analysis['genuine_mean']} ± {analysis['genuine_std']}")
    print(f"    Impostor mean ± std : {analysis['impostor_mean']} ± {analysis['impostor_std']}")
    gap = round(analysis['genuine_mean'] - analysis['impostor_mean'], 4)
    print(f"    Separation gap      : {gap}")

    print(f"\n  Threshold analysis (sample):")
    print(f"  {'Threshold':>10} | {'FAR':>8} | {'FRR':>8} | {'Accuracy':>10}")
    print(f"  {'-'*46}")

    results = analysis["results"]
    # Print every 5th threshold for readability
    for r in results[::5]:
        marker = " ← EER" if r["threshold"] == analysis["eer_threshold"] else ""
        print(f"  {r['threshold']:>10.2f} | "
              f"{r['far']:>8.4f} | "
              f"{r['frr']:>8.4f} | "
              f"{r['accuracy']:>10.4f}{marker}")

    print(f"\n  {'='*46}")
    print(f"  EER threshold    : {analysis['eer_threshold']}")
    print(f"  EER FAR / FRR    : {analysis['eer_far']} / {analysis['eer_frr']}")
    print(f"  Best accuracy    : {analysis['best_accuracy']*100:.1f}%"
          f"  at threshold {analysis['best_acc_threshold']}")

    print(f"\n  ✅ RECOMMENDED THRESHOLD: {analysis['eer_threshold']}")
    print(f"\n  Update your server/.env:")
    print(f"    THRESHOLD_ALLOW={analysis['eer_threshold']}")
    print("="*60 + "\n")


async def run_calibration():
    ensure_dir()
    data = load_existing()

    print("\n" + "="*60)
    print("  THRESHOLD CALIBRATION")
    print("="*60)
    print(f"  Genuine scores collected : {len(data['genuine'])}")
    print(f"  Impostor scores collected: {len(data['impostor'])}")
    print(f"\n  Collect at least:")
    print(f"    20 genuine  (registered users)")
    print(f"    20 impostor (unregistered people)\n")

    camera     = Camera()
    pipeline   = FacePipeline()
    aggregator = FrameAggregator(n_frames=N_FRAMES)

    cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Calibration", 640, 480)

    while True:
        print("\n" + "-"*60)
        print("  Options:")
        print("  [1] Collect GENUINE score (registered user)")
        print("  [2] Collect IMPOSTOR score (unregistered person)")
        print("  [3] Run analysis + show report")
        print("  [4] Save report to file and quit")
        print("-"*60)
        choice = input("  Choice: ").strip()

        if choice in ("1", "2"):
            label = "genuine" if choice == "1" else "impostor"
            name  = input(f"  Person name (for notes): ").strip() or "unknown"

            print(f"\n  Collecting {label} score for [{name}]...")
            embedding = capture_embedding(camera, pipeline, aggregator)

            if embedding is None:
                print("  [WARN] No embedding captured — skipped.")
                continue

            print("  Getting score from server...")
            score = await get_score_from_server(embedding)

            if score is None:
                print("  [ERROR] No score returned — is server running?")
                continue

            data[label].append(score)
            save_scores(data)

            verdict = "✅ ALLOW" if score > 0.50 else "❌ DENY"
            print(f"\n  Score : {score:.4f}  →  {verdict}")
            print(f"  Total {label} scores: {len(data[label])}")

        elif choice == "3":
            if len(data["genuine"]) < 5 or len(data["impostor"]) < 5:
                print("  [WARN] Need at least 5 genuine + 5 impostor scores.")
                continue
            analysis = analyze_scores(data)
            print_report(analysis, data)

        elif choice == "4":
            if len(data["genuine"]) >= 5 and len(data["impostor"]) >= 5:
                analysis = analyze_scores(data)
                print_report(analysis, data)

                # Save full report
                report_file = os.path.join(OUTPUT_DIR, "calibration_report.json")
                with open(report_file, "w") as f:
                    json.dump({
                        "scores":   data,
                        "analysis": analysis
                    }, f, indent=2)
                print(f"  Report saved to: {report_file}")
            break

    camera.release()
    cv2.destroyAllWindows()
    print("\n  [CALIBRATION] Done.")


if __name__ == "__main__":
    asyncio.run(run_calibration())