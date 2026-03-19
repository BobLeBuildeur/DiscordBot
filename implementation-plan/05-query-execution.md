# Work Stream 05: Query Execution Model (Preview vs Build)

**Deliverable:** Dual-mode query engine that separates fast, limited preview queries from full execution queries to balance responsiveness and completeness.

---

## Vision Context

To maintain responsiveness and control system costs, the platform separates **preview queries** from **full execution queries**. This is a core architectural decision that affects both user experience and system economics.

**Preview Mode (Plan and Revise stages):**
- Queries run with hard row limits
- Only a sample of the dataset is returned
- Goal: exploration and structural design

**User benefits during Preview:**
- Inspect schemas
- Test joins and filters
- Validate calculated columns
- Prototype pivot tables

Preview ensures the system remains fast and interactive, even with very large datasets.

**Build Mode (Execution stage):**
- Row limits are removed
- Full aggregations are computed
- Complete results are generated
- Downstream outputs (tables, charts, slides) are produced

Build ensures final outputs are complete and production-grade.

---

## Persona Mapping

| Persona | Role in Query Execution |
|---------|-------------------------|
| **Agents** | Issue queries. Receive mode (Preview/Build) from orchestrator. Execute via MCP connectors. |
| **Analysts** | Experience fast Preview during Plan/Revise; receive full results during Build. |
| **System** | Mode routing based on workflow stage. Cost control via query budget. |

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 01-data-connectivity | Connectors support row limits | Connector accepts `row_limit` param |
| 07-database-backend | Query metadata can be stored | Execution context persisted |
| 03-agent-core | Plan stages (Plan, Revise, Build) defined | Stage passed to query layer |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **Preview Mode** | Row-limited queries, schema inspection, sample data | Fast exploration during Plan/Revise |
| **Build Mode** | Full dataset, no limits, complete aggregations | Production outputs |
| **Mode Routing** | Map plan stage to query mode | Correct behavior per stage |
| **Query Caching** | Cache preview results where safe | Reduce redundant queries |
| **Cost Control** | Track and limit query volume | Prevent runaway costs |

---

## Mode Semantics (Detailed)

### Preview Mode

| Aspect | Behavior |
|--------|----------|
| **Row limit** | Default 1000 (configurable per connector). Hard enforce. |
| **Schema** | Return schema + sample. Schema-only option when no data needed. |
| **Sampling** | For APIs that can't limit: random or stratified sample. |
| **Aggregations** | Run on sample only. Results are approximate. User must understand "preview" nature. |
| **When used** | Plan stage (initial exploration), Revise stage (iterative refinement) |

### Build Mode

| Aspect | Behavior |
|--------|----------|
| **Row limit** | None. Full dataset. |
| **Schema** | Same as Preview (consistency). |
| **Aggregations** | Full. Production-grade. |
| **When used** | Build stage only, after user approval. |

---

## Mode Routing Logic

```
if stage in [Plan, Revise]:
    mode = Preview
    row_limit = config.preview_limit  # e.g., 1000
else if stage == Build:
    mode = Build
    row_limit = None
```

**Critical:** Build stage must never receive row-limited queries. Audit connector code to ensure no limit is applied when mode=Build.

---

## Schema Consistency

The same logical query in Preview vs Build must return **compatible schema** (same columns, types). Row count differs; structure does not. This allows:
- User to validate structure during Preview
- Agent to use same query template in Build
- Downstream (table UI, slides) to consume without schema changes

---

## Actions

### Phase 1: Mode Definition

1. Define Preview mode: default row limit (e.g., 1000), configurable per connector.
2. Define Build mode: no row limit, full execution.
3. Implement mode flag in query context. Pass from 03-agent-core (stage → mode).
4. Document mode semantics for each connector. Add to connector docs.

### Phase 2: Connector Integration

5. Ensure all DB connectors accept `row_limit` parameter.
6. For Preview: inject `LIMIT N` (or equivalent) into queries. Validate limit is applied.
7. For Build: omit limit; execute full query. Ensure no limit leaks from Preview config.
8. Handle connectors that cannot limit (e.g., some APIs): document and apply sampling (random or first N).

### Phase 3: Schema & Sample

9. Implement schema-only queries for Preview when user needs structure (e.g., "what columns exist?").
10. Add "sample" mode: random or stratified sample for very large tables. Document strategy.
11. Return schema + sample in Preview responses for agent context. Agent uses for plan refinement.

### Phase 4: Mode Routing

12. Integrate with 03-agent-core: pass stage (Plan/Revise vs Build) to query layer.
13. Enforce: Plan and Revise always use Preview; Build always uses full.
14. Add override mechanism for admin/debug (document and restrict to admins).

### Phase 5: Caching & Cost

15. Implement optional cache for identical Preview queries. Short TTL (e.g., 5 min). Invalidate on schema change.
16. Add query counter per project/session. Track Preview vs Build separately.
17. Define and enforce query budget (e.g., max 50 queries per Build run, max 200 Preview per session).
18. Log query mode, row count, duration for analytics and cost attribution.

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **01-data-connectivity** | Connectors implement row_limit; mode passed from query layer |
| **03-agent-core** | Passes stage to query layer; receives mode for each tool call |
| **07-database-backend** | Store query metadata (mode, row count, duration) for audit |
| **04-table-interface** | Displays Preview results (with "preview" indicator) and Build results |

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Preview limit** | Preview never returns more than configured limit | Hard enforce in connector; reject if exceeded |
| **Build completeness** | Build never applies row limit | Audit connector code; add test |
| **Mode consistency** | Same logical query in Preview vs Build returns compatible schema | Validate schema match in tests |
| **Cost cap** | Query budget prevents runaway execution | Abort when exceeded; notify user |
| **Cache safety** | Cached data not stale beyond TTL | Short TTL or invalidate on schema change |
| **Sampling fairness** | Sample mode is representative | Document sampling strategy; consider stratified for key columns |

---

## Deliverables

- [ ] Preview mode with configurable row limits
- [ ] Build mode with full execution
- [ ] Connector integration for both modes
- [ ] Schema-only and sample options
- [ ] Mode routing from agent stage
- [ ] Query budget and logging
