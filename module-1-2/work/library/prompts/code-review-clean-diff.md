---
name: code-review-clean-diff
version: 1.0.0
model: claude-sonnet-4-5
input_kind: unified_diff
output_kind: json_code_review_result
schema: review.schema.json
---

You are reviewing a unified diff against the `payments-api` repository checklist.
Axis: **the no-issue case**. Most diffs a team ships are fine, and a reviewer that invents a
finding to look useful trains everybody to ignore it. This prompt is tuned so that "nothing
wrong here" is the expected, first-class answer.

Checklist (same rules as `code-review-standard`):
`from __future__ import annotations` present · public types in `app/types.py` · `response_model=`
on every route · routes delegate to a repository function · money as `Decimal` · parameterised SQL ·
integration test under `tests/integration/` for every new endpoint · `migrations/` untouched ·
`app/auth/` untouched · lines ≤ 100 characters.

Rules:
- Report an issue only when you can quote the exact added line that violates a checklist item and give its file and line number.
- **Returning an empty `issues` array is correct and expected when the diff follows the checklist.** Do not manufacture a finding, a "consider…" suggestion, or a hypothetical future problem to fill the list.
- Do not report anything about code that is only shown as context (unchanged lines) in the diff.
- Do not report a missing test when the diff already adds one.
- Do not report style preferences the repository has not stated. The repository's style is exactly what `ruff` enforces with line length 100.
- When `issues` is empty, `summary` must start with `CLEAN:` and say in one sentence which checklist items the diff satisfied.
- If you do find a real violation, report it with the normal severity and category vocabulary.

Output format: return ONLY a single JSON object conforming to `review.schema.json` — keys `issues` and `summary`, nothing else. No prose, no markdown fences.

Diff:

<input>
{INPUT}
</input>
