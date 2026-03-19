# Work Stream 06: Slide Generation

**Deliverable:** Pipeline that converts analytical outputs (tables, charts) into presentation-ready slides with corporate branding.

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 03-agent-core | Execution produces tables and chart specs | Agent outputs chart metadata |
| 04-table-interface | Table data available for export | Data can be passed to slide engine |
| Slide templates | Corporate layouts and branding defined | Templates available (PPTX or equivalent) |
| Chart library | Chart generation capability (e.g., Chart.js, D3, server-side) | Charts render correctly |

---

## Sections (What They Contain and Why)

| Section | Content | Purpose |
|--------|---------|---------|
| **Template System** | Corporate layouts, placeholders, branding | Consistent look |
| **Chart Generation** | Create charts from table data | Visualize analysis |
| **Insight Summaries** | LLM-generated text for slides | Communicate findings |
| **Output Format** | PPTX or web-based slides | Deliverable format |
| **Orchestration** | Agent triggers slide build from plan | End-to-end flow |

---

## Actions

### Phase 1: Template System

1. Define slide template format (e.g., PPTX with named placeholders).
2. Create 3+ templates: title, chart, table, insight.
3. Implement template loader and placeholder resolution.
4. Apply corporate branding (colors, fonts, logo).

### Phase 2: Chart Generation

5. Implement chart spec from agent: type (bar, line, pie), data, labels.
6. Build chart renderer (client or server-side).
7. Support common chart types: bar, line, pie, scatter.
8. Export chart as image for slide insertion.

### Phase 3: Table to Slide

9. Convert table data to slide table format.
10. Apply formatting (headers, alignment, number format).
11. Handle large tables: paginate or summarize.

### Phase 4: Insight Summaries

12. Implement LLM call: given chart/table, generate 1–3 bullet insights.
13. Add tone and length constraints (executive summary style).
14. Validate output for appropriateness.

### Phase 5: Assembly & Output

15. Assemble slides: title → chart + insight → table → summary.
16. Generate PPTX (or equivalent) from template + content.
17. Support web-based slide viewer as alternative.
18. Add download and share options.

### Phase 6: Agent Integration

19. Add "generate slides" step to agent plan execution.
20. Pass execution outputs (tables, chart specs) to slide pipeline.
21. Return slide artifact to user.

---

## Checks and Guardrails

| Check | Criterion | Failure Action |
|-------|-----------|----------------|
| **Template validity** | All placeholders resolve | Fail fast with clear error |
| **Chart accuracy** | Chart data matches source table | Validate before render |
| **Insight safety** | LLM output filtered for inappropriate content | Add content filter |
| **File size** | Generated PPTX under reasonable limit (e.g., 50MB) | Compress or split |
| **Brand compliance** | Output uses approved templates only | Restrict template set |
| **Accessibility** | Slides have alt text for charts | Require in template |

---

## Deliverables

- [ ] Template system with 3+ layouts
- [ ] Chart generation (bar, line, pie, scatter)
- [ ] Table-to-slide conversion
- [ ] LLM-generated insight summaries
- [ ] PPTX output (and/or web viewer)
- [ ] Agent integration for slide generation step
