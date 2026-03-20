from __future__ import annotations

import json
from typing import Annotated, Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.orchestrator.engine import OrchestrationResult, OrchestratorEngine

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class CreateSessionRequest(BaseModel):
    problem_statement: str = Field(min_length=1)


class SessionMessageRequest(BaseModel):
    message: str = Field(min_length=1)


def get_engine(request: Request) -> OrchestratorEngine:
    return request.app.state.orchestrator_engine


def _sse_event(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _stream_result(result: OrchestrationResult) -> Iterator[str]:
    yield _sse_event("session", {"session_id": result.session.session_id})
    for chunk in result.iter_chunks():
        yield _sse_event("chunk", {"content": chunk})
    yield _sse_event("final", result.final_event_payload())


@router.post("/sessions")
def create_session(
    payload: CreateSessionRequest,
    engine: Annotated[OrchestratorEngine, Depends(get_engine)],
) -> StreamingResponse:
    result = engine.start_session(payload.problem_statement)
    return StreamingResponse(_stream_result(result), media_type="text/event-stream")


@router.post("/sessions/{session_id}/messages")
def add_message(
    session_id: str,
    payload: SessionMessageRequest,
    engine: Annotated[OrchestratorEngine, Depends(get_engine)],
) -> StreamingResponse:
    result = engine.advance_session(session_id, payload.message)
    return StreamingResponse(_stream_result(result), media_type="text/event-stream")


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    engine: Annotated[OrchestratorEngine, Depends(get_engine)],
) -> dict[str, object]:
    session = engine.get_session(session_id)
    return session.model_dump(mode="json")
