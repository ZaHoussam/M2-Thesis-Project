# ================================================================
#  core/display.py — OpenCV camera window renderer
#  Draws bounding box, score bar, zone color, and status overlay
#  on the live camera feed.
# ================================================================
import cv2
import numpy as np


# ── Zone colors in BGR (OpenCV uses BGR not RGB) ─────────────────
ZONE_COLORS = {
    "ALLOW":         (117, 158, 29),   # green
    "MFA_CHALLENGE": (39,  159, 239),  # amber
    "DENY":          (74,  75,  226),  # red
    "SCANNING":      (180, 180, 180),  # gray — no result yet
    "MFA_PENDING":   (39,  159, 239),  # same as MFA
}

# ── Zone labels shown on screen ───────────────────────────────────
ZONE_LABELS = {
    "ALLOW":         "ALLOW",
    "MFA_CHALLENGE": "MFA REQUIRED",
    "DENY":          "DENIED",
    "SCANNING":      "SCANNING...",
    "MFA_PENDING":   "ENTER PIN",
}

FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD  = cv2.FONT_HERSHEY_DUPLEX


def draw_frame(
    frame:     np.ndarray,
    bbox:      tuple | None,       # (x1, y1, x2, y2) or None
    state:     str,                # SCANNING | ALLOW | MFA_CHALLENGE | DENY | MFA_PENDING
    score:     float | None,       # cosine similarity score (0.0 – 1.0)
    user_name: str | None,         # displayed on ALLOW
    pin_len:   int = 0,            # how many PIN digits entered so far
) -> np.ndarray:
    """
    Draw all UI elements on the frame and return it.
    Does NOT modify the original — works on a copy.
    """
    out = frame.copy()
    h, w = out.shape[:2]
    color = ZONE_COLORS.get(state, ZONE_COLORS["SCANNING"])

    # ── 1. Face bounding box ─────────────────────────────────────
    if bbox is not None:
        x1, y1, x2, y2 = bbox
        # Outer box
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        # Corner accents — draw thick corners over the rectangle
        _draw_corners(out, x1, y1, x2, y2, color, thickness=3, length=20)

    # ── 2. Top status bar (semi-transparent dark strip) ──────────
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (w, 44), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, out, 0.25, 0, out)

    # Lab label (left)
    cv2.putText(out, "Lab A  |  Door 1",
                (12, 28), FONT, 0.5, (180, 180, 180), 1, cv2.LINE_AA)

    # Live dot (right side) — blinking handled by frame count
    dot_color = (29, 158, 117) if (cv2.getTickCount() // int(cv2.getTickFrequency() * 0.6)) % 2 == 0 else (60, 80, 60)
    cv2.circle(out, (w - 60, 22), 5, dot_color, -1)
    cv2.putText(out, "LIVE",
                (w - 50, 28), FONT, 0.4, (140, 180, 140), 1, cv2.LINE_AA)

    # ── 3. Bottom result bar ─────────────────────────────────────
    overlay2 = out.copy()
    cv2.rectangle(overlay2, (0, h - 80), (w, h), (15, 15, 15), -1)
    cv2.addWeighted(overlay2, 0.80, out, 0.20, 0, out)

    # Zone label
    label = ZONE_LABELS.get(state, "SCANNING...")
    label_size = cv2.getTextSize(label, FONT_BOLD, 0.75, 2)[0]
    label_x    = (w - label_size[0]) // 2
    cv2.putText(out, label,
                (label_x, h - 48), FONT_BOLD, 0.75, color, 2, cv2.LINE_AA)

    # Score bar
    if score is not None:
        _draw_score_bar(out, score, color, w, h)

    # User name on ALLOW
    if state == "ALLOW" and user_name:
        name_size = cv2.getTextSize(user_name, FONT, 0.55, 1)[0]
        name_x    = (w - name_size[0]) // 2
        cv2.putText(out, f"Welcome,  {user_name}",
                    (name_x, h - 16), FONT, 0.52, (140, 220, 140), 1, cv2.LINE_AA)

    # PIN dots on MFA_PENDING
    if state == "MFA_PENDING":
        _draw_pin_dots(out, pin_len, w, h, color)

    # ── 4. Scan guide box (when no face found) ───────────────────
    if bbox is None and state == "SCANNING":
        _draw_guide_box(out, w, h)

    return out


# ── Helpers ───────────────────────────────────────────────────────

def _draw_corners(img, x1, y1, x2, y2, color, thickness=3, length=20):
    """Draw corner brackets instead of a full rectangle — cleaner look."""
    # Top-left
    cv2.line(img, (x1, y1),          (x1 + length, y1),       color, thickness)
    cv2.line(img, (x1, y1),          (x1,          y1 + length), color, thickness)
    # Top-right
    cv2.line(img, (x2, y1),          (x2 - length, y1),       color, thickness)
    cv2.line(img, (x2, y1),          (x2,          y1 + length), color, thickness)
    # Bottom-left
    cv2.line(img, (x1, y2),          (x1 + length, y2),       color, thickness)
    cv2.line(img, (x1, y2),          (x1,          y2 - length), color, thickness)
    # Bottom-right
    cv2.line(img, (x2, y2),          (x2 - length, y2),       color, thickness)
    cv2.line(img, (x2, y2),          (x2,          y2 - length), color, thickness)


def _draw_score_bar(img, score: float, color: tuple, w: int, h: int):
    """Draw a horizontal score bar with percentage fill."""
    bar_x1    = 20
    bar_x2    = w - 20
    bar_y     = h - 28
    bar_h     = 6
    bar_total = bar_x2 - bar_x1

    # Background track
    cv2.rectangle(img,
                  (bar_x1, bar_y),
                  (bar_x2, bar_y + bar_h),
                  (60, 60, 60), -1)

    # Filled portion
    filled = int(bar_total * max(0.0, min(1.0, score)))
    if filled > 0:
        cv2.rectangle(img,
                      (bar_x1, bar_y),
                      (bar_x1 + filled, bar_y + bar_h),
                      color, -1)

    # Threshold markers
    for thresh, label in [(0.60, "0.60"), (0.85, "0.85")]:
        tx = bar_x1 + int(bar_total * thresh)
        cv2.line(img, (tx, bar_y - 4), (tx, bar_y + bar_h + 4), (200, 200, 200), 1)

    # Score text
    score_text = f"score: {score:.2f}"
    cv2.putText(img, score_text,
                (bar_x1, bar_y - 8), FONT, 0.38,
                (200, 200, 200), 1, cv2.LINE_AA)


def _draw_pin_dots(img, pin_len: int, w: int, h: int, color: tuple):
    """Draw 4 PIN entry dots — filled for entered digits."""
    total_dots = 4
    dot_r      = 7
    spacing    = 28
    total_w    = (total_dots - 1) * spacing
    start_x    = (w - total_w) // 2
    dot_y      = h - 16

    for i in range(total_dots):
        cx = start_x + i * spacing
        if i < pin_len:
            cv2.circle(img, (cx, dot_y), dot_r, color, -1)       # filled
        else:
            cv2.circle(img, (cx, dot_y), dot_r, (100, 100, 100), 1)  # empty


def _draw_guide_box(img, w: int, h: int):
    """Draw a centered dashed guide rectangle when no face is detected."""
    cx, cy  = w // 2, h // 2
    gw, gh  = 160, 200
    x1, y1  = cx - gw // 2, cy - gh // 2
    x2, y2  = cx + gw // 2, cy + gh // 2
    color   = (80, 80, 80)

    # Dashed rectangle — draw small segments
    _draw_dashed_rect(img, x1, y1, x2, y2, color)

    hint = "Position face here"
    ts   = cv2.getTextSize(hint, FONT, 0.42, 1)[0]
    cv2.putText(img, hint,
                ((w - ts[0]) // 2, y2 + 20),
                FONT, 0.42, (100, 100, 100), 1, cv2.LINE_AA)


def _draw_dashed_rect(img, x1, y1, x2, y2, color, dash=8, gap=5):
    """Draw a dashed rectangle border."""
    for side in ["top", "bottom", "left", "right"]:
        if side == "top":
            pts = [(x, y1) for x in range(x1, x2, dash + gap)]
            for p in pts:
                cv2.line(img, p, (min(p[0] + dash, x2), y1), color, 1)
        elif side == "bottom":
            pts = [(x, y2) for x in range(x1, x2, dash + gap)]
            for p in pts:
                cv2.line(img, p, (min(p[0] + dash, x2), y2), color, 1)
        elif side == "left":
            pts = [(x1, y) for y in range(y1, y2, dash + gap)]
            for p in pts:
                cv2.line(img, p, (x1, min(p[1] + dash, y2)), color, 1)
        elif side == "right":
            pts = [(x2, y) for y in range(y1, y2, dash + gap)]
            for p in pts:
                cv2.line(img, p, (x2, min(p[1] + dash, y2)), color, 1)