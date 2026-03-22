from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class NextAction(str, Enum):
    ASK_FOLLOW_UP = "ask_follow_up"
    CREATE_PLAN = "create_plan"
    REFINE_PLAN = "refine_plan"
    WAIT_FOR_USER = "wait_for_user"


class TurnRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class TurnRecord(BaseModel):
    role: TurnRole
    kind: str
    content: str
    inline_feedback: list["PlanInlineFeedbackItem"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    prompt_name: str | None = None
    prompt_path: str | None = None


class StateCheck(BaseModel):
    needs_more_information: bool
    next_action: NextAction
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_threshold: float = Field(ge=0.0, le=1.0)
    reason: str
    missing_information: list[str] = Field(default_factory=list)


class PromptResponseMetadata(BaseModel):
    prompt_name: str
    prompt_path: str
    confidence: float = Field(ge=0.0, le=1.0)
    next_action: NextAction
    missing_information: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedResponse(BaseModel):
    content: str
    metadata: PromptResponseMetadata


class PlanInlineFeedbackItem(BaseModel):
    quoted_text: str = Field(min_length=1)
    comment: str = Field(min_length=1)


class PlanVersion(BaseModel):
    version: int
    markdown: str
    created_at: datetime = Field(default_factory=utc_now)
    source_action: NextAction
    based_on_user_message: str | None = None


class StepArtifact(BaseModel):
    step_index: int
    kind: str
    created_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    schema_version: str = "1.0"
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    problem_statement: str
    conversation_history: list[TurnRecord] = Field(default_factory=list)
    current_plan_markdown: str | None = None
    plan_versions: list[PlanVersion] = Field(default_factory=list)
    latest_state_check: StateCheck | None = None
    latest_response_metadata: PromptResponseMetadata | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    step_count: int = 0
