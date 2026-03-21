from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any, Protocol

from pydantic import ValidationError

from backend.config import Settings
from backend.orchestrator.models import NextAction, PromptResponseMetadata, StateCheck
from backend.orchestrator.prompts import BuiltPrompt

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    OpenAI = None

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    def run_state_check(self, prompt: BuiltPrompt) -> StateCheck: ...

    def generate_follow_up_questions_stream(self, prompt: BuiltPrompt) -> Iterator[str]: ...

    def generate_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]: ...

    def refine_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]: ...

    def extract_generation_metadata(
        self, metadata_prompt: BuiltPrompt, generation_prompt: BuiltPrompt
    ) -> PromptResponseMetadata: ...


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

    def extract_generation_metadata(
        self, metadata_prompt: BuiltPrompt, generation_prompt: BuiltPrompt
    ) -> PromptResponseMetadata:
        # Small JSON task; same model as state check unless we add a dedicated setting later.
        try:
            raw = self._run_json_prompt(metadata_prompt, self.settings.openai_state_check_model)
            return PromptResponseMetadata(
                prompt_name=generation_prompt.name,
                prompt_path=str(generation_prompt.path),
                confidence=float(raw.get("confidence", 0.0)),
                next_action=NextAction(raw.get("next_action", NextAction.WAIT_FOR_USER.value)),
                missing_information=list(raw.get("missing_information", [])),
                raw_metadata=raw,
            )
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
            # TODO(observability): Treat metadata extraction failures as a first-class signal:
            # emit metrics, a trace span, or structured events (e.g. metadata_extraction_failed)
            # so operators can detect this path without relying on generic error logs alone.
            logger.warning("Response metadata extraction failed: %s", exc, exc_info=True)
            return PromptResponseMetadata(
                prompt_name=generation_prompt.name,
                prompt_path=str(generation_prompt.path),
                confidence=0.0,
                next_action=NextAction.WAIT_FOR_USER,
                missing_information=["metadata extraction failed"],
                raw_metadata={"error": str(exc)},
            )

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
