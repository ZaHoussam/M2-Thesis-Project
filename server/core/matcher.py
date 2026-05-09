# ================================================================
#  core/matcher.py — ArcFace cosine similarity + decision logic
#
#  Changes from previous version:
#    - Removed Zone B (MFA_CHALLENGE) — binary ALLOW / DENY only
#    - Recalibrated thresholds for ArcFace score range
#    - Added weighted top-K matching for stability
#    - Added margin check — if top-2 scores too close → DENY
#
#  ArcFace score ranges (cosine similarity):
#    Genuine  : 0.80 – 0.95
#    Impostor : 0.20 – 0.40
#    Threshold: 0.50 (safe midpoint)
# ================================================================
from dataclasses import dataclass
from typing import Literal
import numpy as np
from config import settings

Decision = Literal["ALLOW", "DENY"]

# Minimum margin between best and second-best match score.
# If two different users score too similarly → ambiguous → DENY.
# Example: best=0.72, second=0.69 → margin=0.03 → DENY (too close)
MARGIN_THRESHOLD = 0.08


@dataclass
class MatchResult:
    decision:         Decision
    similarity_score: float        # best score found
    user_id:          int | None   # matched user id
    margin:           float        # gap between best and second-best


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two 512-d vectors.
    ArcFace embeddings are already L2-normalised —
    so this reduces to a simple dot product.
    We keep the full formula for safety.
    """
    vec_a = np.array(a, dtype=np.float32)
    vec_b = np.array(b, dtype=np.float32)

    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def find_best_match(
    incoming: list[float],
    candidates: list[dict],
) -> MatchResult:
    """
    Compare incoming embedding against all stored embeddings.

    Strategy — weighted top-K per user:
      1. Compute cosine score vs every stored embedding
      2. Group scores by user_id
      3. Per user — take average of top-2 scores (more stable than max)
      4. Pick the user with the highest averaged score
      5. Apply margin check between top-1 and top-2 users
      6. Apply threshold → ALLOW or DENY

    candidates format:
      [{"user_id": int, "embedding": [...], "angle_label": str}, ...]
    """

    if not candidates:
        return MatchResult(
            decision         = "DENY",
            similarity_score = 0.0,
            user_id          = None,
            margin           = 0.0,
        )

    # Step 1 — compute all scores
    scores_by_user: dict[int, list[float]] = {}
    for row in candidates:
        uid   = row["user_id"]
        score = cosine_similarity(incoming, row["embedding"])
        if uid not in scores_by_user:
            scores_by_user[uid] = []
        scores_by_user[uid].append(score)

    # Step 2 — per user: average of top-2 scores
    user_best: dict[int, float] = {}
    for uid, score_list in scores_by_user.items():
        top_k = sorted(score_list, reverse=True)[:2]
        user_best[uid] = float(np.mean(top_k))

    # Step 3 — rank users by their best score
    ranked = sorted(user_best.items(), key=lambda x: x[1], reverse=True)

    best_uid,   best_score   = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    margin       = best_score - second_score

    # Step 4 — threshold decision
    if best_score < settings.threshold_allow:
        return MatchResult(
            decision         = "DENY",
            similarity_score = round(best_score, 4),
            user_id          = None,
            margin           = round(margin, 4),
        )

    # Step 5 — margin check
    # Even if score is above threshold, if two users score
    # too similarly it means the system is uncertain — deny
    if len(ranked) > 1 and margin < MARGIN_THRESHOLD:
        return MatchResult(
            decision         = "DENY",
            similarity_score = round(best_score, 4),
            user_id          = None,
            margin           = round(margin, 4),
        )

    return MatchResult(
        decision         = "ALLOW",
        similarity_score = round(best_score, 4),
        user_id          = best_uid,
        margin           = round(margin, 4),
    )