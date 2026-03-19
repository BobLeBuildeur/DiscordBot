# Work Stream 05: Query Execution Model (Preview vs Build)

**Deliverable:** Dual-mode query engine that separates fast, limited preview queries from full execution queries to balance responsiveness and completeness.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 01-data-connectivity | Connectors support row limits | Connector accepts limit param |
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

## Actions

### Phase 1: Mode Definition

1. Define Preview mode: default row limit (e.g., 1000), configurable per connector.
2. Define Build mode: no row limit, full execution.
3. Implement mode flag in query context (passed from agent/orchestrator).
4. Document mode semantics for each connector.

### Phase 2: Connector Integration

5. Ensure all DB connectors accept `row_limit` parameter.
6. For Preview: inject `LIMIT N` (or equivalent) into queries.
7. For Build: omit limit; execute full query.
8. Handle connectors that cannot limit (e.g., some APIs): document and apply sampling.

### Phase 3: Schema & Sample

9. Implement schema-only queries (no data) for Preview when user needs structure.
10. Add "sample" mode: random or stratified sample for very large tables.
11. Return schema + sample in Preview responses for agent context.

### Phase 4: Mode Routing

12. Integrate with 03-agent-core: pass stage (Plan/Revise vs Build) to query layer.
13. Enforce: Plan and Revise always use Preview; Build always uses full.
14. Add override mechanism for admin/debug (document and restrict).

### Phase 5: Caching & Cost

15. Implement optional cache for identical Preview queries (short TTL).
16. Add query counter per project/session.
17. Define and enforce query budget (e.g., max queries per Build run).
18. Log query mode, row count, duration for analytics.

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Preview limit** | Preview never returns more than configured limit | Hard enforce in connector |
| **Build completeness** | Build never applies row limit | Audit connector code |
| **Mode consistency** | Same logical query in Preview vs Build returns compatible schema | Validate schema match |
| **Cost cap** | Query budget prevents runaway execution | Abort when exceeded |
| **Cache safety** | Cached data not stale beyond TTL | Short TTL or invalidate on schema change |
| **Sampling fairness** | Sample mode is representative | Document sampling strategy |

---

## Deliverables

- [ ] Preview mode with configurable row limits
- [ ] Build mode with full execution
- [ ] Connector integration for both modes
- [ ] Schema-only and sample options
- [ ] Mode routing from agent stage
- [ ] Query budget and logging
