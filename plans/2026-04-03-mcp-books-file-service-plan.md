# MCP Books File Service (FastMCP / STDIO)

## Goal

Add a **new monorepo service** that runs a **Model Context Protocol (MCP) server** over **STDIO**, backed by **Markdown files with YAML frontmatter** (“books”). The server gives agents and orchestration a **bounded, inspectable** way to create, update, delete, retrieve, and search organizational knowledge (Guidelines-style **knowledge** books and **SOP** books), matching the MVP milestone direction that Knowledge Admins maintain structured content agents can use consistently.

**Success looks like:**

- Books live as `.md` files under a configurable directory; each file’s **basename (without `.md`)** is the book **name** (kebab-case slug derived from a **5–20 word** descriptive title).
- Frontmatter records **`type`** (`knowledge` | `sop`) and **`summary`** (short description of contents).
- **Tools** implement mutations: write (LLM-generated), update (LLM-assisted merge of feedback into existing body), delete.
- **Resources** implement reads: fetch body **without frontmatter** by name; search by context string over **title (filename)** then **summary (frontmatter)** and return **matching book names**.
- **Generators** exist per book type, driven by **versioned prompt templates** in-repo and a single LLM client configuration.

**Won’t do in this plan:** Multi-tenant isolation, a full “knowledge service” HTTP API, CMS UI, or a separate audit log service. The **orchestration server** will consume the books MCP for **read-path enrichment** (see [Orchestration integration](#orchestration-integration-servicesorchestration-server)). Replace this file-store with a DB only when scale pain appears (**opinionated simplicity** pillar).

---

## Pillars alignment

| Pillar | How this plan aligns |
|--------|----------------------|
| **State is explicit, not implicit** | Book content is the **source of truth on disk** (markdown + frontmatter). Orchestration persists enrichment as **`steps/*-knowledge.json`** (and/or session state) so runs are reconstructable; enrichment is **not** hidden process-only state. |
| **Small steps toward user value** | One deployable MCP process + file store delivers **agent-usable** CRUD and search without building the full MVP knowledge stack. |
| **Opinionated simplicity** | STDIO transport, FastMCP, one LLM provider for generation, **flat directory** of files—no premature microservices or event buses. |

---

## Relationship to milestones

- **`milestones/MVP.md` — Knowledge:** The books MCP plus orchestration **read-path** integration (registry, discovery, silent enrichment) advances “Guidelines and SOPs” that agents can **retrieve** in-session. **Admin authoring UX** and a dedicated **HTTP CRUD API** remain follow-ups.
- **`milestones/MVP.md` — Tools:** The orchestration server maintains a **committed JSON registry** of MCPs, runs **discovery on startup**, and invokes the books MCP for **enrichment** on session creation **before** generation prompts (**including** the first **problem-understanding** turn when routed there)—establishing a concrete tool/MCP pattern for later expansion.

---

## Preconditions

- **Python 3.11+** for the service runtime.
- **`mcp`** / **FastMCP** (exact package pinned in the service’s `pyproject.toml` or `requirements.txt`).
- **LLM access** for write/update paths: e.g. **`OPENAI_API_KEY`** (or the same env pattern as `services/orchestration-server/` if you want consistency). Document required env vars in `services/<name>/README.md`.
- **Writable directory** for books, e.g. `BOOKS_DATA_DIR` defaulting to something like `services/books-mcp/data/books/` for local dev (gitignored).
- **Optional:** `BOOKS_MAX_CONTENT_CHARS` (or equivalent) default **1000** for `write_book` / `update_book` persisted body length after sanitization.
- Monorepo layout: implementation lives under **`services/books-mcp/`** (or `services/mcp-books/`—pick one name and keep all code there).
- **Orchestration integration:** `services/orchestration-server/` must add the **MCP Python SDK / client** capable of STDIO transport to subprocess MCP servers, subprocess management, and (if not already present) FastAPI **lifespan** for startup discovery.
- **Orchestration enrichment:** Configurable cap on books pulled into prompts (**default: 5**), e.g. `ORCH_BOOKS_ENRICHMENT_MAX`.

---

## Used Tools

- **Python 3.11+** — runtime.
- **FastMCP** — MCP server, STDIO transport, tools and resources registration.
- **PyYAML** — parse/serialize frontmatter (or `ruamel.yaml` if you need round-trip preservation; start with one library and stay consistent).
- **LLM HTTP client** — OpenAI-compatible API for generation (reuse patterns from orchestration-server if practical: small wrapper, configurable model name).
- **Prompt templates** — markdown files under `services/books-mcp/prompts/generators/` (or similar), one per type, plus shared fragments if needed.
- **`pytest`**, **`ruff`** — tests and lint.
- **Orchestration:** MCP **client** (STDIO subprocess + handshake) for registry discovery and enrichment calls; **FastAPI lifespan** for startup.

---

## Schema and on-disk format

**Path:** `{BOOKS_DATA_DIR}/{book-name}.md` where `book-name` matches **`^[a-z0-9]+(-[a-z0-9]+)*$`** (kebab-case segments).

**Frontmatter (YAML), required keys:**

- `type`: `knowledge` | `sop` (machine values; document that “SoP” in prose maps to `sop`).
- `summary`: short string describing contents (used in search and for agent skim).

**Body:** Markdown. For **`sop`**, generators must produce a clear structure: **goal** plus **ordered steps**, each step with enough description to execute (per your table). For **`knowledge`**, free-form informative markdown.

**Title rule:** The **book name** (filename stem) encodes a **5–20 word** descriptive title: implement by having the LLM output a proposed title phrase, then **slugify to kebab-case** and **validate word count** on the slug’s hyphen-separated segments interpreted as words (or validate on the natural-language title before slugifying—choose one approach and document it). Reject or retry generation if out of range.

---

## Generators

| `type` | Role | Prompt strategy |
|--------|------|-----------------|
| `knowledge` | Free-form reference material | Prompt emphasizes factual organization, headings, and clarity; includes user **context**. |
| `sop` | Standard operating procedure | Prompt enforces **goal** + **numbered steps** with descriptions; includes **context**. |

**Interface (conceptual):** `generate(type: str, context: str) -> GeneratedBook` where `GeneratedBook` contains `title_words` (for validation), `slug`, `summary`, `body_markdown`.

Implementation: a **registry** mapping `type` → async callable; each loads its prompt template, fills `context` and `type`, calls the LLM once (or a bounded small sequence if you split “title+summary” vs “body”—prefer **one call** for simplicity unless quality suffers).

---

## MCP surface

### Tools (mutations)

1. **`write_book`** (names may vary; keep descriptive in FastMCP)
   - **Input:** `type` (`knowledge` | `sop`), `context` (string).
   - **Behavior:** Run the generator; build frontmatter; **sanitize** final body and related text fields; enforce a **configurable maximum length** on persisted book body content (**default: 1000 characters**); write `{slug}.md`; return the **book name** (slug) and path or confirmation.
   - **Errors:** LLM failure, validation failure (word count, slug collision—if file exists, fail or use explicit overwrite policy; **default: fail** to avoid silent overwrite), **rejection if sanitized content exceeds max length**.

2. **`update_book`**
   - **Input:** `book_name` (exact match to filename stem), `feedback` (string; “content” in your spec—treat as review feedback to merge).
   - **Behavior:** Read existing file; parse frontmatter + body; call LLM with **current body + feedback** and type-specific “revise” prompt; **sanitize** the revised body; enforce the **same configurable max length** (**default: 1000 characters**); write back **same `book_name`** with updated body and **revised `summary` if needed** (LLM or heuristic—prefer updating summary when scope changes; **summary** should also respect length/sanitization policy where applicable).
   - **Errors:** Not found, parse errors, LLM errors, **rejection if output exceeds max length after sanitization**.

**Sanitization and length (both tools):** Define a single policy (e.g. strip null bytes, normalize newlines, optional HTML/script stripping if ever mixed into markdown) and document it in the service README. Expose max length via env (e.g. `BOOKS_MAX_CONTENT_CHARS=1000`) so operators can tune without code changes.

3. **`delete_book`**
   - **Input:** `book_name` (exact match).
   - **Behavior:** Delete file if present; idempotent delete can be a product choice (document: return 404 vs success if missing).

### Resources (reads)

Align with FastMCP capabilities (adjust names to library conventions):

1. **Get book** — Given **book name**, return **markdown body only** (strip YAML frontmatter). Expose as a **resource URI** e.g. `book://{name}` or `books/{name}.md` per FastMCP docs. If the protocol makes search awkward as a “resource,” implement **read-only tools** that are documented as the retrieval API—**prefer true Resources** for get-by-name first.

2. **Find books** — **Input:** `query` (context string). **Algorithm:**
   - List all `*.md` in `BOOKS_DATA_DIR`.
   - **Stage A:** Keep files whose **stem** matches the query (substring or token match—define as **case-insensitive substring** on the kebab name, optionally also match with spaces replaced by hyphens).
   - **Stage B:** For candidates from A, parse frontmatter and filter by **`summary`** containing the query (case-insensitive substring) or use a second pass: if Stage A is empty, fall back to summary-only search across all books—**your spec says:** filter by title first, then **again** by summary among title matches; if that yields none, document whether to return empty list or broaden (default: **empty list** to stay predictable).
   - **Return:** List of **book names** (stems), as resource content (e.g. JSON list) or plain text one per line—pick JSON for machine consumers.

Document the exact search semantics in the service README so agents behave consistently.

---

## Orchestration integration (`services/orchestration-server/`)

Wire the orchestration server so it can **list configured MCPs**, **discover capabilities at startup**, and **enrich a new session** with book search results **after** the initial problem statement is saved and **before** the **state check**—so **`problem-understanding.md`** (when selected) and later **plan** prompts see organizational knowledge without exposing it to the client (see ordering below).

### MCP registry (JSON, committed)

- Add a **version-controlled** file, e.g. `services/orchestration-server/config/mcp-registry.json`, describing each MCP the orchestrator may use.
- **Suggested shape per entry:** stable `id` (e.g. `books`), **STDIO launch** `command` (argv list), optional `cwd`, optional `env` overrides, and optional flags for **enabled** / **roles** (e.g. `enrichment: true`).
- Paths should be **repo-root-relative** or documented env overrides so local dev and deployment stay reproducible.

### Discovery on server start

- During FastAPI **lifespan** (or equivalent startup hook), for each **enabled** registry entry:
  - Start the MCP subprocess (STDIO) using the official **Python MCP client** (same ecosystem as FastMCP servers).
  - Run the MCP **initialize** handshake and cache **tool** and **resource** lists (names, schemas if exposed).
  - Store the result in an in-memory **`McpRegistryRuntime`** (or similar) attached to `app.state` for reuse across requests.
- **Failure policy:** If discovery fails for an MCP, log clearly and mark that entry **unavailable**; orchestration continues without it (enrichment becomes a no-op for books). Do not crash the API process unless the team chooses **fail-fast** in a later hardening pass.

### Information enrichment (silent, persisted)

**When:** Immediately **after** a new session is created and the initial **`problem_statement`** user turn is persisted, and **before** the **state check** LLM call for that same turn. That guarantees enrichment exists **before** any **`problem-understanding.md`** call on the first turn and remains available for **`plan-generation.md`** and **`plan-refinement.md`** on later turns (same session).

**Ordering (recommended):**

1. Persist session + initial user turn (existing behavior).
2. **Knowledge enrichment** (MCP find + optional per-book fetch).
3. **State check** (`state-check.md`).
4. **Generation** (`problem-understanding`, `plan-generation`, or `plan-refinement` per `StateCheck`).

**What it does:**

1. Call the **books MCP** using the **discovered** find-books capability (resource or tool—use whatever the books server exposes; map name in registry metadata if needed).
2. Use the **current problem statement** (and/or latest user message on that turn) as the **search query/context** string.
3. Take at most **`N` matched books** for fetch (**default `N=5`**), configurable via orchestration settings/env (e.g. `ORCH_BOOKS_ENRICHMENT_MAX=5`). Apply the cap **after** find-books returns names (stable ordering: document whether alphabetical or search rank).
4. For each selected book name, **fetch body** (no frontmatter) and assemble a single structured markdown block (e.g. headings per book name + body).
5. **Persist** the outcome as:
   - A **step artifact** on disk with **`kind`: `knowledge`** (payload: raw MCP responses or normalized `{ "books": [...], "snippet": "..." }`—keep it inspectable for debugging).
   - **Conversation history** for LLM context: append a **`TurnRecord`** with **`kind`: `knowledge`** and `content` set to the assembled text (or a compact representation the prompts expect). This satisfies “persisted to history for the LLM.”
6. **Silent to the frontend:** Do **not** emit SSE `chunk` events for enrichment. Do **not** include knowledge content in `final_event_payload`’s `assistant_message` (it must remain the real assistant turn only). For **`GET /sessions/{session_id}`**, **strip** or **redact** `conversation_history` entries with `kind == "knowledge"` from the JSON returned to clients **or** move enrichment to a dedicated `SessionState` field that is never serialized to the API schema—choose one approach; **prefer filtering** if you keep using `conversation_history` for LLM assembly.

### Prompt injection scope

- Add matched book text to **`PromptManager._render_context`** so **every** prompt that uses `_render_context` receives the same structured context, including **`state-check.md`**, **`problem-understanding.md`**, **`plan-generation.md`**, **`plan-refinement.md`**, and **`response-metadata.md`** (unless a specific prompt must opt out in code—avoid one-off duplication).
- Implement a dedicated subsection in the rendered context, e.g. `# Organizational knowledge (matched books)`, populated from the persisted `knowledge` turn / session fields assembled during enrichment (up to **`N`** books, **default 5**).

### Guardrails (orchestration)

- Timeouts on MCP calls; cap **fetched books** at **`N` (default 5, configurable)** and optionally add a **total character** budget for the `# Organizational knowledge` block to protect context limits.
- If MCP is down, proceed with empty enrichment and optionally a single **non-user-visible** log line in step payload.

---

## Steps

1. **Scaffold service**
   1.1. Create `services/books-mcp/` with package layout (`src/` or flat module—match repo conventions).
   1.2. Add `pyproject.toml` or `requirements.txt` with pinned **`mcp`**, **FastMCP**, **PyYAML** (or chosen YAML lib), **pytest**, **ruff**.
   1.3. Add `README.md`: STDIO run command, env vars (`BOOKS_DATA_DIR`, `BOOKS_MAX_CONTENT_CHARS`, `OPENAI_API_KEY`, etc.).
   1.4. Add `.gitignore` for `data/`, `__pycache__/`, venv; reuse or symlink monorepo ruff config if applicable.

2. **Storage module**
   2.1. Resolve `BOOKS_DATA_DIR` at startup; create directory if missing.
   2.2. Implement `safe_book_path(book_name: str) -> Path` rejecting `..`, path separators, and invalid characters.
   2.3. Implement list/read/write/delete for `{slug}.md`; atomic write (temp file + replace) where appropriate.
   2.4. Split file into **YAML frontmatter** + **markdown body**; raise clear errors on parse failure or missing keys (`type`, `summary`).

3. **Validation**
   3.1. Kebab-case and **5–20 word** title rules for generated slugs; document validation vs slug word-count semantics.
   3.2. Validate `type` ∈ {`knowledge`, `sop`} at read/write boundaries.
   3.3. Implement **sanitization** (null bytes, newline normalization; document any optional stripping).
   3.4. Enforce **max body length** from env (**default 1000** chars) after sanitization; return structured errors (or document truncate policy) when LLM output exceeds limit.
   3.5. Unit tests for edge cases: empty body, exactly at limit, one char over limit.

4. **LLM client**
   4.1. Read model name and API key from env (align naming with orchestration-server if desired).
   4.2. Async or sync wrapper matching generator call sites; configurable **timeouts**.
   4.3. Map provider errors to stable error strings / exceptions for MCP tool handlers.

5. **Prompt files**
   5.1. Add `prompts/generators/knowledge.md` and `prompts/generators/sop.md` with placeholders for **context** and output shape (SOP: goal + numbered steps).
   5.2. Add `prompts/revise.md` (or per-type revise) for **`update_book`**.
   5.3. Keep prompts committed and load by path from package root.

6. **Generators**
   6.1. Define `GeneratedBook` (or equivalent): slug, summary, body, title validation fields.
   6.2. Implement registry `type -> generator`; each loads its template, calls LLM, runs **slug + title** validation.
   6.3. Apply **sanitize + max length** before returning; fail if still over limit.
   6.4. Unit tests with **mocked LLM** returning controlled strings (happy path + oversize response).

7. **FastMCP app**
   7.1. Implement tool handlers: **`write_book`**, **`update_book`**, **`delete_book`** wiring storage + generators + validation.
   7.2. Implement **get book** and **find books** as resources or read tools per FastMCP patterns; match names used in orchestration registry metadata.
   7.3. Register MCP server; expose **STDIO** entrypoint (`python -m books_mcp` or chosen module).
   7.4. Smoke test: launch subprocess, single `initialize` + list tools/resources.

8. **Integration tests (books MCP)**
   8.1. Fixture: temp `BOOKS_DATA_DIR`.
   8.2. **Write** → file exists with valid frontmatter; **read** body without frontmatter.
   8.3. **Find** with substring on name and summary per plan semantics.
   8.4. **Update** and **delete**; assert **max length** and **sanitize** on write/update paths.

9. **Orchestration: registry + runtime**
   9.1. Add `services/orchestration-server/config/mcp-registry.json` with at least the **books** entry: `command`, `cwd`, `env`, `enabled`, `enrichment: true`.
   9.2. Pydantic (or similar) schema for registry entries; validate on load.
   9.3. Implement **`McpRegistryRuntime`**: spawn STDIO client per entry, run **initialize**, cache **tools** and **resources** lists.
   9.4. On discovery failure for one entry: log, mark unavailable, continue (no crash).

10. **Orchestration: lifespan**
    10.1. Add FastAPI **lifespan** context to `create_app` (or equivalent): run MCP discovery once at startup.
    10.2. Attach **`McpRegistryRuntime`** to `app.state`; expose getter used by routes/engine factory.
    10.3. Plumb runtime (or enrichment service) into **`OrchestratorEngine`** construction—constructor or factory pattern to keep tests injectable.

11. **Orchestration: enrichment**
    11.1. Add settings: **`ORCH_BOOKS_ENRICHMENT_MAX`** (default **5**), timeouts, optional char budget.
    11.2. Implement **`KnowledgeEnrichmentService`**: call books MCP **find** with problem statement as query; take first **`N`** names (document ordering); **get** each body.
    11.3. Assemble markdown block for `# Organizational knowledge`; append **`TurnRecord(kind="knowledge", ...)`** and **`append_step_artifact(..., kind="knowledge", ...)`**; **`save_session`**.
    11.4. Hook **`start_session_streaming`**: after persisting initial **user-message** step, run enrichment **before** **`_stream_turn`** (before state check). No-op if books MCP unavailable.
    11.5. Ensure enrichment does not add SSE **chunk** events.

12. **Orchestration: prompts**
    12.1. Extend **`PromptManager._render_context`** to append **`# Organizational knowledge (matched books)`** from session (knowledge turn or dedicated field).
    12.2. Verify **`build_state_check_prompt`**, **`build_problem_understanding_prompt`**, **`build_plan_generation_prompt`**, **`build_plan_refinement_prompt`**, and **`build_response_metadata_prompt`** all pick up the section (via shared `_render_context` or explicit calls).
    12.3. Update **`state-check.md`** / other prompts only if headings need to mention the new section for model clarity.

13. **Orchestration: API**
    13.1. **`GET /sessions/{session_id}`**: serialize session with **`conversation_history` filtered** to exclude `kind == "knowledge"` (or equivalent client-safe DTO).
    13.2. Confirm **`final_event_payload`** / SSE **final** event never includes knowledge text in fields meant for the Analyst.
    13.3. Add or adjust tests for API contract so frontend tests do not see silent turns.

14. **Orchestration tests**
    14.1. Mock MCP client: discovery returns tools/resources; find returns names; get returns bodies.
    14.2. Assert **`steps/*-knowledge.json`** exists after session start with enrichment.
    14.3. Assert **`_render_context`** contains the organizational knowledge block when enrichment ran.
    14.4. Assert **at most five** books used by default; override env to **2** or **10** and assert cap respected.
    14.5. Regression: state check + follow-up/plan prompts still run when enrichment is empty (MCP down).

---

## Guardrails

- **Path safety:** Never construct paths from unchecked user strings; book names must match strict kebab pattern.
- **Idempotency and collisions:** `write_book` must not silently overwrite; return a clear error if the file exists.
- **LLM failures:** Surface errors to the MCP client; do not write partial files without cleanup.
- **Mutation content:** `write_book` / `update_book` must **sanitize** and **reject or truncate** per configured **max length** (default **1000** chars)—document behavior when LLM output exceeds the limit.
- **Frontmatter:** Fail closed on missing/invalid `type` or `summary` when reading for search/update.
- **Quality:** Run `ruff check` and `pytest` before merge; add at least one test per tool and one for search ordering.
- **MVP knowledge principle:** Avoid opaque dumps—generators must produce **structured, labeled** markdown (especially for `sop`).
- **Orchestration:** MCP registry JSON must stay **reviewable** (PR-visible); discovery failures degrade gracefully; **never** leak silent `knowledge` turns to HTTP or SSE user-visible fields.

---

## Follow-ups / deferred work

- Extend MCP registry beyond books (other STDIO servers) with the same discovery pattern; document operator runbooks.
- **Auth / tenant isolation** if books are ever multi-customer.
- **Audit log** of writes/deletes if compliance requires it (**state pillar** extension).
- Additional types beyond `knowledge` and `sop` via new generator + prompt + enum extension.
