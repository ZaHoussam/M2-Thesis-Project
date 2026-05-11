# ================================================================
#  routers/verify.py — WebSocket /ws/verify
#  Binary ALLOW / DENY — no MFA zone
# ================================================================
from db import session
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.matcher import find_best_match
from db.session   import get_session
from db.models    import FaceEmbedding, User, AccessLog

router = APIRouter(tags=["Verification"])


@router.websocket("/ws/verify")
async def ws_verify(websocket: WebSocket):
    """
    WebSocket endpoint for live face authentication.

    Client sends:
        {"embedding": [512 floats], "lab_id": 1}

    Server responds:
        {"decision": "ALLOW" | "DENY",
         "similarity_score": 0.91,
         "user_id": 3,
         "margin": 0.21,
         "message": "..."}
    """
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
                        "user_id":     r.user_id,
                        "embedding":   r.embedding,
                    }
                    for r in rows
                ]

                # Match — with latency measurement
    
                t_start = time.perf_counter()
                result  = find_best_match(embedding, candidates)
                latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

                # Log — add latency_ms to response
                log = AccessLog(
                    user_id          = result.user_id,
                    lab_id           = lab_id,
                    outcome          = result.decision,
                    similarity_score = result.similarity_score,
                )
                session.add(log)

            messages = {
                "ALLOW": f"Access granted. Score: {result.similarity_score} margin: {result.margin}",
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

    except WebSocketDisconnect:
        pass