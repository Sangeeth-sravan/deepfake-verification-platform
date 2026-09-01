import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Real-Time Deepfake & Digital Identity Verification Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    DATABASE_URL: str = "sqlite:///./database/verification.db"
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "../uploads"
    REPORT_DIR: str = "../results/reports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
