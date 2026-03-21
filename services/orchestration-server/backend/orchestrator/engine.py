from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Iterable

from backend.config import Settings
from backend.integrations.openai_client import LLMClient
from backend.orchestrator.models import (
    GeneratedResponse,
    NextAction,
    PlanVersion,
    SessionState,
    StateCheck,
    TurnRecord,
    TurnRole,
)
from backend.orchestrator.prompts import BuiltPrompt, PromptManager
from backend.orchestrator.store import FileBackedSessionStore


@dataclass
class OrchestrationResult:
    session: SessionState
    assistant_turn: TurnRecord
    state_check: StateCheck
    response: GeneratedResponse
    chunk_size: int

    def iter_chunks(self) -> Iterable[str]:
        """Slice full content for tests/helpers (HTTP streaming uses OpenAI deltas)."""
        content = self.assistant_turn.content
        for start in range(0, len(content), self.chunk_size):
            yield content[start : start + self.chunk_size]

    def final_event_payload(self) -> dict[str, object]:
        return {
            "session_id": self.session.session_id,
            "assistant_kind": self.assistant_turn.kind,
            "assistant_message": self.assistant_turn.content,
            "state_check": self.state_check.model_dump(mode="json"),
            "response_metadata": self.response.metadata.model_dump(mode="json"),
            "current_plan_markdown": self.session.current_plan_markdown,
        }


