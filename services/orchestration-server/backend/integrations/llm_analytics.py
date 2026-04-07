"""PostHog LLM analytics context and capture (server-side).

Uses threading.local() so context survives across sync generator yields when Starlette
runs the iterator in a worker thread (ContextVar tokens can be wrong across those hops).
"""

from __future__ import annotations

import logging
import os
import threading
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_tl = threading.local()

_posthog_client: Any = None


def _get_posthog():
    global _posthog_client
    if _posthog_client is not None:
        return _posthog_client
    api_key = os.environ.get("POSTHOG_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from posthog import Posthog
    except ImportError:
        logger.warning("posthog package not installed; LLM analytics disabled")
        return None
    host = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com").strip() or "https://us.i.posthog.com"
    _posthog_client = Posthog(api_key, host=host)
    return _posthog_client


def begin_orchestrator_turn(session_id: str) -> str:
    """Call at the start of a sync engine turn; paired with end_orchestrator_turn."""
    trace_id = str(uuid.uuid4())
    _tl.analytics = {
        "session_id": session_id,
        "trace_id": trace_id,
        "last_span_id": trace_id,
    }
    return trace_id


def end_orchestrator_turn() -> None:
    if hasattr(_tl, "analytics"):
        delattr(_tl, "analytics")


def _ctx() -> dict[str, Any] | None:
    return getattr(_tl, "analytics", None)


def emit_ai_generation(
    *,
    span_name: str,
    model: str,
    provider: str,
    latency_seconds: float,
    input_tokens: int | None,
    output_tokens: int | None,
    prompt_name: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a single $ai_generation-style event to PostHog when configured."""
    client = _get_posthog()
    if client is None:
        return

    ctx = _ctx() or {}
    session_id = str(ctx.get("session_id", "unknown"))
    trace_id = str(ctx.get("trace_id", ""))
    parent_span_id = str(ctx.get("last_span_id", trace_id))
    span_id = str(uuid.uuid4())
    if ctx:
        ctx["last_span_id"] = span_id

    props: dict[str, Any] = {
        "$ai_provider": provider,
        "$ai_model": model,
        "$ai_latency": latency_seconds,
        "$ai_span_name": span_name,
        "$ai_trace_id": trace_id,
        "$ai_span_id": span_id,
        "$ai_parent_id": parent_span_id,
        "source": "orchestration-server",
    }
    if input_tokens is not None:
        props["$ai_input_tokens"] = input_tokens
    if output_tokens is not None:
        props["$ai_output_tokens"] = output_tokens
    if prompt_name:
        props["prompt_name"] = prompt_name
    if extra:
        props.update(extra)

    distinct_id = f"orch_session:{session_id}"
    try:
        client.capture(distinct_id=distinct_id, event="$ai_generation", properties=props)
    except Exception:
        logger.exception("PostHog capture failed for span %s", span_name)


def emit_product_event(event_name: str, properties: dict[str, Any] | None = None) -> None:
    """Optional server-side product events (e.g. turn completed)."""
    client = _get_posthog()
    if client is None:
        return
    ctx = _ctx() or {}
    session_id = str(ctx.get("session_id", "unknown"))
    props = {"source": "orchestration-server", **(properties or {})}
    try:
        client.capture(distinct_id=f"orch_session:{session_id}", event=event_name, properties=props)
    except Exception:
        logger.exception("PostHog product capture failed for %s", event_name)


def emit_metadata_extraction_failed(error_summary: str) -> None:
    client = _get_posthog()
    if client is None:
        return
    ctx = _ctx() or {}
    session_id = str(ctx.get("session_id", "unknown"))
    props = {
        "source": "orchestration-server",
        "error_summary": error_summary[:500],
    }
    try:
        client.capture(
            distinct_id=f"orch_session:{session_id}",
            event="metadata_extraction_failed",
            properties=props,
        )
    except Exception:
        logger.exception("PostHog capture failed for metadata_extraction_failed")
