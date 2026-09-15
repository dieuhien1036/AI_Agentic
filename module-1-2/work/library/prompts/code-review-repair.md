---
name: code-review-repair
version: 1.0.0
model: claude-sonnet-4-5
input_kind: invalid_output_plus_validator_errors
output_kind: json_code_review_result
schema: review.schema.json
---

A previous code-review response failed JSON Schema validation. Repair it.

You are given the original (invalid) output and the exact complaint from the validator
(`work/validate/validate.py`, JSON Schema draft-07).

Rules:
- Fix **only** what the validator complained about. Preserve every valid finding, its wording, its file, and its line number.
- Do not add new findings. Do not delete a finding unless the validator says the finding itself is unfixable (for example, a `file` field that is not a string and has no recoverable value).
- Map an out-of-vocabulary value to the nearest legal one rather than dropping the issue:
  - `severity` must be one of `blocker`, `major`, `minor`, `nit` — e.g. `critical` → `blocker`, `high` → `major`, `low` → `minor`, `info` → `nit`.
  - `category` must be one of `correctness`, `security`, `performance`, `style`, `testing` — e.g. `vulnerability` → `security`, `formatting` → `style`, `tests` → `testing`.
- Remove any property the schema does not allow (`additionalProperties: false`) — but first fold its information into `message` or `suggestion` if it carries meaning.
- Coerce types rather than inventing values: `"line": "45"` → `45`. If a required field is genuinely absent and cannot be recovered from the text, drop that one issue and say so in `summary`.
- Truncate a `message` longer than 280 characters at a sentence boundary; do not paraphrase it into something new.
- Keep `summary` unchanged unless it is itself invalid, in which case write the shortest faithful replacement.

Output format: return ONLY the corrected JSON object conforming to `review.schema.json` — keys `issues` and `summary`, nothing else. No prose, no markdown fences, no diff, no explanation of what you changed.

Original output:

<original>
{ORIGINAL}
</original>

Validator errors:

<errors>
{ERRORS}
</errors>
