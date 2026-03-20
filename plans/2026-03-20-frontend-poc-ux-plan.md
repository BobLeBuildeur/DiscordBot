# Frontend PoC — UX, behavior & technical architecture

## Goal

Ship the smallest possible analyst-facing UI that proves the orchestration flow end-to-end: open app → describe the problem → see server feedback in a scrollable history → continue the conversation on the same session. Success is not polish or feature breadth; it is that an Analyst can complete the journey without confusion and the UI behavior matches the stated states and API contract.

**Won’t do:** Rich layout systems, auth flows, configuration panels unrelated to the chat loop, or visual design beyond what default HTML plus minimal local CSS needs to distinguish roles and keep the history usable. **Design systems** and **end-to-end testing frameworks** are explicitly out of scope (see Technical architecture).

---

## Preconditions

- **Monorepo:** A new self-contained service lives under **`services/orchestration-web/`** (name may be adjusted, but the UI remains a sibling service to `services/orchestration-server/`, not embedded inside it).
- **Orchestration server** is running and reachable from the browser for the PoC (base URL via public env, e.g. `PUBLIC_ORCHESTRATION_API_URL`), with **CORS** allowed for the web app origin when dev/proxy differs.
- **API contract:** The UI uses the orchestration HTTP API only—**`POST /orchestrator/sessions`** to start a session with the initial problem, and **`POST /orchestrator/sessions/{session_id}/messages`** for follow-ups. **`GET /orchestrator/sessions/{session_id}`** exists on the server but **must not** be used in this PoC to load prior transcript (see out of scope below).
- **Agent payloads:** Server responses that appear in the history (the **agent** role) are **Markdown**. The client still applies the agreed strategy to extract embedded JSON (e.g. `session_id`) from the first response when needed; the string shown as the agent message body is then rendered as **HTML** inside **`HistoryItem`** (see implementation steps).
- The first response shape is understood well enough to parse embedded JSON from the response text and read `session_id` so the client can navigate to the session URL and transition to “session active.”
- **Tooling:** Node.js version compatible with the chosen SvelteKit release; `npm`/`pnpm`/`bun` per service lockfile once the app is scaffolded.

**Won’t do:** Assume production hosting, SSO, or backend changes beyond what the PoC contract already defines.

---

## Used Tools

- **SvelteKit** as the application shell (routing, build, dev server).
- **Svelte 5 with runes** (`$state`, `$derived`, `$props`, `$effect` as needed) for session-scoped UI state: message list, input value, in-flight requests, and parsed `session_id`.
- **`fetch`** from the client (or small `src/lib` helpers) toward the orchestration server base URL—no extra API layer in another service.
- **Markdown → HTML** for agent turns: a **small** Markdown compiler (e.g. `marked`, `markdown-it`, or similar lightweight choice) plus a **sanitization** pass before injecting HTML into the DOM (e.g. DOMPurify or an isomorphic equivalent), since Svelte `{@html …}` is unsafe without it.
- **Default HTML controls** inside Svelte components (`<textarea>`, `<button>`, semantic wrappers); **minimal component-local or global CSS** only where defaults are insufficient.

**Won’t do:** Adopt a design system, component library, or E2E runner (Playwright/Cypress/etc.) for this PoC.

---

## Technical architecture

### Placement in the monorepo

- The front end is a **new service**: **`services/orchestration-web/`** containing its own `package.json`, SvelteKit config, `src/`, and service-local README or run instructions.
- It **depends on the orchestration server only at runtime** (HTTP): no direct Python imports or shared code is required for the PoC unless the repo later introduces an intentional shared package.

### Integration with the orchestration server

| Action | HTTP | Notes |
|--------|------|--------|
| Start session + initial problem | `POST {base}/orchestrator/sessions` | Body matches server contract; response body includes **Markdown** for display; response text parsed for JSON / `session_id` per agreed rules. |
| Send follow-up | `POST {base}/orchestrator/sessions/{session_id}/messages` | Same: agent-visible content is **Markdown** rendered to HTML in **`HistoryItem`**. |
| Load existing transcript | `GET …/sessions/{session_id}` | **Out of scope** for this PoC—do not implement hydration from this endpoint. |

