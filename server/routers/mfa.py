# ================================================================
#  routers/mfa.py — POST /verify-mfa
#  Validates MFA token + PIN after a Zone B challenge
# ================================================================
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from core.jwt import verify_mfa_token
from core.security import verify_pin
from db.session import get_session
from db.models import MfaSession, User, AccessLog
from schemas.auth import MfaVerifyRequest, MfaVerifyResponse

router = APIRouter(prefix="/verify-mfa", tags=["MFA"])


@router.post("", response_model=MfaVerifyResponse)
async def verify_mfa(body: MfaVerifyRequest):
    # Step 1 — decode and validate JWT signature + expiry
    try:
        payload = verify_mfa_token(body.mfa_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = int(payload["sub"])
    jti     = payload["jti"]

    async with get_session() as session:

        # Step 2 — look up mfa_session row by jti
        mfa_sess = await session.scalar(
            select(MfaSession).where(MfaSession.jti == jti)
        )

        if not mfa_sess:
            raise HTTPException(status_code=401, detail="MFA session not found.")

        if mfa_sess.is_used:
            raise HTTPException(status_code=401, detail="MFA token already used.")

        if mfa_sess.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="MFA token has expired.")

        # Step 3 — verify PIN against stored bcrypt hash
        user = await session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive.")

        pin_ok = verify_pin(body.pin, user.pin_hash)

        # Step 4 — mark token as used (prevent replay)
        mfa_sess.is_used = True

        # Step 5 — log outcome
        outcome = "MFA_SUCCESS" if pin_ok else "MFA_FAIL"
        log = AccessLog(
            user_id          = user_id,
            lab_id           = mfa_sess.lab_id,
            outcome          = outcome,
            similarity_score = mfa_sess.similarity_score,
            mfa_session_id   = mfa_sess.id,
        )
        session.add(log)

    if not pin_ok:
        return MfaVerifyResponse(
            decision = "MFA_FAIL",
            user_id  = None,
            message  = "Incorrect PIN. Access denied.",
        )

    return MfaVerifyResponse(
        decision = "MFA_SUCCESS",
        user_id  = user_id,
        message  = f"PIN verified. Welcome, {user.full_name}!",
    )
