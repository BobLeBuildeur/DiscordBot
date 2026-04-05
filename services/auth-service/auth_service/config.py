from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    auth_users_dir: Path = Field(
        default=SERVICE_ROOT / "data" / "users",
        validation_alias="AUTH_USERS_DIR",
    )
    jwt_signing_secret: str = Field(
        ...,
        min_length=16,
        validation_alias="JWT_SIGNING_SECRET",
    )
    jwt_expires_days: float = Field(default=30.0, ge=0.01, validation_alias="JWT_EXPIRES_DAYS")
    auth_password_pepper: str | None = Field(default=None, validation_alias="AUTH_PASSWORD_PEPPER")
    cors_origins: str = Field(default="*", validation_alias="AUTH_CORS_ORIGINS")
    auth_http_create_user_enabled: bool = Field(
        default=False,
        validation_alias="AUTH_HTTP_CREATE_USER_ENABLED",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
