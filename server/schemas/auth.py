# ================================================================
#  schemas/auth.py — Request / response models
# ================================================================
from pydantic import BaseModel
from typing import Literal


class VerifyRequest(BaseModel):
    embedding: list[float]
    lab_id:    int


class VerifyResponse(BaseModel):
    decision:         Literal["ALLOW", "DENY"]
    similarity_score: float
    user_id:          int | None = None
    margin:           float | None = None
    message:          str