from __future__ import annotations

from pathlib import Path

from books_mcp.storage import list_book_stems, parse_book_file, read_book_raw


def find_book_names(data_root: Path, query: str) -> list[str]:
    """Stage A: stem matches query (case-insensitive substring). Stage B: summary matches query."""
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
            if q in fm.summary.lower():
                result.append(stem)
        except (OSError, ValueError):
            continue
    return sorted(result)
