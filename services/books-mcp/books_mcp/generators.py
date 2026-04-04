from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from books_mcp.config import PACKAGE_ROOT, Settings
from books_mcp.llm import BooksLLMClient
from books_mcp.validation import (
    enforce_max_length,
    sanitize_text,
    slugify_phrase,
    validate_slug_word_count,
)

BookType = Literal["knowledge", "sop"]


@dataclass
class GeneratedBook:
    book_name: str
    summary: str
    body_markdown: str


def _load_prompt(name: str) -> str:
    path = PACKAGE_ROOT / "prompts" / "generators" / name
    return path.read_text(encoding="utf-8")


def _load_revise_prompt() -> str:
    path = PACKAGE_ROOT / "prompts" / "revise.md"
    return path.read_text(encoding="utf-8")


def generate_book(llm: BooksLLMClient, settings: Settings, book_type: BookType, context: str) -> GeneratedBook:
    if book_type == "knowledge":
        system = _load_prompt("knowledge.md")
    else:
        system = _load_prompt("sop.md")
    user = f"# Context\n{context.strip()}\n\nRespond with JSON only:\n"
    user += (
        '{"title_phrase": "<5-20 word descriptive title>", '
        '"summary": "<short summary for frontmatter>", '
        '"body_markdown": "<markdown body>"}'
    )
    data = llm.complete_json_system_user(system=system, user=user)
    title_phrase = sanitize_text(str(data.get("title_phrase", ""))).strip()
    summary = sanitize_text(str(data.get("summary", ""))).strip()
    body = sanitize_text(str(data.get("body_markdown", "")))
    slug = slugify_phrase(title_phrase)
    if not slug:
        raise ValueError("Could not derive kebab-case slug from title_phrase")
    validate_slug_word_count(slug)
    enforce_max_length(body, settings.books_max_content_chars)
    if len(summary) > 500:
        raise ValueError("Summary is too long (max 500 characters).")
    return GeneratedBook(book_name=slug, summary=summary, body_markdown=body)


def revise_book(
    llm: BooksLLMClient,
    settings: Settings,
    *,
    book_type: str,
    current_summary: str,
    body: str,
    feedback: str,
) -> tuple[str, str]:
    system = _load_revise_prompt()
    user = "\n".join(
        [
            f"# Book type\n{book_type}",
            f"# Current summary\n{current_summary}",
            f"# Current body\n{body}",
            f"# Feedback to incorporate\n{feedback}",
            "",
            "Respond with JSON only:",
            '{"summary": "<updated summary if needed>", "body_markdown": "<full revised body>"}',
        ]
    )
    data = llm.complete_json_system_user(system=system, user=user)
    summary = sanitize_text(str(data.get("summary", ""))).strip()
    new_body = sanitize_text(str(data.get("body_markdown", "")))
    enforce_max_length(new_body, settings.books_max_content_chars)
    if len(summary) > 500:
        raise ValueError("Summary is too long (max 500 characters).")
    return summary, new_body
