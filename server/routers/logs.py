import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from db.session import get_session
from db.models  import AccessLog, User, Lab

router = APIRouter(prefix="/logs", tags=["Logs"])


# ── Response schemas ──────────────────────────────────────────────
class LogEntry(BaseModel):
    id:               int
    user_id:          int | None
    user_name:        str | None
    lab_id:           int
    outcome:          str
    similarity_score: float | None
    latency_ms:       float | None
    created_at:       datetime

    class Config:
        from_attributes = True


class LogStats(BaseModel):
    total_attempts:    int
    total_allow:       int
    total_deny:        int
    allow_rate:        float
    avg_score_allow:   float | None
    avg_score_deny:    float | None
    avg_latency_ms:    float | None
    min_latency_ms:    float | None
    max_latency_ms:    float | None


# ── GET /logs ─────────────────────────────────────────────────────
@router.get("", response_model=list[LogEntry])
async def get_logs(
    limit:   int = Query(default=50,  ge=1, le=500),
    offset:  int = Query(default=0,   ge=0),
    outcome: str = Query(default=None),   # ALLOW or DENY filter
    lab_id:  int = Query(default=None),
):
    """
    Return recent access logs — newest first.
    Optional filters: outcome, lab_id.
    """
    async with get_session() as session:
        query = (
            select(
                AccessLog.id,
                AccessLog.user_id,
                User.full_name.label("user_name"),
                AccessLog.lab_id,
                AccessLog.outcome,
                AccessLog.similarity_score,
                AccessLog.latency_ms,
                AccessLog.created_at,
            )
            .outerjoin(User, User.id == AccessLog.user_id)
            .order_by(desc(AccessLog.created_at))
        )

        if outcome:
            query = query.where(AccessLog.outcome == outcome.upper())
        if lab_id:
            query = query.where(AccessLog.lab_id == lab_id)

        query = query.offset(offset).limit(limit)
        rows  = await session.execute(query)

        return [
            LogEntry(
                id               = r.id,
                user_id          = r.user_id,
                user_name        = r.user_name,
                lab_id           = r.lab_id,
                outcome          = r.outcome,
                similarity_score = r.similarity_score,
                latency_ms       = r.latency_ms,
                created_at       = r.created_at,
            )
            for r in rows
        ]


# ── GET /logs/stats ───────────────────────────────────────────────
@router.get("/stats", response_model=LogStats)
async def get_log_stats(
    lab_id: int = Query(default=None),
):
    """
    Return summary statistics across all access logs.
    Useful for thesis evaluation table.
    """
    async with get_session() as session:
        base = select(AccessLog)
        if lab_id:
            base = base.where(AccessLog.lab_id == lab_id)

        rows = await session.execute(base)
        logs = rows.scalars().all()

        if not logs:
            return LogStats(
                total_attempts  = 0,
                total_allow     = 0,
                total_deny      = 0,
                allow_rate      = 0.0,
                avg_score_allow = None,
                avg_score_deny  = None,
                avg_latency_ms  = None,
                min_latency_ms  = None,
                max_latency_ms  = None,
            )

        allow_logs   = [l for l in logs if l.outcome == "ALLOW"]
        deny_logs    = [l for l in logs if l.outcome == "DENY"]
        latency_logs = [l.latency_ms for l in logs if l.latency_ms is not None]

        def safe_avg(values):
            return round(sum(values) / len(values), 4) if values else None

        return LogStats(
            total_attempts  = len(logs),
            total_allow     = len(allow_logs),
            total_deny      = len(deny_logs),
            allow_rate      = round(len(allow_logs) / len(logs), 4),
            avg_score_allow = safe_avg([l.similarity_score for l in allow_logs if l.similarity_score]),
            avg_score_deny  = safe_avg([l.similarity_score for l in deny_logs  if l.similarity_score]),
            avg_latency_ms  = safe_avg(latency_logs),
            min_latency_ms  = round(min(latency_logs), 3) if latency_logs else None,
            max_latency_ms  = round(max(latency_logs), 3) if latency_logs else None,
        )


# ── GET /logs/user/{user_id} ──────────────────────────────────────
@router.get("/user/{user_id}", response_model=list[LogEntry])
async def get_user_logs(
    user_id: int,
    limit:   int = Query(default=20, ge=1, le=100),
):
    """Return recent access logs for a specific user."""
    async with get_session() as session:
        rows = await session.execute(
            select(
                AccessLog.id,
                AccessLog.user_id,
                User.full_name.label("user_name"),
                AccessLog.lab_id,
                AccessLog.outcome,
                AccessLog.similarity_score,
                AccessLog.latency_ms,
                AccessLog.created_at,
            )
            .outerjoin(User, User.id == AccessLog.user_id)
            .where(AccessLog.user_id == user_id)
            .order_by(desc(AccessLog.created_at))
            .limit(limit)
        )
        return [
            LogEntry(
                id               = r.id,
                user_id          = r.user_id,
                user_name        = r.user_name,
                lab_id           = r.lab_id,
                outcome          = r.outcome,
                similarity_score = r.similarity_score,
                latency_ms       = r.latency_ms,
                created_at       = r.created_at,
            )
            for r in rows
        ]

# Shared set of connected dashboard clients
dashboard_clients: set[WebSocket] = set()


@router.websocket("/ws")
async def ws_logs(websocket: WebSocket):
    """
    Live access log feed for the admin dashboard.
    Pushes every new access event to all connected dashboards.
    """
    await websocket.accept()
    dashboard_clients.add(websocket)
    print(f"[DASHBOARD] Client connected. Total: {len(dashboard_clients)}")
    try:
        while True:
            # Keep connection alive — wait for client ping
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        dashboard_clients.discard(websocket)
        print(f"[DASHBOARD] Client disconnected. Total: {len(dashboard_clients)}")


async def broadcast_log_event(event: dict):
    """
    Called from verify.py after every authentication.
    Pushes the event to all connected dashboard clients.
    """
    import json
    dead = set()
    for client in dashboard_clients:
        try:
            await client.send_text(json.dumps(event))
        except Exception:
            dead.add(client)
    dashboard_clients -= dead