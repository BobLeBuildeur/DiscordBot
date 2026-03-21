# Plan feedback (inline comments) — PoC UX

## Goal

Deliver **Word-style inline plan feedback** in the orchestration web client so Analysts can select part of a generated plan, attach comments **anchored in the document flow** next to that selection, optionally add a global note in the message input, and send one message that produces a **new revised plan** as the next assistant turn. The experience must be polished enough for **customer demos**: full-width plan, obvious add-feedback affordance, and readable frozen history after send.

**Success looks like:**

- Assistant turns whose kind is `plan` render as a **dedicated plan history item** that uses the **full width** of the history container (no side column).
- While that plan is the **active editable** draft (just streamed, not yet followed by a sent analyst message), the Analyst can select text, see a **“+”** control near the selection, add feedback that appears **anchored to that selection** via normal document layout (see Conceptual model). They edit in an **auto-growing textarea**, and collapse to a **single-line summary** when focus leaves. **Empty** feedback removed on blur.
- After the Analyst sends the **next** message (with or without extra text in the main input), that plan item **freezes**: **native text selection** still works for copy/read, but **no new comments** can be added (no “+”, no new anchors). Inline feedback on frozen items appears in a **reading** state (non-editable).
- The server receives **structured feedback** (each comment paired with the exact quoted plan substring) plus the **freeform message** and **current plan markdown**, calls the existing refinement path, and returns a **new** `plan` assistant turn; persistence replays correctly on session reload.

**Won’t do (this milestone):**

- Collaborative real-time editing, comments on non-plan assistant messages, or resolving overlapping selections across arbitrary markdown DOM in a fully general way beyond a pragmatic PoC (character-offset or range-based anchoring with documented limitations).
- Changing orchestration product pillars or replacing file-backed session storage.

## Preconditions

- PoC orchestration stack from `[plans/2026-03-19-agentic-orchestrator-poc.md](2026-03-19-agentic-orchestrator-poc.md)` is in place: `services/orchestration-server/` (engine, prompts, SSE API) and `services/orchestration-web/` (session page, History).
- `POST /orchestrator/sessions/{session_id}/messages` exists and the engine already branches to plan refinement when a plan exists (`plan_feedback` user turn kind in `engine.py`).
- `GET /orchestrator/sessions/{session_id}` returns persisted `SessionState` including `conversation_history` entries with `role`, `kind`, and `content`.
- Team accepts a **schema bump** for persisted turns or an equivalent backward-compatible extension so inline feedback survives reload (see Steps).

## Used Tools

- **Svelte 5** (`services/orchestration-web/`) for UI components and state.
- Existing **markdown rendering** (`renderMarkdown` / `HistoryItem.svelte` patterns).
- **FastAPI** + **Pydantic** (`services/orchestration-server/backend/api/orchestrator.py`, `backend/orchestrator/models.py`) for request and session models.
- **Prompt markdown** under `services/orchestration-server/prompts/orchestrator/` (`plan-refinement.md` and context assembly in `backend/orchestrator/prompts.py`).
- `**pytest`** and `**ruff**` for server tests and lint.
- Browser APIs: `Selection`, `Range`, and **minimal** positioning only where unavoidable (e.g. a floating “+” near the selection). Prefer **in-flow DOM** placement for comment UI so the engine handles layout. Optional: `element.focus()`, `requestAnimationFrame` for focus-after-render.

## Conceptual model

### History item type `plan`

The server already labels assistant plan outputs with `assistant_turn.kind == "plan"`. The web client today maps all assistant turns to a generic agent bubble. This feature **special-cases** `kind === 'plan'` (from hydrated history) and the **in-progress streamed plan** (final SSE payload with `assistant_kind === 'plan'`).

Each plan history item has:

- **Full-width** rendered markdown (same sanitization pipeline as today).
- **Comments anchored to selections** using **document flow**, not a parallel column: after the user confirms “+”, the comment block is inserted as a **sibling or adjacent in-flow node** tied to the selected range’s DOM context (e.g. immediately after the block element that contains the selection, or a small wrapper pattern that keeps layout linear). The browser’s normal block layout stacks plan text and comments—**no ongoing `top`/`left` sync**, no `ResizeObserver` loop for alignment.

