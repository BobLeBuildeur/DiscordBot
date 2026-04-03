
# Foundation

## Colors

| Token                  | Value     | Intent                | Usage                                                                                |
| ---------------------- | --------- | --------------------- | ------------------------------------------------------------------------------------ |
| `color.primary`        | `#2FB7B2` | Brand primary color   | Used for headers, active states, and key highlights. Defines system identity.        |
| `color.primary.light`  | `#6FD3CF` | Primary soft variant  | Used for hover states and subtle accents. Should not replace primary emphasis.       |
| `color.background`     | `#F5F7FA` | App background        | Base background for all pages. Ensures low visual noise.                             |
| `color.surface`        | `#FFFFFF` | Surface container     | Used for cards and panels. Always sits above background.                             |
| `color.border`         | `#E6EAF0` | Divider color         | Used for borders and separators. Maintains structure without heavy contrast.         |
| `color.text.primary`   | `#2E2E2E` | Primary text color    | Used for main content and high-emphasis text. Ensures readability.                   |
| `color.text.secondary` | `#7A8599` | Secondary text color  | Used for labels and metadata. Reduces visual hierarchy weight.                       |
| `color.success`        | `#4CAF50` | Positive feedback     | Used for growth indicators and success states. Typically paired with upward trends.  |
| `color.warning`        | `#F5A623` | Warning or highlight  | Used for attention or categorical distinction. Avoid overuse in core flows.          |
| `color.data.1`         | `#4A90E2` | Data series primary   | Default color for charts and data visualizations. Ensures consistency across graphs. |
| `color.data.2`         | `#7FB3FF` | Data series secondary | Used for secondary chart series. Maintains visual differentiation.                   |

**Composition:** Tints, overlays, and code chrome should be built with `color-mix(in srgb, …)` (or equivalent) from these tokens in `tokens.css` or component styles—do not add new named color tokens for one-off shades.

## Spacing

| Token       | Value  | Intent            | Usage                                                                     |
| ----------- | ------ | ----------------- | ------------------------------------------------------------------------- |
| `spacing.1` | `8px`  | Base spacing unit | Used for tight spacing like icon gaps. Foundation for all layout spacing. |
| `spacing.2` | `12px` | Small spacing     | Used within components for compact layouts. Maintains readability.        |
| `spacing.3` | `16px` | Default spacing   | Primary padding for cards and containers. Most common spacing value.      |
| `spacing.4` | `24px` | Section spacing   | Used between components and sections. Creates visual separation.          |
| `spacing.5` | `32px` | Layout spacing    | Used for large layout gaps. Defines page-level rhythm.                    |

## Radii

| Token      | Value | Intent         | Usage                                                               |
| ---------- | ----- | -------------- | ------------------------------------------------------------------- |
| `radius.1` | `6px` | Small radius   | Used for inputs and controls. Slight rounding for compact elements. |
| `radius.2` | `8px` | Default radius | Used for cards and containers. Standard rounding across system.     |

## Elevation

| Token      | Value                        | Intent           | Usage                                                            |
| ---------- | ---------------------------- | ---------------- | ---------------------------------------------------------------- |
| `shadow.1` | `0 1px 3px rgba(0,0,0,0.05)` | Subtle elevation | Used for cards and surfaces. Provides depth without distraction. |
| `shadow.2` | `0 4px 14px rgba(15, 23, 42, 0.12)` | Emphasized elevation | Floating controls and elements that must read above `shadow.1` cards. |

**Composition:** Focus rings and one-off depth may still use `color-mix` with foundation colors; prefer named shadow tokens when the pattern is reused.

## Typography

### Base

| Token                 | Value                           | Intent              | Usage                                                      |
| --------------------- | ------------------------------- | ------------------- | ---------------------------------------------------------- |
| `font.family`         | `"Inter", "Roboto", sans-serif` | Base font family    | Applied globally across UI. Ensures consistent typography. |
| `font.weight.regular` | `400`                           | Regular weight      | Used for body text. Default readable weight.               |
| `font.weight.medium`  | `500`                           | Medium emphasis     | Used for labels and UI elements. Adds slight emphasis.     |
| `font.weight.bold`    | `600`                           | Strong emphasis     | Used for KPIs and headings. Creates hierarchy.             |
| `font.lineHeight`     | `1.4`                           | Default line height | Applied to all text. Balances density and readability.     |

### Scale

| Token         | Value  | Intent            | Usage                                                  |
| ------------- | ------ | ----------------- | ------------------------------------------------------ |
| `font.size.1` | `12px` | Caption size      | Used for metadata and annotations. Lowest hierarchy.   |
| `font.size.2` | `13px` | Small body text   | Used for secondary content. Supports compact layouts.  |
| `font.size.3` | `14px` | Default body size | Used for most text content. Baseline readability.      |
| `font.size.4` | `16px` | Emphasized text   | Used for labels and important text. Slight prominence. |
| `font.size.5` | `24px` | Section title     | Used for page or section headings. High visibility.    |
| `font.size.6` | `28px` | KPI value size    | Used for key metrics. Maximum emphasis in UI.          |

### Semantic

| Token            | References             | Intent               | Usage                                                         |
| ---------------- | ---------------------- | -------------------  | ------------------------------------------------------------- |
| `text.primary`   | `color.text.primary`   | Main text role       | Used for all primary content. Ensures consistent readability. |
| `text.secondary` | `color.text.secondary` | Secondary text role  | Used for labels and supporting info. Reduces visual weight.   |
| `bg.app`         | `color.background`     | App background role  | Applied to page background. Defines base layer.               |
| `bg.card`        | `color.surface`        | Card background role | Used for all surfaces and containers. Separates content.      |
| `bg.hover`       | `color.primary.light`  | Hover background     | Used for hover states. Provides subtle interaction feedback.  |
| `bg.active`      | `color.primary.light`  | Active background    | Used for selected states. Indicates current selection.        |

---

## Layout

Grid columns, gutters, section spacing, container width, and **responsive breakpoints** are defined at the component layer in [components.md](components.md#grid) (`## Grid`). The CSS bridge exposes `layout.*` and `breakpoint.*` custom properties in [tokens.css](../../services/orchestration-web/src/lib/styles/tokens.css).
