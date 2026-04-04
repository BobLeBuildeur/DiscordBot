from __future__ import annotations

from pathlib import Path

import pytest

from books_mcp.search import find_book_names
from books_mcp.storage import BookFrontmatter, parse_book_file, write_book_file


def test_parse_roundtrip(tmp_path: Path) -> None:
    fm = BookFrontmatter(type="knowledge", summary="About widgets")
    target = write_book_file(tmp_path, "alpha-beta-gamma-delta-epsilon", fm, "# Body\n")
    raw = target.read_text(encoding="utf-8")
    out_fm, body = parse_book_file(raw)
    assert out_fm.type == "knowledge"
    assert out_fm.summary == "About widgets"
    assert "Body" in body


def test_find_books_two_stage(tmp_path: Path) -> None:
    # Same query must match stem (stage A) and summary (stage B).
    fm = BookFrontmatter(type="knowledge", summary="acme operations reporting pipeline")
    write_book_file(
        tmp_path,
        "acme-handbook-for-teams-with-enough-words-in-title-here-now-today",
        fm,
        "x",
    )
    fm2 = BookFrontmatter(type="knowledge", summary="unrelated")
    write_book_file(
        tmp_path,
        "other-handbook-for-teams-with-enough-words-in-title-here-now-today",
        fm2,
        "y",
    )

    q = "acme"
    names = find_book_names(tmp_path, q)
    assert "acme-handbook-for-teams-with-enough-words-in-title-here-now-today" in names
    assert "other-handbook-for-teams-with-enough-words-in-title-here-now-today" not in names


def test_find_books_stage_a_passes_stage_b_fails(tmp_path: Path) -> None:
    """Stem matches (stage A) but summary does not contain the query (stage B) — book is dropped."""
    fm = BookFrontmatter(
        type="knowledge",
        summary="Onboarding checklist with no shared token from the filename",
    )
    write_book_file(
        tmp_path,
        "shared-token-guide-for-new-hires-with-enough-words-in-stem-here",
        fm,
        "body",
    )
    names = find_book_names(tmp_path, "shared-token")
    assert names == []


def test_find_books_title_only_no_summary_match(tmp_path: Path) -> None:
    fm = BookFrontmatter(type="knowledge", summary="something else entirely")
    write_book_file(tmp_path, "foo-bar-baz-qux-quux-corge", fm, "x")
    names = find_book_names(tmp_path, "foo")
    assert names == []
