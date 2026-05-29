# ================================================================
#  core/antispoof.py — Silent-Face anti-spoofing detector
# ================================================================
import cv2
import numpy as np
import onnxruntime as ort
import os


class AntiSpoofDetector:

    INPUT_SIZE  = (80, 80)

    # Threshold tuning guide:
    #   0.50 → permissive — accept if real_prob > 50%
    #   0.60 → balanced   — recommended starting point
    #   0.80 → strict     — may reject real faces
    REAL_THRESH = 0.55

    def __init__(self, model_path: str = "../models/silent_face.onnx"):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Silent-Face model not found at: {model_path}\n"
                f"Run: python convert_antispoof.py"
            )

        self._session    = ort.InferenceSession(
            model_path,
            providers = ["CPUExecutionProvider"]
        )
        self._input_name  = self._session.get_inputs()[0].name
        self._output_name = self._session.get_outputs()[0].name
        self._n_classes   = self._session.get_outputs()[0].shape[-1]

        print(f"[ANTISPOOF] Model loaded: {model_path}")
        print(f"[ANTISPOOF] Output classes: {self._n_classes} | Threshold: {self.REAL_THRESH}")

    def predict(self, face_crop_bgr: np.ndarray) -> dict:
        # Step 1 — resize to 80x80
        resized = cv2.resize(face_crop_bgr, self.INPUT_SIZE)

        # Step 2 — normalize [0, 1]
        img = resized.astype(np.float32) / 255.0

        # Step 3 — HWC → CHW + batch dim
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)

        # Step 4 — inference
        raw   = self._session.run(
            [self._output_name],
            {self._input_name: img}
        )[0][0]

        # Step 5 — softmax
        exp   = np.exp(raw - raw.max())
        probs = exp / exp.sum()

        spoof_prob = float(probs[0])
        real_prob  = float(probs[1]) if len(probs) >= 2 else float(1 - probs[0])

        is_real = spoof_prob < 0.5

        return {
            "is_real":    is_real,
            "real_prob":  round(real_prob,  4),
            "spoof_prob": round(spoof_prob, 4),
            "label":      "REAL" if is_real else "SPOOF",
        }

    def is_real_face(self, face_crop_bgr: np.ndarray) -> bool:
        return self.predict(face_crop_bgr)["is_real"]