- **Base URL** is configured for the browser (e.g. SvelteKit `PUBLIC_ORCHESTRATION_API_URL`). Local dev may use a Vite proxy to the orchestration server to simplify CORS during development; that is an implementation detail inside the web service.

### Routing and session id in the URL

- **Pre-session:** A route **without** a session id in the path (e.g. **`/`**) shows empty history and the input; the analyst is **ready to start a new session**.
- **After a successful start-session response** and once `session_id` is known: the app **navigates** (e.g. `goto`) to a route that **includes the session id in the path**, such as **`/session/[sessionId]`** (exact path convention is an implementation choice as long as the id is a path segment, not a secret query hack).
- **Follow-up messages** use the **`sessionId` from `$page.params`** (and the same value for API calls) so the URL reflects the active session and can be bookmarked—even though **restoring chat content from the server is out of scope**.
- **Cold load** of `/session/[sessionId]` (e.g. refresh or pasted link): the PoC **does not** fetch historical messages; the history may start empty while the id in the URL still identifies the session for **new** `POST …/messages` calls. (Document this limitation in the service README if it confuses testers.)

### Stack constraints

- **SvelteKit + Svelte 5 runes** are mandatory for new UI logic in this service.
- **Out of scope:** third-party **design systems**, headless UI kits used as a “platform,” and **E2E testing frameworks** (manual smoke only unless unit tests are added without E2E).

### Svelte component mapping

