# Work Stream 01: Data Connectivity

**Deliverable:** MCP server framework, data connectors, and Python execution environment that enable agents to query enterprise systems and run analysis.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 00-preconditions met | All global preconditions satisfied | 00-preconditions.md sign-off |
| Data source inventory | At least 3 data sources identified | Document in data catalog |
| Auth model defined | How agents authenticate to each source | Auth spec documented |
| Network access | Agents can reach target systems | Connectivity test passed |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **MCP Server Framework** | Protocol implementation, tool registration | Agents discover and invoke data tools |
| **Database Connectors** | SQL/NoSQL adapters for internal DBs | Query enterprise data |
| **API Connectors** | REST/GraphQL clients for internal APIs | Pull operational metrics |
| **Python Sandbox** | Isolated execution for analysis code | Run transforms, stats, models |
| **Data Schema Registry** | Metadata about available datasets | Agents understand structure |

---

## Actions

### Phase 1: MCP Foundation

1. Implement MCP protocol server (or integrate existing implementation).
2. Define tool interface: `query_database`, `call_api`, `execute_python`.
3. Register tools with agent runtime.
4. Add authentication passthrough (service account, OAuth, etc.).

### Phase 2: Connectors

5. Build database connector for primary data warehouse (e.g., PostgreSQL, Snowflake).
6. Build API connector for key operational systems.
7. Implement row-limit parameter for preview mode (used by 05-query-execution).
8. Add error handling and retry logic.

### Phase 3: Python Environment

9. Provision sandboxed Python environment (container or VM).
10. Pre-install common libraries (pandas, numpy, scipy, etc.).
11. Implement `execute_python` tool with timeout and resource limits.
12. Add output serialization (DataFrame → JSON/CSV).

### Phase 4: Schema Registry

13. Create schema registry (DB or config) for datasets.
14. Populate with table/column metadata for primary sources.
15. Expose schema via MCP tool for agent discovery.

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **MCP compliance** | Server responds to standard MCP requests | Fix protocol implementation |
| **Auth isolation** | Each connector uses least-privilege credentials | Do not use broad admin accounts |
| **Row limits** | Preview queries enforce hard row limit (e.g., 1000) | Reject queries without limit in preview |
| **Python safety** | Sandbox blocks file system, network (except allowed) | Audit and restrict capabilities |
| **Timeout** | All connector calls have timeout (e.g., 60s) | Prevent runaway queries |
| **Schema accuracy** | Registry reflects actual DB structure | Validate against live schema |

---

## Deliverables

- [ ] MCP server with registered data tools
- [ ] At least 2 working connectors (DB + API)
- [ ] Python sandbox with execute_python tool
- [ ] Schema registry with 3+ datasets
- [ ] Documentation for adding new connectors
