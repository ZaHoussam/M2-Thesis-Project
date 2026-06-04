# ================================================================
#  test_antispoof2.py — direct antispoof model test (OPTIMIZED)
#  Optimized for Phone Cameras / DroidCam feeds
#  Run: python test_antispoof2.py
# ================================================================
import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = "../models/silent_face.onnx"

# ── Load antispoof model ──────────────────────────────────────────
print("Loading antispoof model...")
session  = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
inp_name = session.get_inputs()[0].name
out_name = session.get_outputs()[0].name
print(f"Input  : {inp_name} {session.get_inputs()[0].shape}")
print(f"Output : {out_name} {session.get_outputs()[0].shape}")

# ── OPTIMIZATION 1: Use a much more robust face cascade ───────────
# 'haarcascade_frontalface_alt2.xml' handles head tilts, expressions, 
# and minor rotations significantly better than 'default.xml'.
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
)

# ── Camera Setup (DroidCam config) ───────────────────────────────
# If using DroidCam via Wi-Fi, replace 0 with your URL: "http://192.168.1.X:4747/video"
CAMERA_SOURCE = 1 
cap = cv2.VideoCapture(CAMERA_SOURCE)

if not cap.isOpened():
    print(f"Cannot open camera source: {CAMERA_SOURCE}")
    exit()

print("\nCamera opened.")
print("SPACE = score your face | Q = quit\n")

cv2.namedWindow("AntiSpoof Test", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AntiSpoof Test", 640, 480)

while True:
    ok, frame = cap.read()
    if not ok:
        continue

    # ── OPTIMIZATION 2: Downscale High-Res Feeds for Detection ─────
    # Phone feeds are too large for Haar Cascades. We process detection at 
    # a fixed width (640px) for speed and reliable sizing, then scale back up.
    target_width = 640
    h_orig, w_orig = frame.shape[:2]
    scale = target_width / float(w_orig)
    target_height = int(h_orig * scale)
    
    frame_small = cv2.resize(frame, (target_width, target_height))
    gray_small  = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
    
    # ── OPTIMIZATION 3: Fix Uneven Lighting ────────────────────────
    # Equalizing the histogram compensates for poor or harsh phone lighting
    gray_small = cv2.equalizeHist(gray_small)

    # ── OPTIMIZATION 4: Tighten Search Parameters ──────────────────
    # scaleFactor=1.05 searches more granularly than 1.1 so it won't skip faces.
    faces_small = face_cascade.detectMultiScale(
        gray_small, 
        scaleFactor=1.05, 
        minNeighbors=4, 
        minSize=(40, 40)
    )

    # Scale the detected coordinates back up to match the original high-res frame
    faces = []
    for (x, y, w, h) in faces_small:
        x_orig = int(x / scale)
        y_orig = int(y / scale)
        w_orig_box = int(w / scale)
        h_orig_box = int(h / scale)
        faces.append((x_orig, y_orig, w_orig_box, h_orig_box))

    display = frame.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(display, (x, y), (x+w, y+h), (29, 158, 117), 2)

    status = f"Faces: {len(faces)}  |  SPACE=score  Q=quit"
    cv2.putText(display, status, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

    cv2.imshow("AntiSpoof Test", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    if key == ord(' '):
        if len(faces) == 0:
            print("No face detected — hold the phone steady and try again.")
            continue

        # Take largest face
        x, y, w, h = max(faces, key=lambda f: f[2]*f[3])

        # Add padding
        pad  = int(max(w, h) * 0.2)
        x1   = max(0, x - pad)
        y1   = max(0, y - pad)
        x2   = min(frame.shape[1], x + w + pad)
        y2   = min(frame.shape[0], y + h + pad)
        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        # Preprocess → 80x80 (High-res crop preserves anti-spoof texture detail!)
        resized = cv2.resize(crop, (80, 80))
        img     = resized.astype(np.float32) / 255.0
        img     = np.transpose(img, (2, 0, 1))
        img     = np.expand_dims(img, axis=0)

        # Run inference
        raw   = session.run([out_name], {inp_name: img})[0][0]

        # Softmax
        exp   = np.exp(raw - raw.max())
        probs = exp / exp.sum()

        print(f"Raw output    : {raw}")
        print(f"Softmax probs : {probs}")

        n = len(probs)
        if n == 2:
            print(f"  [0] spoof : {probs[0]:.4f}")
            print(f"  [1] real  : {probs[1]:.4f}")
            real_prob = probs[1]
        elif n == 3:
            print(f"  [0] spoof : {probs[0]:.4f}")
            print(f"  [1] real  : {probs[1]:.4f}")
            print(f"  [2] other : {probs[2]:.4f}")
            real_prob = probs[1]
        else:
            print(f"  probs: {probs}")
            real_prob = probs[1] if n > 1 else probs[0]

        verdict = "✅ REAL" if real_prob >= 0.50 else "❌ SPOOF"
        print(f"Real prob     : {real_prob:.4f}")
        print(f"Decision      : {verdict}")
        print(f"--- press SPACE again for another sample ---\n")

cap.release()
cv2.destroyAllWindows()