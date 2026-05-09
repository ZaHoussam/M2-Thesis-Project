# ================================================================
#  routers/enroll.py — POST /enroll
#  One embedding per user — no multiple angles
# ================================================================
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
import traceback

from db.session import get_session
from db.models import User, FaceEmbedding
from schemas.enroll import EnrollRequest, EnrollResponse

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

            # Create user
            user = User(
                full_name = body.full_name,
                email     = body.email,
                role      = body.role,
            )
            session.add(user)
            await session.flush()

            # Store single embedding — no angle label needed
            face = FaceEmbedding(
                user_id   = user.id,
                embedding = body.embedding,
            )
            session.add(face)

            user_id   = user.id
            full_name = user.full_name
            email     = user.email

        return EnrollResponse(
            user_id   = user_id,
            full_name = full_name,
            email     = email,
            message   = "User enrolled successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {type(e).__name__}: {str(e)}"
        )