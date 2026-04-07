from __future__ import annotations

import json
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

MAX_TAGS = 24
MAX_TAG_LEN = 64


@dataclass
class GeneratedBook:
    book_name: str
    summary: str
    body_markdown: str
    tags: list[str]


def _normalize_tags_from_llm(data: dict) -> list[str]:
    raw = data.get("tags")
    if raw is None:
        raise ValueError("Missing required field: tags")
    if not isinstance(raw, list):
        raise ValueError("tags must be a list of strings")
    out: list[str] = []
    for item in raw:
        t = sanitize_text(str(item)).strip()
        if not t:
            continue
        t = t[:MAX_TAG_LEN]
        out.append(t)
        if len(out) >= MAX_TAGS:
            break
    if not out:
        raise ValueError("At least one non-empty tag is required")
    return out


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
        '"summary": "<short summary; must end with related keywords, e.g. ... — keyword1, keyword2>", '
        '"tags": ["<keyword>", "..."], '
        '"body_markdown": "<markdown body>"}'
    )
    data = llm.complete_json_system_user(
        system=system, user=user, analytics_span_name="books_generate_book"
    )
    title_phrase = sanitize_text(str(data.get("title_phrase", ""))).strip()
    summary = sanitize_text(str(data.get("summary", ""))).strip()
    body = sanitize_text(str(data.get("body_markdown", "")))
    tags = _normalize_tags_from_llm(data)
    slug = slugify_phrase(title_phrase)
    if not slug:
        raise ValueError("Could not derive kebab-case slug from title_phrase")
    validate_slug_word_count(slug)
    enforce_max_length(body, settings.books_max_content_chars)
    if len(summary) > 500:
        raise ValueError("Summary is too long (max 500 characters).")
    return GeneratedBook(book_name=slug, summary=summary, body_markdown=body, tags=tags)


def revise_book(
    llm: BooksLLMClient,
    settings: Settings,
    *,
    book_type: str,
    current_summary: str,
    current_tags: list[str],
    body: str,
    feedback: str,
) -> tuple[str, str, list[str]]:
    system = _load_revise_prompt()
    tags_json = json.dumps(current_tags)
    user = "\n".join(
        [
            f"# Book type\n{book_type}",
            f"# Current summary\n{current_summary}",
            f"# Current tags (JSON array)\n{tags_json}",
            f"# Current body\n{body}",
            f"# Feedback to incorporate\n{feedback}",
            "",
            "Respond with JSON only:",
            '{"summary": "<updated summary; end with related keywords consistent with tags>", '
            '"tags": ["<keyword>", "..."], '
            '"body_markdown": "<full revised body>"}',
        ]
    )
    data = llm.complete_json_system_user(
        system=system, user=user, analytics_span_name="books_revise_book"
    )
    summary = sanitize_text(str(data.get("summary", ""))).strip()
    new_body = sanitize_text(str(data.get("body_markdown", "")))
    tags = _normalize_tags_from_llm(data)
    enforce_max_length(new_body, settings.books_max_content_chars)
    if len(summary) > 500:
        raise ValueError("Summary is too long (max 500 characters).")
    return summary, new_body, tags
