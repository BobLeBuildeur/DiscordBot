---
name: report-bug
description: >-
  Gathers a structured report (problem, workaround, impact), classifies it as a
  bug vs improvement with user confirmation, in context of the latest milestone
  and plan, then opens a GitHub issue in this repository. Use when the user
  wants to report a bug, suggest a UI tweak, file a GitHub issue, or run the
  “Report bug” workflow. Assigns the GitHub issue to the repo milestone that
  best matches the current local milestone document.
---

# Report bug

## Goal

Capture enough context to tie the item to ongoing work, classify **Bug** vs **Improvement** (infer, then confirm with the customer), collect three narrative sections, and create a GitHub issue in the **current repository** using the body template below. **Assign** the issue to the **GitHub milestone** that best matches the selected local milestone file (see **Create the issue**).

## 1. Establish feature context (read before asking)

Do this **before** or **while** engaging the customer so labels/title/body reflect what is being built.

**Milestone**

- List `milestones/*.md` (repo root).
- Prefer the file with the **latest `YYYY-MM-DD-` date prefix** in the filename (ISO 8601; for valid dates, lexicographic order matches chronological order), per `.cursor/rules/milestones.mdc`.
- If **two or more** files share that **same date**, prefer the one with the **latest git commit** touching it (`git log -1 --format=%ct -- milestones/<file>`); if still tied, pick lexicographically greatest remainder of the filename.
- If **no** file matches `^\d{4}-\d{2}-\d{2}-.+\.md$`, fall back to the **most recently modified** `.md` in `milestones/` and mention in the issue that milestone filenames should use the dated prefix.
- Unless the user names a different milestone file, read the chosen file only as needed: **top heading** (e.g. “PoC Milestone”) and a short scope line for the issue title or intro. Keep the **heading** and the **filename slug** (the part after `YYYY-MM-DD-`, without `.md`) in mind—they are the primary strings used later to **match** a **GitHub** milestone title.

**Plan**

- List `plans/*.md` under repo root `plans/`.
- Prefer the plan with the **latest `YYYY-MM-DD-` date prefix** in the filename. If two share a date, prefer the one with the latest git commit touching that file (`git log -1 --format=%ct -- plans/<file>`).
- Skim the **Goal** (and Preconditions if present) so the issue can reference the intended feature.

If `milestones/` or `plans/` is missing or empty, say so briefly in the issue body under a short “Context” note instead of guessing.

## 2. Bug vs improvement (infer, then confirm)

Use these definitions when classifying:

- **Bug** — Deviation from **established** behavior: something that should work but does not (broken expectation, regression, or spec/plan says it should behave one way and it does not).
- **Improvement** — Small change (often UI/UX polish) that does **not** break or contradict established behavior; it makes the experience better without fixing a failure.

**Steps**

1. After you have at least a **Problem** draft (and optional context from milestone/plan), infer **Bug** or **Improvement** from wording and from what the milestone/plan already promises vs what the user describes.
2. State your inference in one short sentence (why it fits that bucket).
3. Show the two definitions above (or a one-line summary each) and **ask the customer to confirm or correct** the classification before creating the issue.
4. If ambiguous (e.g. “it works but feels wrong”), say so and let the customer choose.

Do not create the issue until the customer has **confirmed** **Bug** or **Improvement**.

## 3. Interview the customer (three sections)

Ask clearly for each section. Do not create the issue until you have **confirmed type** (bug-vs-improvement step above), **Problem**, and **Impact**; **Workaround** may be explicitly “None”.

| Section | What to collect |
|--------|------------------|
| **Problem** | Brief description of what is going wrong (expected vs actual). |
| **Workaround** | How to mitigate operationally, if any. If none, record as `None` or `_None_`. |
| **Impact** | **T-shirt size** (`XS`, `S`, `M`, `L`, or `XL`) **and** a brief note on why it matters (e.g. customer confusion, data risk, blocked workflow). |

## 4. GitHub issue body template

Use **exactly** these level-1 headings and **this order**. Do **not** prefix lines with Markdown blockquotes (`>`) unless the user explicitly wants that.

```markdown
# Bug or improvement
**Bug**

# Problem
<brief description>

# Workaround
<mitigation, or None>

# Impact
**<XS|S|M|L|XL>**
<brief description of impact>
```

