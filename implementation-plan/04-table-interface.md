# Work Stream 04: Interactive Table Interface

**Deliverable:** Excel-inspired table UI that serves as both an analysis workspace and a control surface for agent workflows.

---

## Vision Context

Users interact with results through a rich table interface inspired by Excel. This is the primary surface where Analysts—who typically work in Excel- and PowerPoint-style environments—engage with the platform.

**Dual role of the table interface:**

1. **Analysis workspace** — Edit data, add calculated columns, create pivot tables, filter and group
2. **Control surface for agent workflows** — Provide structured feedback to plans, approve or revise

**Capabilities (from vision):**
- Editing data directly
- Adding calculated columns
- Creating pivot tables
- Filtering and grouping data
- Providing structured feedback to plans

This bridges the gap between agent outputs and user control. Analysts supervise their agentic workforce through this interface.

---

## Persona Mapping

| Persona | Role in Table Interface |
|---------|--------------------------|
| **Analysts** | Primary users. Create projects, view and edit plan outputs, add calculated columns, create pivots, approve/revise plans, review results. |
| **Agents** | Produce table data as outputs. Receive feedback from table edits (e.g., "user added column X") for Revise stage. |
| **Knowledge Admins** | Rare users. May use tables to validate Book content or SOP outputs. |

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 03-agent-core | Plan and execution outputs available | Agent returns table data (JSON/CSV) |
| Frontend stack chosen | React, Vue, or equivalent selected | Tech stack documented |
| Design system (optional) | Components and patterns defined | UI kit or Figma available |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **Table Rendering** | Display tabular data with columns, rows, types | Core analysis workspace |
| **Editing** | In-cell edit, add/remove rows and columns | User refines data |
| **Calculations** | Formula support, calculated columns | Extend analysis |
| **Pivot & Aggregation** | Pivot tables, filtering, grouping | Deeper analysis |
| **Plan Control** | Feedback to plans, approval actions | Bridge to agent workflow |
| **Responsiveness** | Performance with large datasets | Usable at scale |

---

## Use Cases by Workflow Stage

### Plan Stage

- Display proposed plan steps in table or list form
- Show expected data sources and outputs
- Allow user to trigger "Revise" or "Approve"

### Revise Stage

- Display sample/preview tables from plan (Preview mode)
- User edits table structure (add column, change filter) → feedback to agent
- User provides natural language feedback in input field
- Table manipulation exports as structured feedback (e.g., "Added calculated column: growth = revenue / prev_revenue")

### Build Stage

- Display full result tables from agent execution
- User can further analyze: pivot, filter, add calculated columns
- Export to CSV/Excel for downstream use
- Trigger slide generation from table/chart selection

---

## Table Interface Architecture

```
Agent Output (JSON/CSV)
        ↓
Table Component (virtualized for large data)
        ↓
┌─────────────────────────────────────────┐
│  Columns: type-aware (text, number, date)│
│  Sorting, filtering, pagination          │
│  In-cell editing → sync to agent context │
│  Calculated columns (formula engine)    │
│  Pivot: rows, columns, values, agg       │
└─────────────────────────────────────────┘
        ↓
Plan Control: Approve | Revise | Export
```

---

## Actions

### Phase 1: Core Table

1. Implement table component with column types (text, number, date, currency).
2. Add sorting and basic filtering (per-column).
3. Support pagination or virtual scrolling for large datasets (10k+ rows).
4. Display data from agent execution (JSON/CSV → table). Handle schema from agent.

### Phase 2: Editing

5. Enable in-cell editing with validation (type-safe).
6. Add row/column add/remove (for user-driven extensions).
7. Implement undo/redo for edits.
8. Sync edits back to agent context for Revise stage (structured diff or full state).

### Phase 3: Calculations

9. Add formula syntax (e.g., SUM, AVG, or Excel-like subset).
10. Implement calculated columns. User defines formula, system computes.
11. Support dependent cell recalculation (DAG of dependencies).
12. Validate formula references (no circular refs, valid column names).

### Phase 4: Pivot & Aggregation

13. Implement pivot table creation: drag rows, columns, values.
14. Add grouping and aggregation (sum, count, average, min, max).
15. Support filter application to pivot views.
16. Export pivot config for agent (structured feedback: "User created pivot: rows=region, values=sum(revenue)").

### Phase 5: Plan Control

17. Display plan steps in table or list form. Show status (pending, running, done).
18. Add "Approve", "Revise", "Reject" actions. Wire to 03-agent-core.
19. Implement feedback input: natural language text area + structured options (e.g., "Add regional breakdown").
20. Show execution status and progress (e.g., "Step 2 of 5 running").

### Phase 6: Polish

21. Add loading states and error handling (timeout, partial failure).
22. Implement export (CSV, Excel). Preserve formatting where possible.
23. Ensure accessibility: keyboard nav, screen readers, ARIA labels.
24. Performance test with 100k+ row datasets. Target: render in <2s for 10k rows.

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **03-agent-core** | Receives plan, execution outputs; sends approval/revise/feedback |
| **05-query-execution** | Displays Preview results during Plan/Revise; full results during Build |
| **06-slide-generation** | User selects table/chart for slide; triggers slide build |
| **07-database-backend** | May persist user edits, pivot configs (optional) |

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Data integrity** | Edits do not corrupt data types | Validate on change; reject invalid |
| **Formula safety** | No arbitrary code execution in formulas | Sandbox or restrict to allowlist (SUM, AVG, etc.) |
| **Feedback clarity** | User feedback reaches agent unambiguously | Add structured options; validate before send |
| **Performance** | Table renders in <2s for 10k rows | Optimize or virtualize |
| **Accessibility** | WCAG 2.1 AA compliance | Audit and fix |
| **Export accuracy** | Exported data matches displayed data | Validate export logic |

---

## Deliverables

- [ ] Table component with sorting, filtering, pagination/virtualization
- [ ] In-cell editing and row/column manipulation
- [ ] Calculated columns and formula support
- [ ] Pivot table creation and aggregation
- [ ] Plan display and approval/revise controls
- [ ] Export to CSV/Excel
- [ ] Performance validated for 10k+ rows
