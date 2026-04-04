from __future__ import annotations

from pathlib import Path

from books_mcp.stopwords import load_stopwords, parse_stopwords_file


def test_load_stopwords_nonempty() -> None:
    assert len(load_stopwords()) >= 50


def test_parse_stopwords_skips_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "sw.txt"
    path.write_text(
        "# ignored line\n\n  foo  \n# another\nbar\n",
        encoding="utf-8",
    )
    assert parse_stopwords_file(path) == frozenset({"foo", "bar"})
