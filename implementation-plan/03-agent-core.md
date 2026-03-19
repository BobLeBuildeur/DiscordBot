# Work Stream 03: Agent Core & Orchestration

**Deliverable:** Agent orchestration engine that implements the Plan → Revise → Build workflow and coordinates execution across MCP tools and Books.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 01-data-connectivity | MCP servers and tools available | Tools callable from agent |
| 02-knowledge-base | Books available for retrieval | Agent can fetch Books |
| LLM API access | Production LLM endpoint configured | Successful completion test |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **Plan Stage** | Plan generation, structured output (steps, data, methods, outputs) | User gets actionable proposal |
| **Revise Stage** | Plan editing, feedback ingestion, constraint application | User controls direction |
| **Build Stage** | Full execution, tool orchestration, artifact production | Complete outputs |
| **Agent Loop** | Iteration between LLM and tools | Agents perform multi-step work |
| **State Management** | Plan state, revision history, execution status | Traceability and resumability |

---

## Actions

### Phase 1: Plan Stage

1. Implement prompt template for plan generation (user task + retrieved Books).
2. Define structured output schema: steps, data_sources, methods, expected_outputs.
3. Build plan generator that calls LLM and parses response.
4. Add Book retrieval: fetch relevant Knowledge and SOP Books for task.
5. Return proposed plan to user (JSON or UI representation).

### Phase 2: Revise Stage

6. Implement plan editor: accept natural language feedback, table edits, constraints.
7. Build feedback processor: map user input to plan modifications.
8. Support iterative revision (multiple rounds before approval).
9. Persist revision history for audit.

### Phase 3: Build Stage

10. Implement execution orchestrator: iterate over approved plan steps.
11. For each step: call MCP tools (query, execute_python), pass Books as context.
12. Enforce Build mode: no row limits, full dataset (coordinate with 05-query-execution).
13. Collect outputs: tables, intermediate results, final artifacts.
14. Handle errors: retry, partial results, user notification.

### Phase 4: Agent Loop & State

15. Implement agent loop: LLM decides next action → execute tool → return result → repeat.
16. Add state persistence: save plan, revisions, execution state to DB.
17. Support resumption: user can resume interrupted execution.
18. Add execution logging for debugging and compliance.

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Plan structure** | Generated plans have required fields | Validate and retry or reject |
| **Tool safety** | Agent cannot invoke tools not in allowlist | Enforce tool registry |
| **Build vs Preview** | Build stage never uses row-limited queries | Coordinate with query layer |
| **Execution timeout** | Single run has max duration (e.g., 30 min) | Abort and save state |
| **Token budget** | LLM calls have token limits | Truncate or summarize context |
| **Idempotency** | Same plan + inputs → same outputs (where applicable) | Document non-determinism |

---

## Deliverables

- [ ] Plan generator with structured output
- [ ] Revise stage with feedback processing
- [ ] Build stage execution engine
- [ ] Agent loop with tool orchestration
- [ ] State persistence and resumption
- [ ] Integration with 04-table-interface for plan display
