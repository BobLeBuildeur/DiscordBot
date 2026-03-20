# Agentic Orchestrator PoC

## Goal

Add a lightweight orchestration service for Analysts that turns a rough problem statement into a markdown plan through a conversational loop. Success means:

- `POST /orchestrator/sessions` creates a session from the initial problem statement and immediately runs a state check.
- `POST /orchestrator/sessions/{session_id}/messages` accepts user answers or plan feedback and streams back either follow-up questions or a markdown plan.
- After each turn, the orchestrator persists a structured `state_check` and the active prompt response metadata, including what the LLM confidence is and whether the next action is `ask_follow_up`, `create_plan`, or `refine_plan`.
- If the returned confidence is below a configurable threshold, the orchestrator asks additional questions before moving on to plan creation or refinement.
- Once a plan exists, the latest markdown plan is always included in later prompt context.
- Every step is saved to disk in an inspectable format so the team can replay real PoC sessions and learn from them.

## Preconditions

- Python 3.11+ is available.
- `OPENAI_API_KEY` is configured for the runtime environment.
- The repository is treated as a monorepo with multiple independent services.
- A dedicated service folder such as `services/orchestration-server/` is available for this work.
- A writable local directory such as `services/orchestration-server/data/orchestrator/` is available for persisted sessions.
- The team accepts a single-node, file-backed design for the PoC.
- The generated markdown plan should follow the structure described in `.cursor/rules/feature-planning.mdc`.
- A configurable confidence threshold is defined, for example in environment-backed config.
- Prompt templates are stored as markdown documents in the repository so they can be revised without changing orchestration code.
- The implementation can mock OpenAI responses in tests; multi-provider support is out of scope for this milestone.

## Used Tools

- Python 3.11+ for the application runtime.
- FastAPI, or the existing Python HTTP layer, for endpoints and streamed responses.
- Pydantic for request, response, and saved-state models.
- OpenAI API for state checks, follow-up questions, plan generation, and plan refinement.
- Markdown prompt documents stored in `services/orchestration-server/prompts/orchestrator/*.md`.
- Standard library file primitives (`pathlib`, `json`, `tempfile`, `os.replace`) for persisted snapshots and step artifacts.
- Server-Sent Events or chunked HTTP streaming for low-latency responses.
- `pytest` for unit and integration tests.
- `ruff` for linting.

## Architectural Design

### Overview

The PoC should use a modular Python server that sits between the customer-facing client and OpenAI. The server receives user requests, decides which orchestration step to run, calls the LLM, streams the user-visible response back to the client, and saves the resulting state and artifacts to local disk.

This architecture is intentionally simple for the PoC:

- one Python server process
- one local file-backed persistence layer
- one LLM provider integration
- modular internal boundaries so components can be swapped or split later as more is learned
- one self-contained service directory inside the monorepo so this service can evolve independently from other services

### High-Level Flow

```text
Client UI
  -> Python API server
  -> Orchestrator engine
  -> Prompt builder + context assembler
  -> OpenAI client
  -> streamed response back through server to client
  -> local artifact store writes session + step files
```

### Core Components

The orchestration server should live in its own monorepo service directory:

`services/orchestration-server/`

That folder should contain the service code, prompts, tests, and local development configuration needed for the PoC. The goal is to keep the orchestration server independent from the rest of the monorepo so it can be changed, tested, or replaced without coupling unrelated services.

1. API Layer - `services/orchestration-server/backend/api/orchestrator.py`, `services/orchestration-server/backend/app.py`
   - Receives:
     - initial problem statement
     - follow-up answers
     - plan feedback
   - Returns:
     - streamed follow-up questions
     - streamed markdown plans
     - inspectable session state
   - Keeps HTTP concerns isolated from orchestration logic.
   - **Won't do:** embed prompt logic, file I/O rules, or branching decisions directly inside route handlers.

2. Orchestrator Engine - `services/orchestration-server/backend/orchestrator/engine.py`
   - Owns the workflow logic for:
     - start session
     - run state check
     - ask follow-up questions
     - create initial plan
     - refine existing plan
   - Decides the next action from the persisted state plus the latest user input.
   - Ensures the latest plan remains in context when present.
   - **Won't do:** hold the authoritative session state only in memory; mix persistence details with HTTP transport code.

