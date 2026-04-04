from __future__ import annotations

import json
from typing import Annotated, Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.orchestrator.engine import OrchestratorEngine
from backend.orchestrator.models import PlanInlineFeedbackItem, SessionState

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class CreateSessionRequest(BaseModel):
    problem_statement: str = Field(min_length=1)


class SessionMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    plan_inline_feedback: list[PlanInlineFeedbackItem] = Field(default_factory=list)


def get_engine(request: Request) -> OrchestratorEngine:
    return request.app.state.orchestrator_engine


def session_payload_for_client(session: SessionState) -> dict[str, object]:
    data = session.model_dump(mode="json")
    history = data.get("conversation_history")
    if isinstance(history, list):
        data["conversation_history"] = [h for h in history if h.get("kind") != "knowledge"]
    return data


def _sse_event(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _sse_from_engine_stream(
    stream: Iterator[tuple[str, dict[str, object]]],
) -> Iterator[str]:
    for kind, data in stream:
        if kind == "session":
            yield _sse_event("session", data)
        elif kind == "chunk":
            yield _sse_event("chunk", data)
        elif kind == "final":
            yield _sse_event("final", data)


@router.post("/sessions")
def create_session(
    payload: CreateSessionRequest,
    engine: Annotated[OrchestratorEngine, Depends(get_engine)],
) -> StreamingResponse:
    return StreamingResponse(
        _sse_from_engine_stream(engine.start_session_streaming(payload.problem_statement)),
        media_type="text/event-stream",
    )


@router.post("/sessions/{session_id}/messages")
def add_message(
    session_id: str,
    payload: SessionMessageRequest,
    engine: Annotated[OrchestratorEngine, Depends(get_engine)],
) -> StreamingResponse:
    return StreamingResponse(
        _sse_from_engine_stream(
            engine.advance_session_streaming(
                session_id,
                payload.message,
                payload.plan_inline_feedback,
            ),
        ),
        media_type="text/event-stream",
    )


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    engine: Annotated[OrchestratorEngine, Depends(get_engine)],
) -> dict[str, object]:
    session = engine.get_session(session_id)
    return session_payload_for_client(session)
