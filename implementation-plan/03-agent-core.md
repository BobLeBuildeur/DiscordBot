# Work Stream 03: Agent Core & Orchestration

**Deliverable:** Agent orchestration engine that implements the Plan → Revise → Build workflow and coordinates execution across MCP tools and Books.

---

## Vision Context

The platform's core workflow is **Plan → Revise → Build**. This work stream implements the engine that powers it.

**Core idea:** Everyone becomes the manager of their own agentic workforce. Users no longer manually execute analytical and reporting tasks. Instead, they plan, supervise, and refine work executed by AI agents.

**Agent responsibilities:**
- Execute approved plans
- Retrieve data from connected systems
- Run analysis and calculations
- Produce outputs (tables, charts, slides)

**Agent interactions:**
- MCP servers (data connectivity)
- Python execution environments
- Books in the knowledge base

---

## Persona Mapping

| Persona | Role in Agent Core |
|---------|--------------------|
| **Analysts** | Create projects, prompt for plans, revise and approve plans, review results, supervise agent execution. They are the "managers" of the agentic workforce. |
| **Agents** | The autonomous workers. They perform Plan generation (with LLM), execute Build (with tools), and respond to Revise feedback. |
| **Knowledge Admins** | Indirect. Their Books are retrieved and used by agents during Plan and Build. |

---

## Workflow Stages (Detailed)

### 1. Plan

**User action:** Prompts the system (e.g., "Analyze sales performance", "Build a monthly operations report", "Create a market analysis presentation").

**System behavior:**
- Retrieves relevant rules via MCP `search_rules` (hybrid search: vector + keyword)
- Calls LLM with user task + rules as context
- Proposes structured plan: steps, required data sources, analysis methods, expected outputs

**Output:** Proposed plan (JSON or UI representation) for user review.

### 2. Revise

**User action:** Reviews and edits the proposed plan before execution.

**Revision mechanisms:**
- Natural language feedback ("Add regional breakdown", "Use last 12 months")
- Table manipulation (add/remove columns, change filters)
- Adding constraints or instructions

**Goals:**
- Business context is captured
- Analytical direction is correct
- Organizational standards are respected

**System behavior:** Feedback processor maps user input to plan modifications. Supports iterative revision (multiple rounds). Persists revision history.

### 3. Build

**User action:** Approves the plan.

**System behavior:**
- Agents execute the full plan
- Retrieve data (full dataset, no row limits—see 05-query-execution)
- Run analysis
- Produce structured outputs
- Create final artifacts (tables, charts, slides)

**Output:** Complete, production-grade results.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 01-data-connectivity | MCP servers and tools available | Tools callable from agent |
| 02-knowledge-base | Rules available via PocketBase; MCP search_rules | Agent can call search_rules |
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

## Plan Output Schema

```json
{
  "task": "Analyze sales performance",
  "steps": [
    {
      "index": 1,
      "action": "Retrieve sales data by region and product",
      "data_source": "sales_warehouse",
      "method": "SQL query",
      "outputs": ["sales_raw"]
    },
    {
      "index": 2,
      "action": "Calculate YoY growth and regional breakdown",
      "data_source": null,
      "method": "Python/pandas",
      "inputs": ["sales_raw"],
      "outputs": ["growth_analysis"]
    },
    {
      "index": 3,
      "action": "Generate summary table and charts",
      "method": "Table + chart spec",
      "inputs": ["growth_analysis"],
      "outputs": ["final_table", "chart_specs"]
    }
  ],
  "data_sources": ["sales_warehouse"],
  "expected_outputs": ["Table: regional sales with growth", "Charts: bar chart by region"]
}
```

---

## Agent Loop (Build Stage)

```
1. Load approved plan
2. For each step:
   a. LLM decides: which tool to call, with what params
   b. Execute tool (query_database, execute_python, etc.)
   c. Return result to LLM
   d. LLM processes result, decides next action
   e. Repeat until step complete
3. Collect outputs (tables, chart specs)
4. Pass to slide generation if plan includes slides
5. Persist final state
```

---

## Actions

### Phase 1: Plan Stage

1. Implement prompt template for plan generation (user task + retrieved Books).
2. Define structured output schema: steps, data_sources, methods, expected_outputs.
3. Build plan generator that calls LLM and parses response (JSON mode or structured output).
4. Add rule retrieval: call MCP `search_rules` with user task; fetch relevant rules for context.
5. Return proposed plan to user (JSON or UI representation via 04-table-interface).

### Phase 2: Revise Stage

6. Implement plan editor: accept natural language feedback, table edits, constraints.
7. Build feedback processor: map user input to plan modifications (LLM-assisted or rule-based).
8. Support iterative revision (multiple rounds before approval).
9. Persist revision history for audit (07-database-backend).

### Phase 3: Build Stage

10. Implement execution orchestrator: iterate over approved plan steps.
11. For each step: call MCP tools (query, execute_python), pass rules as context.
12. Enforce Build mode: no row limits, full dataset (coordinate with 05-query-execution).
13. Collect outputs: tables, intermediate results, final artifacts.
14. Handle errors: retry, partial results, user notification.

### Phase 4: Agent Loop & State

15. Implement agent loop: LLM decides next action → execute tool → return result → repeat.
16. Add state persistence: save plan, revisions, execution state to DB (07-database-backend).
17. Support resumption: user can resume interrupted execution.
18. Add execution logging for debugging and compliance.

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **01-data-connectivity** | Agent invokes MCP tools during Build |
| **02-knowledge-base** | Agent calls search_rules at Plan; uses rules as context during Build |
| **04-table-interface** | Displays plan, approval/revise controls, execution status, results |
| **05-query-execution** | Pass stage (Plan/Revise vs Build) to query layer for mode routing |
| **06-slide-generation** | Trigger slide build from plan outputs |
| **07-database-backend** | Persist plans, revisions, runs, steps |

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Plan structure** | Generated plans have required fields (steps, data_sources, etc.) | Validate and retry or reject |
| **Tool safety** | Agent cannot invoke tools not in allowlist | Enforce tool registry |
| **Build vs Preview** | Build stage never uses row-limited queries | Coordinate with 05-query-execution |
| **Execution timeout** | Single run has max duration (e.g., 30 min) | Abort and save state |
| **Token budget** | LLM calls have token limits | Truncate or summarize context |
| **Idempotency** | Same plan + inputs → same outputs (where applicable) | Document non-determinism (LLM, sampling) |

---

## Deliverables

- [ ] Plan generator with structured output
- [ ] Revise stage with feedback processing
- [ ] Build stage execution engine
- [ ] Agent loop with tool orchestration
- [ ] State persistence and resumption
- [ ] Integration with 04-table-interface for plan display
