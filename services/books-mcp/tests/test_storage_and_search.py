from __future__ import annotations

from pathlib import Path

import pytest

from books_mcp.llm import BooksLLMClient
from books_mcp.search import find_book_names
from books_mcp.storage import BookFrontmatter, parse_book_file, write_book_file

# Default product threshold: match plan / config default.
_RATIO = 0.3


def _minimal_book(tmp_path: Path, stem: str) -> None:
    fm = BookFrontmatter(type="knowledge", summary="summary", tags=["tag"])
    write_book_file(tmp_path, stem, fm, "body\n")


def test_parse_roundtrip(tmp_path: Path) -> None:
    fm = BookFrontmatter(type="knowledge", summary="About widgets")
    target = write_book_file(tmp_path, "alpha-beta-gamma-delta-epsilon", fm, "# Body\n")
    raw = target.read_text(encoding="utf-8")
    out_fm, body = parse_book_file(raw)
    assert out_fm.type == "knowledge"
    assert out_fm.summary == "About widgets"
    assert out_fm.tags == []
    assert "Body" in body


def test_find_books_acme_short_stem(tmp_path: Path) -> None:
    """Intent token matches a high fraction of short stems."""
    _minimal_book(tmp_path, "acme-guide")
    _minimal_book(tmp_path, "other-guide")
    names = find_book_names(tmp_path, "acme", ratio_threshold=_RATIO)
    assert names == ["acme-guide"]


def test_find_books_ratio_below_threshold_dropped(tmp_path: Path) -> None:
    """Many segments, one token: ratio can fall at or below threshold."""
    _minimal_book(tmp_path, "x-y-z-w-a-b-c-d-e-f")
    names = find_book_names(tmp_path, "x", ratio_threshold=_RATIO)
    assert names == []


def test_extract_search_intent_heuristic_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from books_mcp.config import Settings

    s = Settings(openai_api_key=None)
    client = BooksLLMClient(s)
    # .env or the environment may still supply a key; force offline heuristic for this unit test.
    client._client = None  # noqa: SLF001
    assert client.extract_search_intent("How to build a house") == "how to build a house"


# --- Explicit matrix (intents simulate LLM output from user text) ---


def test_example_how_to_build_a_house(tmp_path: Path) -> None:
    _minimal_book(tmp_path, "build-a-house")
    assert "build-a-house" in find_book_names(tmp_path, "build house", ratio_threshold=_RATIO)


def test_example_paint_a_car_red(tmp_path: Path) -> None:
    _minimal_book(tmp_path, "paint-car")
    assert "paint-car" in find_book_names(tmp_path, "paint car red", ratio_threshold=_RATIO)


def test_example_learn_to_sail_dingy_sailing_basics(tmp_path: Path) -> None:
    _minimal_book(tmp_path, "sailing-basics")
    assert "sailing-basics" in find_book_names(tmp_path, "sailing basics", ratio_threshold=_RATIO)


def test_example_bake_a_cake_not_cook_a_meal(tmp_path: Path) -> None:
    _minimal_book(tmp_path, "cook-a-meal")
    assert find_book_names(tmp_path, "bake cake", ratio_threshold=_RATIO) == []


def test_example_wedding_planning_guide(tmp_path: Path) -> None:
    _minimal_book(tmp_path, "wedding-planning-guide")
    assert "wedding-planning-guide" in find_book_names(
        tmp_path, "wedding planning guide", ratio_threshold=_RATIO
    )


def test_example_wedding_intent_not_intimate_party_book(tmp_path: Path) -> None:
    _minimal_book(tmp_path, "wedding-planning-guide")
    _minimal_book(tmp_path, "instructions-on-intimate-party-setup")
    names = find_book_names(tmp_path, "wedding planning guide", ratio_threshold=_RATIO)
    assert "wedding-planning-guide" in names
    assert "instructions-on-intimate-party-setup" not in names
