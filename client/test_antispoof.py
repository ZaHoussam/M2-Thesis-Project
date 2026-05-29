# ================================================================
#  test_antispoof2.py — direct antispoof model test
#  No InsightFace — uses OpenCV face detection only
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
print(f"Num classes: {session.get_outputs()[0].shape[-1]}")

# ── OpenCV face detector (no InsightFace needed) ──────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera.")
    exit()

print("\nCamera opened.")
print("SPACE = score your face | Q = quit\n")

cv2.namedWindow("AntiSpoof Test", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AntiSpoof Test", 640, 480)

while True:
    ok, frame = cap.read()
    if not ok:
        continue

    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

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
            print("No face detected — move closer and try again.")
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

        # Preprocess → 80x80
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