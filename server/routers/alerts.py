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

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, desc

from db.session import get_session
from db.models import SecurityAlert

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# ── Connection Manager for WebSockets ─────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[ALERTS] Dashboard connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"[ALERTS] Dashboard disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        # Optimize: Serialize once out of the loop instead of per-client
        payload = json.dumps(message, default=str)
        
        # Broadcast concurrently so a slow client network doesn't halt the queue
        tasks = [client.send_text(payload) for client in self.active_connections]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clean up any dead connections discovered during broadcast
        dead_clients = [
            client for client, res in zip(self.active_connections, results) 
            if isinstance(res, Exception)
        ]
        for client in dead_clients:
            self.disconnect(client)

manager = ConnectionManager()


# ── Response schema ───────────────────────────────────────────────
class AlertEntry(BaseModel):
    id:          int
    lab_id:      int
    alert_type:  str
    description: str
    severity:    str
    is_resolved: bool
    created_at:  datetime

    # Modern Pydantic V2 configuration syntax
    model_config = ConfigDict(from_attributes=True)


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
            raise HTTPException(status_code=404, detail="Alert not found.")
        
        alert.is_resolved = True
        session.add(alert)
        await session.commit()  # Fixed: Added commit to persist changes
        
    return {"alert_id": alert_id, "message": "Alert resolved."}


# ── WebSocket /alerts/ws ──────────────────────────────────────────
@router.websocket("/ws")
async def ws_alerts(websocket: WebSocket):
    """Live alert feed — pushes new alerts to dashboard instantly."""
    await manager.connect(websocket)
    try:
        while True:
            # Efficiently waits for incoming traffic or client-side disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Broadcast helper ──────────────────────────────────────────────
async def broadcast_alert(alert_data: dict) -> None:
    """Called from verify.py when an alert fires."""
    await manager.broadcast(alert_data)