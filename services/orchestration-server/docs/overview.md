# Orchestration server — architecture overview

This document summarizes how `services/orchestration-server/` is structured: HTTP API, orchestration engine, file-backed sessions, prompts, OpenAI integration, and optional MCP-backed **books knowledge** on new sessions (orchestrator-owned; MCP layer is transport + discovery only).

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
        BK[BooksKnowledgeForNewSession]
    end

    subgraph Integrations["Integrations"]
        OAI[OpenAIOrchestratorClient]
        OAIAPI[(OpenAI API)]
    end

    subgraph MCP["MCP (optional)"]
        MR[McpRegistryRuntime]
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
    OE -.-> BK
    BK --> MR
    BK --> BMCP
    MR --> REG
    MR -.-> BMCP
    PM --> PROMPTS
    FS --> DATA
```

## Startup (lifespan)

On startup, unless a test injects a pre-built `OrchestratorEngine`, the app loads the MCP registry, discovers each enabled server (stdio handshake, tool/resource lists), then constructs `BooksKnowledgeForNewSession` and wires it into `OrchestratorEngine` as `pre_generation_hook` (runs after the first user turn is saved, before the state-check LLM call).

```mermaid
sequenceDiagram
    participant App as FastAPI lifespan
    participant Reg as mcp-registry.json
    participant Disc as discover_registry
    participant RT as McpRegistryRuntime
    participant BK as BooksKnowledgeForNewSession
    participant Eng as OrchestratorEngine

    App->>Reg: read paths / cwd
    App->>Disc: discover MCP servers
    Disc->>Disc: stdio + initialize + list_tools / list_resources
    Disc-->>RT: cached discovery
    App->>BK: new(store, runtime)
    App->>Eng: new(..., pre_generation_hook=BK)
```

## New session flow (with books knowledge)

For `POST /orchestrator/sessions`, the engine persists the initial user turn, may run the books hook (silent `knowledge` turn + step artifact), then runs state check and generation (follow-up, plan, or refinement) with prompts that include **organizational knowledge** when present.

```mermaid
sequenceDiagram
    participant API as POST /sessions
    participant Eng as OrchestratorEngine
    participant FS as FileBackedSessionStore
    participant BK as BooksKnowledgeForNewSession
    participant MCP as books-mcp
    participant OAI as OpenAI

    API->>Eng: start_session_streaming
    Eng->>FS: create_session + user-message step
    Eng->>BK: __call__(session) [if tools available]
    BK->>MCP: find_books + get_book (stdio)
    MCP-->>BK: book bodies
    BK->>FS: append knowledge step + turn (kind=knowledge)
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
| `backend/orchestrator/tools/books_knowledge.py` | Books MCP call pattern + session updates for new sessions |
| `backend/mcp/runtime.py` | Registry discovery |
| `backend/mcp/stdio_client.py` | Shared MCP STDIO session helper (transport) |
| `config/mcp-registry.json` | Committed MCP launch commands (e.g. `books-mcp`) |
