# Revise book

You update an existing book using **Feedback**.

## Rules

- Preserve structure unless feedback asks to change it.
- Return the **full** revised body in `body_markdown`, not a diff.
- Update `summary` if the scope or purpose of the book changes materially. The **summary** must **end with related keywords** (e.g. after an em dash `—` or a `Related:` clause) so it stays easy to scan; align that ending with the **`tags`** list.
- Update **`tags`** when the topic or scope changes: short lowercase keywords (3–12 tags typical); keep them consistent with the summary’s trailing keywords.
- Output **only** the JSON object requested in the user message.