Every **named UI building block** in [Interface composition](#interface-composition-non-functional) is implemented as a **`.svelte` file** (not a plain function component in another framework). Suggested mapping:

| Design concept | Svelte module (under `src/lib/…` or colocated) | Responsibility |
|----------------|-----------------------------------------------|----------------|
| **History** (scrollable list container) | e.g. `History.svelte` | Renders an ordered list of items; owns scroll-to-bottom behavior for its container; receives the list of turns via props or parent runes. |
| **History item** | e.g. `HistoryItem.svelte` | **Props:** message body + **`role: 'agent' \| 'analyst'`**. For **`analyst`**, render body as **plain text** (escaped). For **`agent`**, convert **Markdown → HTML** (then **sanitize**) and render inside the component (e.g. Svelte `{@html}` into a single wrapper). Applies minimal styling per role. |
| **Input** (textarea + send) | e.g. `MessageInput.svelte` | Controlled value, submit action, optional disabled state while sending. |

- **Route files** (`+page.svelte`, optional `+layout.svelte`) **compose** these components; they may hold page-level rune state and `fetch` orchestration, but the **three design components above remain distinct Svelte components** rather than inlined duplicates.

---

## User experience overview

### States (what the Analyst should feel)

| State | What they see | What they can do |
|--------|----------------|------------------|
| **First open / ready to start session** | Empty or welcome history plus the input (textarea + send). | Enter the initial problem and send once. |
| **Session active** | History is a **sequence of history item components** (each turn is one item), newest at the bottom. | Send follow-up messages; input clears after send; view scrolls to latest. |

### Journey (numbered)

1. **First open:** Analyst lands on the app and immediately sees the **input** component (history may be empty or a single neutral placeholder—keep it minimal).
2. **Ready to start session:** Analyst types the **initial problem** and submits.
3. **Request:** Front end sends **one** request that starts a new session and includes the problem statement.
4. **First response:** Server reply (Markdown) is rendered as a new **history item** with role **agent** as **HTML**; client extracts JSON from the text, obtains **session id**, **updates the browser URL** to include that id (e.g. `/session/{sessionId}`), and state becomes **session active**.
5. **Ongoing:** For each further user message, client calls the **messages** endpoint for the current session (using the id from the URL); each analyst turn and each agent turn is a new **history item** appended at the **bottom** in order; after send and after new responses, the view **scrolls to the bottom**.

---

## Behavior-driven design (acceptance criteria)

### First open → ready to start session

**Given** the analyst first opens the app  
**Then** they are presented with the input component (textarea + send)  
**And** the application state is **ready to start a new session** (no `session_id` yet).

### First prompt → start session

**Given** the app is ready to start a session  
**When** the analyst provides the first prompt  
**Then** the app sends the problem statement to the API that **starts** a new session (not the follow-up messages route)  
**And** the problem statement appears in the history as a **history item** with role **analyst**.

### First response → session active

**Given** the app is ready to start a session  
**When** the first response is received  
**Then** the app extracts JSON content from the response text (per agreed parsing rules)  
**And** the app stores the **session id** for subsequent calls (and reads it from the URL on the session route)  
**And** the **session id is appended to the URL** (path segment) via client-side navigation  
**And** the state moves to **session active**  
**And** the response appears in the history as a **history item** with role **agent**, with **Markdown converted to HTML** (and sanitized) for display.

### Session active — user message

**Given** the session is active  
**When** the analyst sends a new input  
**Then** the message is sent to the **messages** endpoint for the current session  
**And** the user’s text is appended at the **bottom** of the history as a **history item** with role **analyst**  
**And** the input is **cleared**  
**And** the page (history region) **scrolls to the bottom**.

### Session active — assistant message

**Given** the session is active  
**When** a response is received  
**Then** the response Markdown is appended at the **bottom** of the history as a **history item** with role **agent**, **rendered as HTML** in that item  
**And** the page **scrolls to the bottom**.

---

## Interface composition (non-functional)

- **Implementation rule:** Each of the following conceptual components is a **Svelte component** (`.svelte`); see [Svelte component mapping](#svelte-component-mapping) for file-level mapping.
- **Two main regions:** (1) **History** — a vertical sequence of **history item** components in chronological order; (2) **Input** — textbox + send button.
- **History item component:** Each message in the thread is one **history item**. Items are rendered **in sequence** (document order = conversation order). A **single property** on each item defines the speaker for both semantics and styling: **`agent`** (orchestrator / server-side response) or **`analyst`** (human input). Implementation may use a prop name such as `role`, `speaker`, or `kind` as long as the allowed values are exactly **`agent`** and **`analyst`**. **Agent** bodies are **Markdown** parsed to HTML **inside `HistoryItem`**; **analyst** bodies stay **plain text** (no Markdown interpretation).
- **History container:** New items are always appended **at the bottom** of the list so the natural reading order matches turn order.
- **Input:** Single textbox and send button; disable send while a request is in flight if that avoids duplicate submissions (optional guardrail—only if default UX suffers without it).
- **Visual distinction:** **Agent** vs **analyst** items must be **visually distinct** using the **minimum** custom CSS, driven by the item’s role property (e.g. `data-role="agent"` / `data-role="analyst"`, or class names derived from the same enum)—labels, borders, or light background tints are enough; no full theme.
- **Styling:** Default HTML appearance everywhere else; no typography or color exploration beyond clarity and the two roles. Add **only** scoped rules if needed so Markdown output (e.g. `pre`, `code`, lists) remains readable inside the agent **`HistoryItem`** wrapper.

---

## Implementation steps (UX-aligned)

1. **Scaffold service:** Create **`services/orchestration-web/`** with SvelteKit, Svelte 5, and runes enabled per project template. Add public env for orchestration base URL and document dev proxy/CORS if used.  
   *Won’t do:* place the app under `services/orchestration-server/` or scatter UI files at repo root.

2. **Routes:** Implement **`/`** (or equivalent) for “no session id yet” and **`/session/[sessionId]`** (or equivalent) for the active session; share the same **History**, **HistoryItem**, and **MessageInput** components on both if the layout is identical, or keep composition DRY via a small layout wrapper component.  
   *Won’t do:* hydrate transcript from **`GET /orchestrator/sessions/{session_id}`**.

3. **Shell layout:** Compose **History** + **MessageInput** in `+page.svelte` (and session page) with default block layout and a scrollable history region.  
   *Won’t do:* complex grid/flex unless needed for scroll containment.

4. **State (runes):** Use `$state` / `$derived` for message list, draft text, pending flags, and derived `sessionId` from `$page.params` on the session route.  
   *Won’t do:* legacy Svelte stores for new code unless the template requires them for adapters.

5. **First-send path (pre-session route):** On first submit, append a **history item** with role **`analyst`**, `POST /orchestrator/sessions`, then on success parse response, append **`agent`** item, **`goto`** `/session/{sessionId}` so the id appears in the URL.  
   *Won’t do:* block the UI without feedback on slow networks.

6. **Follow-up path (session route):** On submit, `POST /orchestrator/sessions/{sessionId}/messages` using the param from the URL; append **`analyst`** then **`agent`** items; clear input; scroll history to bottom.  
   *Won’t do:* prepend messages or require manual scroll.

7. **History rendering:** **`HistoryItem.svelte`** per turn; **`History.svelte`** maps the list and handles scroll-to-bottom.  
   *Won’t do:* one monolithic transcript blob.

8. **Agent Markdown in `HistoryItem`:** Implement a single rendering path for **`role === 'agent'`**: run the body through **Markdown → HTML**, then **sanitize** the HTML string, then bind with **`{@html …}`** (or equivalent) inside a dedicated wrapper element in **`HistoryItem.svelte`** so lists, code fences, emphasis, etc. display correctly. For **`role === 'analyst'`**, render with normal text binding so user input is not interpreted as HTML/Markdown.  
   *Won’t do:* skip sanitization when using `{@html}`; run Markdown for analyst messages.

9. **Smoke validation:** Manual walkthrough against a running orchestration server; **no E2E framework** for this PoC. Optional **unit tests** for pure helpers (e.g. JSON extraction, sanitize + markdown pipeline) only if low-cost.  
   *Won’t do:* Playwright/Cypress (or similar) as a project dependency for this milestone.

---

## Guardrails

- **Monorepo boundary:** UI code and dependencies live under **`services/orchestration-web/`**; call **`services/orchestration-server/`** only via HTTP.
- **Size:** Few files, minimal dependencies; every addition must trace to a stated BDD or NFR; **no design-system or E2E** dependencies.
- **Contract:** Document `PUBLIC_ORCHESTRATION_API_URL`, `POST /orchestrator/sessions`, and `POST /orchestrator/sessions/{id}/messages` in the web service README; keep request/response shapes aligned with server tests.
- **Parsing:** Define one clear strategy for “JSON in text” (e.g. fenced block, last JSON object, regex)—same behavior on success and clear error on failure. After extraction, the **display string** passed to **`HistoryItem`** for the agent should still be valid **Markdown** (e.g. strip only the JSON block if the contract calls for separation).
- **Markdown safety:** Never inject unsanitized HTML from the server; **sanitize** after Markdown compilation and before `{@html}`.
- **URL:** After session start, **session id must appear in the path**; do not rely on hidden global state alone for the active id.
- **Out of scope reminder:** No **GET**-based **chat restore**, no **design system**, no **E2E testing framework**.
- **Accessibility (light touch):** Use labels associated with the textarea and a sensible button name so default focus/tab order remains usable.
- **Done means:** All Gherkin scenarios are demonstrable in the browser with Svelte components as specified, default-plus-minimal styling, **`agent` vs `analyst`** history items, **agent Markdown rendered as sanitized HTML in `HistoryItem`**, and URL updating after the first response.

---

## Appendix — traceability (quick matrix)

| Requirement | UX / technical artifact |
|-------------|-------------------------|
| First open shows input | Pre-session `+page.svelte` + **MessageInput** |
| First send → start session | `POST /orchestrator/sessions` |
| First response → JSON + session id + active | Parser + **HistoryItem** (`agent`) + `goto` session URL |
| Session id in URL | `/session/[sessionId]` (or chosen equivalent) |
| Follow-up → messages API | `POST /orchestrator/sessions/{id}/messages` with param from URL |
| Append + clear + scroll | **MessageInput** + **History** + **HistoryItem** (`analyst`) |
| Agent vs analyst styling | **HistoryItem** `role` prop + minimal CSS |
| Agent Markdown → HTML | **HistoryItem**: markdown lib + sanitize + `{@html}` |
| Analyst plain text | **HistoryItem**: text/escaped content, no Markdown |
| No transcript restore | Do not call `GET /orchestrator/sessions/{id}` for history |

This plan is intentionally narrow so implementation can stay small while still validating the concept with a realistic Analyst session, a dedicated **orchestration-web** service, and **SvelteKit + runes** aligned to the existing orchestration HTTP API.
