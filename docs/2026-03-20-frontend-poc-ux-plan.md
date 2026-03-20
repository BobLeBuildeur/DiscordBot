# Frontend PoC — UX & behavior plan

## Goal

Ship the smallest possible analyst-facing UI that proves the orchestration flow end-to-end: open app → describe the problem → see server feedback in a scrollable history → continue the conversation on the same session. Success is not polish or feature breadth; it is that an Analyst can complete the journey without confusion and the UI behavior matches the stated states and API contract.

**Won’t do:** Rich layout systems, auth flows, multiple pages, configuration panels, or visual design beyond what default HTML needs to distinguish roles and keep the history usable.

---

## Preconditions

- The orchestration HTTP API is reachable from the browser (base URL configurable, e.g. env or a single constant), including CORS if the UI is served from a different origin.
- Endpoints exist (or will exist) for: starting a session with an initial problem statement, and sending further messages for a session id returned by the first response.
- The first response shape is understood well enough to parse embedded JSON (e.g. from streamed or plain text) and read `session_id` (or equivalent) so the client can transition to “session active.”
- A minimal static hosting or dev-server story is defined (single HTML page or tiny bundled app) so Analysts can open the app in one step.

**Won’t do:** Assume production hosting, SSO, or backend changes beyond what the PoC contract already defines.

---

## Used Tools

- A minimal front-end surface: preferably a single page with default HTML semantics; add only the smallest amount of CSS/JS needed for state, parsing, `fetch`, and scroll behavior.
- Browser `fetch` (or equivalent) for `POST` to start session and `POST` to session messages.
- No design system requirement; native `<textarea>`, `<button>`, and block elements for the history.

**Won’t do:** Introduce a large framework or component library unless required solely to run the PoC in this repo—default is “as small as possible.”

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
4. **First response:** Server reply is rendered as a new **history item** with role **agent**; client extracts JSON from the text, persists **session id**, state becomes **session active**.
5. **Ongoing:** For each further user message, client calls the **messages** endpoint for the current session; each analyst turn and each agent turn is a new **history item** appended at the **bottom** in order; after send and after new responses, the view **scrolls to the bottom**.

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
**And** the app stores the **session id** for subsequent calls  
**And** the state moves to **session active**  
**And** the response (or a readable rendering of it) appears in the history as a **history item** with role **agent**.

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
**Then** the response text is appended at the **bottom** of the history as a **history item** with role **agent**  
**And** the page **scrolls to the bottom**.

---

## Interface composition (non-functional)

- **Two main regions:** (1) **History** — a vertical sequence of **history item** components in chronological order; (2) **Input** — textbox + send button.
- **History item component:** Each message in the thread is one **history item**. Items are rendered **in sequence** (document order = conversation order). A **single property** on each item defines the speaker for both semantics and styling: **`agent`** (orchestrator / server-side response) or **`analyst`** (human input). Implementation may use a prop name such as `role`, `speaker`, or `kind` as long as the allowed values are exactly **`agent`** and **`analyst`**.
- **History container:** New items are always appended **at the bottom** of the list so the natural reading order matches turn order.
- **Input:** Single textbox and send button; disable send while a request is in flight if that avoids duplicate submissions (optional guardrail—only if default UX suffers without it).
- **Visual distinction:** **Agent** vs **analyst** items must be **visually distinct** using the **minimum** custom CSS, driven by the item’s role property (e.g. `data-role="agent"` / `data-role="analyst"`, or class names derived from the same enum)—labels, borders, or light background tints are enough; no full theme.
- **Styling:** Default HTML appearance everywhere else; no typography or color exploration beyond clarity and the two roles.

---

## Implementation steps (UX-aligned)

1. **Shell layout:** One page with two regions—scrollable history container and fixed input strip (or input below history)—using default block layout.  
   *Won’t do:* complex grid/flex unless needed for scroll containment.

2. **State machine (implicit or explicit):** `idle_new_session` ↔ `session_active` driven by presence of `session_id` and successful first response.  
   *Won’t do:* extra states (e.g. “draft”) unless required for error recovery.

3. **First-send path:** On first submit, append a **history item** with role **`analyst`** (the problem statement), then call start-session with the same body; show a minimal loading indicator or disabled send if needed so the Analyst knows something is happening.  
   *Won’t do:* block the UI without feedback on slow networks.

4. **Parse and store:** On first response, run the agreed JSON extraction on the response text, read `session_id`, append a **history item** with role **`agent`** for the visible response, then flip to `session_active`.  
   *Won’t do:* silently drop failures—surface a short inline error in the history or under the input.

5. **Follow-up path:** On subsequent submits, POST to messages with stored `session_id`; append **`analyst`** history item, clear input, scroll history to bottom; on response, append **`agent`** history item, scroll again.  
   *Won’t do:* prepend messages or require manual scroll.

6. **History rendering:** Implement a reusable **history item** component (or equivalent primitive) and append one instance per turn. Each instance receives body text plus the **`agent` | `analyst`** property; the history list only composes these items in order.  
   *Won’t do:* one monolithic blob for the whole transcript; rich markdown rendering unless the PoC explicitly requires it.

7. **Smoke validation:** Manual walkthrough of the full journey against a running API; optionally one automated test if the repo already has a front-end test harness—otherwise document the manual checklist.  
   *Won’t do:* large E2E matrix; keep checks aligned to the Gherkin above.

---

## Guardrails

- **Size:** Few files, minimal dependencies; every addition must trace to a stated BDD or NFR.
- **Contract:** Document the exact start-session and messages URLs, method, and body shape next to the UI code or in this plan’s appendix when implemented.
- **Parsing:** Define one clear strategy for “JSON in text” (e.g. fenced block, last JSON object, regex)—same behavior on success and clear error on failure.
- **Accessibility (light touch):** Use labels associated with the textarea and a sensible button name so default focus/tab order remains usable.
- **Done means:** All Gherkin scenarios above are demonstrable in the browser with default-plus-minimal styling, a **sequence of history item components**, and two visually distinct variants driven by **`agent` vs `analyst`** on each item.

---

## Appendix — traceability (quick matrix)

| Requirement | UX artifact |
|-------------|-------------|
| First open shows input | Layout + initial state |
| First send → start session | Wire first submit to start-session API |
| First response → JSON + session id + active | Parser + state + history item (`agent`) |
| Follow-up → messages API | Wire submit when `session_id` present |
| Append + clear + scroll | Input handler + history item (`analyst`) + scroll container |
| Agent vs analyst styling | History item role property + minimal CSS |

This plan is intentionally narrow so implementation can stay small while still validating the concept with a realistic Analyst session.