class OrchestratorEngine:
    def __init__(
        self,
        settings: Settings,
        store: FileBackedSessionStore,
        prompt_manager: PromptManager,
        llm_client: LLMClient,
    ) -> None:
        self.settings = settings
        self.store = store
        self.prompt_manager = prompt_manager
        self.llm_client = llm_client

    def start_session(self, problem_statement: str) -> OrchestrationResult:
        session_id: str | None = None
        for kind, data in self.start_session_streaming(problem_statement):
            if kind == "session":
                session_id = str(data["session_id"])
            if kind == "final":
                break
        assert session_id is not None
        return self._result_from_session(self.store.load_session(session_id))

    def start_session_streaming(
        self, problem_statement: str
    ) -> Iterator[tuple[str, dict[str, object]]]:
        session = self.store.create_session(problem_statement=problem_statement)
        initial_turn = TurnRecord(
            role=TurnRole.USER,
            kind="problem_statement",
            content=problem_statement,
        )
        session.conversation_history.append(initial_turn)
        self.store.append_step_artifact(
            session,
            "user-message",
            {"turn": initial_turn.model_dump(mode="json")},
        )
        self.store.save_session(session)
        yield from self._stream_turn(session, problem_statement)

    def advance_session(self, session_id: str, user_message: str) -> OrchestrationResult:
        for kind, _data in self.advance_session_streaming(session_id, user_message):
            if kind == "final":
                break
        return self._result_from_session(self.store.load_session(session_id))

    def advance_session_streaming(
        self, session_id: str, user_message: str
    ) -> Iterator[tuple[str, dict[str, object]]]:
        session = self.store.load_session(session_id)
        message_kind = "plan_feedback" if session.current_plan_markdown else "user_message"
        user_turn = TurnRecord(
            role=TurnRole.USER,
            kind=message_kind,
            content=user_message,
        )
        session.conversation_history.append(user_turn)
        self.store.append_step_artifact(
            session,
            "user-message",
            {"turn": user_turn.model_dump(mode="json")},
        )
        self.store.save_session(session)
        yield from self._stream_turn(session, user_message)

    def get_session(self, session_id: str) -> SessionState:
        return self.store.load_session(session_id)

    def _stream_turn(
        self, session: SessionState, latest_user_message: str
    ) -> Iterator[tuple[str, dict[str, object]]]:
        yield ("session", {"session_id": session.session_id})

        state_prompt = self.prompt_manager.build_state_check_prompt(session, latest_user_message)
        state_check = self.llm_client.run_state_check(state_prompt)
        state_check = self._apply_confidence_gate(state_check)
        session.latest_state_check = state_check
        self.store.append_step_artifact(
            session,
            "state-check",
            {
                "prompt_name": state_prompt.name,
                "prompt_path": str(state_prompt.path),
                "state_check": state_check.model_dump(mode="json"),
            },
        )

        prompt, assistant_kind, stream_kind = self._resolve_generation_prompt(
            session, latest_user_message, state_check
        )

        stream_iter = self._generation_stream(stream_kind, prompt)
        parts: list[str] = []
        for delta in stream_iter:
            parts.append(delta)
            yield ("chunk", {"content": delta})

        full_text = "".join(parts)
        response = self.llm_client.finalize_generation(full_text, prompt)

        assistant_turn = TurnRecord(
            role=TurnRole.ASSISTANT,
            kind=assistant_kind,
            content=response.content,
            prompt_name=response.metadata.prompt_name,
            prompt_path=response.metadata.prompt_path,
        )
        session.conversation_history.append(assistant_turn)
        session.latest_response_metadata = response.metadata

        self.store.append_step_artifact(
            session,
            "assistant-message",
            {
                "turn": assistant_turn.model_dump(mode="json"),
                "metadata": response.metadata.model_dump(mode="json"),
            },
        )

        if assistant_kind == "plan":
            plan_version = PlanVersion(
                version=len(session.plan_versions) + 1,
                markdown=response.content,
                source_action=state_check.next_action,
                based_on_user_message=latest_user_message,
            )
            session.plan_versions.append(plan_version)
            session.current_plan_markdown = response.content
            self.store.append_markdown_artifact(
                session,
                f"plan-v{plan_version.version}",
                response.content,
                {
                    "prompt_name": response.metadata.prompt_name,
                    "prompt_path": response.metadata.prompt_path,
                    "metadata": response.metadata.model_dump(mode="json"),
                    "source_action": state_check.next_action.value,
                },
            )

        self.store.save_session(session)

        result = OrchestrationResult(
            session=session,
            assistant_turn=assistant_turn,
            state_check=state_check,
            response=response,
            chunk_size=self.settings.stream_chunk_size,
        )
        yield ("final", result.final_event_payload())

    def _result_from_session(self, session: SessionState) -> OrchestrationResult:
        assistant_turn = session.conversation_history[-1]
        assert assistant_turn.role == TurnRole.ASSISTANT
        meta = session.latest_response_metadata
        assert meta is not None
        sc = session.latest_state_check
        assert sc is not None
        response = GeneratedResponse(content=assistant_turn.content, metadata=meta)
        return OrchestrationResult(
            session=session,
            assistant_turn=assistant_turn,
            state_check=sc,
            response=response,
            chunk_size=self.settings.stream_chunk_size,
        )

    def _resolve_generation_prompt(
        self,
        session: SessionState,
        latest_user_message: str,
        state_check: StateCheck,
    ) -> tuple[BuiltPrompt, str, str]:
        if state_check.next_action == NextAction.ASK_FOLLOW_UP:
            prompt = self.prompt_manager.build_problem_understanding_prompt(
                session,
                latest_user_message,
            )
            return prompt, "follow_up_questions", "follow_up"

        if state_check.next_action == NextAction.CREATE_PLAN:
            prompt = self.prompt_manager.build_plan_generation_prompt(session, latest_user_message)
            return prompt, "plan", "create_plan"

        prompt = self.prompt_manager.build_plan_refinement_prompt(session, latest_user_message)
        return prompt, "plan", "refine_plan"

    def _generation_stream(self, stream_kind: str, prompt: BuiltPrompt) -> Iterator[str]:
        if stream_kind == "follow_up":
            yield from self.llm_client.generate_follow_up_questions_stream(prompt)
        elif stream_kind == "create_plan":
            yield from self.llm_client.generate_plan_stream(prompt)
        else:
            yield from self.llm_client.refine_plan_stream(prompt)

    def _apply_confidence_gate(self, state_check: StateCheck) -> StateCheck:
        if state_check.confidence >= self.settings.llm_confidence_threshold:
            return state_check

        reason = (
            f"Confidence {state_check.confidence:.2f} is below the configured threshold "
            f"{self.settings.llm_confidence_threshold:.2f}. {state_check.reason}"
        )
        return state_check.model_copy(
            update={
                "needs_more_information": True,
                "next_action": NextAction.ASK_FOLLOW_UP,
                "confidence_threshold": self.settings.llm_confidence_threshold,
                "reason": reason.strip(),
            }
        )
