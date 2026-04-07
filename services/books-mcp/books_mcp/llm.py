from __future__ import annotations

import json
import re
import time
from typing import Any

from openai import OpenAI

from books_mcp.config import PACKAGE_ROOT, Settings
from books_mcp.posthog_analytics import emit_ai_generation


def _heuristic_search_intent(user_text: str, max_words: int) -> str:
    words = re.findall(r"\S+", user_text.strip())
    if not words:
        return ""
    return " ".join(words[:max_words]).lower()


def _load_search_intent_system_prompt(settings: Settings) -> str:
    path = PACKAGE_ROOT / "prompts" / "search_intent.md"
    raw = path.read_text(encoding="utf-8")
    return raw.replace("{max_words}", str(settings.books_find_intent_max_words))


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("Model did not return a JSON object")
    return json.loads(m.group(0))


class BooksLLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = (
            OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)
            if settings.openai_api_key
            else None
        )

    def complete_json_system_user(
        self, *, system: str, user: str, analytics_span_name: str = "books_llm_json"
    ) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not set; cannot generate books.")
        started = time.perf_counter()
        resp = self._client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        in_tok, out_tok = _openai_usage_tokens(getattr(resp, "usage", None))
        emit_ai_generation(
            span_name=analytics_span_name,
            model=self._settings.openai_model,
            provider="openai",
            latency_seconds=time.perf_counter() - started,
            input_tokens=in_tok,
            output_tokens=out_tok,
            extra={"user_text_length": len(user)},
        )
        content = resp.choices[0].message.content
        if not content:
            raise RuntimeError("Empty model response")
        return _extract_json_object(content)

    def extract_search_intent(self, user_text: str) -> str:
        """Return a short plain-text search intent (at most ``books_find_intent_max_words`` words).

        Without ``OPENAI_API_KEY``, uses the first *N* words of *user_text* (lowercased).
        """
        s = self._settings
        text = user_text.strip()
        if not text:
            return ""
        if self._client is None:
            return _heuristic_search_intent(text, s.books_find_intent_max_words)

        system = _load_search_intent_system_prompt(s)
        started = time.perf_counter()
        resp = self._client.chat.completions.create(
            model=s.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )
        in_tok, out_tok = _openai_usage_tokens(getattr(resp, "usage", None))
        emit_ai_generation(
            span_name="books_search_intent",
            model=s.openai_model,
            provider="openai",
            latency_seconds=time.perf_counter() - started,
            input_tokens=in_tok,
            output_tokens=out_tok,
            extra={"user_text_length": len(text)},
        )
        content = resp.choices[0].message.content
        if not content:
            return _heuristic_search_intent(text, s.books_find_intent_max_words)

        intent = " ".join(content.split())
        words = intent.split()
        if len(words) > s.books_find_intent_max_words:
            intent = " ".join(words[: s.books_find_intent_max_words])
        return intent.lower()


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
