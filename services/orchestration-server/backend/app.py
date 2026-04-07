from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.orchestrator import router as orchestrator_router
from backend.config import Settings, get_settings
from backend.integrations.openai_client import OpenAIOrchestratorClient
from backend.mcp.runtime import discover_registry
from backend.orchestrator.engine import OrchestratorEngine
from backend.orchestrator.prompts import PromptManager
from backend.orchestrator.store import FileBackedSessionStore
from backend.orchestrator.tools.books_knowledge import BooksKnowledgeForNewSession


def build_engine(settings: Settings) -> OrchestratorEngine:
    store = FileBackedSessionStore(settings.data_root)
    prompt_manager = PromptManager(settings.prompt_root)
    llm_client = OpenAIOrchestratorClient(settings)
    return OrchestratorEngine(settings, store, prompt_manager, llm_client)


def create_app(
    settings: Settings | None = None,
    engine: OrchestratorEngine | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.orchestrator_engine is not None:
            yield
            return
        store = FileBackedSessionStore(resolved_settings.data_root)
        runtime = await discover_registry(resolved_settings)
        app.state.mcp_runtime = runtime
        books_knowledge = BooksKnowledgeForNewSession(resolved_settings, store, runtime)
        app.state.orchestrator_engine = OrchestratorEngine(
            resolved_settings,
            store,
            PromptManager(resolved_settings.prompt_root),
            OpenAIOrchestratorClient(resolved_settings),
            pre_generation_hook=books_knowledge,
        )
        yield

    app = FastAPI(title="Agentic Orchestrator PoC", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.orchestrator_engine = engine

    origins = resolved_settings.cors_origins
    if origins.strip() == "*":
        allow = ["*"]
    else:
        allow = [o.strip() for o in origins.split(",") if o.strip()]
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
