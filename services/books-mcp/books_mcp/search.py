"""Book discovery by **stem match ratio**: intent tokens vs kebab-case filename segments.

``find_books`` (in :mod:`books_mcp.server`) first obtains a short **intent** string via
:meth:`books_mcp.llm.BooksLLMClient.extract_search_intent` (LLM, or the first *N* words
without an API key), then scores each book stem. There is **no** summary/tag filter in
this module—only the stem matters.
"""

from __future__ import annotations

import re
from pathlib import Path

from books_mcp.storage import list_book_stems

_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Minimum length for prefix matches between intent tokens and stem segments (``plan``/``planning``).
_PREFIX_MIN_LEN = 4


def tokenize_intent(intent: str) -> list[str]:
    """Lowercase alphanumeric tokens from *intent*."""
    return _TOKEN_RE.findall(intent.lower())


def ratio_for_stem(stem: str, intent_tokens: list[str]) -> float:
    """Return matched_segments / len(segments) for *stem* (hyphen-split, non-empty)."""
    segments = [s for s in stem.lower().split("-") if s]
    if not segments:
        return 0.0
    matched = sum(
        1 for seg in segments if any(_segment_matches_token(seg, t) for t in intent_tokens)
    )
    return matched / len(segments)


def _segment_matches_token(seg: str, token: str) -> bool:
    if seg == token:
        return True
    if len(token) >= _PREFIX_MIN_LEN and (seg.startswith(token) or token.startswith(seg)):
        return True
    if len(seg) >= _PREFIX_MIN_LEN and (seg.startswith(token) or token.startswith(seg)):
        return True
    return False


def find_book_names(data_root: Path, intent: str, *, ratio_threshold: float) -> list[str]:
    """Return book stems whose **stem match ratio** is **strictly greater** than *ratio_threshold*.

    The ratio is the fraction of hyphen-separated stem segments that match at least one
    intent token (equality or prefix match with length >= :data:`_PREFIX_MIN_LEN`).
    """
    intent_tokens = tokenize_intent(intent)
    if not intent_tokens:
        return []

    out: list[str] = []
    for stem in list_book_stems(data_root):
        if ratio_for_stem(stem, intent_tokens) > ratio_threshold:
            out.append(stem)
    return sorted(out)
