# Stateless Agentic Orchestration Server

## Context

This feature extends the PoC's `Plan -> Revise -> Build` concept by defining the execution substrate for the future Build stage without turning the backend into a long-lived stateful process. The design follows Void-like paradigms: state is an explicit artifact, each request advances work by one observable step, execution is resumable from disk, and the server remains a thin coordinator rather than a hidden autonomous runtime.

## Goal

Add a Python orchestration server that lets Analysts and Agents start a task, execute exactly one step per API call, and resume work from a local session file instead of in-memory process state. Success means:

- `POST /start-task` creates a task state file for a new session.
- `POST /run-step?step_id=<id>` loads the session file, executes one step, records iterations, memory updates, metrics, and final output for that step, then saves the state back to disk.
- `POST /continue` loads the same state file, selects the next runnable step, advances exactly one step, and saves the result.
- Restarting the server does not lose task progress because the JSON file is the source of truth.
- Operators can inspect a task's current plan, step history, and memory directly from the saved state file.

## Preconditions

- Python 3.11+ is available for typing, `pathlib`, `contextlib`, and modern async/server support.
- The PoC's Plan and Revise stages are already capable of producing an approved ordered plan that can be handed to Build-stage execution.
- A writable local directory such as `./data/sessions/` is available to persist one JSON file per task.
- A clear contract exists for how a planned step becomes an executable step definition:
  - either direct execution from user-approved markdown plan content, or
  - a normalization pass that converts the approved plan into structured steps.
- The implementation chooses one Python API framework before coding begins; FastAPI is the recommended default for typed request/response models.
- The team accepts the single-node persistence model for this feature phase; this plan does not introduce shared databases, queues, or distributed locks.

## Used Tools

- Python 3.11+ for the application runtime.
- FastAPI for HTTP endpoints and request/response validation.
- Pydantic for state models, endpoint schemas, and JSON serialization contracts.
- `uvicorn` for local server execution.
- Standard library file primitives (`pathlib`, `json`, `tempfile`, `os.replace`) for atomic state persistence.
- A lightweight file-locking mechanism for same-task concurrency protection:
  - preferred: `filelock` Python package, or
  - fallback: POSIX locking if the deployment target stays Linux-only.
- `pytest` for unit and integration tests.
- `httpx` or FastAPI `TestClient` for endpoint tests.
- `ruff` for linting and import hygiene.
- `mypy` for type-checking core orchestration and state models.

## Steps

1. Define the domain model in `server/domain/state.py` and `server/domain/events.py`.
   - Create typed models for:
     - `TaskState`
     - `PlanStep`
     - `StepIteration`
     - `MemoryEntry` or `memory: dict[str, str]`
     - `TaskMetrics`
   - Extend the approximate state shape into a stricter schema with:
     - `status` enums such as `pending`, `running`, `completed`, `failed`, `blocked`
     - `current_step_id`
     - `error` fields for failed steps
     - iteration timestamps and attempt numbers
   - **Won't do:** keep the state as an untyped free-form dictionary; mix API payloads and persistence models in route handlers.

2. Implement file-backed state persistence in `server/storage/session_store.py`.
   - Store each session at `data/sessions/{task_id}.json`.
   - Implement:
     - `create_task(state: TaskState) -> TaskState`
     - `load_task(task_id: str) -> TaskState`
     - `save_task(state: TaskState) -> TaskState`
   - Use temp-file write plus atomic rename to prevent partial writes.
   - Add per-task lock files so concurrent `run-step` or `continue` requests for the same task cannot corrupt state.
   - **Won't do:** hold task state in module globals; rely on non-atomic direct overwrite writes; ignore concurrent request collisions.

3. Add step execution primitives in `server/orchestrator/step_runner.py`.
   - Create a pure orchestration boundary:
     - input: loaded `TaskState`, target `step_id`, execution context
     - output: updated `TaskState`
   - Represent each run as one iteration appended to `steps[n].iterations`.
   - Update `memory` with summarized outputs keyed by step name or canonical step ID.
   - Write `final_output`, `confidence`, duration, token/tool metrics, and failure metadata back into the step record.
   - Keep the runner stateless between requests; all continuity comes from loaded state.
   - **Won't do:** spawn a background worker that keeps hidden session memory; mutate state outside the loaded-and-saved request cycle.

4. Introduce an executor registry in `server/orchestrator/executors.py`.
   - Define a small executor interface such as `execute(step: PlanStep, state: TaskState) -> StepResult`.
   - Support initial executor types like:
     - `llm_reasoning`
     - `tool_call`
     - `synthesis`
     - `human_input_required`
   - This keeps the server close to Void-style explicit work units: each step is inspectable, typed, and routed through a known executor.
   - **Won't do:** encode step-specific branching logic directly in API endpoints; let arbitrary strings invoke arbitrary code paths without validation.

5. Build task lifecycle services in `server/orchestrator/task_service.py`.
   - Implement:
     - `start_task(task, plan) -> TaskState`
     - `run_step(task_id, step_id) -> TaskState`
     - `continue_task(task_id) -> TaskState`
     - `get_next_runnable_step(state) -> PlanStep | None`
   - `start_task` should normalize the approved plan into structured steps, set timestamps, initialize metrics, and persist the first state file.
   - `continue_task` should select the next `pending` or retryable step and advance exactly one step.
   - **Won't do:** let `/continue` silently execute the entire remaining plan; make next-step selection opaque or inconsistent.

