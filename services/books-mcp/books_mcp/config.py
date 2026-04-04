from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


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


def get_settings() -> Settings:
    return Settings()
