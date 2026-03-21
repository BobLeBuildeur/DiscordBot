from __future__ import annotations

import json

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.orchestrator.engine import OrchestratorEngine
from backend.orchestrator.models import (
    GeneratedResponse,
    NextAction,
    PromptResponseMetadata,
    StateCheck,
)
from backend.orchestrator.prompts import PromptManager
from backend.orchestrator.store import FileBackedSessionStore
from tests.conftest import FakeLLMClient


def _response(
    content: str,
    prompt_name: str,
    prompt_path: str,
    confidence: float,
) -> GeneratedResponse:
    return GeneratedResponse(
        content=content,
        metadata=PromptResponseMetadata(
            prompt_name=prompt_name,
            prompt_path=prompt_path,
            confidence=confidence,
            next_action=NextAction.WAIT_FOR_USER,
            missing_information=[],
            raw_metadata={"confidence": confidence},
        ),
    )


def _build_test_client(test_settings, llm_client: FakeLLMClient) -> TestClient:
    engine = OrchestratorEngine(
        test_settings,
        FileBackedSessionStore(test_settings.data_root),
        PromptManager(test_settings.prompt_root),
        llm_client,
    )
    return TestClient(create_app(settings=test_settings, engine=engine))


def _parse_sse(text: str) -> dict[str, list[dict[str, object]]]:
    events: dict[str, list[dict[str, object]]] = {}
    for block in [segment.strip() for segment in text.split("\n\n") if segment.strip()]:
        lines = block.splitlines()
        event = lines[0].removeprefix("event: ").strip()
        payload = json.loads(lines[1].removeprefix("data: ").strip())
        events.setdefault(event, []).append(payload)
    return events


def test_api_streams_session_and_persists_final_state(test_settings):
    llm_client = FakeLLMClient(
        state_checks=[
            StateCheck(
                needs_more_information=True,
                next_action=NextAction.ASK_FOLLOW_UP,
                confidence=0.81,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="Need scope details.",
                missing_information=["scope"],
            ),
            StateCheck(
                needs_more_information=False,
                next_action=NextAction.CREATE_PLAN,
                confidence=0.93,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="Enough information for a first draft.",
                missing_information=[],
            ),
        ],
        follow_up_responses=[
            _response(
                "Please share the intended audience and the success criteria.",
                "Problem Understanding",
                str(test_settings.prompt_root / "problem-understanding.md"),
                0.81,
            )
        ],
        plan_responses=[
            _response(
                (
                    "## Goal\n\nDraft the plan.\n\n## Preconditions\n\n- Audience known.\n\n"
                    "## Used Tools\n\n- FastAPI.\n\n## Steps\n\n1. Draft the workflow.\n\n"
                    "## Guardrails\n\n- Keep artifacts on disk."
                ),
                "Plan Generation",
                str(test_settings.prompt_root / "plan-generation.md"),
                0.93,
            )
        ],
    )
    client = _build_test_client(test_settings, llm_client)

    with client.stream(
        "POST",
        "/orchestrator/sessions",
        json={"problem_statement": "Build a planning assistant."},
    ) as response:
        assert response.status_code == 200
        first_stream = "".join(response.iter_text())

    first_events = _parse_sse(first_stream)
    session_id = first_events["session"][0]["session_id"]
    assert first_events["chunk"][0]["content"].startswith("Please share")
    assert first_events["final"][0]["state_check"]["next_action"] == "ask_follow_up"
    assert llm_client.metadata_prompts[0].path.name == "response-metadata.md"

    with client.stream(
        "POST",
        f"/orchestrator/sessions/{session_id}/messages",
        json={
            "message": ("The audience is operations leadership and success means faster approvals.")
        },
    ) as response:
        assert response.status_code == 200
        second_stream = "".join(response.iter_text())

    second_events = _parse_sse(second_stream)
    assert second_events["final"][0]["assistant_kind"] == "plan"
    assert second_events["final"][0]["current_plan_markdown"].startswith("## Goal")
    assert llm_client.metadata_prompts[1].path.name == "response-metadata.md"

    session_response = client.get(f"/orchestrator/sessions/{session_id}")
    assert session_response.status_code == 200
    session_payload = session_response.json()
    assert session_payload["latest_state_check"]["next_action"] == "create_plan"
    assert session_payload["current_plan_markdown"].startswith("## Goal")
