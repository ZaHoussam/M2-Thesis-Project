# ================================================================
#  core/alert_engine.py — Security alert detection engine
#
#  Three patterns detected:
#    1. CONSECUTIVE_DENY  — 5 DENYs in 60 seconds per lab
#    2. HIGH_VOLUME       — 10 attempts in 30 seconds per lab
#    3. SUSPICIOUS_MOVEMENT — high detection score variance
#                             over rolling window per lab
#
#  All state is kept in memory — fast, no DB reads per frame.
#  Alerts are written to DB and broadcast to dashboard.
# ================================================================
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


# ── Configuration ─────────────────────────────────────────────────
DENY_THRESHOLD        = 5     # Pattern 1 — DENYs needed
DENY_WINDOW_SECONDS   = 60    # Pattern 1 — within this window

VOLUME_THRESHOLD      = 10    # Pattern 2 — attempts needed
VOLUME_WINDOW_SECONDS = 30    # Pattern 2 — within this window

MOVEMENT_WINDOW       = 20    # Pattern 3 — frames to track
MOVEMENT_VAR_THRESHOLD = 0.015 # Pattern 3 — variance above this = suspicious
MOVEMENT_MIN_FRAMES   = 10    # Pattern 3 — minimum frames before checking

# Cooldown — don't fire same alert type more than once per window
ALERT_COOLDOWN_SECONDS = 120


@dataclass
class LabState:
    """Per-lab sliding window state — kept in memory."""

    # Pattern 1 — DENY timestamps
    deny_times:     Deque[float] = field(default_factory=deque)

    # Pattern 2 — all attempt timestamps
    attempt_times:  Deque[float] = field(default_factory=deque)

    # Pattern 3 — detection score history
    det_scores:     Deque[float] = field(default_factory=deque)

    # Cooldown tracker — last alert time per type
    last_alert:     dict = field(default_factory=dict)


# Global state — one LabState per lab_id
_lab_states: dict[int, LabState] = {}


def _get_state(lab_id: int) -> LabState:
    if lab_id not in _lab_states:
        _lab_states[lab_id] = LabState()
    return _lab_states[lab_id]


def _is_on_cooldown(state: LabState, alert_type: str) -> bool:
    last = state.last_alert.get(alert_type, 0)
    return (time.time() - last) < ALERT_COOLDOWN_SECONDS


def _set_cooldown(state: LabState, alert_type: str) -> None:
    state.last_alert[alert_type] = time.time()


def _prune(dq: deque, window: float) -> None:
    """Remove timestamps older than window seconds."""
    now = time.time()
    while dq and (now - dq[0]) > window:
        dq.popleft()


# ── Public API ────────────────────────────────────────────────────

def record_attempt(
    lab_id:    int,
    decision:  str,          # "ALLOW" or "DENY"
    det_score: float | None, # RetinaFace detection confidence
) -> list[dict]:
    """
    Called after every authentication decision.
    Returns list of triggered alerts (empty if none).

    Each alert dict:
        {
            "lab_id":      int,
            "alert_type":  str,
            "description": str,
            "severity":    str,
        }
    """
    now   = time.time()
    state = _get_state(lab_id)
    alerts: list[dict] = []

    # ── Record attempt timestamp ──────────────────────────────
    state.attempt_times.append(now)

    # ── Record DENY timestamp ─────────────────────────────────
    if decision == "DENY":
        state.deny_times.append(now)

    # ── Record detection score ────────────────────────────────
    if det_score is not None:
        state.det_scores.append(det_score)
        if len(state.det_scores) > MOVEMENT_WINDOW:
            state.det_scores.popleft()

    # ── Prune old timestamps ──────────────────────────────────
    _prune(state.deny_times,    DENY_WINDOW_SECONDS)
    _prune(state.attempt_times, VOLUME_WINDOW_SECONDS)

    # ── Pattern 1 — consecutive DENYs ────────────────────────
    if (
        len(state.deny_times) >= DENY_THRESHOLD
        and not _is_on_cooldown(state, "CONSECUTIVE_DENY")
    ):
        alerts.append({
            "lab_id":      lab_id,
            "alert_type":  "CONSECUTIVE_DENY",
            "description": (
                f"{len(state.deny_times)} unauthorized access attempts "
                f"detected at Lab {lab_id} within {DENY_WINDOW_SECONDS} seconds. "
                f"Possible intruder."
            ),
            "severity": "HIGH",
        })
        _set_cooldown(state, "CONSECUTIVE_DENY")
        state.deny_times.clear()

    # ── Pattern 2 — high volume ───────────────────────────────
    if (
        len(state.attempt_times) >= VOLUME_THRESHOLD
        and not _is_on_cooldown(state, "HIGH_VOLUME")
    ):
        alerts.append({
            "lab_id":      lab_id,
            "alert_type":  "HIGH_VOLUME",
            "description": (
                f"{len(state.attempt_times)} authentication attempts "
                f"in {VOLUME_WINDOW_SECONDS} seconds at Lab {lab_id}. "
                f"Possible automated attack."
            ),
            "severity": "CRITICAL",
        })
        _set_cooldown(state, "HIGH_VOLUME")
        state.attempt_times.clear()

    # ── Pattern 3 — suspicious movement ──────────────────────
    if (
        len(state.det_scores) >= MOVEMENT_MIN_FRAMES
        and not _is_on_cooldown(state, "SUSPICIOUS_MOVEMENT")
    ):
        scores = list(state.det_scores)
        mean   = sum(scores) / len(scores)
        var    = sum((s - mean) ** 2 for s in scores) / len(scores)

        if var > MOVEMENT_VAR_THRESHOLD:
            alerts.append({
                "lab_id":      lab_id,
                "alert_type":  "SUSPICIOUS_MOVEMENT",
                "description": (
                    f"Suspicious movement pattern detected at Lab {lab_id}. "
                    f"Detection score variance: {var:.4f} "
                    f"(threshold: {MOVEMENT_VAR_THRESHOLD}). "
                    f"Subject may be moving erratically in front of camera."
                ),
                "severity": "MEDIUM",
            })
            _set_cooldown(state, "SUSPICIOUS_MOVEMENT")
            state.det_scores.clear()

    return alerts


def get_lab_state_summary(lab_id: int) -> dict:
    """
    Return current window counts for a lab — useful for debugging.
    """
    state = _get_state(lab_id)
    _prune(state.deny_times,    DENY_WINDOW_SECONDS)
    _prune(state.attempt_times, VOLUME_WINDOW_SECONDS)
    return {
        "lab_id":          lab_id,
        "deny_count":      len(state.deny_times),
        "attempt_count":   len(state.attempt_times),
        "det_score_count": len(state.det_scores),
    }