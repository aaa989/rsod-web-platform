from pydantic import BaseModel
from typing import Optional
import os


class MinIOConfig(BaseModel):
    host: str = "localhost"
    port: int = 9000
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    secure: bool = False
    models_bucket: str = "rsod-models"
    original_bucket: str = "rsod-original"
    results_bucket: str = "rsod-results"

class Settings(BaseModel):
    APP_NAME: str = "RSOD Detection Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "static/uploads"
    RESULT_DIR: str = "static/results"

    YOLO_MODEL_PATH: str = "yolo11n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    minio: MinIOConfig = MinIOConfig()


def get_settings() -> Settings:
    settings = Settings()

    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                line = line.split("#")[0].strip()
                if not line:
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if hasattr(settings, key):
                        try:
                            setattr(settings, key, type(getattr(settings, key))(value))
                        except ValueError:
                            pass

    return settings


settings = get_settings()