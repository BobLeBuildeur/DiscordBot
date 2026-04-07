"""Server-side PostHog capture for books MCP LLM calls (optional when POSTHOG_API_KEY is set)."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_posthog_client: Any = None


def _client():
    global _posthog_client
    if _posthog_client is not None:
        return _posthog_client
    api_key = os.environ.get("POSTHOG_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from posthog import Posthog
    except ImportError:
        logger.warning("posthog not installed; books MCP analytics disabled")
        return None
    host = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com").strip() or "https://us.i.posthog.com"
    _posthog_client = Posthog(api_key, host=host)
    return _posthog_client


def emit_ai_generation(
    *,
    span_name: str,
    model: str,
    provider: str,
    latency_seconds: float,
    input_tokens: int | None,
    output_tokens: int | None,
    extra: dict[str, Any] | None = None,
) -> None:
    ph = _client()
    if ph is None:
        return
    props: dict[str, Any] = {
        "$ai_provider": provider,
        "$ai_model": model,
        "$ai_latency": latency_seconds,
        "$ai_span_name": span_name,
        "source": "books-mcp",
    }
    if input_tokens is not None:
        props["$ai_input_tokens"] = input_tokens
    if output_tokens is not None:
        props["$ai_output_tokens"] = output_tokens
    if extra:
        props.update(extra)
    try:
        ph.capture(distinct_id="books_mcp_service", event="$ai_generation", properties=props)
    except Exception:
        logger.exception("PostHog capture failed for books span %s", span_name)
