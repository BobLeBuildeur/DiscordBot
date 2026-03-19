# Work Stream 07: Database & Backend

**Deliverable:** Persistence layer for plans, projects, Books, execution state, and user data.

---

## Vision Context

The platform requires a robust persistence layer to support:

- **Analysts** creating projects, storing plans, and reviewing execution history
- **Agents** having resumable execution and audit trails
- **Knowledge Admins** maintaining Books with versioning
- **System** tracking data sources, query metadata, and artifacts

The database is the backbone that enables the Plan → Revise → Build workflow to be traceable, resumable, and auditable.

---

## Persona Mapping

| Persona | Role in Database & Backend |
|---------|----------------------------|
| **Analysts** | Create projects, store plans, view execution history. Consume API for table interface. |
| **Agents** | Execution state persisted for resumption. Plan and run metadata stored. |
| **Knowledge Admins** | Books CRUD. Version history. |
| **System** | DataSources config, schema registry, query logs. |

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

## Entity Relationship Overview

```
User
  └── Project (1:N)
        └── Plan (1:N)
              ├── PlanRevision (1:N)
              └── ExecutionRun (1:N)
                    └── ExecutionStep (1:N)

Book (org-level)
  └── BookVersion (1:N)

DataSource (org or project-level)
```

---

## Detailed Schema

### User

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | string | Login identifier |
| name | string | Display name |
| created_at | timestamp | Audit |
| updated_at | timestamp | Audit |

### Project

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to User |
| name | string | Project name |
| created_at | timestamp | Audit |
| updated_at | timestamp | Audit |

### Plan

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| project_id | UUID | FK to Project |
| content | JSONB | Plan structure (steps, data_sources, etc.) |
| status | enum | draft, approved, executed |
| version | int | Increment on revision |
| created_at | timestamp | Audit |
| updated_at | timestamp | Audit |

### PlanRevision

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| plan_id | UUID | FK to Plan |
| content | JSONB | Full plan or diff |
| created_at | timestamp | Audit |
| created_by | UUID | FK to User (optional) |

### ExecutionRun

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| plan_id | UUID | FK to Plan |
| status | enum | pending, running, completed, failed |
| started_at | timestamp | When execution began |
| completed_at | timestamp | When execution ended |
| outputs | JSONB | Tables, chart specs, slide refs |
| error_message | text | If failed |

### ExecutionStep

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| run_id | UUID | FK to ExecutionRun |
| step_index | int | Order in plan |
| tool_calls | JSONB | Tool name, params |
| results | JSONB | Tool outputs |
| status | enum | pending, running, completed, failed |

### Book

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | string | Book name |
| type | enum | knowledge, sop |
| content | JSONB | Book content |
| version | int | Current version |
| created_at | timestamp | Audit |
| updated_at | timestamp | Audit |

### DataSource

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | string | Display name |
| connector_type | string | postgres, rest, etc. |
| config | encrypted | Connection details |
| schema_ref | string | Reference to schema registry |

---

## API Endpoints (REST)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /projects | List user's projects |
| POST | /projects | Create project |
| GET | /projects/:id | Get project with plans |
| GET | /projects/:id/plans | List plans |
| POST | /projects/:id/plans | Create plan |
| PATCH | /plans/:id | Update plan (revise) |
| POST | /plans/:id/approve | Approve plan |
| POST | /plans/:id/execute | Start execution |
| GET | /runs/:id | Get run status and outputs |
| GET | /books | List books (Knowledge Admin) |
| POST | /books | Create book |
| PATCH | /books/:id | Update book |

---

## Actions

### Phase 1: Schema Design

1. Define entities: User, Project, Plan, PlanRevision, ExecutionRun, ExecutionStep, Book, DataSource.
2. Design schema with indexes: project_id, plan_id, run_id, user_id.
3. Add audit fields: created_at, updated_at, created_by.
4. Document schema in migration files or schema-as-code.

### Phase 2: Core Tables

5. Implement Projects table.
6. Implement Plans table with content (JSONB).
7. Implement PlanRevisions table.
8. Implement ExecutionRuns table with outputs (JSONB).
9. Implement ExecutionSteps table.

### Phase 3: Books & Data Sources

10. Implement Books table (or integrate with 02-knowledge-base).
11. Implement DataSources table with encrypted config.
12. Add DataSource-to-Project or org-level association.

### Phase 4: API Layer

13. Implement CRUD endpoints for Projects, Plans, ExecutionRuns.
14. Add endpoints for plan approval, execution start, status poll.
15. Implement authentication (JWT, OAuth) and authorization (user can only access own projects).
16. Add pagination and filtering for list endpoints.

### Phase 5: Migrations & Backup

17. Set up migration tool (e.g., Alembic, Flyway).
18. Create initial migration from schema.
19. Define backup and recovery procedure.
20. Document connection pooling and performance tuning.

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **01-data-connectivity** | DataSource config stored; schema registry may use same DB |
| **02-knowledge-base** | Books table; CRUD API |
| **03-agent-core** | Persist plans, revisions, runs, steps |
| **04-table-interface** | API for plans, runs, outputs |
| **05-query-execution** | Store query metadata (optional) |
| **06-slide-generation** | Store slide artifacts (file ref or blob) |

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
