# ================================================================
#  config.py — Typed settings loaded from .env
# ================================================================
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ─────────────────────────────────────────────
    database_url: str

    # ── Thresholds (ArcFace recalibrated) ────────────────────
    # ArcFace scores are higher than FaceNet
    # Typical genuine scores: 0.80–0.95
    # Typical impostor scores: 0.20–0.40
    threshold_allow: float = 0.50   # score above this → ALLOW
    threshold_deny:  float = 0.50   # score below this → DENY
                                    # binary — no MFA zone

    # ── Server ───────────────────────────────────────────────
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # ── Enrollment ───────────────────────────────────────────
    max_embeddings_per_user: int = 5
    min_face_size:           int = 80


settings = Settings()