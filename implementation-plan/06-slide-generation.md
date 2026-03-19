# Work Stream 06: Slide Generation

**Deliverable:** Pipeline that converts analytical outputs (tables, charts) into presentation-ready slides with corporate branding.

---

## Vision Context

The platform bridges the gap between **Analysis → Communication**. Results move seamlessly from tables into executive presentations.

**Features (from vision):**
- Use of approved corporate slide layouts
- Automatic chart generation
- Structured insight summaries
- Consistent corporate branding

**Use cases:**
- Monthly operations report → slide deck
- Market analysis → presentation
- Quarterly financial review → executive summary slides

Analysts who work in PowerPoint-style environments expect this flow. Slide generation completes the Plan → Revise → Build workflow by producing the final communication artifact.

---

## Persona Mapping

| Persona | Role in Slide Generation |
|---------|---------------------------|
| **Analysts** | Request slide generation as part of plan (e.g., "Create market analysis presentation"). Review and share slides. |
| **Agents** | Produce table data and chart specs during Build. Trigger slide pipeline. Pass outputs to slide engine. |
| **Knowledge Admins** | May define slide templates or branding standards in Books (optional). |

---

## Preconditions

| Precondition | Description | Verification |
|--------------|-------------|--------------|
| 03-agent-core | Execution produces tables and chart specs | Agent outputs chart metadata |
| 04-table-interface | Table data available for export | Data can be passed to slide engine |
| Slide templates | Corporate layouts and branding defined | Templates available (PPTX or equivalent) |
| Chart library | Chart generation capability (Chart.js, D3, server-side) | Charts render correctly |

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

## Slide Flow: Analysis → Communication

```
Build Stage Outputs
├── Table: regional_sales (columns: region, revenue, growth)
├── Chart spec: { type: "bar", x: "region", y: "revenue" }
└── Chart spec: { type: "line", x: "month", y: "revenue", series: "region" }
        ↓
Slide Pipeline
├── 1. Title slide (from plan task)
├── 2. Chart slide: bar chart + LLM insight bullets
├── 3. Chart slide: line chart + LLM insight bullets
├── 4. Table slide: summary table (formatted)
├── 5. Summary slide: key takeaways (LLM-generated)
        ↓
PPTX (or web viewer)
```

---

## Template Types

| Template | Purpose | Placeholders |
|----------|---------|--------------|
| **Title** | Deck title, subtitle | title, subtitle, date |
| **Chart** | Chart + insight bullets | chart_image, insight_1, insight_2, insight_3 |
| **Table** | Formatted data table | table_data, caption |
| **Insight** | Text-only summary | bullets, headline |
| **Section** | Section divider | section_title |

---

## Chart Spec (from Agent)

```json
{
  "type": "bar",
  "title": "Revenue by Region",
  "data": {
    "labels": ["North", "South", "East", "West"],
    "values": [120, 95, 110, 88]
  },
  "options": {
    "x_label": "Region",
    "y_label": "Revenue ($M)",
    "colors": ["#1a73e8", "#34a853", "#fbbc04", "#ea4335"]
  }
}
```

Supported types: bar, line, pie, scatter. Agent produces spec; slide engine renders to image for PPTX insertion.

---

## Insight Summaries (LLM)

Given a chart or table, the LLM generates 1–3 bullet insights in executive summary style.

**Prompt context:** Chart/table data, chart type, business context (from plan).

**Constraints:** Tone (professional), length (1–2 sentences per bullet), no speculation beyond data.

**Safety:** Content filter for inappropriate output.

---

## Actions

### Phase 1: Template System

1. Define slide template format (e.g., PPTX with named placeholders, or HTML/CSS for web).
2. Create 3+ templates: title, chart, table, insight.
3. Implement template loader and placeholder resolution.
4. Apply corporate branding (colors, fonts, logo). Store in template or config.

### Phase 2: Chart Generation

5. Implement chart spec parser: type, data, labels, options.
6. Build chart renderer (client or server-side). Use Chart.js, D3, or python-pptx with matplotlib.
7. Support common chart types: bar, line, pie, scatter.
8. Export chart as image (PNG/SVG) for slide insertion.

### Phase 3: Table to Slide

9. Convert table data to slide table format. Handle column headers, alignment.
10. Apply formatting (headers bold, number format for currency/percent).
11. Handle large tables: paginate across slides or summarize (top N rows, aggregations).

### Phase 4: Insight Summaries

12. Implement LLM call: given chart/table, generate 1–3 bullet insights.
13. Add tone and length constraints (executive summary style).
14. Validate output for appropriateness. Add content filter if needed.

### Phase 5: Assembly & Output

15. Assemble slides: title → chart + insight → table → summary. Order configurable.
16. Generate PPTX (e.g., python-pptx, pptxgenjs) from template + content.
17. Support web-based slide viewer as alternative (HTML/CSS or reveal.js).
18. Add download and share options (link, email).

### Phase 6: Agent Integration

19. Add "generate slides" step to agent plan execution. Optional step based on user task.
20. Pass execution outputs (tables, chart specs) to slide pipeline.
21. Return slide artifact to user. Store in project for download.

---

## Integration Points

| Work Stream | Integration |
|-------------|-------------|
| **03-agent-core** | Agent produces chart specs; triggers slide build; returns artifact |
| **04-table-interface** | User may select table/chart for slide; triggers build |
| **07-database-backend** | Store generated slides (file ref or blob) in project |
| **02-knowledge-base** | (Optional) SOPs or Books define slide structure for report types |

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
