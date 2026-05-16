# ================================================================
#  routers/alerts.py — Security alerts endpoints
#
#  GET  /alerts           — list recent alerts
#  GET  /alerts/active    — unresolved alerts only
#  PUT  /alerts/{id}/resolve — mark alert as resolved
#  WebSocket /alerts/ws   — live alert feed for dashboard
# ================================================================
import asyncio
import json
from datetime import datetime

from fastapi  import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select, desc

from db.session import get_session
from db.models  import SecurityAlert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# Connected dashboard clients for live alert feed
alert_clients: set[WebSocket] = set()


# ── Response schema ───────────────────────────────────────────────
class AlertEntry(BaseModel):
    id:          int
    lab_id:      int
    alert_type:  str
    description: str
    severity:    str
    is_resolved: bool
    created_at:  datetime

    class Config:
        from_attributes = True


# ── GET /alerts ───────────────────────────────────────────────────
@router.get("", response_model=list[AlertEntry])
async def get_alerts(limit: int = 50):
    """Return recent security alerts — newest first."""
    async with get_session() as session:
        rows = await session.execute(
            select(SecurityAlert)
            .order_by(desc(SecurityAlert.created_at))
            .limit(limit)
        )
        return rows.scalars().all()


# ── GET /alerts/active ────────────────────────────────────────────
@router.get("/active", response_model=list[AlertEntry])
async def get_active_alerts():
    """Return only unresolved alerts."""
    async with get_session() as session:
        rows = await session.execute(
            select(SecurityAlert)
            .where(SecurityAlert.is_resolved == False)
            .order_by(desc(SecurityAlert.created_at))
        )
        return rows.scalars().all()


# ── PUT /alerts/{id}/resolve ──────────────────────────────────────
@router.put("/{alert_id}/resolve")
async def resolve_alert(alert_id: int):
    """Mark an alert as resolved."""
    async with get_session() as session:
        alert = await session.get(SecurityAlert, alert_id)
        if not alert:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Alert not found.")
        alert.is_resolved = True
        session.add(alert)
    return {"alert_id": alert_id, "message": "Alert resolved."}


# ── WebSocket /alerts/ws ──────────────────────────────────────────
@router.websocket("/ws")
async def ws_alerts(websocket: WebSocket):
    """Live alert feed — pushes new alerts to dashboard instantly."""
    await websocket.accept()
    alert_clients.add(websocket)
    print(f"[ALERTS] Dashboard connected. Total: {len(alert_clients)}")
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        alert_clients.discard(websocket)
        print(f"[ALERTS] Dashboard disconnected. Total: {len(alert_clients)}")


# ── Broadcast helper ──────────────────────────────────────────────
async def broadcast_alert(alert_data: dict) -> None:
    """Called from verify.py when an alert fires."""
    dead = set()
    for client in alert_clients:
        try:
            await client.send_text(json.dumps(alert_data))
        except Exception:
            dead.add(client)
    alert_clients -= dead