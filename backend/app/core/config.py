from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str | None = None
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BOT_TOKEN: str | None = None
    UPLOAD_DIR: str = str(PROJECT_ROOT / "uploads")
    MAX_FILE_SIZE_MB: int = 50

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_database_url(cls, value: str) -> str:
        if isinstance(value, str):
            if value.startswith("postgresql://"):
                return value.replace("postgresql://", "postgresql+asyncpg://", 1)
            if value.startswith("postgresql+psycopg2://"):
                return value.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        return value

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(PROJECT_ROOT / ".env.local")),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
