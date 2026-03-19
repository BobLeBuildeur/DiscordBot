# Work Stream 01: Data Connectivity

**Deliverable:** MCP server framework, data connectors, and Python execution environment that enable agents to query enterprise systems and run analysis.

---

## Vision Context

Agents are the autonomous workers of the platform. They execute approved plans by:

- **Retrieving data** from connected systems (databases, APIs)
- **Running analysis** and calculations (Python environment)
- **Producing outputs** (tables, charts, slides)

Data connectivity is the bridge between the agentic workforce and the organization's data. Without it, agents cannot perform the Plan → Revise → Build workflow.

**Architecture alignment:** Agents connect to enterprise systems through MCP servers. Capabilities include querying internal databases, retrieving operational metrics, accessing APIs, and pulling structured and unstructured data. Agents also use Python environments for data analysis, statistical calculations, data transformations, and modeling.

---

## Persona Mapping

| Persona | Role in Data Connectivity |
|---------|---------------------------|
| **Agents** | Primary consumers. They invoke MCP tools to query databases, call APIs, and execute Python. |
| **Analysts** | Indirect users. They benefit from agent outputs but do not configure connectors. |
| **Knowledge Admins** | Reference data sources in SOPs. May need to understand available connectors. |

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 00-preconditions met | All global preconditions satisfied | 00-preconditions.md sign-off |
| Data source inventory | At least 3 data sources identified (e.g., sales DB, CRM API, metrics warehouse) | Document in data catalog |
| Auth model defined | How agents authenticate to each source (service account, OAuth, API key) | Auth spec documented |
| Network access | Agents can reach target systems from execution environment | Connectivity test passed |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **MCP Server Framework** | Protocol implementation, tool registration, discovery | Agents discover and invoke data tools |
| **Database Connectors** | SQL/NoSQL adapters for internal DBs (PostgreSQL, Snowflake, etc.) | Query enterprise data |
| **API Connectors** | REST/GraphQL clients for internal APIs | Pull operational metrics |
| **Python Sandbox** | Isolated execution for analysis code | Run transforms, stats, models |
| **Data Schema Registry** | Metadata about available datasets (tables, columns, types) | Agents understand structure for planning |

---

## Detailed Architecture

### MCP (Model Context Protocol)

MCP standardizes how agents interact with external tools. The platform implements or integrates an MCP server that:

1. **Exposes tools** — `query_database`, `call_api`, `execute_python`, `get_schema`
2. **Handles requests** — Receives tool calls from the agent runtime, executes, returns results
3. **Manages auth** — Passes credentials securely to connectors (no credential leakage to LLM)

### Connector Types

| Connector | Use Case | Preview Support |
|-----------|----------|-----------------|
| **Database** | Sales data, operational metrics, data warehouse | `LIMIT N` or equivalent |
| **REST API** | CRM, ERP, external services | Pagination or sample |
| **GraphQL** | Flexible data fetching | Limit argument |

### Python Environment

Agents generate Python code for:

- **Data transformations** — Reshape, join, filter
- **Statistical calculations** — Mean, median, regression
- **Modeling** — Forecasting, clustering (within sandbox limits)

The sandbox must:

- Block file system write (except temp)
- Block outbound network (except allowed data sources)
- Enforce CPU/memory limits
- Timeout long-running code (e.g., 60s)

---

## Actions

### Phase 1: MCP Foundation

1. Implement MCP protocol server (or integrate existing implementation, e.g., `@modelcontextprotocol/sdk`).
2. Define tool interface: `query_database`, `call_api`, `execute_python`, `get_schema`.
3. Register tools with agent runtime. Ensure tool descriptions are clear for LLM tool selection.
4. Add authentication passthrough (service account, OAuth, etc.). Credentials stored in secure vault, never in prompts.

### Phase 2: Connectors

5. Build database connector for primary data warehouse (e.g., PostgreSQL, Snowflake, BigQuery).
6. Build API connector for key operational systems (REST with auth).
7. Implement row-limit parameter for preview mode. Connectors must accept `row_limit` and enforce it when in Preview stage (see 05-query-execution).
8. Add error handling and retry logic (exponential backoff for transient failures).

### Phase 3: Python Environment

9. Provision sandboxed Python environment (container or VM with resource limits).
10. Pre-install common libraries: pandas, numpy, scipy, matplotlib (for chart data).
11. Implement `execute_python` tool with timeout (e.g., 60s) and memory limit (e.g., 2GB).
12. Add output serialization: DataFrame → JSON/CSV for table interface consumption.

### Phase 4: Schema Registry

13. Create schema registry (DB or config) for datasets. Store: table name, columns, types, sample values.
14. Populate with table/column metadata for primary sources. Keep in sync with actual schema.
15. Expose schema via MCP tool `get_schema` for agent discovery during Plan stage.

---

## Example Tool Invocations

**Query database (Preview mode):**
```json
{
  "tool": "query_database",
  "params": {
    "data_source": "sales_warehouse",
    "query": "SELECT region, SUM(revenue) FROM sales GROUP BY region",
    "row_limit": 1000
  }
}
```

**Execute Python:**
```json
{
  "tool": "execute_python",
  "params": {
    "code": "import pandas as pd; df = pd.DataFrame(data); df['growth'] = df['revenue'].pct_change(); df.to_json()"
  }
}
```

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **03-agent-core** | Agent invokes MCP tools during Build stage |
| **05-query-execution** | Connectors receive `row_limit` in Preview, omit in Build |
| **02-knowledge-base** | SOPs reference data sources by name (from schema registry) |
| **07-database-backend** | DataSource config stored in DB; schema registry may use same storage |

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **MCP compliance** | Server responds to standard MCP requests | Fix protocol implementation |
| **Auth isolation** | Each connector uses least-privilege credentials | Do not use broad admin accounts |
| **Row limits** | Preview queries enforce hard row limit (e.g., 1000) | Reject queries without limit in preview |
| **Python safety** | Sandbox blocks file system, network (except allowed) | Audit and restrict capabilities |
| **Timeout** | All connector calls have timeout (e.g., 60s) | Prevent runaway queries |
| **Schema accuracy** | Registry reflects actual DB structure | Validate against live schema; add sync job |

---

## Deliverables

- [ ] MCP server with registered data tools
- [ ] At least 2 working connectors (DB + API)
- [ ] Python sandbox with execute_python tool
- [ ] Schema registry with 3+ datasets
- [ ] Documentation for adding new connectors
