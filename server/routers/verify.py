# ================================================================
#  routers/verify.py — WebSocket /ws/verify
#  Binary ALLOW / DENY — with latency + alert engine + antispoof
# ================================================================
import json
import time
import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.matcher      import find_best_match
from core.alert_engine import record_attempt
from db.session        import get_session
from db.models         import FaceEmbedding, User, AccessLog, SecurityAlert
from routers.logs      import broadcast_log_event
from routers.alerts    import broadcast_alert

router = APIRouter(tags=["Verification"])


@router.websocket("/ws/verify")
async def ws_verify(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)

            embedding  = data.get("embedding", [])
            lab_id     = data.get("lab_id", 1)
            det_score  = data.get("det_score", None)
            is_spoof   = data.get("is_spoof", False)
            spoof_prob = float(data.get("spoof_prob") or 0.0)

            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # ── Handle spoof attempt ──────────────────────────
            if is_spoof:
                async with get_session() as session:

                    # Log as DENY
                    log = AccessLog(
                        user_id          = None,
                        lab_id           = lab_id,
                        outcome          = "DENY",
                        similarity_score = None,
                        latency_ms       = 0.0,
                    )
                    session.add(log)

                    # Save spoof alert directly
                    spoof_alert = SecurityAlert(
                        lab_id      = lab_id,
                        alert_type  = "CONSECUTIVE_DENY",
                        description = (
                            f"Presentation attack detected at Lab {lab_id}. "
                            f"Spoof probability: {spoof_prob:.3f}. " if spoof_prob else "Spoof probability: unknown. "
                            f"Access blocked by anti-spoofing module."
                        ),
                        severity = "CRITICAL",
                    )
                    session.add(spoof_alert)

                print(f"[SPOOF] 🚨 Presentation attack blocked — Lab {lab_id} — prob={spoof_prob:.3f}")

                await broadcast_alert({
                    "lab_id":      lab_id,
                    "alert_type":  "CONSECUTIVE_DENY",
                    "description": (
                        f"Presentation attack detected. "
                        f"Spoof probability: {spoof_prob:.3f}."
                    ),
                    "severity":    "CRITICAL",
                    "is_resolved": False,
                    "created_at":  now_iso,
                })

                await websocket.send_text(json.dumps({
                    "decision": "DENY",
                    "message":  "Presentation attack detected. Access blocked.",
                    "is_spoof": True,
                }))
                continue

            # ── Validate embedding ────────────────────────────
            if not embedding or len(embedding) != 512:
                await websocket.send_text(json.dumps({
                    "decision": "DENY",
                    "message":  "Invalid embedding."
                }))
                continue

            triggered_alerts = []

            async with get_session() as session:

                # Load stored embeddings
                rows = await session.execute(
                    select(
                        FaceEmbedding.user_id,
                        FaceEmbedding.embedding,
                    )
                    .join(User, User.id == FaceEmbedding.user_id)
                    .where(User.is_active == True)
                )
                candidates = [
                    {"user_id": r.user_id, "embedding": r.embedding}
                    for r in rows
                ]

                # Match + latency
                t_start    = time.perf_counter()
                result     = find_best_match(embedding, candidates)
                latency_ms = round((time.perf_counter() - t_start) * 1000, 3)

                # Log
                log = AccessLog(
                    user_id          = result.user_id,
                    lab_id           = lab_id,
                    outcome          = result.decision,
                    similarity_score = result.similarity_score,
                    latency_ms       = latency_ms,
                )
                session.add(log)

                # Alert engine
                triggered = record_attempt(
                    lab_id    = lab_id,
                    decision  = result.decision,
                    det_score = det_score,
                )

                for alert_data in triggered:
                    alert = SecurityAlert(
                        lab_id      = alert_data["lab_id"],
                        alert_type  = alert_data["alert_type"],
                        description = alert_data["description"],
                        severity    = alert_data["severity"],
                    )
                    session.add(alert)
                    triggered_alerts.append(alert_data)
                    print(
                        f"[ALERT] 🚨 {alert_data['alert_type']} "
                        f"— {alert_data['severity']} — Lab {lab_id}"
                    )

            # Send response
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

            print(
                f"[AUTH] {result.decision:<5} "
                f"score={result.similarity_score:.4f} "
                f"margin={result.margin:.4f} "
                f"latency={latency_ms:.1f}ms"
            )

            # Broadcast to dashboard
            await broadcast_log_event({
                "outcome":          result.decision,
                "similarity_score": result.similarity_score,
                "latency_ms":       latency_ms,
                "user_id":          result.user_id,
                "lab_id":           lab_id,
                "created_at":       now_iso,
            })

            for alert_data in triggered_alerts:
                await broadcast_alert({
                    **alert_data,
                    "is_resolved": False,
                    "created_at":  now_iso,
                })

    except WebSocketDisconnect:
        pass