3. Prompt and Context Module - `services/orchestration-server/backend/orchestrator/prompts.py`
   - Loads markdown prompt documents from `services/orchestration-server/prompts/orchestrator/`.
   - Builds the prompts for:
     - state checks
     - follow-up question generation
     - markdown plan generation
     - markdown plan refinement
   - Assembles context from:
     - problem statement
     - conversation history
     - latest plan markdown
     - latest user feedback
   - Keeps prompt evolution isolated so the team can revise prompting strategy without rewriting the server flow.
   - **Won't do:** scatter prompt templates across multiple handlers or storage utilities; hardcode all prompt bodies inline in Python modules.

4. LLM Client Adapter - `services/orchestration-server/backend/integrations/openai_client.py`
   - Wraps OpenAI request and streaming behavior behind a narrow interface.
   - Example interface:
     - `run_state_check(...)`
     - `stream_follow_up_questions(...)`
     - `stream_plan(...)`
     - `stream_plan_refinement(...)`
   - Each call should return user-visible output plus structured metadata including confidence.
   - Makes it easier to adjust models, parameters, or even providers later.
   - **Won't do:** let orchestration code depend directly on raw provider SDK calls everywhere.

5. Configuration - `services/orchestration-server/backend/config.py`
   - Stores runtime settings such as:
     - `LLM_CONFIDENCE_THRESHOLD`
     - prompt document root
     - model names
   - Keeps the confidence threshold adjustable without changing orchestration logic.
   - **Won't do:** bury thresholds and model choices in unrelated handlers.

6. Persistence Layer - `services/orchestration-server/backend/orchestrator/store.py`
   - Saves the canonical session snapshot and per-step artifacts to local disk.
   - Provides a small interface such as:
     - `create_session(...)`
     - `load_session(session_id)`
     - `save_session(state)`
     - `append_step_artifact(session_id, artifact)`
   - Keeps saved state explicit and inspectable.
   - **Won't do:** rely on logs, process globals, or opaque caches as the system of record.

7. Domain Models - `services/orchestration-server/backend/orchestrator/models.py`
   - Defines typed models for:
     - session state
     - turn records
     - state checks
     - plan versions
     - step artifacts
   - Gives the PoC a stable internal contract even if storage shape or API payloads evolve.
   - **Won't do:** pass around untyped dictionaries for every internal boundary.

### Suggested Module Boundaries

```text
services/
  orchestration-server/
    backend/
      app.py
      config.py
      api/
        orchestrator.py
      orchestrator/
        engine.py
        models.py
        prompts.py
        store.py
      integrations/
        openai_client.py
    prompts/
      orchestrator/
        state-check.md
        problem-understanding.md
        plan-generation.md
        plan-refinement.md
    tests/
      test_orchestrator_store.py
      test_orchestrator_engine.py
      test_orchestrator_api.py
```

These boundaries keep the architecture modular in the specific areas most likely to change during the PoC:

- prompt strategy may change as we learn how to ask better follow-up questions
- state shape may change as we learn what must be persisted for debugging and evaluation
- provider integration may change as models or vendors are compared
- storage may later move from local disk to a hosted store without rewriting the orchestration loop
- API transport may later expand beyond simple HTTP streaming
- other monorepo services may evolve independently without needing to import this service directly

### Request Lifecycle

1. Client sends a request to the Python server.
2. API layer validates the payload and loads or creates the session.
3. Orchestrator engine selects the correct markdown prompt document for the current state.
4. Engine assembles the current context, including the latest markdown plan when present.
5. Engine calls the LLM client adapter for a state check and records the returned confidence.
6. Based on the state check and confidence threshold, the engine chooses one next action:
   - ask follow-up questions
   - create plan
   - refine plan
7. The chosen LLM call is streamed back through the API layer to the client.
8. The final output, post-step `state_check`, confidence value, and updated session snapshot are saved locally.
9. The request completes only after the updated state is persisted.

### Local Storage Design

The server should save files in a way that supports inspection without extra tooling.

Example layout:

```text
services/
  orchestration-server/
    data/
      orchestrator/
        {session_id}/
          session.json
          steps/
            001-user-message.json
            002-state-check.json
            003-follow-up-questions.json
            004-user-message.json
            005-state-check.json
            006-plan-v1.md
            007-plan-v1-metadata.json
```

- `session.json` is the latest canonical snapshot.
- `steps/` contains append-only artifacts for reconstruction and debugging.
- Plan markdown should be saved as markdown, with optional JSON metadata beside it.
- Each step artifact should record which prompt document was used and what confidence was returned.
- Writes should use temp-file plus atomic rename where practical.

