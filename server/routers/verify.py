# ================================================================
#  routers/verify.py — WebSocket /ws/verify
#  Binary ALLOW / DENY — with latency measurement
# ================================================================
import json
import time
from routers.logs import broadcast_log_event
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.matcher import find_best_match
from db.session   import get_session
from db.models    import FaceEmbedding, User, AccessLog

router = APIRouter(tags=["Verification"])


@router.websocket("/ws/verify")
async def ws_verify(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)

            embedding = data.get("embedding", [])
            lab_id    = data.get("lab_id", 1)

            if len(embedding) != 512:
                await websocket.send_text(json.dumps({
                    "decision": "DENY",
                    "message":  "Invalid embedding length."
                }))
                continue

            async with get_session() as session:

                # Load all active embeddings
                rows = await session.execute(
                    select(
                        FaceEmbedding.user_id,
                        FaceEmbedding.embedding,
                    )
                    .join(User, User.id == FaceEmbedding.user_id)
                    .where(User.is_active == True)
                )
                candidates = [
                    {
                        "user_id":   r.user_id,
                        "embedding": r.embedding,
                    }
                    for r in rows
                ]

                # ── Measure matching latency ──────────────────
                t_start    = time.perf_counter()
                result     = find_best_match(embedding, candidates)
                latency_ms = round((time.perf_counter() - t_start) * 1000, 3)

                # ── Log with latency ──────────────────────────
                log = AccessLog(
                    user_id          = result.user_id,
                    lab_id           = lab_id,
                    outcome          = result.decision,
                    similarity_score = result.similarity_score,
                    latency_ms       = latency_ms,
                )
                session.add(log)

            messages = {
                "ALLOW": f"Access granted. Score: {result.similarity_score}",
                "DENY":  f"Access denied.  Score: {result.similarity_score}",
            }

            await websocket.send_text(json.dumps({
                "decision":         result.decision,
                "similarity_score": result.similarity_score,
                "user_id":          result.user_id,
                "margin":           result.margin,
                "latency_ms":       latency_ms,
                "message":          messages[result.decision],
            }))

            # Print to server terminal for monitoring
            print(
                f"[AUTH] {result.decision:<5} "
                f"score={result.similarity_score:.4f} "
                f"margin={result.margin:.4f} "
                f"latency={latency_ms:.1f}ms"
            )
            # Broadcast to dashboard live feed
            await broadcast_log_event({
                "id":               log.id if hasattr(log, 'id') else None,
                "outcome":          result.decision,
                "similarity_score": result.similarity_score,
                "latency_ms":       latency_ms,
                "user_id":          result.user_id,
                "lab_id":           lab_id,
                "created_at":       __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            })

    except WebSocketDisconnect:
        pass