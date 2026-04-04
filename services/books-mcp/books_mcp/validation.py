from __future__ import annotations

import re

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MIN_TITLE_WORDS = 5
MAX_TITLE_WORDS = 20


def sanitize_text(text: str) -> str:
    """Strip null bytes and normalize newlines for persisted markdown."""
    cleaned = text.replace("\x00", "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    return cleaned


def slugify_phrase(phrase: str) -> str:
    raw = phrase.strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw


def validate_slug_word_count(slug: str) -> None:
    parts = [p for p in slug.split("-") if p]
    n = len(parts)
    if n < MIN_TITLE_WORDS or n > MAX_TITLE_WORDS:
        msg = f"Book title slug must encode {MIN_TITLE_WORDS}-{MAX_TITLE_WORDS} words; got {n}."
        raise ValueError(msg)


def assert_valid_book_name(name: str) -> None:
    if not name or ".." in name or "/" in name or "\\" in name:
        raise ValueError("Invalid book name.")
    if not SLUG_PATTERN.match(name):
        raise ValueError("Book name must be kebab-case (lowercase letters, digits, hyphens).")


def enforce_max_length(text: str, max_chars: int) -> None:
    if len(text) > max_chars:
        raise ValueError(f"Content exceeds maximum length of {max_chars} characters after sanitization.")
