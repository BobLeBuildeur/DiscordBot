from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any, Protocol

from backend.config import Settings
from backend.orchestrator.models import (
    GeneratedResponse,
    NextAction,
    PromptResponseMetadata,
    StateCheck,
)
from backend.orchestrator.prompts import BuiltPrompt

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    OpenAI = None


class LLMClient(Protocol):
    def run_state_check(self, prompt: BuiltPrompt) -> StateCheck: ...

    def generate_follow_up_questions_stream(self, prompt: BuiltPrompt) -> Iterator[str]: ...

    def generate_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]: ...

    def refine_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]: ...

    def finalize_generation(self, accumulated: str, prompt: BuiltPrompt) -> GeneratedResponse: ...


class OpenAIOrchestratorClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = (
            OpenAI(api_key=settings.openai_api_key) if OpenAI and settings.openai_api_key else None
        )

    def run_state_check(self, prompt: BuiltPrompt) -> StateCheck:
        payload = self._run_json_prompt(prompt, self.settings.openai_state_check_model)
        payload["confidence_threshold"] = self.settings.llm_confidence_threshold
        return StateCheck.model_validate(payload)

    def generate_follow_up_questions_stream(self, prompt: BuiltPrompt) -> Iterator[str]:
        yield from self._stream_text_prompt(prompt, self.settings.openai_generation_model)

    def generate_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]:
        yield from self._stream_text_prompt(prompt, self.settings.openai_generation_model)

    def refine_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]:
        yield from self._stream_text_prompt(prompt, self.settings.openai_generation_model)

    def finalize_generation(self, accumulated: str, prompt: BuiltPrompt) -> GeneratedResponse:
        content, raw_metadata = _split_markdown_and_metadata(accumulated)
        metadata = PromptResponseMetadata(
            prompt_name=prompt.name,
            prompt_path=str(prompt.path),
            confidence=float(raw_metadata.get("confidence", 0.0)),
            next_action=NextAction(raw_metadata.get("next_action", NextAction.WAIT_FOR_USER.value)),
            missing_information=list(raw_metadata.get("missing_information", [])),
            raw_metadata=raw_metadata,
        )
        return GeneratedResponse(content=content, metadata=metadata)

    def _run_json_prompt(self, prompt: BuiltPrompt, model: str) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI-backed orchestrator.")

        response = self._client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def _stream_text_prompt(self, prompt: BuiltPrompt, model: str) -> Iterator[str]:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI-backed orchestrator.")

        stream = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta.content if choice.delta else None
            if delta:
                yield delta


def _split_markdown_and_metadata(text: str) -> tuple[str, dict[str, Any]]:
    matches = list(re.finditer(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL))
    if not matches:
        return text.strip(), {}

    last_match = matches[-1]
    markdown = text[: last_match.start()].strip()
    metadata = json.loads(last_match.group(1))
    return markdown, metadata
