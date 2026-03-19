# State is Explicit, Not Implicit

Never hide state inside processes. Persist agent steps, plans, tool outputs, and decisions so execution can be reconstructed from logs and events; process memory must not be the system of record.

## What it means

- Persist all agent steps.
- Persist all plans.
- Persist all tool outputs.
- Persist all decisions.
- Reconstruct execution from logs and events.

## Why it matters

- Debugging becomes possible.
- Enables replay, audit, and evaluation.
- Required for enterprise trust.
