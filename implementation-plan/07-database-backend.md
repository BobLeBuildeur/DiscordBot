# Work Stream 07: Database & Backend

**Deliverable:** Persistence layer for plans, projects, Books, execution state, and user data.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 00-preconditions | Infrastructure and security defined | Preconditions sign-off |
| Data model draft | Entity relationships sketched | ER diagram or schema draft |
| DB technology chosen | PostgreSQL, MongoDB, or equivalent | Technology selected |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **Schema Design** | Tables/collections for core entities | Structured storage |
| **Projects & Plans** | User projects, plans, revisions | Traceability |
| **Execution State** | Runs, steps, outputs, status | Resumption and audit |
| **Books Storage** | Knowledge and SOP storage | Part of 02-knowledge-base |
| **API Layer** | REST or GraphQL for frontend | Decouple UI from DB |
| **Migrations** | Schema versioning and migration | Safe evolution |

---

## Actions

### Phase 1: Schema Design

1. Define entities: User, Project, Plan, PlanRevision, ExecutionRun, ExecutionStep, Book, DataSource.
2. Design schema with indexes for common queries (e.g., project_id, run_id).
3. Add audit fields: created_at, updated_at, created_by.
4. Document schema in migration files or schema-as-code.

### Phase 2: Core Tables

5. Implement Projects table: id, name, user_id, created_at.
6. Implement Plans table: id, project_id, content (JSON), status, version.
7. Implement PlanRevisions table: id, plan_id, diff or full content, created_at.
8. Implement ExecutionRuns table: id, plan_id, status, started_at, completed_at, outputs.
9. Implement ExecutionSteps table: id, run_id, step_index, tool_calls, results, status.

### Phase 3: Books & Data Sources

10. Implement Books table (or integrate with 02-knowledge-base): id, name, type, content, version.
11. Implement DataSources table: id, name, connector_type, config (encrypted), schema_ref.
12. Add DataSource-to-Project or org-level association.

### Phase 4: API Layer

13. Implement CRUD endpoints for Projects, Plans, ExecutionRuns.
14. Add endpoints for plan approval, execution start, status poll.
15. Implement authentication and authorization (user can only access own projects).
16. Add pagination and filtering for list endpoints.

### Phase 5: Migrations & Backup

17. Set up migration tool (e.g., Alembic, Flyway).
18. Create initial migration from schema.
19. Define backup and recovery procedure.
20. Document connection pooling and performance tuning.

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Referential integrity** | Foreign keys enforced | Fix schema |
| **Sensitive data** | Credentials and secrets encrypted at rest | Audit encryption |
| **Index coverage** | No full table scans on hot paths | Add indexes |
| **API auth** | All endpoints require authentication | Block unauthenticated access |
| **Rate limiting** | API has rate limits | Prevent abuse |
| **Migration rollback** | Migrations are reversible | Test rollback |

---

## Deliverables

- [ ] Schema for Projects, Plans, Revisions, Runs, Steps
- [ ] Books and DataSources storage
- [ ] REST or GraphQL API for core entities
- [ ] Authentication and authorization
- [ ] Migration framework
- [ ] Backup procedure documented
