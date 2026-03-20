# orchestration-web

Analyst-facing web UI for the orchestration server. Built with **SvelteKit** and **Svelte 5 runes**.

## Quick start

```bash
# From services/orchestration-web/
cp .env.example .env    # adjust if needed
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` by default.

## Environment variables

| Variable                        | Purpose                                                                                  | Default (dev) |
|---------------------------------|------------------------------------------------------------------------------------------|---------------|
| `PUBLIC_ORCHESTRATION_API_URL`  | Base URL for the orchestration API. Leave empty during local dev to use the Vite proxy.   | *(empty)*     |

### Vite proxy (local development)

When `PUBLIC_ORCHESTRATION_API_URL` is empty, requests to `/orchestrator/*` are proxied to `http://localhost:8000` by Vite (see `vite.config.ts`). Make sure the orchestration server is running on that port.

## Routes

| Path                      | Purpose                                  |
|---------------------------|------------------------------------------|
| `/`                       | New session — submit a problem statement |
| `/session/[sessionId]`    | Active session — continue conversation   |

## API contract

The UI talks to two endpoints on the orchestration server via **SSE** (Server-Sent Events):

| Action           | Endpoint                                                | Request body                        |
|------------------|---------------------------------------------------------|-------------------------------------|
| Start session    | `POST /orchestrator/sessions`                           | `{ "problem_statement": "..." }`    |
| Follow-up        | `POST /orchestrator/sessions/{session_id}/messages`     | `{ "message": "..." }`             |

Both endpoints return an SSE stream with events:

1. **`session`** — `{ "session_id": "..." }` (identifies the session)
2. **`chunk`** — `{ "content": "..." }` (streaming markdown)
3. **`final`** — full payload including `assistant_message`, `state_check`, etc.

> **Out of scope:** `GET /orchestrator/sessions/{session_id}` is not used. If you refresh a session page, the chat history starts empty but the session ID is preserved for new messages.

## Architecture

- **History** — scrollable list of conversation turns, auto-scrolls to bottom
- **HistoryItem** — single turn; agent messages render Markdown → sanitized HTML; analyst messages render as plain text
- **MessageInput** — textarea + send button with Enter-to-send

Agent Markdown is compiled with `marked` and sanitized with `DOMPurify` before injection via `{@html}`.

## Scripts

| Command             | Description                  |
|---------------------|------------------------------|
| `npm run dev`       | Start dev server             |
| `npm run build`     | Production build             |
| `npm run preview`   | Preview production build     |
| `npm run check`     | TypeScript + Svelte checks   |
