from __future__ import annotations

from backend.orchestrator.engine import OrchestratorEngine
from backend.orchestrator.models import (
    GeneratedResponse,
    NextAction,
    PlanInlineFeedbackItem,
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


def build_engine(
    test_settings,
    llm_client: FakeLLMClient,
    *,
    pre_generation_hook=None,
) -> OrchestratorEngine:
    store = FileBackedSessionStore(test_settings.data_root)
    prompt_manager = PromptManager(test_settings.prompt_root)
    return OrchestratorEngine(
        test_settings,
        store,
        prompt_manager,
        llm_client,
        pre_generation_hook=pre_generation_hook,
    )


def test_pre_generation_hook_runs_after_first_user_turn_before_llm(test_settings):
    """Same Callable[[SessionState], None] contract can back multiple tool strategies later."""
    seen: list[str] = []

    def hook(session):
        seen.append(session.session_id)
        assert session.conversation_history[-1].kind == "problem_statement"

    llm_client = FakeLLMClient(
        state_checks=[
            StateCheck(
                needs_more_information=True,
                next_action=NextAction.ASK_FOLLOW_UP,
                confidence=0.81,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="Need details.",
                missing_information=["x"],
            )
        ],
        follow_up_responses=[
            _response(
                "Question?",
                "Problem Understanding",
                str(test_settings.prompt_root / "problem-understanding.md"),
                0.81,
            )
        ],
    )
    engine = build_engine(test_settings, llm_client, pre_generation_hook=hook)
    result = engine.start_session("Hello")
    assert len(seen) == 1
    assert seen[0] == result.session.session_id
    assert llm_client.state_check_prompts


def test_engine_asks_follow_up_when_confidence_is_below_threshold(test_settings):
    llm_client = FakeLLMClient(
        state_checks=[
            StateCheck(
                needs_more_information=False,
                next_action=NextAction.CREATE_PLAN,
                confidence=0.42,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="The problem statement lacks audience and scope details.",
                missing_information=["audience", "scope"],
            )
        ],
        follow_up_responses=[
            _response(
                (
                    "I understand the broad goal. Who will use this output, "
                    "and what decisions should it support?"
                ),
                "Problem Understanding",
                str(test_settings.prompt_root / "problem-understanding.md"),
                0.58,
            )
        ],
    )

    engine = build_engine(test_settings, llm_client)
    result = engine.start_session("Build an operations reporting workflow.")

    assert result.state_check.next_action == NextAction.ASK_FOLLOW_UP
    assert result.assistant_turn.kind == "follow_up_questions"
    assert "below the configured threshold" in result.state_check.reason
    assert llm_client.follow_up_prompts[0].path.name == "problem-understanding.md"
    assert llm_client.metadata_prompts[0].path.name == "response-metadata.md"
    assert not llm_client.plan_prompts


def test_engine_generates_and_refines_plan_with_latest_plan_in_context(test_settings):
    llm_client = FakeLLMClient(
        state_checks=[
            StateCheck(
                needs_more_information=True,
                next_action=NextAction.ASK_FOLLOW_UP,
                confidence=0.8,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="Need target audience details.",
                missing_information=["target audience"],
            ),
            StateCheck(
                needs_more_information=False,
                next_action=NextAction.CREATE_PLAN,
                confidence=0.92,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="Enough information to create the first plan.",
                missing_information=[],
            ),
            StateCheck(
                needs_more_information=False,
                next_action=NextAction.REFINE_PLAN,
                confidence=0.94,
                confidence_threshold=test_settings.llm_confidence_threshold,
                reason="Feedback is actionable.",
                missing_information=[],
            ),
        ],
        follow_up_responses=[
            _response(
                "To shape the plan well, who is the audience and what outcome matters most?",
                "Problem Understanding",
                str(test_settings.prompt_root / "problem-understanding.md"),
                0.8,
            )
        ],
        plan_responses=[
            _response(
                (
                    "## Goal\n\nCreate the first plan.\n\n## Preconditions\n\n"
                    "- Clarified audience.\n\n## Used Tools\n\n- FastAPI.\n\n## Steps\n\n"
                    "1. Create the workflow.\n\n## Guardrails\n\n- Keep it inspectable."
                ),
                "Plan Generation",
                str(test_settings.prompt_root / "plan-generation.md"),
                0.92,
            )
        ],
        refinement_responses=[
            _response(
                (
                    "## Goal\n\nCreate a revised plan for executives.\n\n## Preconditions\n\n"
                    "- Clarified audience.\n\n## Used Tools\n\n- FastAPI.\n\n## Steps\n\n"
                    "1. Revise the workflow.\n\n## Guardrails\n\n- Keep it inspectable."
                ),
                "Plan Refinement",
                str(test_settings.prompt_root / "plan-refinement.md"),
                0.94,
            )
        ],
    )
    engine = build_engine(test_settings, llm_client)

    first_turn = engine.start_session("Build a planning workflow.")
    assert first_turn.assistant_turn.kind == "follow_up_questions"
    assert llm_client.metadata_prompts[0].path.name == "response-metadata.md"
    session_id = first_turn.session.session_id

    second_turn = engine.advance_session(
        session_id,
        "The audience is the operations leadership team.",
    )
    assert second_turn.assistant_turn.kind == "plan"
    assert second_turn.session.current_plan_markdown.startswith("## Goal")
    assert llm_client.plan_prompts[0].path.name == "plan-generation.md"
    assert llm_client.metadata_prompts[1].path.name == "response-metadata.md"

    third_turn = engine.advance_session(
        session_id,
        "Refine it for executive review and add approval criteria.",
        [
            PlanInlineFeedbackItem(
                quoted_text="Create the first plan.",
                comment="Make this explicitly for executive stakeholders.",
            )
        ],
    )
    assert third_turn.assistant_turn.kind == "plan"
    assert third_turn.session.current_plan_markdown.startswith("## Goal\n\nCreate a revised plan")
    assert len(third_turn.session.plan_versions) == 2
    assert llm_client.refinement_prompts[0].path.name == "plan-refinement.md"
    assert "Create the first plan." in llm_client.refinement_prompts[0].user_prompt
    assert "Inline Plan Feedback" in llm_client.refinement_prompts[0].user_prompt
    assert "Selected text: Create the first plan." in llm_client.refinement_prompts[0].user_prompt
    assert (
        third_turn.session.conversation_history[-2].inline_feedback[0].comment
        == "Make this explicitly for executive stakeholders."
    )
    assert llm_client.metadata_prompts[2].path.name == "response-metadata.md"
