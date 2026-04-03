# Step 1 — Token semantics

## Purpose

Verify that **design tokens used in Svelte (and scoped component styles)** match the **intent** documented in the design registry—not just that a variable exists, but that it is **appropriate for the UI role** (e.g. success state vs warning color, primary text vs secondary).

## Inputs (read before auditing)

1. [.cursor/design/tokens.md](../../../design/tokens.md) — foundation tokens, semantic aliases, typography, spacing, radii, elevation.
2. [.cursor/design/components.md](../../../design/components.md) — when a component pattern names specific tokens for a slot (e.g. card surface → `bg.card`), use that as the expected mapping for that pattern.
3. [services/orchestration-web/src/lib/styles/tokens.css](../../../../services/orchestration-web/src/lib/styles/tokens.css) — authoritative list of `--*` names; anything in code not defined here (unless dynamically set) is invalid for Step 1.

## Scope

- **Include:** all `*.svelte` files under the audit scope (default: `services/orchestration-web/`).
- **Include:** `<style>` blocks and any `style=` attributes that reference `var(--…)`.
- **Optional extension:** `*.css` in `services/orchestration-web/src/lib/styles/` if the user wants global layers audited in the same pass.

## Registry → CSS variable map

Design docs use **dot notation**; components use **kebab-case** custom properties. Use this mapping when interpreting `var(--…)`:

| Registry name | CSS variable |
| ------------- | ------------ |
| `color.primary` | `--color-primary` |
| `color.primary.light` | `--color-primary-light` |
| `color.background` | `--color-background` |
| `color.surface` | `--color-surface` |
| `color.border` | `--color-border` |
| `color.text.primary` | `--color-text-primary` |
| `color.text.secondary` | `--color-text-secondary` |
| `color.success` | `--color-success` |
| `color.warning` | `--color-warning` |
| `color.data.1` | `--color-data-1` |
| `color.data.2` | `--color-data-2` |
| `text.primary` | `--text-primary` |
| `text.secondary` | `--text-secondary` |
| `bg.app` | `--bg-app` |
| `bg.card` | `--bg-card` |
| `bg.hover` | `--bg-hover` |
| `bg.active` | `--bg-active` |
| `spacing.1` … `spacing.5` | `--spacing-1` … `--spacing-5` |
| `radius.1`, `radius.2` | `--radius-1`, `--radius-2` |
| `shadow.1`, `shadow.2` | `--shadow-1`, `--shadow-2` |
| `font.family` | `--font-family` |
| `font.weight.regular` … `bold` | `--font-weight-regular` … `--font-weight-bold` |
| `font.lineHeight` | `--font-line-height` |
| `font.size.1` … `font.size.6` | `--font-size-1` … `--font-size-6` |
| `layout.grid.columns` | `--layout-grid-columns` |
| `layout.grid.gap` | `--layout-grid-gap` |
| `layout.section.gap` | `--layout-section-gap` |
| `layout.container.maxWidth` | `--layout-container-max-width` |
| `breakpoint.*` | `--breakpoint-*` (see `tokens.css`) |

**Composition:** `color-mix(in srgb, var(--color-…), …)` is valid when built from foundation variables per tokens.md and [.cursor/rules/design-tokens.mdc](../../../rules/design-tokens.mdc).

## Procedure

1. **Enumerate token usage** in scope: search for `var(--` in `*.svelte` (and optional `*.css`). Collect each distinct `--*` name per file.
2. **Validate names:** every `--*` must exist on `:root` in `tokens.css` (or be a known stack like `var(--text-primary)` chaining to one that exists). Flag unknown custom properties.
3. **Semantic intent check** (for each usage site):
   - Read surrounding markup / class names / copy (e.g. “Error”, “Success”, “Muted label”).
   - Compare the chosen token to the **Intent** and **Usage** columns in `tokens.md` for the registry name (use the mapping table above).
   - Compare to **components.md** when the file implements a documented pattern (card, grid, etc.) and that doc specifies tokens for a slot.
   - **Mismatch example:** using `--color-warning` for a success banner, or `--text-secondary` for the only headline on a screen when the intent is primary content.
4. **Literal values** (per [.cursor/rules/frontend-design-system.mdc](../../../rules/frontend-design-system.mdc)):
   - Flag **hex, rgb/hsl, raw px/rem for spacing** in component styles **except** where rules allow (e.g. `color-mix` / `rgba` **only** combining documented `var(--…)`).
   - Documented exceptions in design docs (e.g. a one-off line-height on a pattern in `components.md`) are **not** literals violations if called out there.
5. **Duplicated semantics:** if two different tokens are used for the same documented role in the same pattern without justification, note as **Med** inconsistency.

## Output for this step

Add a **Step 1 — Semantics** section to the audit report using the template in [SKILL.md](../SKILL.md). For each issue, state:

- **File** and **approximate location** (line or selector).
- **Token(s)** involved and **which registry intent** they contradict (quote a short phrase from `tokens.md` or `components.md` if useful).
- **Severity** and **fix** (which token or pattern should apply).

## Pass criteria

Step 1 passes when there are no **High** findings and **Med** findings are either absent or explicitly deferred by the user.
