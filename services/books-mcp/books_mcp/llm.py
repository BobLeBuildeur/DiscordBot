from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from books_mcp.config import Settings


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

    def complete_json_system_user(self, *, system: str, user: str) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not set; cannot generate books.")
        resp = self._client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        content = resp.choices[0].message.content
        if not content:
            raise RuntimeError("Empty model response")
        return _extract_json_object(content)
