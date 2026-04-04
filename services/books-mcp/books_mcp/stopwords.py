"""Load English stop words for `find_books` token matching.

The word list lives in :file:`stopwords_en.txt` next to this module so operators can
add or remove entries **without changing Python**. Format:

- One lowercase word per line.
- Lines whose first non-whitespace character is ``#`` are comments.
- Blank lines are ignored.

The set is loaded once per process the first time :func:`load_stopwords` runs.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def parse_stopwords_file(path: Path) -> frozenset[str]:
    words: set[str] = set()
    raw = path.read_text(encoding="utf-8")
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        words.add(stripped.lower())
    return frozenset(words)


@lru_cache(maxsize=1)
def load_stopwords() -> frozenset[str]:
    """Return the stopword set from ``stopwords_en.txt`` beside this package."""
    path = Path(__file__).resolve().parent / "stopwords_en.txt"
    return parse_stopwords_file(path)
