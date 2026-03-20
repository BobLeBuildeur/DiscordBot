from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.orchestrator.models import SessionState, TurnRole


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
    ) -> BuiltPrompt:
        return self._build("plan-refinement.md", session, latest_message, "Plan Refinement")

    def _build(
        self,
        filename: str,
        session: SessionState,
        latest_message: str,
        name: str,
    ) -> BuiltPrompt:
        path = self.prompt_root / filename
        system_prompt = path.read_text(encoding="utf-8")
        return BuiltPrompt(
            name=name,
            path=path,
            system_prompt=system_prompt,
            user_prompt=self._render_context(session, latest_message),
        )

    def _render_context(self, session: SessionState, latest_message: str) -> str:
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