**Layout principle (PoC):** Prefer **native layout** (block flow, flex/grid only for trivial local grouping inside one item). Avoid per-frame or scroll-synced absolute positioning of comment panels.

### Editable vs frozen (plan item)


| State        | When                                                                                                                                                          | Behavior                                                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Editable** | The plan is the latest assistant output in the live session **and** the user has not yet sent a subsequent analyst message that completed a server round-trip | Text selection enabled; “+” to add feedback; feedback active/inactive editing states apply.                                                                                          |
| **Frozen**   | Loaded from `GET` session, or after the user sends the next message and the stream completes                                                                  | **Default browser selection** on plan text (copy, highlight) works as usual. **No** “+” affordance and **no** new anchored comments. Existing feedback UI in **reading** state only. |


**Note:** During streaming, treat the plan as editable only after `final` (or optionally allow selection on partial stream with clear UX—default to post-final for simplicity).

### Feedback component states


| State        | When                                                   | UI                                                                   |
| ------------ | ------------------------------------------------------ | -------------------------------------------------------------------- |
| **Active**   | Component has focus or is explicitly selected for edit | `textarea` grows with content (auto-resize).                         |
| **Inactive** | Editable parent, not focused                           | Collapsed height (~one line), show truncated preview or placeholder. |
| **Reading**  | Parent plan is **frozen**                              | Same text as inactive but styled disabled/read-only (no editing).    |


When multiple feedback blocks attach to the **same** anchor region, **stack them vertically** in normal flow (e.g. a local flex column with gap)—still no global column beside the plan.

**Removal rule:** When the parent plan is **editable** and a feedback component **loses focus** (is unselected) and its text is **empty** (whitespace-only counts as empty), **remove** that feedback entry from the list / DOM.

**Focus rule:** When the Analyst presses **“+”**, the new feedback component’s **textarea is focused immediately** (and caret placed inside), so typing can start without an extra click.

### Applying feedback

On send:

1. Client validates that **if** the latest assistant turn is an editable `plan`, **either** there is at least one inline comment **or** the message input is non-empty (product rule: avoid empty sends—adjust if product prefers allowing “apply with no comments”).
2. Client **freezes** the current plan item in local state immediately (optimistic) or upon `final` (simpler consistency: freeze when send starts).
3. Request body includes:
  - `message`: string (main input; may be empty if comments-only is allowed).
  - `plan_feedback`: structured list, e.g. `{ quoted_text: string, body: string }[]` (exact field names chosen in implementation), each `quoted_text` copied from the plan at selection time.
4. Server builds refinement context: **current plan markdown**, **freeform message**, and **enumerated comments with quoted spans**, then calls existing `refine_plan_stream` path.
5. Response is a new assistant `plan` turn; UI appends it as a **new editable** plan item.

---

## Behavior-driven design (acceptance criteria)

### Assistant returns plan — history item type and editable state

**Given** the assistant returns a plan (`assistant` turn kind `**plan`**)  
**Then** the history renders that turn as a **plan** history item  
**And** the plan item is **editable** until the analyst completes the next send (successful round-trip).

### Editable plan — text selection shows add-feedback control

**Given** the plan item is **editable**  
**When** the analyst selects text in the plan body  
**Then** a **“+”** control appears near the selection (minimal positioning only; e.g. one-off placement from `Range` / selection rect).

### Editable plan — “+” adds anchored feedback and focuses textarea