### Prompt Documents and Confidence Gating

Prompt selection should be state-driven and file-backed.

- `services/orchestration-server/prompts/orchestrator/problem-understanding.md`
  - used when the session starts and when the system needs more follow-up questions
  - explains that the agent's role is to understand the problem, its scope, and the expected outcomes
- `services/orchestration-server/prompts/orchestrator/plan-generation.md`
  - used when enough context exists to create the first plan
  - specifies the required markdown output format using `.cursor/rules/feature-planning.mdc`
- `services/orchestration-server/prompts/orchestrator/plan-refinement.md`
  - used when a plan already exists and the analyst provides feedback
  - asks the model to improve the plan based on that feedback while preserving useful existing content
- `services/orchestration-server/prompts/orchestrator/state-check.md`
  - used to produce the structured workflow decision after each turn
  - requires a confidence value in the response

Every prompt path should return a confidence value in structured metadata. The state-check response should always return at least:

- `needs_more_information`
- `next_action`
- `confidence`
- `reason`
- `missing_information`

Confidence should affect orchestration behavior directly:

- if `confidence < LLM_CONFIDENCE_THRESHOLD`, ask more follow-up questions
- if `confidence >= LLM_CONFIDENCE_THRESHOLD`, proceed with the requested next action
- if a plan exists but confidence is low, ask clarifying questions before refining again

This keeps the loop adaptive without introducing hidden logic outside the saved state.

### Modularity Principles

- Keep business workflow logic in the orchestrator engine, not in the API layer.
- Keep provider-specific code behind an adapter boundary.
- Keep persistence behind a store boundary.
- Keep prompts separate from orchestration control flow.
- Keep the saved state schema explicit and versionable.
- Prefer replacing one module over rewriting the whole server when the PoC reveals a better approach.

## Steps

1. Define the orchestrator state in `services/orchestration-server/backend/orchestrator/models.py`.
   - Add models for `SessionState`, `TurnRecord`, `PlanVersion`, and `StateCheck`.
   - `StateCheck` should capture the post-step decision explicitly, for example:
     - `needs_more_information: bool`
     - `next_action: ask_follow_up | create_plan | refine_plan | wait_for_user`
     - `confidence: float`
     - `confidence_threshold: float`
     - `reason`
     - `missing_information`
   - `SessionState` should keep `problem_statement`, `conversation_history`, `current_plan_markdown`, `plan_versions`, and the latest `state_check`.
   - **Won't do:** infer workflow state only from loose chat history; keep the current plan only in transient process memory.

2. Create the self-contained monorepo service folder at `services/orchestration-server/`.
   - Keep the orchestration server independent from other services by colocating its code, prompts, tests, and local runtime files under this directory.
   - Add at least:
     - `services/orchestration-server/backend/`
     - `services/orchestration-server/prompts/`
     - `services/orchestration-server/tests/`
   - **Won't do:** spread orchestration-server files across unrelated root-level folders; couple service internals to another service's directory structure.

3. Implement file-backed session storage in `services/orchestration-server/backend/orchestrator/store.py`.
   - Save the latest snapshot at `services/orchestration-server/data/orchestrator/{session_id}/session.json`.
   - Save each step as a separate artifact such as `services/orchestration-server/data/orchestrator/{session_id}/steps/{step_index}-{kind}.json`.
   - Persist at least:
     - session creation
     - each user message
     - each LLM state-check result
     - each streamed assistant result
     - each new or revised markdown plan
     - the prompt document path used for each LLM step
     - the returned confidence metadata for each LLM step
   - Use temp-file plus rename for snapshot writes so saved sessions stay readable after interruptions.
   - **Won't do:** introduce a database, queue, or metrics pipeline for the PoC; rely on logs alone for reconstruction.

4. Build the orchestration loop in `services/orchestration-server/backend/orchestrator/engine.py`.
   - `start_session(problem_statement)` should create the session, run the first state check, and decide whether to ask follow-up questions or draft a plan.
   - `advance_session(session_id, user_message)` should load the snapshot, append the new user input, rerun the state check, and branch to:
     - follow-up question generation
     - first plan generation
     - plan refinement
   - If the returned confidence is below the configured threshold, the engine should ask follow-up questions before creating or refining the plan.
   - Once `current_plan_markdown` exists, include it in every later state-check and refinement prompt.
   - Keep the loop user-driven: one user turn in, one streamed assistant turn out, then persist the updated state.
   - **Won't do:** execute the full plan automatically; create hidden background loops; add Build-stage task execution.

