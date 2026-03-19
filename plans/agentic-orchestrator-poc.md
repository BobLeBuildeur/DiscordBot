# Agentic Orchestrator PoC

## Goal

Add a lightweight orchestration service for Analysts that turns a rough problem statement into a markdown plan through a conversational loop. Success means:

- `POST /orchestrator/sessions` creates a session from the initial problem statement and immediately runs a state check.
- `POST /orchestrator/sessions/{session_id}/messages` accepts user answers or plan feedback and streams back either follow-up questions or a markdown plan.
- After each turn, the orchestrator persists a structured `state_check` that says whether more information is required or whether the next action is `ask_follow_up`, `create_plan`, or `refine_plan`.
- Once a plan exists, the latest markdown plan is always included in later prompt context.
- Every step is saved to disk in an inspectable format so the team can replay real PoC sessions and learn from them.

## Preconditions

- Python 3.11+ is available.
- `OPENAI_API_KEY` is configured for the runtime environment.
- A writable local directory such as `data/orchestrator/` is available for persisted sessions.
- The team accepts a single-node, file-backed design for the PoC.
- The generated markdown plan should follow the structure described in `.cursor/rules/feature-planning.mdc`.
- The implementation can mock OpenAI responses in tests; multi-provider support is out of scope for this milestone.

## Used Tools

- Python 3.11+ for the application runtime.
- FastAPI, or the existing Python HTTP layer, for endpoints and streamed responses.
- Pydantic for request, response, and saved-state models.
- OpenAI API for state checks, follow-up questions, plan generation, and plan refinement.
- Standard library file primitives (`pathlib`, `json`, `tempfile`, `os.replace`) for persisted snapshots and step artifacts.
- Server-Sent Events or chunked HTTP streaming for low-latency responses.
- `pytest` for unit and integration tests.
- `ruff` for linting.

## Steps

1. Define the orchestrator state in `backend/orchestrator/models.py`.
   - Add models for `SessionState`, `TurnRecord`, `PlanVersion`, and `StateCheck`.
   - `StateCheck` should capture the post-step decision explicitly, for example:
     - `needs_more_information: bool`
     - `next_action: ask_follow_up | create_plan | refine_plan | wait_for_user`
     - `reason`
     - `missing_information`
   - `SessionState` should keep `problem_statement`, `conversation_history`, `current_plan_markdown`, `plan_versions`, and the latest `state_check`.
   - **Won't do:** infer workflow state only from loose chat history; keep the current plan only in transient process memory.

2. Implement file-backed session storage in `backend/orchestrator/store.py`.
   - Save the latest snapshot at `data/orchestrator/{session_id}/session.json`.
   - Save each step as a separate artifact such as `data/orchestrator/{session_id}/steps/{step_index}-{kind}.json`.
   - Persist at least:
     - session creation
     - each user message
     - each LLM state-check result
     - each streamed assistant result
     - each new or revised markdown plan
   - Use temp-file plus rename for snapshot writes so saved sessions stay readable after interruptions.
   - **Won't do:** introduce a database, queue, or metrics pipeline for the PoC; rely on logs alone for reconstruction.

3. Build the orchestration loop in `backend/orchestrator/engine.py`.
   - `start_session(problem_statement)` should create the session, run the first state check, and decide whether to ask follow-up questions or draft a plan.
   - `advance_session(session_id, user_message)` should load the snapshot, append the new user input, rerun the state check, and branch to:
     - follow-up question generation
     - first plan generation
     - plan refinement
   - Once `current_plan_markdown` exists, include it in every later state-check and refinement prompt.
   - Keep the loop user-driven: one user turn in, one streamed assistant turn out, then persist the updated state.
   - **Won't do:** execute the full plan automatically; create hidden background loops; add Build-stage task execution.

4. Create focused prompt builders in `backend/orchestrator/prompts.py`.
   - Add separate prompts for:
     - state check
     - follow-up question generation
     - initial markdown plan generation
     - markdown plan refinement from user comments
   - The plan-generation prompt should require the markdown structure described in `.cursor/rules/feature-planning.mdc`.
   - The refinement prompt should include both the latest plan markdown and the latest user feedback.
   - **Won't do:** use one oversized prompt that mixes orchestration decisions and final user output without structured intermediate state.

5. Expose a small streaming API in `backend/api/orchestrator.py` and `backend/app.py`.
   - Add:
     - `POST /orchestrator/sessions` for the initial problem statement
     - `POST /orchestrator/sessions/{session_id}/messages` for answers and plan feedback
     - `GET /orchestrator/sessions/{session_id}` for inspectability of the saved state
   - Stream assistant output as it is generated, then emit a final event or response chunk containing the saved `state_check` and `session_id`.
   - Keep the payloads simple so a thin PoC client can render chat text and markdown plans without a complex protocol.
   - **Won't do:** defer all output until the model finishes; design a production-grade websocket layer before validating the user experience.

6. Add end-to-end tests in `tests/test_orchestrator_store.py`, `tests/test_orchestrator_engine.py`, and `tests/test_orchestrator_api.py`.
   - Mock OpenAI responses to cover:
     - more information needed
     - enough information to create a plan
     - plan refinement after user comments
     - the plan being included in refinement context
     - step artifacts being written to disk
     - streamed responses finishing with a persisted final state
   - **Won't do:** depend on live OpenAI calls in CI; test only the happy path.

7. Update supporting docs in `milestones/PoC.md` and a short implementation note such as `docs/orchestrator-poc.md` if a new docs folder is added.
   - Align the milestone with the smaller `problem -> clarify -> plan -> refine` loop.
   - Document that observability for the PoC is disk inspectability rather than dashboards or production telemetry.
   - **Won't do:** reintroduce Build-stage scope or expand the README into full system design docs.

## Guardrails

- Optimize for learning and user validation, not production hardening.
- Keep the first implementation single-process and file-backed.
- After every orchestrator step, persist an explicit `state_check` before the request is considered complete.
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
