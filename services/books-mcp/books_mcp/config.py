from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

_DEFAULT_LOG_PATH = PACKAGE_ROOT / "data" / "logs" / "books-mcp.log"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    books_data_dir: Path = Field(
        default=PACKAGE_ROOT / "data" / "books",
        validation_alias="BOOKS_DATA_DIR",
    )
    books_max_content_chars: int = Field(default=1000, ge=1, validation_alias="BOOKS_MAX_CONTENT_CHARS")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", validation_alias="BOOKS_OPENAI_MODEL")
    openai_timeout_seconds: float = Field(default=120.0, ge=5.0, validation_alias="BOOKS_OPENAI_TIMEOUT")

    books_log_path: Path = Field(default=_DEFAULT_LOG_PATH, validation_alias="BOOKS_LOG_PATH")
    books_log_level: str = Field(default="INFO", validation_alias="BOOKS_LOG_LEVEL")
    books_log_max_bytes: int = Field(default=5_242_880, ge=1_024, validation_alias="BOOKS_LOG_MAX_BYTES")
    books_log_backup_count: int = Field(default=3, ge=0, le=20, validation_alias="BOOKS_LOG_BACKUP_COUNT")
    books_log_mirror_stderr: bool = Field(
        default=True,
        validation_alias="BOOKS_LOG_MIRROR_STDERR",
    )


def get_settings() -> Settings:
    return Settings()
