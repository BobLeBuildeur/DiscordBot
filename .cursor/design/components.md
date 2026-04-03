# Component tokens

This document is the **second level** of the design system: named UI patterns (**components**) and the **foundation tokens** they compose. Foundation values live in [tokens.md](tokens.md); this file does not duplicate hex or introduce new palette values—it only maps patterns to foundation names.

When implementing or refactoring a component, add or update its section here so the registry stays aligned with code.

---

## `card`

**Intent:** A resting surface that sits above `bg.app`, with primary text and subtle elevation—used for contained content such as user-authored messages.

**Reference implementations:**

- Analyst branch of [HistoryItem.svelte](../../services/orchestration-web/src/lib/components/HistoryItem.svelte) (`.history-item[data-role='analyst']` and shared `.history-item` container spacing).
- [PlanHistoryItem.svelte](../../services/orchestration-web/src/lib/components/PlanHistoryItem.svelte) (`.plan-history-item` — agent plan turns use the same card chrome).

| Slot | Role | Foundation token(s) | Notes |
| ---- | ---- | -------------------- | ----- |
| Surface fill | Card chrome | `bg.card` → `color.surface` | `background` via `var(--bg-card)` |
| Foreground | Body copy | `text.primary` → `color.text.primary` | `color` via `var(--text-primary)` |
| Elevation | Depth on app background | `shadow.1` | `box-shadow` via `var(--shadow-1)` |
| Elevation (emphasis) | Float above other cards | `shadow.2` | Stronger lift—e.g. plan “add feedback” control (`.selection-add` in PlanHistoryItem) |
| Padding inline | Horizontal inset | `spacing.3` | `16px` — `var(--spacing-3)` |
| Padding block | Vertical inset | `spacing.2` | `12px` — `var(--spacing-2)` |
| Corner | Rounded container | `radius.1` | `6px` — `var(--radius-1)` |
| Stack spacing | Gap to next row in a list | `spacing.1` | `8px` — `margin-bottom` via `var(--spacing-1)` |

**Composition note:** The shared `.message-body` wrapper uses `line-height: 1.55` for chat readability (slightly looser than foundation `font.lineHeight` `1.4`). If this becomes a shared standard, promote it to a foundation or bridge token; until then it remains a local composition on this pattern.

---

## Grid

**Intent:** A **12-column** responsive layout system: consistent gutters, section rhythm, and a capped content width. All spacing references resolve to [tokens.md](tokens.md) (`spacing.*`).

### Layout tokens

| Token | References | Intent | Usage |
| ----- | ---------- | ------ | ----- |
| `layout.grid.columns` | `12` | Grid column count | Defines layout structure. Standard responsive grid. |
| `layout.grid.gap` | `spacing.4` | Grid spacing | Space between grid items. Keeps layout breathable. |
| `layout.section.gap` | `spacing.5` | Section spacing | Separates major sections. Improves readability. |
| `layout.container.maxWidth` | `spacing.5 * 40` (1280px) | Max content width | Constrains content width. Prevents over-stretching. |

**CSS bridge:** `tokens.css` exposes `--layout-grid-columns`, `--layout-grid-gap`, `--layout-section-gap`, `--layout-container-max-width` (see below).

### Responsive breakpoints

**Mobile-first:** base styles apply from **0px** (mobile small). Widen layouts using `min-width` at the thresholds below.

| Device | Min width | Typical range | Usage |
| ------ | --------- | ------------- | ----- |
| **Mobile (small)** | `0px` | 0–479px | Default styles, single-column layouts |
| **Mobile (large)** | `480px` | 480–639px | Larger phones, improved spacing |
| **Tablet (portrait)** | `640px` | 640–767px | First multi-column layouts |
| **Tablet (landscape)** | `768px` | 768–1023px | Standard tablet breakpoint |
| **Desktop (small)** | `1024px` | 1024–1279px | Laptops, main desktop layout |
| **Desktop (large)** | `1280px` | 1280–1535px | Wide screens, more whitespace |
| **Desktop (XL)** | `1536px` | 1536px+ | Large monitors |

**CSS bridge:** `--breakpoint-mobile-lg` (480px), `--breakpoint-tablet` (640px), `--breakpoint-tablet-landscape` (768px), `--breakpoint-desktop` (1024px), `--breakpoint-desktop-lg` (1280px), `--breakpoint-desktop-xl` (1536px).

### How to use

1. **Page shell** — Wrap primary content in a **container** centered on wide viewports:

   - `max-width: var(--layout-container-max-width)`
   - `margin-inline: auto`
   - Horizontal padding: use `spacing.3` or `spacing.4` (`var(--spacing-3)` / `var(--spacing-4)`) so text does not touch viewport edges on small screens.

2. **12-column grid** — On a region that should behave as the standard grid:

   - `display: grid`
   - `grid-template-columns: repeat(var(--layout-grid-columns), minmax(0, 1fr))` so columns track and shrink correctly.
   - `gap: var(--layout-grid-gap)` for gutters between cells.

3. **Spanning columns** — Place items with `grid-column: span N` where `N` is 1–12. Example: one column on mobile (`span 12`), two columns from tablet up (`@media (min-width: var(--breakpoint-tablet)) { span 6 }`).

4. **Sections** — Stack major blocks (hero, feature bands, footers) with vertical gap or margin using `var(--layout-section-gap)` instead of ad-hoc `rem` values.

5. **Breakpoints** — Prefer `@media (min-width: var(--breakpoint-*))` so thresholds stay aligned with this table. Order queries from **smallest min-width to largest** (mobile-first). Optional: combine with `container` queries where a component must respond to its own width, not the viewport.

6. **Discreet steps** — Avoid extra breakpoints between these values unless a screen design clearly requires it; fewer steps keep behavior predictable across pages.
