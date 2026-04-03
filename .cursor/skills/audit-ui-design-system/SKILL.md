---
name: audit-ui-design-system
description: >-
  Audits the orchestration web UI for alignment with the repo design system:
  token semantics, UX patterns, and documented components. Runs as ordered steps
  defined in separate markdown files under this skill. Use when the user asks
  for a UI audit, design system review, token semantics check, or to verify
  Svelte components follow .cursor/design and tokens.css.
---

# Audit UI, UX, and design system application

## Goal

Produce a structured findings report by executing **step documents** in order. Each step is a standalone file under [steps/](steps/) so the workflow can grow without bloating this file.

**Default scope:** `services/orchestration-web/**/*.svelte` plus global styles that feed the app (`services/orchestration-web/src/lib/styles/**`). Narrow or widen only if the user specifies (e.g. a single route or component).

## Authority (shared)

| Layer | Path |
| ----- | ---- |
| Token registry (names, intent, usage) | [.cursor/design/tokens.md](../../design/tokens.md) |
| Component patterns (slots → tokens) | [.cursor/design/components.md](../../design/components.md) |
| CSS bridge (`:root` custom properties) | [services/orchestration-web/src/lib/styles/tokens.css](../../../services/orchestration-web/src/lib/styles/tokens.css) |
| Agent rules | [.cursor/rules/design-tokens.mdc](../../rules/design-tokens.mdc), [.cursor/rules/frontend-design-system.mdc](../../rules/frontend-design-system.mdc) |

## How to run the audit

1. **Confirm scope** with the user if unclear (whole service vs path).
2. **Execute steps in numerical order** unless the user limits the run to specific steps (e.g. “semantics only”).
3. For each step, **read the step file first**, then gather evidence (search, read files), then record results under that step in the report.
4. **Do not skip** reading the step document: it may refine rules or scope beyond this SKILL.

## Step index

| Order | File | Focus |
| ----- | ---- | ----- |
| 1 | [steps/01-semantics.md](steps/01-semantics.md) | Token **semantics**: each `var(--*)` in `.svelte` files matches documented **intent** for that token; literals and undocumented vars are flagged. |
| *TBD* | Add `steps/02-*.md` (and so on) | Future steps (e.g. component pattern compliance, a11y, motion). |

When new steps are added, extend the table above in the same commit.

## Report template

Use this structure so results are comparable across runs:

```markdown
# Design system audit

**Scope:** <paths>
**Date:** <ISO date if known>

## Summary
- <2–4 bullets: severity mix and themes>

## Step 1 — Semantics
### Passes
- <brief>

### Issues
| Location | Severity | Finding | Suggested fix |
| -------- | -------- | ------- | --------------- |
| `path/file.svelte` | High/Med/Low | … | … |

## Step 2 — <title>
…
```

**Severity:** **High** = violates documented intent or project rules (e.g. forbidden literals); **Med** = ambiguous or inconsistent semantics; **Low** = nit or follow-up.

## Guardrails

- Prefer **evidence**: cite file + line or a short code excerpt for each issue.
- Treat [.cursor/design/tokens.md](../../design/tokens.md) **Intent** and **Usage** columns as the semantic contract for foundation and semantic tokens.
- Treat [.cursor/design/components.md](../../design/components.md) as the contract for **component-level** token choices once Step 2+ exists; Step 1 still uses it when a component section names specific tokens for a pattern.
- If registry and `tokens.css` disagree, flag as **registry/bridge drift** and cite both.
