# ================================================================
#  core/antispoof.py — Texture-based anti-spoofing
#
#  Uses Local Binary Pattern (LBP) texture analysis.
#  Real skin has complex micro-texture — pores, fine hairs.
#  Printed photos and phone screens have uniform, flat texture.
#
#  No external model needed — pure OpenCV + numpy.
#
#  How it works:
#    1. Convert face crop to grayscale
#    2. Compute LBP texture map
#    3. Analyze texture variance and frequency distribution
#    4. Low variance = flat texture = SPOOF
#    5. High variance = complex texture = REAL
# ================================================================
import cv2
import numpy as np


class AntiSpoofDetector:

    # Tuning parameters — adjust based on your camera
    # Lower TEXTURE_THRESHOLD = more permissive (fewer false SPOOFs)
    # Higher TEXTURE_THRESHOLD = stricter (catches more attacks)
    TEXTURE_THRESHOLD = 45.0   # Laplacian variance threshold
    LBP_THRESHOLD     = 0.35   # LBP uniformity threshold

    def __init__(self, model_path: str = None):
        # model_path ignored — texture-based, no model needed
        print("[ANTISPOOF] Texture-based anti-spoofing loaded.")
        print(f"[ANTISPOOF] Laplacian threshold : {self.TEXTURE_THRESHOLD}")
        print(f"[ANTISPOOF] LBP threshold       : {self.LBP_THRESHOLD}")

    def _compute_lbp(self, gray: np.ndarray) -> float:
        """
        Compute Local Binary Pattern uniformity score.
        Real faces have diverse LBP patterns.
        Printed/screen faces have repetitive uniform patterns.
        Returns a score 0.0–1.0 — lower = more uniform = more likely spoof.
        """
        h, w   = gray.shape
        lbp    = np.zeros_like(gray, dtype=np.uint8)
        radius = 1

        # Compute LBP for each pixel
        for dy, dx in [(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1)]:
            shifted     = np.roll(np.roll(gray, dy, axis=0), dx, axis=1)
            lbp         = lbp * 2 + (gray >= shifted).astype(np.uint8)

        # Histogram of LBP values
        hist, _    = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
        hist       = hist.astype(float) / hist.sum()

        # Entropy — how diverse are the patterns?
        entropy    = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0]))
        max_entropy = np.log2(256)

        return float(entropy / max_entropy)

    def _compute_texture_variance(self, gray: np.ndarray) -> float:
        """
        Laplacian variance — measures image sharpness and texture complexity.
        Real faces: high variance (complex texture)
        Printed/screen: lower variance (flat, uniform)
        """
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        return float(lap.var())

    def _compute_frequency_score(self, gray: np.ndarray) -> float:
        """
        Frequency domain analysis using FFT.
        Phone screens have characteristic frequency patterns.
        Real faces have more natural frequency distribution.
        """
        f       = np.fft.fft2(gray.astype(float))
        fshift  = np.fft.fftshift(f)
        mag     = np.abs(fshift)

        # Ratio of high-frequency to low-frequency energy
        h, w    = gray.shape
        cy, cx  = h // 2, w // 2
        r       = min(h, w) // 6

        # Low-frequency region (center)
        low_mask         = np.zeros((h, w), dtype=bool)
        y, x             = np.ogrid[:h, :w]
        low_mask[(y-cy)**2 + (x-cx)**2 <= r**2] = True

        low_energy  = mag[low_mask].sum()
        high_energy = mag[~low_mask].sum()
        total       = low_energy + high_energy + 1e-8

        return float(high_energy / total)

    def predict(self, face_crop_bgr: np.ndarray) -> dict:
        """
        Classify face crop as REAL or SPOOF using texture analysis.

        Returns:
            is_real    : bool
            real_prob  : float  (0.0 – 1.0)
            spoof_prob : float  (0.0 – 1.0)
            label      : "REAL" or "SPOOF"
            scores     : dict of individual scores (for debugging)
        """
        # Resize to standard size for consistent analysis
        resized = cv2.resize(face_crop_bgr, (128, 128))
        gray    = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Score 1 — texture variance (main signal)
        tex_var  = self._compute_texture_variance(gray)

        # Score 2 — LBP diversity
        lbp_score = self._compute_lbp(gray)

        # Score 3 — frequency ratio
        freq_score = self._compute_frequency_score(gray)

        # Combine scores — weighted decision
        # Texture variance is the strongest signal
        tex_norm   = min(tex_var / 200.0, 1.0)   # normalize to [0,1]
        combined   = (tex_norm * 0.6) + (lbp_score * 0.3) + (freq_score * 0.1)

        # Convert to real/spoof probability
        real_prob  = float(np.clip(combined, 0.0, 1.0))
        spoof_prob = 1.0 - real_prob

        # Decision — threshold at 0.40
        # Below 0.40 combined score = SPOOF
        is_real = combined >= 0.40

        return {
            "is_real":    is_real,
            "real_prob":  round(real_prob,  4),
            "spoof_prob": round(spoof_prob, 4),
            "label":      "REAL" if is_real else "SPOOF",
            "scores": {
                "texture_variance": round(tex_var,    2),
                "lbp_diversity":    round(lbp_score,  4),
                "freq_ratio":       round(freq_score, 4),
                "combined":         round(combined,   4),
            }
        }

    def is_real_face(self, face_crop_bgr: np.ndarray) -> bool:
        return self.predict(face_crop_bgr)["is_real"]