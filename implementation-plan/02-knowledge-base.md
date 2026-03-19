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

## Book Types

### Knowledge Books

Domain knowledge used by agents to reason about problems.

| Content Type | Examples |
|--------------|----------|
| Metric definitions | Revenue, ARR, churn rate, CAC |
| Industry benchmarks | Typical conversion rates, retention by segment |
| Business concepts | What constitutes a qualified lead, SLA definitions |
| Data dictionaries | Column meanings, valid values, relationships |

### SOP (Standard Operating Procedure) Books

Step-by-step instructions for executing common business processes.

| Content Type | Examples |
|--------------|----------|
| Report generation | How to generate a monthly sales report |
| Analysis workflows | How to analyze customer churn |
| Review processes | How to prepare a quarterly financial review |

Agents can combine multiple Books to perform complex workflows (e.g., Sales Report SOP + Metric Definitions Knowledge + Data Dictionary).

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

## Detailed Book Schema

### Knowledge Book Structure

```yaml
id: string
name: string
type: knowledge
version: number
content:
  sections:
    - name: "Metric Definitions"
      items:
        - term: "ARR"
          definition: "Annual Recurring Revenue. Sum of..."
        - term: "Churn Rate"
          definition: "Percentage of customers lost..."
    - name: "Data Dictionary"
      items:
        - table: "sales"
          column: "revenue"
          description: "Total deal value in USD"
metadata:
  tags: [sales, finance, metrics]
  data_sources: [sales_warehouse]
```

### SOP Book Structure

```yaml
id: string
name: string
type: sop
version: number
content:
  steps:
    - index: 1
      action: "Retrieve sales data by region"
      data_source: sales_warehouse
      inputs: []
      outputs: [sales_by_region]
    - index: 2
      action: "Calculate YoY growth"
      data_source: null
      inputs: [sales_by_region]
      outputs: [growth_analysis]
    - index: 3
      action: "Generate summary table"
      inputs: [growth_analysis]
      outputs: [final_table]
  required_books: [metric_definitions, data_dictionary]
metadata:
  tags: [sales, reporting]
```

---

## Actions

### Phase 1: Book Model

1. Define Book schema: id, name, type (knowledge | sop), content (JSON), metadata, version.
2. Implement storage (DB or file-based) for Books. Integrate with 07-database-backend.
3. Create CRUD API for Book management. Knowledge Admin UI will consume this.
4. Add type-specific validation: SOP must have ordered steps; Knowledge must have structured sections.

### Phase 2: Knowledge Books

5. Create template for Knowledge Books (sections: definitions, benchmarks, concepts, data dictionary).
6. Implement ingestion from markdown or structured format (YAML/JSON).
7. Build search/retrieval for agents: embedding-based (semantic) or keyword. Agent calls `get_books_for_task(task_description)`.
8. Populate 3+ initial Knowledge Books (e.g., metric definitions, data dictionary, industry benchmarks).

### Phase 3: SOP Books

9. Create template for SOP Books (steps, inputs, outputs, data sources, required_books).
10. Implement step validation: each step has inputs, outputs, and data source (where applicable).
11. Populate 2+ initial SOPs (e.g., monthly sales report, churn analysis).
12. Link SOPs to required Books and data sources. Validate references exist.

### Phase 4: Composition & Governance

13. Implement agent API: `get_books_for_task(task_description)`. Return relevant Knowledge + SOP Books.
14. Add versioning: immutable versions on edit. Past versions cannot be modified.
15. Define approval workflow for new/updated Books (optional): draft → review → published.
16. Create Knowledge Admin UI for creating and editing Books. Basic CRUD + preview.

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
| **SOP completeness** | Each step has inputs, outputs, and data source (where applicable) | Block publish until complete |
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