Under **# Bug or improvement**, put only **`Bug`** or **`Improvement`** in bold (the customer-confirmed choice). Optionally add one short line of rationale after a blank line if it helps triage; do not paste the full definitions unless the user asks.

**Title:** Imperative or symptom-focused, optionally prefixed with a short scope hint from the milestone/plan (e.g. `[PoC] Plan hydrates frozen on cold load`).

## 5. Create the issue

- Run from the **repository root** so `gh` targets this repo.
- Require GitHub CLI: `gh issue create` with `--title` and `--body` (heredoc or file is fine).
- If `gh` is missing or not authenticated, say what failed and give the user the final title + body to paste manually on GitHub.

**GitHub milestone (assign to best match)**

1. From the **local milestone** chosen in step 1, build match hints: the document’s **first Markdown heading** (strip leading `#` / trim) and the **kebab-case slug** from the filename after the date prefix (e.g. `2026-03-19-proof-of-concept.md` → `proof-of-concept`). Optionally normalize hints (lowercase, replace `-` with spaces) for comparison.
2. List **open** milestones on this repo, e.g. `gh api "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/milestones" --jq '.[] | select(.state=="open") | .title'` (or equivalent). If none are open, you may include **closed** milestones as a fallback.
3. Pick the **single** GitHub milestone **title** that **best** matches the local hints: prefer **case-insensitive exact** match on heading or slug; else **substring** (hint contained in title or title in hint); else closest **token overlap** (significant words in common). The string passed to `gh` must be the **exact** `title` returned by the API.
4. Pass `--milestone "<exact title>"` to `gh issue create`.
5. If there is **no** reasonable match, **omit** `--milestone`, state that in the reply, and list the GitHub milestone titles you found so the customer can rename/create milestones or assign manually.
6. If the customer **insists** on a different GitHub milestone than your pick, use their choice.

**Example body** (format only; not blockquoted in the real issue):

```markdown
# Bug or improvement
**Bug**

# Problem
Plan always hydrating as frozen on cold load

# Workaround
Ask LLM to regenerate plan

# Impact
**M**
Workaround not intuitive for the customer
```

## 6. After creation

Reply with the issue URL (from `gh issue create` output). If a GitHub milestone was assigned, name it. If none was assigned, remind the customer they can set it on GitHub. Optionally add one sentence tying the issue to the local milestone/plan you read.

## 7. Add the issue to GitHub Project "Discord Bot - Backlog" (ID 4)

After creating the issue, add it to the GitHub Project and set custom fields.

1. Resolve the repo owner and keep the created issue URL:
   - `OWNER="$(gh repo view --json owner -q .owner.login)"`
   - `ISSUE_URL="<issue url from gh issue create>"`
2. Add the issue to project number `4`:
   - `ITEM_ID="$(gh project item-add 4 --owner "$OWNER" --url "$ISSUE_URL" --format json --jq '.id')"`
3. Resolve project and field metadata:
   - `PROJECT_ID="$(gh project view 4 --owner "$OWNER" --format json --jq '.id')"`
   - `gh project field-list 4 --owner "$OWNER" --format json` to find:
     - `Type` field id and the single-select option ids for `Bug` / `Improvement`
     - `Impact` field id and the single-select option ids for `XS` / `S` / `M` / `L` / `XL`
4. Map values from earlier sections:
   - `Type` = confirmed value from **Bug vs improvement** (`Bug` or `Improvement`)
   - `Impact` = confirmed T-shirt size from **Impact** (`XS|S|M|L|XL`)
5. Set project fields on the item:
   - `gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "<TYPE_FIELD_ID>" --single-select-option-id "<TYPE_OPTION_ID>"`
   - `gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "<IMPACT_FIELD_ID>" --single-select-option-id "<IMPACT_OPTION_ID>"`
6. If auth/scope errors mention projects (for example `insufficient OAuth scope`), refresh auth and retry:

```bash
gh auth refresh -s project
```

7. In the final response, include:
   - issue URL
   - assigned GitHub milestone (if any)
   - project assignment confirmation: `Discord Bot - Backlog` (ID `4`)
   - the `Type` and `Impact` values set on the project item
