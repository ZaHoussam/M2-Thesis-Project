# ================================================================
#  client/config.py — Client settings loaded from .env
# ================================================================
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    server_ws_url:   str = "ws://localhost:8000/ws/verify"
    server_rest_url: str = "http://localhost:8000"
    lab_id:          int = 1
    camera_index:    int | str = 0
    onnx_model_path: str = "../models/w600k_r50.onnx"
    min_face_size:   int = 80


settings = ClientSettings()
