from __future__ import annotations

import json
import logging
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

log = logging.getLogger(__name__)

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
    log.info("write_book start type=%s context_len=%s", type, len(context))
    if log.isEnabledFor(logging.DEBUG):
        preview = context[:200] + ("..." if len(context) > 200 else "")
        log.debug("write_book context preview: %s", preview)
    try:
        llm = _llm()
        gen = generate_book(llm, settings, type, context)
        path = safe_book_path(settings.books_data_dir, gen.book_name)
        if path.exists():
            raise ValueError(f"Book already exists: {gen.book_name}")
        fm = BookFrontmatter(type=type, summary=gen.summary)
        write_book_file(settings.books_data_dir, gen.book_name, fm, gen.body_markdown)
    except ValueError as e:
        log.warning("write_book: %s", e)
        raise
    except Exception:
        log.exception("write_book failed")
        raise
    log.info("write_book success book_name=%s path=%s", gen.book_name, path)
    return json.dumps({"book_name": gen.book_name, "path": str(path)})


@mcp.tool
def update_book(book_name: str, feedback: str) -> str:
    """Revise an existing book by incorporating feedback (exact book_name / file stem)."""
    log.info("update_book start book_name=%s feedback_len=%s", book_name, len(feedback))
    if log.isEnabledFor(logging.DEBUG):
        preview = feedback[:200] + ("..." if len(feedback) > 200 else "")
        log.debug("update_book feedback preview: %s", preview)
    try:
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
    except FileNotFoundError:
        log.warning("update_book not found: %s", book_name)
        raise
    except ValueError as e:
        log.warning("update_book validation or parse error: %s", e)
        raise
    except Exception:
        log.exception("update_book failed")
        raise
    log.info("update_book success book_name=%s", book_name)
    return json.dumps({"book_name": book_name, "updated": True})


@mcp.tool
def delete_book(book_name: str) -> str:
    """Delete a book by exact name. Returns whether a file was removed."""
    log.info("delete_book start book_name=%s", book_name)
    try:
        assert_valid_book_name(book_name)
        removed = delete_book_file(settings.books_data_dir, book_name)
    except ValueError as e:
        log.warning("delete_book invalid name: %s", e)
        raise
    except Exception:
        log.exception("delete_book failed")
        raise
    log.info("delete_book done book_name=%s removed=%s", book_name, removed)
    return json.dumps({"book_name": book_name, "deleted": removed})


@mcp.tool
def find_books(query: str) -> str:
    """Search books: title (stem) match then summary match; returns JSON list of book names."""
    log.info("find_books start query=%s query_len=%s", query, len(query))
    if log.isEnabledFor(logging.DEBUG):
        log.debug("find_books query preview: %s", query[:200] + ("..." if len(query) > 200 else ""))
    try:
        names = find_book_names(settings.books_data_dir, query)
    except Exception:
        log.exception("find_books failed query=%s", query)
        raise
    log.info("find_books success query=%s count=%s", query, len(names))
    return json.dumps(names)


@mcp.tool
def get_book(book_name: str) -> str:
    """Return markdown body only (no YAML frontmatter) for an exact book name."""
    log.info("get_book start book_name=%s", book_name)
    try:
        assert_valid_book_name(book_name)
        body = read_book_body_only(settings.books_data_dir, book_name)
    except FileNotFoundError:
        log.warning("get_book not found: %s", book_name)
        raise
    except ValueError as e:
        log.warning("get_book validation error: %s", e)
        raise
    except Exception:
        log.exception("get_book failed")
        raise
    log.info("get_book success book_name=%s body_len=%s", book_name, len(body))
    return body


@mcp.resource("book://{name}")
def book_resource(name: str) -> str:
    """Markdown body for a book (no frontmatter)."""
    log.info("book_resource read start name=%s", name)
    try:
        assert_valid_book_name(name)
        body = read_book_body_only(settings.books_data_dir, name)
    except FileNotFoundError:
        log.warning("book_resource not found: %s", name)
        raise
    except ValueError as e:
        log.warning("book_resource invalid name: %s", e)
        raise
    except Exception:
        log.exception("book_resource read failed name=%s", name)
        raise
    log.info("book_resource read success name=%s body_len=%s", name, len(body))
    return body
