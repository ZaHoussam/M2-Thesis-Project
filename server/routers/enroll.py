# ================================================================
#  routers/enroll.py — POST /enroll
#  Registers a new user with a face embedding
#  PIN and MFA removed — ArcFace only authentication
# ================================================================
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
import traceback

from db.session import get_session
from db.models import User, FaceEmbedding
from schemas.enroll import EnrollRequest, EnrollResponse
from config import settings

router = APIRouter(prefix="/enroll", tags=["Enrollment"])


@router.post("", response_model=EnrollResponse, status_code=201)
async def enroll_user(body: EnrollRequest):
    try:
        async with get_session() as session:

            # Check email not already registered
            existing = await session.scalar(
                select(User).where(User.email == body.email)
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Email {body.email} already registered."
                )

            # Create user — no PIN needed anymore
            user = User(
                full_name = body.full_name,
                email     = body.email,
                role      = body.role,
            )
            session.add(user)
            await session.flush()

            # Store face embedding
            face = FaceEmbedding(
                user_id     = user.id,
                embedding   = body.embedding,
                angle_label = body.angle_label,
            )
            session.add(face)

            user_id   = user.id
            full_name = user.full_name
            email     = user.email

        return EnrollResponse(
            user_id   = user_id,
            full_name = full_name,
            email     = email,
            message   = f"User enrolled successfully with angle '{body.angle_label}'.",
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {type(e).__name__}: {str(e)}"
        )


@router.post("/{user_id}/add-angle", response_model=EnrollResponse)
async def add_face_angle(user_id: int, body: EnrollRequest):
    try:
        async with get_session() as session:

            user = await session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found.")

            count = await session.scalar(
                select(func.count()).where(FaceEmbedding.user_id == user_id)
            )
            if count >= settings.max_embeddings_per_user:
                raise HTTPException(
                    status_code=400,
                    detail=f"Max {settings.max_embeddings_per_user} embeddings per user reached."
                )

            face = FaceEmbedding(
                user_id     = user_id,
                embedding   = body.embedding,
                angle_label = body.angle_label,
            )
            session.add(face)

            user_id_out = user.id
            full_name   = user.full_name
            email       = user.email

        return EnrollResponse(
            user_id   = user_id_out,
            full_name = full_name,
            email     = email,
            message   = f"Angle '{body.angle_label}' added. Total: {count + 1}/{settings.max_embeddings_per_user}.",
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {type(e).__name__}: {str(e)}"
        )