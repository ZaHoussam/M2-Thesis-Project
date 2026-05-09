# ================================================================
#  db/models.py — SQLAlchemy ORM models
#  Updated for v2.0 — MFA removed, PIN removed
# ================================================================
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, CheckConstraint, DateTime,
    Float, ForeignKey, Integer, String, ARRAY
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.session import Base


# ── Labs ─────────────────────────────────────────────────────────
class Lab(Base):
    __tablename__ = "labs"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    name:       Mapped[str]      = mapped_column(String(100), nullable=False)
    location:   Mapped[str]      = mapped_column(String(255), nullable=True)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ── Users ─────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    full_name:  Mapped[str]      = mapped_column(String(150), nullable=False)
    email:      Mapped[str]      = mapped_column(String(255), nullable=False, unique=True)
    role:       Mapped[str]      = mapped_column(String(50), default="researcher")
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Removed: mfa_sessions relationship
    embeddings: Mapped[list["FaceEmbedding"]] = relationship(
        back_populates = "user",
        cascade        = "all, delete-orphan"
    )


# ── Face Embeddings ───────────────────────────────────────────────
class FaceEmbedding(Base):
    __tablename__  = "face_embeddings"
    __table_args__ = (
        CheckConstraint("array_length(embedding, 1) = 512", name="chk_embedding_length"),
    )

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    embedding:  Mapped[list]     = mapped_column(ARRAY(Float), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="embeddings")


# ── Access Logs ───────────────────────────────────────────────────
class AccessLog(Base):
    __tablename__  = "access_logs"
    __table_args__ = (
        # Removed MFA outcomes — binary only
        CheckConstraint(
            "outcome IN ('ALLOW', 'DENY')",
            name = "chk_outcome"
        ),
    )

    id:               Mapped[int]      = mapped_column(Integer, primary_key=True)
    user_id:          Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    lab_id:           Mapped[int]      = mapped_column(ForeignKey("labs.id",  ondelete="CASCADE"))
    outcome:          Mapped[str]      = mapped_column(String(20), nullable=False)
    similarity_score: Mapped[float]    = mapped_column(Float, nullable=True)
    created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())