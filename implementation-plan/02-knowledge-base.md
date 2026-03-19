# Work Stream 02: Knowledge Base (Books)

**Deliverable:** Book system—reusable containers of domain knowledge and SOPs that agents combine when executing tasks.

---

## Vision Context

Books replace the traditional idea of isolated prompts or tools with **composable institutional knowledge** that agents use across projects. They encode organizational standards and expertise so that the agentic workforce operates consistently and correctly.

**Core philosophy:** By encoding expertise into reusable Books, organizations scale knowledge across teams and power a coordinated agentic workforce.

**Book characteristics:**

- Reusable across the organization
- Combinable by agents when executing tasks
- Encode organizational standards and expertise
- Can contain multiple types of content

---

## Persona Mapping

| Persona | Role in Knowledge Base |
|---------|-------------------------|
| **Knowledge Admins** | Create and maintain Books. Define SOPs and organizational standards. Encode domain expertise. Ensure consistency across agent workflows. |
| **Agents** | Consume Books during Plan and Build. Combine multiple Books for complex workflows. Use Knowledge for reasoning, SOPs for step-by-step execution. |
| **Analysts** | Benefit from consistent, standards-compliant outputs. May request new Books via Knowledge Admins. |

---

## Book Types (Extensible)

All Books share the same schema. The `type` property is **extensible**—new types can be added without schema changes. Agents and retrieval logic can use type for filtering and prioritization.

### Built-in Types

| Type | Purpose | Examples |
|------|---------|----------|
| **knowledge** | Domain knowledge for reasoning | Metric definitions, benchmarks, data dictionaries |
| **sop** | Step-by-step procedures | Report generation, analysis workflows, review processes |

### Extending Types

Organizations may define custom types (e.g., `playbook`, `template`, `checklist`). The schema does not restrict type values. Retrieval and agent behavior for custom types should be documented per deployment.

Agents can combine multiple Books of any type to perform complex workflows (e.g., Sales Report SOP + Metric Definitions + Data Dictionary).

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 01-data-connectivity | MCP framework and connectors available | Agents can query data referenced in SOPs |
| Knowledge Admin assigned | Person(s) responsible for maintaining Books | Role confirmed and staffed |
| Initial content identified | At least 5 knowledge items and 2 SOPs to encode | Content list documented with SMEs |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **Book Model** | Data structure for Books (metadata, content, type) | Consistent representation |
| **Knowledge Books** | Domain knowledge, metrics, benchmarks, data dictionaries | Agents reason with org context |
| **SOP Books** | Step-by-step procedures for common tasks | Standardize agent workflows |
| **Book Composition** | How agents combine multiple Books | Support complex workflows |
| **Versioning & Governance** | Edit history, approval workflow | Maintain quality and traceability |

---

## Unified Book Schema

All Books use the same schema. Content is always **markdown**. The `type` property is a string and is **extensible**.

```yaml
id: string
name: string
type: string          # Extensible: "knowledge", "sop", or custom (e.g., "playbook", "template")
version: number
content: string       # Markdown. Structure and conventions are type-specific but format is always markdown.
metadata:
  tags: string[]      # For retrieval and filtering
  data_sources: string[]  # Optional. Referenced data sources (e.g., sales_warehouse)
  # Additional metadata keys may be added per type or deployment
created_at: timestamp
updated_at: timestamp
```

### Example: Knowledge Book (type: knowledge)

```markdown
# Metric Definitions

## ARR
Annual Recurring Revenue. Sum of subscription revenue normalized to a yearly run rate.

## Churn Rate
Percentage of customers lost in a given period. Formula: (lost customers / start customers) × 100.

# Data Dictionary

## sales.revenue
Total deal value in USD. Excludes taxes and discounts.
```

### Example: SOP Book (type: sop)

```markdown
# Monthly Sales Report

## Step 1: Retrieve sales data by region
- **Data source:** sales_warehouse
- **Output:** sales_by_region

## Step 2: Calculate YoY growth
- **Input:** sales_by_region
- **Output:** growth_analysis

## Step 3: Generate summary table
- **Input:** growth_analysis
- **Output:** final_table
- **Required books:** metric_definitions, data_dictionary
```

Markdown allows rich formatting (headers, lists, tables, code blocks) while keeping a single, simple content format across all book types.

---

## Actions

### Phase 1: Book Model

1. Define unified Book schema: id, name, type (string, extensible), content (markdown string), metadata, version.
2. Implement storage (DB or file-based) for Books. Integrate with 07-database-backend.
3. Create CRUD API for Book management. Knowledge Admin UI will consume this.
4. Add validation: content must be valid markdown; type must be non-empty; metadata.tags optional.

### Phase 2: Content & Retrieval

5. Create markdown templates or conventions for built-in types (knowledge, sop). Document structure expectations per type.
6. Implement markdown ingestion and storage. Content stored as string; no parsing required for storage.
7. Build search/retrieval for agents: embedding-based (semantic) or keyword. Agent calls `get_books_for_task(task_description)`.
8. Populate 3+ initial Knowledge Books and 2+ SOP Books in markdown format.

### Phase 3: Type Extensibility

9. Document how to add custom book types. Type is a string; no enum restriction.
10. Implement type-aware retrieval (optional): filter or rank by type when relevant.
11. For SOP-type Books: document markdown conventions (e.g., "Step N:", "Data source:", "Required books:") for agent parsing.
12. Validate metadata.data_sources and required_books references when present in content (optional, via convention).

### Phase 4: Composition & Governance

13. Implement agent API: `get_books_for_task(task_description)`. Return relevant Books of any type.
14. Add versioning: immutable versions on edit. Past versions cannot be modified.
15. Define approval workflow for new/updated Books (optional): draft → review → published.
16. Create Knowledge Admin UI for creating and editing Books. Markdown editor with preview.

---

## Example: Agent Combining Books

**User task:** "Analyze sales performance for Q3"

**Agent retrieval:** Fetches:
- **SOP:** "Monthly Sales Report" (steps for data retrieval, aggregation, summary)
- **Knowledge:** "Metric Definitions" (revenue, growth, etc.)
- **Knowledge:** "Data Dictionary" (sales table schema)

**Agent execution:** Follows SOP steps, uses Metric Definitions for calculations, uses Data Dictionary to construct correct queries.

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **03-agent-core** | Agent retrieves Books at Plan stage; uses as context during Build |
| **01-data-connectivity** | SOPs reference data sources; schema registry informs data dictionary |
| **07-database-backend** | Books table; CRUD API |
| **04-table-interface** | (Future) Knowledge Admin UI for Book editing |

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Book uniqueness** | No duplicate Book names within type | Reject or merge |
| **Content format** | Content is valid markdown | Reject or sanitize |
| **Type extensibility** | Type accepts any non-empty string; built-in types documented | Do not restrict to enum |
| **Agent retrieval** | Agents receive relevant Books for test tasks (e.g., "sales report" → sales SOP) | Tune retrieval or add metadata/tags |
| **Version immutability** | Past versions cannot be edited | Enforce in storage layer |
| **Content quality** | SME review for initial Books | Do not auto-publish without review |

---

## Deliverables

- [ ] Book storage and CRUD API
- [ ] 3+ Knowledge Books populated
- [ ] 2+ SOP Books populated
- [ ] Agent retrieval integration (`get_books_for_task`)
- [ ] Knowledge Admin UI (basic)
