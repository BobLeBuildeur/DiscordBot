# Orchestration server

HTTP API for an **agentic orchestrator proof of concept**. The service runs a multi-step workflow over a user’s problem statement: it checks whether enough context exists to plan, may ask follow-up questions, generates a structured plan, and supports plan refinement. Sessions and orchestration state are persisted on disk; LLM calls go to the OpenAI API.

## Stack

- **Python** 3.11+ (Docker image uses 3.12)
- **FastAPI** + **Uvicorn**
- **OpenAI** client for state checks, follow-ups, and plan generation/refinement

## API overview

Base path: `/orchestrator`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/orchestrator/sessions` | Start a session from a problem statement; response is **Server-Sent Events** (`text/event-stream`). |
| `POST` | `/orchestrator/sessions/{session_id}/messages` | Send a user message to advance the session; SSE stream. |
| `GET` | `/orchestrator/sessions/{session_id}` | Return the current session as JSON. |

Interactive docs: `GET /docs` (Swagger UI) when the server is running.

## Configuration

Environment variables are read via [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). Common options:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | **Required** for real LLM calls. Without it, OpenAI requests will fail. |
| `OPENAI_STATE_CHECK_MODEL` | Model for state checks (default: `gpt-4.1-mini`). |
| `OPENAI_GENERATION_MODEL` | Model for generation/refinement (default: `gpt-4.1-mini`). |
| `LLM_CONFIDENCE_THRESHOLD` | Threshold for proceeding vs. asking follow-ups (default: `0.75`). |
| `DATA_ROOT` | Session storage directory (default: `data/orchestrator` under the service root). |
| `PROMPT_ROOT` | Directory of markdown prompts (default: `prompts/orchestrator`). |
| `STREAM_CHUNK_SIZE` | SSE chunk size for streamed text (default: `160`). |

Optional `.env` in the working directory is loaded when present (see `backend/config.py`).

## Run locally (without Docker)

From this directory (`services/orchestration-server/`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
export OPENAI_API_KEY=sk-...   # optional for development; required for live LLM calls
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Run tests:

```bash
pytest
```

## Run with Docker

Build from the **service directory** (recommended):

```bash
cd services/orchestration-server
docker build -t orchestration-server .
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -v orchestration-data:/app/data/orchestrator \
  orchestration-server
```

Or build from the **monorepo root**:

```bash
docker build -f services/orchestration-server/Dockerfile -t orchestration-server services/orchestration-server
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs).

The `-v` mount keeps session data across container restarts. Omit it for ephemeral storage.

## Project layout

| Path | Role |
|------|------|
| `backend/` | FastAPI app, orchestrator engine, session store, OpenAI integration |
| `prompts/orchestrator/` | Markdown prompts for the orchestration stages |
| `data/orchestrator/` | Default on-disk session store (created at runtime) |
| `tests/` | Pytest suite |
