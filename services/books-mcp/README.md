# books-mcp

MCP server (STDIO) for Markdown “books” with YAML frontmatter. See `plans/2026-04-03-mcp-books-file-service-plan.md`.

## Local install (virtual environment)

Do not install into the system Python. From this directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Docker

Build and run the same code in a container; the image installs the package into `/opt/venv`:

```bash
docker build -t books-mcp:latest .
docker run -i --rm -e OPENAI_API_KEY -e BOOKS_DATA_DIR=/data/books -v "$(pwd)/data/books:/data/books" books-mcp:latest
```

Attach stdin/stdout for MCP clients. Override `BOOKS_DATA_DIR` and mount a volume for persistent books.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOOKS_DATA_DIR` | `./data/books` under the package root | Where `*.md` books are stored |
| `BOOKS_MAX_CONTENT_CHARS` | `1000` | Max body length after sanitization for `write_book` / `update_book` |
| `OPENAI_API_KEY` | (none) | Required for LLM-backed `write_book` / `update_book`; if unset, `find_books` uses a heuristic intent (first *N* words of the query). |
| `BOOKS_OPENAI_MODEL` | `gpt-4.1-mini` | Model for generation |
| `BOOKS_OPENAI_TIMEOUT` | `120` | OpenAI request timeout (seconds) |
| `BOOKS_LOG_PATH` | `<package>/data/logs/books-mcp.log` | Rotating log file path (parent dirs created on startup) |
| `BOOKS_LOG_LEVEL` | `INFO` | Set `DEBUG` for verbose tool traces (lengths/previews; not full LLM payloads) |
| `BOOKS_LOG_MAX_BYTES` | `5242880` | Max size per log file before rotation (~5 MiB) |
| `BOOKS_LOG_BACKUP_COUNT` | `3` | Number of rotated backups to keep |
| `BOOKS_LOG_MIRROR_STDERR` | `true` | When true, **WARNING** and **ERROR** also go to stderr (INFO/DEBUG stay file-only so MCP stdout stays protocol-clean) |
| `BOOKS_FIND_STEM_MATCH_RATIO` | `0.3` | `find_books`: include a book only if **strictly more** than this fraction of its kebab-case **stem segments** match the search intent (e.g. `0.3` means greater than 30%; `2/7` does not pass). |
| `BOOKS_FIND_INTENT_MAX_WORDS` | `10` | Max words for the LLM (or heuristic) search intent string. |

Logs are written under the service `data/` tree (gitignored by default). Do not point log output at stdout when using STDIO transport.

## Book frontmatter

Each `*.md` file starts with YAML frontmatter:

- **`type`:** `knowledge` or `sop`
- **`summary`:** short description; generators are instructed to **end the summary with related keywords** (e.g. after `—` or `Related:`) for quick scanning
- **`tags`:** list of short keywords (optional on disk for legacy files; omitted or empty means `[]`). New books from `write_book` include non-empty tags.

## `find_books` search

1. **Intent:** The user `query` is compressed to a short search intent (at most **`BOOKS_FIND_INTENT_MAX_WORDS`**) using [`prompts/search_intent.md`](prompts/search_intent.md) and the configured OpenAI model. If **`OPENAI_API_KEY`** is unset, the intent is the first *N* words of the query (lowercased), so search still works offline.
2. **Tokenize** that intent into alphanumeric tokens.
3. **Stem score:** For each book, split the filename stem on `-` into segments. Count how many segments **match** any intent token (exact match, or prefix match when both sides are at least 4 characters).
4. **Include** the book if `matched_segments / num_segments` is **strictly greater than** `BOOKS_FIND_STEM_MATCH_RATIO` (default 0.3). Summary and tags are **not** used for this filter.

There is no synonym/embedding layer; matching is lexical on stems only.
