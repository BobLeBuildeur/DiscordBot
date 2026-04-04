from __future__ import annotations

import json
from typing import Literal

from fastmcp import FastMCP

from books_mcp.config import get_settings
from books_mcp.generators import generate_book, revise_book
from books_mcp.llm import BooksLLMClient
from books_mcp.search import find_book_names
from books_mcp.storage import (
    BookFrontmatter,
    delete_book_file,
    read_book_body_only,
    safe_book_path,
    write_book_file,
)
from books_mcp.validation import assert_valid_book_name

settings = get_settings()
settings.books_data_dir.mkdir(parents=True, exist_ok=True)

mcp = FastMCP(
    "books-mcp",
    instructions="File-backed knowledge and SOP books with YAML frontmatter (type, summary).",
)


def _llm() -> BooksLLMClient:
    return BooksLLMClient(settings)


@mcp.tool
def write_book(
    type: Literal["knowledge", "sop"],
    context: str,
) -> str:
    """Create a new book from LLM-generated content. Fails if the book file already exists."""
    llm = _llm()
    gen = generate_book(llm, settings, type, context)
    path = safe_book_path(settings.books_data_dir, gen.book_name)
    if path.exists():
        raise ValueError(f"Book already exists: {gen.book_name}")
    fm = BookFrontmatter(type=type, summary=gen.summary)
    write_book_file(settings.books_data_dir, gen.book_name, fm, gen.body_markdown)
    return json.dumps({"book_name": gen.book_name, "path": str(path)})


@mcp.tool
def update_book(book_name: str, feedback: str) -> str:
    """Revise an existing book by incorporating feedback (exact book_name / file stem)."""
    assert_valid_book_name(book_name)
    from books_mcp.storage import parse_book_file, read_book_raw

    raw = read_book_raw(settings.books_data_dir, book_name)
    fm, body = parse_book_file(raw)
    llm = _llm()
    new_summary, new_body = revise_book(
        llm,
        settings,
        book_type=fm.type,
        current_summary=fm.summary,
        body=body,
        feedback=feedback,
    )
    new_fm = BookFrontmatter(type=fm.type, summary=new_summary)
    write_book_file(settings.books_data_dir, book_name, new_fm, new_body)
    return json.dumps({"book_name": book_name, "updated": True})


@mcp.tool
def delete_book(book_name: str) -> str:
    """Delete a book by exact name. Returns whether a file was removed."""
    assert_valid_book_name(book_name)
    removed = delete_book_file(settings.books_data_dir, book_name)
    return json.dumps({"book_name": book_name, "deleted": removed})


@mcp.tool
def find_books(query: str) -> str:
    """Search books: title (stem) match then summary match; returns JSON list of book names."""
    names = find_book_names(settings.books_data_dir, query)
    return json.dumps(names)


@mcp.tool
def get_book(book_name: str) -> str:
    """Return markdown body only (no YAML frontmatter) for an exact book name."""
    assert_valid_book_name(book_name)
    return read_book_body_only(settings.books_data_dir, book_name)


@mcp.resource("book://{name}")
def book_resource(name: str) -> str:
    """Markdown body for a book (no frontmatter)."""
    assert_valid_book_name(name)
    return read_book_body_only(settings.books_data_dir, name)
