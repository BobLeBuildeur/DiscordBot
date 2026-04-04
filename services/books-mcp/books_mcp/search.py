from __future__ import annotations

from pathlib import Path

from books_mcp.storage import BookFrontmatter, list_book_stems, parse_book_file, read_book_raw


def _stage_b_matches(fm: BookFrontmatter, q: str) -> bool:
    if q in fm.summary.lower():
        return True
    return any(q in tag.lower() for tag in fm.tags)


def find_book_names(data_root: Path, query: str) -> list[str]:
    """Stage A: stem matches query (case-insensitive substring). Stage B: summary or tags match query."""
    q = query.strip().lower()
    if not q:
        return []

    stems = list_book_stems(data_root)
    stage_a: list[str] = []
    for stem in stems:
        stem_l = stem.lower()
        if q in stem_l:
            stage_a.append(stem)
            continue
        hyphen_query = q.replace(" ", "-")
        if hyphen_query and hyphen_query in stem_l:
            stage_a.append(stem)

    result: list[str] = []
    for stem in stage_a:
        try:
            raw = read_book_raw(data_root, stem)
            fm, _ = parse_book_file(raw)
            if _stage_b_matches(fm, q):
                result.append(stem)
        except (OSError, ValueError):
            continue
    return sorted(result)
