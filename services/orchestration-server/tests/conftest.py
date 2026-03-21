from __future__ import annotations

from collections.abc import Iterable, Iterator

import pytest

from backend.config import SERVICE_ROOT, Settings
from backend.orchestrator.models import GeneratedResponse, PromptResponseMetadata, StateCheck
from backend.orchestrator.prompts import BuiltPrompt


class FakeLLMClient:
    def __init__(
        self,
        *,
        state_checks: Iterable[StateCheck],
        follow_up_responses: Iterable[GeneratedResponse] = (),
        plan_responses: Iterable[GeneratedResponse] = (),
        refinement_responses: Iterable[GeneratedResponse] = (),
        stream_chunk_size: int = 24,
    ) -> None:
        self.state_checks = list(state_checks)
        self.follow_up_responses = list(follow_up_responses)
        self.plan_responses = list(plan_responses)
        self.refinement_responses = list(refinement_responses)
        self.stream_chunk_size = stream_chunk_size
        self.state_check_prompts = []
        self.follow_up_prompts = []
        self.plan_prompts = []
        self.refinement_prompts = []
        self.metadata_prompts: list[BuiltPrompt] = []
        self._stream_pending: GeneratedResponse | None = None
        self._stream_accumulated = ""

    def run_state_check(self, prompt):
        self.state_check_prompts.append(prompt)
        return self.state_checks.pop(0)

    def _yield_content_chunks(self, content: str) -> Iterator[str]:
        step = max(1, self.stream_chunk_size)
        for start in range(0, len(content), step):
            yield content[start : start + step]

    def generate_follow_up_questions_stream(self, prompt) -> Iterator[str]:
        self.follow_up_prompts.append(prompt)
        self._stream_pending = self.follow_up_responses.pop(0)
        self._stream_accumulated = ""
        for chunk in self._yield_content_chunks(self._stream_pending.content):
            self._stream_accumulated += chunk
            yield chunk

    def generate_plan_stream(self, prompt) -> Iterator[str]:
        self.plan_prompts.append(prompt)
        self._stream_pending = self.plan_responses.pop(0)
        self._stream_accumulated = ""
        for chunk in self._yield_content_chunks(self._stream_pending.content):
            self._stream_accumulated += chunk
            yield chunk

    def refine_plan_stream(self, prompt) -> Iterator[str]:
        self.refinement_prompts.append(prompt)
        self._stream_pending = self.refinement_responses.pop(0)
        self._stream_accumulated = ""
        for chunk in self._yield_content_chunks(self._stream_pending.content):
            self._stream_accumulated += chunk
            yield chunk

    def extract_generation_metadata(
        self, metadata_prompt: BuiltPrompt, generation_prompt: BuiltPrompt
    ) -> PromptResponseMetadata:
        pending = self._stream_pending
        self._stream_pending = None
        if pending is None:
            raise RuntimeError("extract_generation_metadata called without a preceding stream")
        if self._stream_accumulated != pending.content:
            raise AssertionError("Streamed text does not match pending generated response")
        self._stream_accumulated = ""
        self.metadata_prompts.append(metadata_prompt)
        return pending.metadata.model_copy(
            update={
                "prompt_name": generation_prompt.name,
                "prompt_path": str(generation_prompt.path),
            }
        )


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    return Settings(
        prompt_root=SERVICE_ROOT / "prompts" / "orchestrator",
        data_root=tmp_path / "data" / "orchestrator",
        stream_chunk_size=24,
        llm_confidence_threshold=0.75,
    )
