# ================================================================
#  schemas/enroll.py — Pydantic models for enrollment
#  PIN removed — ArcFace only
# ================================================================
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field


class EnrollRequest(BaseModel):
    full_name:   str         = Field(..., min_length=2, max_length=150)
    email:       EmailStr
    role:        str         = Field(default="researcher")
    embedding:   list[float] = Field(..., min_length=512, max_length=512)


class EnrollResponse(BaseModel):
    user_id:   int
    full_name: str
    email:     str
    message:   str