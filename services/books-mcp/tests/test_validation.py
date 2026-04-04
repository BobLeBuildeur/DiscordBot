from __future__ import annotations

import pytest

from books_mcp.validation import (
    assert_valid_book_name,
    enforce_max_length,
    sanitize_text,
    slugify_phrase,
    validate_slug_word_count,
)


def test_sanitize_strips_null() -> None:
    assert sanitize_text("a\x00b") == "ab"


def test_slug_word_count() -> None:
    slug = "one-two-three-four-five"
    validate_slug_word_count(slug)
    with pytest.raises(ValueError):
        validate_slug_word_count("one-two")


def test_enforce_max_length() -> None:
    enforce_max_length("a" * 10, 10)
    with pytest.raises(ValueError):
        enforce_max_length("a" * 11, 10)


def test_assert_valid_book_name() -> None:
    assert_valid_book_name("a-b-c-d-e")
    with pytest.raises(ValueError):
        assert_valid_book_name("../etc")
