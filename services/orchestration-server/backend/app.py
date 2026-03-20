from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.orchestrator import router as orchestrator_router
from backend.config import Settings, get_settings
from backend.integrations.openai_client import OpenAIOrchestratorClient
from backend.orchestrator.engine import OrchestratorEngine
from backend.orchestrator.prompts import PromptManager
from backend.orchestrator.store import FileBackedSessionStore


def build_engine(settings: Settings) -> OrchestratorEngine:
    store = FileBackedSessionStore(settings.data_root)
    prompt_manager = PromptManager(settings.prompt_root)
    llm_client = OpenAIOrchestratorClient(settings)
    return OrchestratorEngine(settings, store, prompt_manager, llm_client)


def create_app(
    settings: Settings | None = None,
    engine: OrchestratorEngine | None = None,
) -> FastAPI:
    app = FastAPI(title="Agentic Orchestrator PoC")
    resolved_settings = settings or get_settings()
    app.state.settings = resolved_settings
    app.state.orchestrator_engine = engine or build_engine(resolved_settings)

    origins = resolved_settings.cors_origins
    allow = ["*"] if origins.strip() == "*" else [o.strip() for o in origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow,
        allow_credentials=allow != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(orchestrator_router)
    return app


app = create_app()
