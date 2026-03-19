# Work Stream 02: Knowledge Base (Books)

**Deliverable:** Book system—reusable containers of domain knowledge and SOPs that agents combine when executing tasks.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 01-data-connectivity | MCP framework and connectors available | Agents can query data |
| Knowledge Admin assigned | Person(s) responsible for maintaining Books | Role confirmed |
| Initial content identified | At least 5 knowledge items and 2 SOPs to encode | Content list documented |

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

## Actions

### Phase 1: Book Model

1. Define Book schema: id, name, type (knowledge | sop), content, metadata, version.
2. Implement storage (DB or file-based) for Books.
3. Create CRUD API for Book management.
4. Add type-specific validation (e.g., SOP must have ordered steps).

### Phase 2: Knowledge Books

5. Create template for Knowledge Books (sections: definitions, benchmarks, concepts).
6. Implement ingestion from markdown or structured format.
7. Build search/retrieval for agents (embedding-based or keyword).
8. Populate 3+ initial Knowledge Books (e.g., metric definitions, data dictionary).

### Phase 3: SOP Books

9. Create template for SOP Books (steps, inputs, outputs, data sources).
10. Implement step validation and dependency checks.
11. Populate 2+ initial SOPs (e.g., monthly sales report, churn analysis).
12. Link SOPs to required Books and data sources.

### Phase 4: Composition & Governance

13. Implement agent API: `get_books_for_task(task_description)`.
14. Add versioning (immutable versions on edit).
15. Define approval workflow for new/updated Books (optional).
16. Create Knowledge Admin UI for creating and editing Books.

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Book uniqueness** | No duplicate Book names within type | Reject or merge |
| **SOP completeness** | Each step has inputs, outputs, and data source | Block publish until complete |
| **Agent retrieval** | Agents receive relevant Books for test tasks | Tune retrieval or add metadata |
| **Version immutability** | Past versions cannot be edited | Enforce in storage layer |
| **Content quality** | SME review for initial Books | Do not auto-publish without review |

---

## Deliverables

- [ ] Book storage and CRUD API
- [ ] 3+ Knowledge Books populated
- [ ] 2+ SOP Books populated
- [ ] Agent retrieval integration
- [ ] Knowledge Admin UI (basic)
