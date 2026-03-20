from __future__ import annotations

from collections.abc import Iterable

import pytest

from backend.config import SERVICE_ROOT, Settings
from backend.orchestrator.models import GeneratedResponse, StateCheck


class FakeLLMClient:
    def __init__(
        self,
        *,
        state_checks: Iterable[StateCheck],
        follow_up_responses: Iterable[GeneratedResponse] = (),
        plan_responses: Iterable[GeneratedResponse] = (),
        refinement_responses: Iterable[GeneratedResponse] = (),
    ) -> None:
        self.state_checks = list(state_checks)
        self.follow_up_responses = list(follow_up_responses)
        self.plan_responses = list(plan_responses)
        self.refinement_responses = list(refinement_responses)
        self.state_check_prompts = []
        self.follow_up_prompts = []
        self.plan_prompts = []
        self.refinement_prompts = []

    def run_state_check(self, prompt):
        self.state_check_prompts.append(prompt)
        return self.state_checks.pop(0)

    def generate_follow_up_questions(self, prompt):
        self.follow_up_prompts.append(prompt)
        return self.follow_up_responses.pop(0)

    def generate_plan(self, prompt):
        self.plan_prompts.append(prompt)
        return self.plan_responses.pop(0)

    def refine_plan(self, prompt):
        self.refinement_prompts.append(prompt)
        return self.refinement_responses.pop(0)


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    return Settings(
        prompt_root=SERVICE_ROOT / "prompts" / "orchestrator",
        data_root=tmp_path / "data" / "orchestrator",
        stream_chunk_size=24,
        llm_confidence_threshold=0.75,
    )
