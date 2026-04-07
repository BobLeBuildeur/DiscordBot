from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parent.parent
MONOREPO_ROOT = SERVICE_ROOT.parent.parent


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
    cors_origins: str = "*"
    monorepo_root: Path = Field(default=MONOREPO_ROOT, validation_alias="MONOREPO_ROOT")
    mcp_registry_path: Path = Field(
        default=SERVICE_ROOT / "config" / "mcp-registry.json",
        validation_alias="MCP_REGISTRY_PATH",
    )
    orch_books_knowledge_max: int = Field(
        default=5,
        ge=0,
        le=50,
        validation_alias=AliasChoices(
            "ORCH_BOOKS_KNOWLEDGE_MAX",
            "ORCH_BOOKS_ENRICHMENT_MAX",
        ),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