6. Expose the HTTP API in `server/api/tasks.py` and `server/app.py`.
   - Add endpoints:
     - `POST /start-task`
     - `POST /run-step`
     - `POST /continue`
     - `GET /tasks/{task_id}`
   - Example request contracts:
     - `POST /start-task` accepts task text plus either a structured plan array or a reference to the approved PoC plan artifact.
     - `POST /run-step` accepts `task_id` and `step_id`.
     - `POST /continue` accepts `task_id`.
   - Return the updated task state or a summarized view that includes latest step status, outputs, and next-step hints.
   - **Won't do:** hide task state behind non-deterministic side effects; make clients guess whether a step actually persisted.

7. Add observability and audit fields in `server/orchestrator/metrics.py` or the state layer.
   - Record:
     - request count per task
     - step duration
     - executor type
     - retry count
     - token/tool usage where available
     - last error
   - Keep these metrics inside the task file for local inspectability during the single-node phase.
   - If metrics become too noisy, split volatile metrics into a sibling file later; keep the primary state file readable.
   - **Won't do:** rely on logs alone as the system of record for task progress.

8. Add tests in `tests/test_session_store.py`, `tests/test_step_runner.py`, and `tests/test_tasks_api.py`.
   - Cover:
     - task creation and file persistence
     - atomic save behavior
     - `run-step` updates only the targeted step
     - `continue` chooses the next runnable step and advances only one step
     - recovery after process restart by reloading from saved JSON
     - concurrent same-task requests are serialized or rejected safely
     - failure paths preserve partial history without corrupting prior steps
   - **Won't do:** test only happy paths; skip restart and concurrency coverage.

9. Document the execution model in `docs/orchestration-server.md` or extend `README.md`.
   - Explain the core loop explicitly:
     - User -> API -> load state -> run one step -> save state
   - Include a sample JSON session file and example request/response bodies.
   - Document non-goals for this phase:
     - no long-running daemon memory
     - no multi-step automatic background loop
     - no distributed persistence
   - **Won't do:** leave the statelessness model implicit; document behavior differently from the API contract.

## Guardrails

- Preserve the PoC's scope boundary: this feature creates Build-stage execution infrastructure, but it must not force the Plan or Revise stages to become stateful server-side workflows.
- Treat the saved task file as the source of truth. The server may cache nothing that is required for correctness across requests.
- Advance exactly one step per mutating endpoint call. A request may retry a step, but it must not silently execute multiple pending steps.
- Do not persist hidden chain-of-thought. Persist observable artifacts only: prompts, tool inputs/outputs where appropriate, summaries, status transitions, user-visible rationale, and metrics.
- Use atomic file writes and per-task locking so a crash or duplicate request cannot leave invalid JSON behind.
- Keep state schema versioned with a field such as `state_version` to make future migrations explicit.
- Keep the session file small and inspectable; store bulky artifacts by reference if outputs grow too large.
- Return deterministic error responses for missing task IDs, missing step IDs, locked tasks, and non-runnable steps.
- Validate all state transitions:
  - `pending -> running -> completed`
  - `pending -> running -> failed`
  - `failed -> running -> completed` for retries
- Run `ruff check`, `mypy`, and `pytest` before implementation is considered complete.
- Confirm alignment with current repository pillars. At present, the repository contains pillar instructions but no concrete pillar files beyond `pillars/README.md`; if new pillars are added later, re-check this plan before implementation.

## Proposed State Shape

```json
{
  "state_version": 1,
  "task_id": "task_123",
  "task": "Build a monthly operations report",
  "plan": ["Collect source data", "Analyze trends", "Draft report"],
  "current_step_id": 2,
  "steps": [
    {
      "step_id": 1,
      "name": "Collect source data",
      "executor": "tool_call",
      "status": "completed",
      "iterations": [
        {
          "attempt": 1,
          "started_at": "2026-03-19T12:00:00Z",
          "finished_at": "2026-03-19T12:00:03Z",
          "summary": "Fetched source files and normalized headers"
        }
      ],
      "final_output": "Normalized dataset stored for downstream analysis",
      "confidence": 0.93,
      "error": null
    }
  ],
  "memory": {
    "step_1": "Normalized dataset is ready",
    "step_2": "Trend analysis pending"
  },
  "metrics": {
    "request_count": 3,
    "step_count_completed": 1,
    "last_executor": "tool_call"
  },
  "created_at": "2026-03-19T12:00:00Z",
  "updated_at": "2026-03-19T12:00:03Z"
}
```

## API Sketch

```text
POST /start-task
  -> validate input
  -> build TaskState
  -> save data/sessions/{task_id}.json
  -> return created state

POST /run-step
  -> load state
  -> lock task file
  -> run requested step
  -> save state
  -> return updated state

POST /continue
  -> load state
  -> lock task file
  -> select next runnable step
  -> run exactly one step
  -> save state
  -> return updated state
```

## Open Questions

- Should `POST /start-task` accept only a structured plan, or should it also parse approved markdown plans produced by the PoC Plan stage?
- Should `memory` remain a simple dictionary in v1, or should it become a typed list of memory entries with scopes such as `task`, `step`, and `artifact`?
- Do we want `GET /tasks/{task_id}` in v1 for inspectability, even though it was not in the original pseudo-code?
- What is the maximum expected size of a local task file before large artifacts should be written out-of-band and referenced from state?
