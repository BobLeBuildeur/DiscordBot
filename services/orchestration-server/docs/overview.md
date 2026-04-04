# Orchestration server — architecture overview

This document summarizes how `services/orchestration-server/` is structured: HTTP API, orchestration engine, file-backed sessions, prompts, OpenAI integration, and optional MCP-based knowledge enrichment.

## Component diagram

```mermaid
flowchart TB
    subgraph Client["Clients"]
        UI[Web UI / Analyst tools]
    end

    subgraph FastAPI["FastAPI app"]
        MW[CORS middleware]
        R["/orchestrator router"]
    end

    subgraph Engine["Orchestration core"]
        OE[OrchestratorEngine]
        PM[PromptManager]
        FS[FileBackedSessionStore]
    end

    subgraph Integrations["Integrations"]
        OAI[OpenAIOrchestratorClient]
        OAIAPI[(OpenAI API)]
    end

    subgraph MCP["MCP (optional)"]
        MR[McpRegistryRuntime]
        KE[KnowledgeEnrichmentService]
        REG["config/mcp-registry.json"]
        BMCP["books-mcp (STDIO)"]
    end

    subgraph Artifacts["On disk"]
        DATA[(data/orchestrator/)]
        PROMPTS[(prompts/orchestrator/*.md)]
    end

    UI --> MW --> R
    R --> OE
    OE --> PM
    OE --> FS
    OE --> OAI
    OAI --> OAIAPI
    OE -.-> KE
    KE --> MR
    KE --> BMCP
    MR --> REG
    MR -.-> BMCP
    PM --> PROMPTS
    FS --> DATA
```

## Startup (lifespan)

On startup, unless a test injects a pre-built `OrchestratorEngine`, the app loads the MCP registry, discovers each enabled server (stdio handshake, tool/resource lists), then constructs `KnowledgeEnrichmentService` and wires it into `OrchestratorEngine` as `session_enrichment`.

```mermaid
sequenceDiagram
    participant App as FastAPI lifespan
    participant Reg as mcp-registry.json
    participant Disc as discover_registry
    participant RT as McpRegistryRuntime
    participant KE as KnowledgeEnrichmentService
    participant Eng as OrchestratorEngine

    App->>Reg: read paths / cwd
    App->>Disc: discover MCP servers
    Disc->>Disc: stdio + initialize + list_tools / list_resources
    Disc-->>RT: cached discovery
    App->>KE: new(store, runtime)
    App->>Eng: new(..., session_enrichment=KE.run)
```

## New session flow (with enrichment)

For `POST /orchestrator/sessions`, the engine persists the initial user turn, may run enrichment (silent `knowledge` turn + step artifact), then runs state check and generation (follow-up, plan, or refinement) with prompts that include **organizational knowledge** when present.

```mermaid
sequenceDiagram
    participant API as POST /sessions
    participant Eng as OrchestratorEngine
    participant FS as FileBackedSessionStore
    participant KE as KnowledgeEnrichmentService
    participant MCP as books-mcp
    participant OAI as OpenAI

    API->>Eng: start_session_streaming
    Eng->>FS: create_session + user-message step
    Eng->>KE: run(session) [if MCP available]
    KE->>MCP: find_books + get_book (stdio)
    MCP-->>KE: book bodies
    KE->>FS: append knowledge step + turn (kind=knowledge)
    Eng->>OAI: state check
    Eng->>OAI: stream generation (plan / follow-up / refine)
    Eng->>FS: assistant steps + session.json
```

## API surface

| Area | Responsibility |
|------|------------------|
| `GET /orchestrator/sessions/{id}` | Returns session JSON; **strips** `conversation_history` entries with `kind == "knowledge"` from the client-facing payload. |
| `POST /orchestrator/sessions` | SSE stream: session id, chunks, final state + metadata. |
| `POST /orchestrator/sessions/{id}/messages` | Continues the session with SSE. |

## Related paths

| Path | Role |
|------|------|
| `backend/app.py` | App factory, lifespan, MCP wiring |
| `backend/api/orchestrator.py` | Routes, client-safe session serialization |
| `backend/orchestrator/engine.py` | Session lifecycle and LLM turns |
| `backend/orchestrator/prompts.py` | Builds prompts; organizational knowledge block |
| `backend/orchestrator/store.py` | JSON + step artifacts under `data_root` |
| `backend/mcp/runtime.py` | Registry discovery |
| `backend/mcp/enrichment.py` | Books MCP calls for new sessions |
| `config/mcp-registry.json` | Committed MCP launch commands (e.g. `books-mcp`) |
