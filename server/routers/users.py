# ================================================================
#  routers/users.py — User management endpoints
#  GET  /users              — list all users
#  GET  /users/{id}         — single user details
#  PUT  /users/{id}/status  — activate or deactivate
#  DELETE /users/{id}       — remove user permanently
# ================================================================
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime

from db.session import get_session
from db.models  import User, FaceEmbedding, AccessLog

router = APIRouter(prefix="/users", tags=["Users"])


# ── Response schemas ──────────────────────────────────────────────
class UserEntry(BaseModel):
    id:               int
    full_name:        str
    email:            str
    role:             str
    is_active:        bool
    embedding_count:  int
    total_attempts:   int
    last_seen:        datetime | None
    created_at:       datetime

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    is_active: bool


# ── GET /users ────────────────────────────────────────────────────
@router.get("", response_model=list[UserEntry])
async def list_users():
    """Return all users with embedding count and last access time."""
    async with get_session() as session:
        rows = await session.execute(select(User).order_by(User.id))
        users = rows.scalars().all()

        result = []
        for user in users:
            # Count embeddings
            emb_count = await session.scalar(
                select(func.count())
                .where(FaceEmbedding.user_id == user.id)
            )
            # Count total attempts
            attempt_count = await session.scalar(
                select(func.count())
                .where(AccessLog.user_id == user.id)
            )
            # Last seen
            last_log = await session.scalar(
                select(AccessLog.created_at)
                .where(AccessLog.user_id == user.id)
                .order_by(AccessLog.created_at.desc())
                .limit(1)
            )
            result.append(UserEntry(
                id              = user.id,
                full_name       = user.full_name,
                email           = user.email,
                role            = user.role,
                is_active       = user.is_active,
                embedding_count = emb_count or 0,
                total_attempts  = attempt_count or 0,
                last_seen       = last_log,
                created_at      = user.created_at,
            ))
        return result


# ── GET /users/{id} ───────────────────────────────────────────────
@router.get("/{user_id}", response_model=UserEntry)
async def get_user(user_id: int):
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        emb_count = await session.scalar(
            select(func.count()).where(FaceEmbedding.user_id == user_id)
        )
        attempt_count = await session.scalar(
            select(func.count()).where(AccessLog.user_id == user_id)
        )
        last_log = await session.scalar(
            select(AccessLog.created_at)
            .where(AccessLog.user_id == user_id)
            .order_by(AccessLog.created_at.desc())
            .limit(1)
        )
        return UserEntry(
            id              = user.id,
            full_name       = user.full_name,
            email           = user.email,
            role            = user.role,
            is_active       = user.is_active,
            embedding_count = emb_count or 0,
            total_attempts  = attempt_count or 0,
            last_seen       = last_log,
            created_at      = user.created_at,
        )


# ── PUT /users/{id}/status ────────────────────────────────────────
@router.put("/{user_id}/status")
async def update_user_status(user_id: int, body: StatusUpdate):
    """Activate or deactivate a user."""
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        user.is_active = body.is_active
        session.add(user)
    return {
        "user_id":   user_id,
        "is_active": body.is_active,
        "message":   f"User {'activated' if body.is_active else 'deactivated'}."
    }


# ── DELETE /users/{id} ────────────────────────────────────────────
@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Permanently delete a user and all their embeddings."""
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        name = user.full_name
        await session.delete(user)
    return {"message": f"User '{name}' deleted permanently."}