5. Create focused prompt builders in `services/orchestration-server/backend/orchestrator/prompts.py`.
   - Load separate markdown prompt documents for:
     - state check
     - follow-up question generation
     - initial markdown plan generation
     - markdown plan refinement from user comments
   - Store those prompt documents in:
     - `services/orchestration-server/prompts/orchestrator/state-check.md`
     - `services/orchestration-server/prompts/orchestrator/problem-understanding.md`
     - `services/orchestration-server/prompts/orchestrator/plan-generation.md`
     - `services/orchestration-server/prompts/orchestrator/plan-refinement.md`
   - Use the problem-understanding prompt both at session start and during low-confidence clarification loops.
   - The plan-generation prompt should require the markdown structure described in `.cursor/rules/feature-planning.mdc`.
   - The refinement prompt should include both the latest plan markdown and the latest user feedback.
   - **Won't do:** use one oversized prompt that mixes orchestration decisions and final user output without structured intermediate state.

6. Add runtime configuration in `services/orchestration-server/backend/config.py`.
   - Define a configurable confidence threshold such as `LLM_CONFIDENCE_THRESHOLD`.
   - Define the prompt root directory so prompt docs can be loaded from disk.
   - **Won't do:** hardcode the confidence threshold in orchestration logic.

7. Expose a small streaming API in `services/orchestration-server/backend/api/orchestrator.py` and `services/orchestration-server/backend/app.py`.
   - Add:
     - `POST /orchestrator/sessions` for the initial problem statement
     - `POST /orchestrator/sessions/{session_id}/messages` for answers and plan feedback
     - `GET /orchestrator/sessions/{session_id}` for inspectability of the saved state
   - Stream assistant output as it is generated, then emit a final event or response chunk containing the saved `state_check`, `confidence`, and `session_id`.
   - Keep the payloads simple so a thin PoC client can render chat text and markdown plans without a complex protocol.
   - **Won't do:** defer all output until the model finishes; design a production-grade websocket layer before validating the user experience.

8. Add end-to-end tests in `services/orchestration-server/tests/test_orchestrator_store.py`, `services/orchestration-server/tests/test_orchestrator_engine.py`, and `services/orchestration-server/tests/test_orchestrator_api.py`.
   - Mock OpenAI responses to cover:
     - more information needed
     - enough information to create a plan
     - plan refinement after user comments
     - low-confidence responses triggering more analyst questions
     - correct markdown prompt document selection by state
     - the plan being included in refinement context
     - step artifacts being written to disk
     - streamed responses finishing with a persisted final state
   - **Won't do:** depend on live OpenAI calls in CI; test only the happy path.

9. Update supporting docs in `milestones/PoC.md` and a short implementation note such as `docs/orchestrator-poc.md` if a new docs folder is added.
   - Align the milestone with the smaller `problem -> clarify -> plan -> refine` loop.
   - Document that observability for the PoC is disk inspectability rather than dashboards or production telemetry.
   - **Won't do:** reintroduce Build-stage scope or expand the README into full system design docs.

## Guardrails

- Optimize for learning and user validation, not production hardening.
- Keep the first implementation single-process and file-backed.
- Keep the orchestration server inside its own monorepo service directory so it stays independent from other services.
- After every orchestrator step, persist an explicit `state_check` before the request is considered complete.
- Require the state check to persist a confidence score on every turn.
- Route prompt selection from markdown files on disk rather than hardcoded inline strings.
- If confidence is below the configured threshold, prefer asking the analyst more questions over forcing plan creation or refinement.
- Treat the latest markdown plan as a first-class artifact and include it in later prompt context whenever it exists.
- Save each step in a human-inspectable format on disk so a reviewer can reconstruct what happened from the saved artifacts.
- Stream responses to the client to reduce perceived latency.
- Keep Build-stage execution out of scope for this milestone.
- Keep observability intentionally light: basic logs plus saved artifacts are enough for the PoC.
- Do not persist hidden chain-of-thought; persist user-visible questions, plans, decisions, and structured state instead.
- Before implementation is considered complete, run `ruff check` and `pytest`.
- Re-check against repository pillars:
  - `pillars/opinionated-simplicity-underrated.md`
  - `pillars/small-steps-toward-user-value.md`
  - `pillars/state-is-explicit-not-implicit.md`
