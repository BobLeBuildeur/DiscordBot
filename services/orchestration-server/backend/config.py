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
    )

    llm_confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    openai_api_key: str | None = None
    openai_state_check_model: str = "gpt-4.1-mini"
    openai_generation_model: str = "gpt-4.1-mini"
    prompt_root: Path = SERVICE_ROOT / "prompts" / "orchestrator"
    data_root: Path = SERVICE_ROOT / "data" / "orchestrator"
    stream_chunk_size: int = Field(default=160, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
