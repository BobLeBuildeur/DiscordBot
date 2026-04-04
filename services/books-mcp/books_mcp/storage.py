from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from books_mcp.validation import assert_valid_book_name, sanitize_text


class BookFrontmatter(BaseModel):
    type: str
    summary: str
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, value: object) -> object:
        if value is None:
            return []
        return value


def safe_book_path(data_root: Path, book_name: str) -> Path:
    assert_valid_book_name(book_name)
    path = (data_root / f"{book_name}.md").resolve()
    root = data_root.resolve()
    if not str(path).startswith(str(root)) or path == root:
        raise ValueError("Path escape rejected.")
    return path


def parse_book_file(content: str) -> tuple[BookFrontmatter, str]:
    if not content.startswith("---"):
        raise ValueError("Book file must start with YAML frontmatter delimited by ---")
    end = content.find("\n---", 3)
    if end == -1:
        raise ValueError("Missing closing --- for frontmatter")
    yaml_block = content[3:end].strip()
    body = content[end + 4 :].lstrip("\n")
    raw = yaml.safe_load(yaml_block)
    if not isinstance(raw, dict):
        raise ValueError("Frontmatter must be a mapping")
    fm = BookFrontmatter.model_validate(raw)
    return fm, body


def serialize_book(fm: BookFrontmatter, body: str) -> str:
    dumped = yaml.safe_dump(
        fm.model_dump(),
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=True,
    ).strip()
    return f"---\n{dumped}\n---\n\n{body}"


def atomic_write_text(target: Path, text: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def list_book_stems(data_root: Path) -> list[str]:
    if not data_root.exists():
        return []
    return sorted(p.stem for p in data_root.glob("*.md") if p.is_file())


def read_book_raw(data_root: Path, book_name: str) -> str:
    path = safe_book_path(data_root, book_name)
    if not path.exists():
        raise FileNotFoundError(book_name)
    return path.read_text(encoding="utf-8")


def read_book_body_only(data_root: Path, book_name: str) -> str:
    raw = read_book_raw(data_root, book_name)
    _, body = parse_book_file(raw)
    return body


def write_book_file(data_root: Path, book_name: str, fm: BookFrontmatter, body: str) -> Path:
    body = sanitize_text(body)
    path = safe_book_path(data_root, book_name)
    atomic_write_text(path, serialize_book(fm, body))
    return path


def delete_book_file(data_root: Path, book_name: str) -> bool:
    path = safe_book_path(data_root, book_name)
    if not path.exists():
        return False
    path.unlink()
    return True
