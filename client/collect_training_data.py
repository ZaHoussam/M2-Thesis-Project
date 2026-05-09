# ================================================================
#  collect_training_data.py — Data collection for SVM training
#
#  What it does:
#    1. Opens camera
#    2. Detects + aligns + embeds each face
#    3. Saves (embedding, label) rows to a CSV file
#
#  Run with: python collect_training_data.py
#
#  Output: training_data/embeddings.csv
#    columns: label, emb_0, emb_1, ..., emb_511
# ================================================================
import asyncio
import csv
import os
import time
import cv2
import numpy as np

from core.camera     import Camera
from core.detector   import FaceDetector
from core.embedder   import FaceEmbedder
from core.display    import draw_frame
from utils.alignment import align_face


# ── Output folder ─────────────────────────────────────────────────
OUTPUT_DIR  = "training_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "embeddings.csv")

# ── How many samples to collect per session ───────────────────────
SAMPLES_PER_SESSION = 30   # collect 30 embeddings per person/label


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def file_exists_with_data() -> bool:
    return os.path.isfile(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0


def get_existing_labels() -> list[str]:
    """Read CSV and return list of labels already collected."""
    if not file_exists_with_data():
        return []
    labels = set()
    with open(OUTPUT_FILE, "r") as f:
        reader = csv.reader(f)
        next(reader, None)   # skip header
        for row in reader:
            if row:
                labels.add(row[0])
    return sorted(labels)


def append_to_csv(label: str, embeddings: list[list[float]]):
    """Append collected embeddings to CSV file."""
    write_header = not file_exists_with_data()
    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            header = ["label"] + [f"emb_{i}" for i in range(512)]
            writer.writerow(header)
        for emb in embeddings:
            writer.writerow([label] + emb)


def print_summary():
    """Print how many samples exist per label in the CSV."""
    if not file_exists_with_data():
        print("  [INFO] No data collected yet.")
        return
    counts = {}
    with open(OUTPUT_FILE, "r") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                counts[row[0]] = counts.get(row[0], 0) + 1
    print("\n  Current dataset:")
    print("  " + "-"*35)
    total = 0
    for label, count in sorted(counts.items()):
        bar = "█" * min(count, 40)
        print(f"  {label:<20} {count:>3} samples  {bar}")
        total += count
    print("  " + "-"*35)
    print(f"  {'TOTAL':<20} {total:>3} samples")


def collect_session(label: str, n_samples: int) -> list[list[float]]:
    """
    Open camera and collect n_samples embeddings for the given label.
    Returns list of embeddings collected.
    """
    camera   = Camera()
    detector = FaceDetector()
    embedder = FaceEmbedder()

    collected  = []
    last_time  = 0
    interval   = 0.3   # collect one sample every 0.3s — allows natural movement

    cv2.namedWindow("Data Collection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Data Collection", 640, 520)

    print(f"\n  [CAMERA] Collecting {n_samples} samples for [{label}]")
    print(f"  Move your head naturally — vary pose, angle, expression.")
    print(f"  Press Q to stop early.\n")

    while len(collected) < n_samples:
        frame = camera.read_frame()
        if frame is None:
            continue

        detection = detector.detect(frame)
        now       = time.time()
        captured_this_frame = False

        if detection and (now - last_time) >= interval:
            crop      = detection["crop"]
            landmarks = detection["landmarks"]

            if landmarks:
                crop = align_face(crop, landmarks)

            embedding = embedder.embed(crop)
            collected.append(embedding)
            last_time = now
            captured_this_frame = True
            print(f"  [{len(collected):>2}/{n_samples}] captured", end="\r")

        # ── Draw progress on frame ───────────────────────────────
        rendered = draw_frame(
            frame     = frame,
            bbox      = detection["bbox"] if detection else None,
            state     = "ALLOW" if captured_this_frame else "SCANNING",
            score     = len(collected) / n_samples,   # use as progress bar
            user_name = f"{label}  [{len(collected)}/{n_samples}]",
        )

        # Progress bar overlay
        progress_text = f"Collecting: {len(collected)}/{n_samples}"
        cv2.putText(rendered, progress_text,
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (29, 158, 117), 2, cv2.LINE_AA)

        cv2.imshow("Data Collection", rendered)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(f"\n  [WARN] Stopped early — {len(collected)} samples collected.")
            break

    camera.release()
    cv2.destroyAllWindows()
    return collected


def main():
    ensure_output_dir()

    print("\n" + "="*55)
    print("  SVM TRAINING DATA COLLECTION")
    print("="*55)
    print("  This script collects face embeddings for SVM training.")
    print("  Collect data for EACH lab member + unknown persons.")
    print()

    # Show existing data
    existing = get_existing_labels()
    if existing:
        print(f"  Already collected labels: {', '.join(existing)}")
        print_summary()
    else:
        print("  No data collected yet — starting fresh.")

    while True:
        print("\n" + "-"*55)
        print("  Options:")
        print("  [1] Collect data for a lab member")
        print("  [2] Collect UNKNOWN persons (important for security)")
        print("  [3] Show current dataset summary")
        print("  [4] Quit and save")
        print("-"*55)

        choice = input("  Choice: ").strip()

        # ── Collect lab member ────────────────────────────────────
        if choice == "1":
            name = input("  Enter person's name (no spaces, e.g. houssam): ").strip().lower()
            if not name:
                print("  [ERROR] Name cannot be empty.")
                continue
            if name == "unknown":
                print("  [ERROR] Use option [2] for unknown persons.")
                continue

            n = input(f"  How many samples? [{SAMPLES_PER_SESSION}]: ").strip()
            n = int(n) if n.isdigit() else SAMPLES_PER_SESSION

            print(f"\n  Ready to collect {n} samples for [{name}].")
            print(f"  TIP: vary your head angle, distance, and expression.")
            input("  Press ENTER to open camera...")

            embeddings = collect_session(name, n)

            if embeddings:
                append_to_csv(name, embeddings)
                print(f"\n  ✅ Saved {len(embeddings)} samples for [{name}]")
            else:
                print("  [WARN] No samples collected — nothing saved.")

        # ── Collect unknown ───────────────────────────────────────
        elif choice == "2":
            n = input(f"  How many unknown samples? [{SAMPLES_PER_SESSION}]: ").strip()
            n = int(n) if n.isdigit() else SAMPLES_PER_SESSION

            print(f"\n  Collecting {n} UNKNOWN samples.")
            print(f"  Ask friends/family who are NOT lab members to stand in front of camera.")
            print(f"  Or use your own face with heavy occlusion (hat, hand covering face).")
            input("  Press ENTER to open camera...")

            embeddings = collect_session("unknown", n)

            if embeddings:
                append_to_csv("unknown", embeddings)
                print(f"\n  ✅ Saved {len(embeddings)} unknown samples.")
            else:
                print("  [WARN] No samples collected — nothing saved.")

        # ── Summary ───────────────────────────────────────────────
        elif choice == "3":
            print_summary()

        # ── Quit ──────────────────────────────────────────────────
        elif choice == "4":
            print_summary()
            print(f"\n  ✅ Data saved to: {OUTPUT_FILE}")
            print(f"  Upload this file to Google Colab for SVM training.")
            print(f"  Goodbye.\n")
            break

        else:
            print("  [ERROR] Invalid choice.")


if __name__ == "__main__":
    main()