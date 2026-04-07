from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from typing import Any, Protocol

from pydantic import ValidationError

from backend.config import Settings
from backend.integrations.llm_analytics import emit_ai_generation, emit_metadata_extraction_failed
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
        payload = self._run_json_prompt(
            prompt, self.settings.openai_state_check_model, span_name="state_check"
        )
        payload["confidence_threshold"] = self.settings.llm_confidence_threshold
        return StateCheck.model_validate(payload)

    def generate_follow_up_questions_stream(self, prompt: BuiltPrompt) -> Iterator[str]:
        yield from self._stream_text_prompt(
            prompt,
            self.settings.openai_generation_model,
            span_name="generation_follow_up",
        )

    def generate_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]:
        yield from self._stream_text_prompt(
            prompt, self.settings.openai_generation_model, span_name="generation_plan"
        )

    def refine_plan_stream(self, prompt: BuiltPrompt) -> Iterator[str]:
        yield from self._stream_text_prompt(
            prompt, self.settings.openai_generation_model, span_name="generation_refine"
        )

    def extract_generation_metadata(
        self, metadata_prompt: BuiltPrompt, generation_prompt: BuiltPrompt
    ) -> PromptResponseMetadata:
        # Small JSON task; same model as state check unless we add a dedicated setting later.
        try:
            raw = self._run_json_prompt(
                metadata_prompt,
                self.settings.openai_state_check_model,
                span_name="response_metadata",
            )
            return PromptResponseMetadata(
                prompt_name=generation_prompt.name,
                prompt_path=str(generation_prompt.path),
                confidence=float(raw.get("confidence", 0.0)),
                next_action=NextAction(raw.get("next_action", NextAction.WAIT_FOR_USER.value)),
                missing_information=list(raw.get("missing_information", [])),
                raw_metadata=raw,
            )
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
            emit_metadata_extraction_failed(type(exc).__name__)
            logger.warning("Response metadata extraction failed: %s", exc, exc_info=True)
            return PromptResponseMetadata(
                prompt_name=generation_prompt.name,
                prompt_path=str(generation_prompt.path),
                confidence=0.0,
                next_action=NextAction.WAIT_FOR_USER,
                missing_information=["metadata extraction failed"],
                raw_metadata={"error": str(exc)},
            )

    def _run_json_prompt(
        self, prompt: BuiltPrompt, model: str, *, span_name: str = "json_prompt"
    ) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI-backed orchestrator.")

        started = time.perf_counter()
        response = self._client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
        )
        in_tok, out_tok = _openai_usage_tokens(getattr(response, "usage", None))
        emit_ai_generation(
            span_name=span_name,
            model=model,
            provider="openai",
            latency_seconds=time.perf_counter() - started,
            input_tokens=in_tok,
            output_tokens=out_tok,
            prompt_name=prompt.name,
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def _stream_text_prompt(
        self, prompt: BuiltPrompt, model: str, *, span_name: str
    ) -> Iterator[str]:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY is required to call the OpenAI-backed orchestrator.")

        started = time.perf_counter()
        stream = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            stream=True,
            stream_options={"include_usage": True},
        )
        usage = None
        for chunk in stream:
            if getattr(chunk, "usage", None) is not None:
                usage = chunk.usage
            choice = chunk.choices[0]
            delta = choice.delta.content if choice.delta else None
            if delta:
                yield delta
        in_tok, out_tok = _openai_usage_tokens(usage)
        emit_ai_generation(
            span_name=span_name,
            model=model,
            provider="openai",
            latency_seconds=time.perf_counter() - started,
            input_tokens=in_tok,
            output_tokens=out_tok,
            prompt_name=prompt.name,
        )


def _openai_usage_tokens(usage: Any) -> tuple[int | None, int | None]:
    if usage is None:
        return None, None
    inp = getattr(usage, "prompt_tokens", None)
    if inp is None:
        inp = getattr(usage, "input_tokens", None)
    out = getattr(usage, "completion_tokens", None)
    if out is None:
        out = getattr(usage, "output_tokens", None)
    return inp, out
