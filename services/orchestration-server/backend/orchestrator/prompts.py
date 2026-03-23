from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.orchestrator.models import PlanInlineFeedbackItem, SessionState, TurnRole


@dataclass(frozen=True)
class BuiltPrompt:
    name: str
    path: Path
    system_prompt: str
    user_prompt: str


class PromptManager:
    def __init__(self, prompt_root: Path) -> None:
        self.prompt_root = prompt_root

    def build_state_check_prompt(self, session: SessionState, latest_message: str) -> BuiltPrompt:
        return self._build("state-check.md", session, latest_message, "State Check")

    def build_problem_understanding_prompt(
        self,
        session: SessionState,
        latest_message: str,
    ) -> BuiltPrompt:
        return self._build(
            "problem-understanding.md",
            session,
            latest_message,
            "Problem Understanding",
        )

    def build_plan_generation_prompt(
        self,
        session: SessionState,
        latest_message: str,
    ) -> BuiltPrompt:
        return self._build("plan-generation.md", session, latest_message, "Plan Generation")

    def build_plan_refinement_prompt(
        self,
        session: SessionState,
        latest_message: str,
        inline_feedback: list[PlanInlineFeedbackItem] | None = None,
    ) -> BuiltPrompt:
        return self._build(
            "plan-refinement.md",
            session,
            latest_message,
            "Plan Refinement",
            inline_feedback=inline_feedback or [],
        )

    def build_response_metadata_prompt(
        self,
        session: SessionState,
        latest_user_message: str,
        assistant_markdown: str,
        assistant_kind: str,
    ) -> BuiltPrompt:
        path = self.prompt_root / "response-metadata.md"
        system_prompt = path.read_text(encoding="utf-8")
        user_prompt = "\n".join(
            [
                self._render_context(session, latest_user_message),
                "",
                "# Assistant message kind",
                assistant_kind,
                "",
                "# Assistant markdown answer",
                assistant_markdown,
            ]
        )
        return BuiltPrompt(
            name="Response Metadata",
            path=path,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _build(
        self,
        filename: str,
        session: SessionState,
        latest_message: str,
        name: str,
        inline_feedback: list[PlanInlineFeedbackItem] | None = None,
    ) -> BuiltPrompt:
        path = self.prompt_root / filename
        system_prompt = path.read_text(encoding="utf-8")
        return BuiltPrompt(
            name=name,
            path=path,
            system_prompt=system_prompt,
            user_prompt=self._render_context(session, latest_message, inline_feedback or []),
        )

    def _render_context(
        self,
        session: SessionState,
        latest_message: str,
        inline_feedback: list[PlanInlineFeedbackItem] | None = None,
    ) -> str:
        feedback = inline_feedback or []
        conversation = self._format_conversation(session)
        latest_plan = session.current_plan_markdown or "None"
        return "\n".join(
            [
                "# Original Problem Statement",
                session.problem_statement,
                "",
                "# Conversation History",
                conversation,
                "",
                "# Latest Analyst Message",
                latest_message,
                "",
                "# Latest Markdown Plan",
                latest_plan,
                "",
                "# Inline Plan Feedback",
                self._format_inline_feedback(feedback),
            ]
        )

    def _format_conversation(self, session: SessionState) -> str:
        if not session.conversation_history:
            return "No prior conversation."

        lines: list[str] = []
        for turn in session.conversation_history:
            role = "Analyst" if turn.role == TurnRole.USER else "Assistant"
            lines.append(f"- {role} ({turn.kind}) at {turn.created_at.isoformat()}: {turn.content}")
        return "\n".join(lines)

    def _format_inline_feedback(self, inline_feedback: list[PlanInlineFeedbackItem]) -> str:
        if not inline_feedback:
            return "No inline feedback provided."

        # TODO(plan-feedback): Ambiguous selections: If the same substring appears multiple times in
        # the plan, PoC may attach feedback to the first match or require disambiguation—call out
        # in release notes.
        lines: list[str] = []
        for index, item in enumerate(inline_feedback, start=1):
            lines.append(f"{index}. Selected text: {item.quoted_text}")
            lines.append(f"   Comment: {item.comment}")
        return "\n".join(lines)
