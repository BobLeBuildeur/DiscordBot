# Orchestration Server Implementation Plan

## Goal

Build a self-contained orchestration service for Analysts that turns a rough business problem
statement into a markdown implementation plan through a small conversational loop. Success
means the service can start a session, ask follow-up questions when confidence is low, create
or refine a markdown plan when confidence is high enough, and persist every step to disk in a
human-inspectable format.

## Preconditions

- Python 3.11+ is available for the service runtime and tests.
- `OPENAI_API_KEY` is available when running against the real provider.
- The service remains self-contained under `services/orchestration-server/`.
- Prompt templates are stored on disk and loaded by path at runtime.
- Local disk under `services/orchestration-server/data/orchestrator/` is writable.

## Used Tools

- FastAPI for the HTTP API and streaming responses.
- Pydantic and pydantic-settings for typed models and runtime configuration.
- OpenAI Python SDK for state checks and generated follow-up questions or plans.
- `pathlib`, `json`, `tempfile`, and `os.replace` for inspectable file-backed persistence.
- `pytest` for unit and API tests.
- `ruff` for linting.

## Steps

1. Create a service-local Python package in `services/orchestration-server/backend/` with
   configuration, API, orchestration, and provider integration modules.
   - Won't do: spread orchestration code across the repository root or unrelated services.
2. Define explicit orchestration state models in
   `services/orchestration-server/backend/orchestrator/models.py`.
   - Won't do: use loose dictionaries as the main internal contract.
3. Implement file-backed session persistence in
   `services/orchestration-server/backend/orchestrator/store.py`.
   - Won't do: introduce a database or rely on logs as the system of record.
4. Load prompt templates from `services/orchestration-server/prompts/orchestrator/` and build
   contextual prompt inputs in `services/orchestration-server/backend/orchestrator/prompts.py`.
   - Won't do: hardcode prompt bodies inline in route handlers.
5. Implement the workflow engine in `services/orchestration-server/backend/orchestrator/engine.py`
   so each user turn runs a state check, applies confidence gating, and returns either
   follow-up questions or a markdown plan.
   - Won't do: execute build-stage work or hidden background loops.
6. Add a narrow OpenAI adapter in
   `services/orchestration-server/backend/integrations/openai_client.py`.
   - Won't do: couple orchestration code directly to raw SDK usage everywhere.
7. Expose `POST /orchestrator/sessions`, `POST /orchestrator/sessions/{session_id}/messages`,
   and `GET /orchestrator/sessions/{session_id}` in the FastAPI app.
   - Won't do: defer all output until a complex client protocol is designed.
8. Add tests for storage, engine branching, prompt selection, persisted artifacts, and streamed
   API responses under `services/orchestration-server/tests/`.
   - Won't do: depend on live OpenAI calls in test runs.

## Guardrails

- Keep the implementation single-process and file-backed.
- Persist the state check and response metadata after every turn.
- Keep the latest markdown plan in prompt context for later refinements.
- Ask follow-up questions when confidence is below `LLM_CONFIDENCE_THRESHOLD`.
- Save steps in human-readable JSON and markdown files.
- Keep build-stage execution out of scope for this milestone.
- Run `ruff check` and `pytest` before considering the work complete.
