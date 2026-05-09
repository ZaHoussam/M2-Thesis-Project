# ================================================================
#  config.py — Typed settings loaded from .env
# ================================================================
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file          = ".env",
        env_file_encoding = "utf-8",
        case_sensitive    = False,
        extra             = "ignore",    # ignore unknown .env variables
    )

    database_url:    str

    threshold_allow: float = 0.50
    threshold_deny:  float = 0.50

    server_host:     str = "0.0.0.0"
    server_port:     int = 8000
    min_face_size:   int = 80


settings = Settings()