**Given** the plan item is **editable**  
**And** the analyst has selected text in the plan  
**When** the analyst clicks **“+”**  
**Then** a feedback block appears **anchored in document flow** at that selection (per implementation in [Steps](#steps))  
**And** the feedback **textarea is focused immediately** so the analyst can type without further interaction.

### Editable plan — multiple comments on the same anchor stack in flow

**Given** the plan item is **editable**  
**When** the analyst adds another comment on the **same** anchor region  
**Then** the new feedback blocks **stack vertically** in normal flow below prior ones for that anchor.

### Feedback block — focus expands to active editing

**Given** a feedback block exists on an **editable** plan  
**When** the analyst focuses the block  
**Then** it becomes **active** with a growing textarea.

### Feedback block — blur collapses to inactive when text present

**Given** a feedback block exists on an **editable** plan  
**And** the block contains **non-whitespace** text  
**When** the analyst moves focus away from the block  
**Then** it collapses to about **one line** in height  
**And** it becomes **inactive**.

### Editable plan — empty feedback removed on blur

**Given** the plan item is **editable**  
**And** a feedback block contains **no** non-whitespace text  
**When** the analyst moves focus away from that block  
**Then** the feedback component is **removed** (not left as an empty shell).

### Send next message — plan item freezes

**Given** the plan item is **editable**  
**When** the analyst sends the **next** message  
**Then** that plan item becomes **frozen**  
**And** it is **no longer editable** afterward.

### Frozen plan — native selection without new comments

**Given** the plan item is **frozen**  
**When** the analyst selects plan text (e.g. with the pointer)  
**Then** **normal browser selection** applies  
**And** **no** **“+”** appears  
**And** **no** new comment can be added.

### Frozen plan — existing feedback is read-only

**Given** the plan item is **frozen**  
**When** the analyst interacts with an existing feedback block  
**Then** it is shown in the **reading** (disabled) presentation  
**And** it is **not** an editable textarea.

---

## Steps

1. **Extend session API contract (server)**
  - In `backend/api/orchestrator.py`, extend `SessionMessageRequest` with an optional structured field (e.g. `plan_inline_feedback: list[{ quoted_text: str, comment: str }] | None`), validated for max count and string lengths suitable for PoC.  
  - **Won’t do:** Skip validation and allow unbounded payloads.
2. **Persist structured feedback with the user turn (server)**
  - Extend `TurnRecord` in `backend/orchestrator/models.py` with an optional JSON-serializable field (e.g. `attachments: dict[str, Any] | None` or a typed `PlanInlineFeedbackItem` list) so `GET` session returns comments for frozen plan items.  
  - In `OrchestratorEngine.advance_session_streaming`, when appending the user turn for `plan_feedback`, attach the structured list from the request body.  
  - Bump `SessionState.schema_version` if the team wants an explicit migration marker; otherwise ensure new fields default so old JSON files still load.  
  - **Won’t do:** Store feedback only client-side with no server record.
3. **Prompt and context assembly (server)**
  - Update `PromptManager.build_plan_refinement_prompt` / `_render_context` (or refinement-specific section) to include a clear block: **“Inline comments on the plan”** listing each `quoted_text` and `comment`, plus **“Analyst message (free text)”**.  
  - Revise `prompts/orchestrator/plan-refinement.md` to instruct the model to preserve structure, apply comments faithfully, and output full revised markdown plan.  
  - **Won’t do:** Rely solely on embedding comments in the flat `message` string without structured context.
4. **Wire engine to use structured data**
  - Ensure `advance_session_streaming` passes the combined context into refinement (the latest user message may duplicate short notes—prefer structured list + message as specified in prompts).  
  - **Won’t do:** Change `create_plan` or follow-up flows unnecessarily.
5. **Types and client API (web)**
  - Replace or extend `Message` in `services/orchestration-web/src/lib/types.ts` with a discriminated union or optional fields: e.g. `kind: 'text' | 'plan'`, `planMarkdown`, `inlineFeedback[]`, `frozen: boolean` derived from session position.  
  - Update `getSession` mapping in `src/lib/api.ts` to parse `conversation_history` entries using `kind` and new attachment fields, not only `role`/`content`.  
  - Update `sendMessage` to accept optional structured feedback and serialize into the POST body.  
  - **Won’t do:** Keep a single `body` string for plan turns without a parallel structure.
6. `**PlanHistoryItem` layout component (web)**
  - Add `services/orchestration-web/src/lib/components/PlanHistoryItem.svelte` (name may vary): **single full-width** column for the plan; comment UI lives **in flow** next to or under the anchored fragment (not a second column).  
  - **Won’t do:** Dual-column grid with fixed feedback rail and scroll-synced alignment.
7. **Selection, “+”, and in-flow anchor (web)**
  - On the editable plan markdown container, listen for `mouseup` / `selectionchange` (debounced) to detect user selections wholly inside the plan root.  
  - Render a small floating “+” near the selection only if needed; keep positioning to the **minimum** (e.g. one `getBoundingClientRect` for the toolbar, or inline control—choose the smallest viable approach).  
  - On “+”: capture **exact `quoted_text`** from the selection; insert the feedback UI using **DOM flow** (e.g. wrap range / insert adjacent block after the containing paragraph or list item so the comment sits **under** the relevant plan segment without absolute coordinates). Persist a stable `id` and anchor metadata for the API (character offsets in source markdown if available, or quoted text + order—document ambiguity if the same substring repeats).  
  - **Immediately** `focus()` the new feedback `textarea` (e.g. after tick/`requestAnimationFrame` if Svelte mount order requires it).  
  - **Won’t do:** Allow selections that span outside the plan root; **won’t do:** continuous layout recomputation for side-aligned panels.
8. `**FeedbackBlock` component (web)**
  - Props: `text`, `state` (`active` | `inactive` | `reading`), `onUpdate`, `onBlur` / focus handlers.  
  - Implement auto-resize textarea in active state; single-line clamp in inactive; readonly/disabled styling in reading.  
  - On blur: if trimmed text is empty and parent is **editable**, **remove** this block and notify parent.  
  - Vertical stacking for multiple comments on the same anchor: local flex column with gap—**in flow**, same anchor container.
9. **Integrate with `History.svelte` / session page**
  - Branch `HistoryItem` vs `PlanHistoryItem` based on assistant `kind === 'plan'`.  
    - Track which message index is the “latest editable plan” using message list length and frozen flags after send.  
    - On `handleSend`, gather all non-empty inline comments, call `sendMessage` with structured payload, then append new messages from stream as today.
10. **SSE final payload (optional hardening)**
  - If the client needs `assistant_kind` before full history reload, ensure `FinalEvent` already exposes it (it does in `types.ts`); use it when replacing the streaming placeholder with a typed plan item.
11. **Tests (server)**
  - Add API/engine tests: POST message with structured feedback yields refinement prompt containing quoted spans; persisted user turn includes attachments.  
    - Extend `tests/conftest.py` fake LLM client if needed to assert prompt content.
12. **Tests / checks (web)**
  - Add minimal component or integration tests if the project already uses Vitest/Playwright; otherwise document manual QA script aligned with the BDD section.  
    - Run existing lint for the web package.

## Guardrails

- **XSS / HTML:** Reuse the same markdown sanitization as `HistoryItem`; do not inject raw user feedback as HTML.
- **Prompt size:** Cap number of inline comments and per-comment length in the API model to avoid runaway tokens.
- **UX consistency:** Typography, borders, and spacing match existing history items; anchored comments should read as secondary to the plan (subtle background, clear hierarchy).
- **Light layout:** No requirement for pixel-perfect side alignment; reject approaches that depend on scroll listeners or `ResizeObserver` solely to pin comments beside arbitrary line boxes unless a later milestone demands it.
- **Quality gates:** `ruff check` and `pytest` on `services/orchestration-server/`; web lint/build as configured in the repo.

## Follow-ups / deferred work

- **Ambiguous selections:** If the same substring appears multiple times in the plan, PoC may attach feedback to the first match or require disambiguation—call out in release notes. Ensure this gets added as a TODO in the code.
- `**TODO(observability)`** in `openai_client.py` for metadata extraction remains unrelated; do not block this feature on it.
- **True block-level anchors** (heading IDs, AST positions) for more stable commenting across edits.

