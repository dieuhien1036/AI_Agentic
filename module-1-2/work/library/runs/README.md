# Schema-constrained run — `code-review-standard`

The constrain → validate → self-repair loop, captured end to end.
Schema: `work/validate/review.schema.json` — the single source of truth. Both the harness
(via each golden's `schema: ../validate/review.schema.json`) and `validate.py` load this same
file, so the two can never disagree about what counts as valid.
Input: the diff in `goldens/review_standard_sample_diff.yaml`.

| File | What it is | Validator |
|---|---|---|
| `code-review-standard_run1.json` | The accepted response. | ✅ exit 0 |
| `code-review-standard_run1_broken.json` | A realistic first attempt that failed validation. | ❌ exit 1, 15 errors |
| `code-review-standard_run1_repaired.json` | `code-review-repair` applied to the broken output + the validator's complaint. | ✅ exit 0 |

## 1. Constrain

`prompts/code-review-standard.md` ends with a hard output contract — one JSON object,
exactly `issues` and `summary`, closed vocabularies for `severity` and `category`,
`message` under 280 characters, no markdown fences.

## 2. Validate

```bash
python3 work/validate/validate.py work/library/runs/code-review-standard_run1.json
```

```
OK: response matches schema
```

The broken attempt is the interesting one. It is *valid JSON* — the failure mode that
actually costs you in production, because `json.loads()` succeeds and the bug surfaces
three services downstream:

```bash
python3 work/validate/validate.py work/library/runs/code-review-standard_run1_broken.json
```

```
VALIDATION FAILED:
  <root>: Additional properties are not allowed ('reviewed_at' was unexpected)
  issues.0: Additional properties are not allowed ('confidence' was unexpected)
  issues.0.category: 'vulnerability' is not one of ['correctness', 'security', 'performance', 'style', 'testing']
  issues.0.line: '40' is not of type 'integer'
  issues.0.message: '...' is too long
  issues.0.severity: 'critical' is not one of ['blocker', 'major', 'minor', 'nit']
  issues.1.severity: 'high' is not one of ['blocker', 'major', 'minor', 'nit']
  issues.2.severity: 'high' is not one of ['blocker', 'major', 'minor', 'nit']
  issues.3.severity: 'high' is not one of ['blocker', 'major', 'minor', 'nit']
  issues.4.category: 'tests' is not one of ['correctness', 'security', 'performance', 'style', 'testing']
  issues.4.severity: 'high' is not one of ['blocker', 'major', 'minor', 'nit']
  issues.5.category: 'tests' is not one of ['correctness', 'security', 'performance', 'style', 'testing']
  issues.5.severity: 'low' is not one of ['blocker', 'major', 'minor', 'nit']
  issues.6.category: 'formatting' is not one of ['correctness', 'security', 'performance', 'style', 'testing']
  issues.6.severity: 'info' is not one of ['blocker', 'major', 'minor', 'nit']
```

Five distinct failure classes, all of them things a model does on an off day:
a **different severity vocabulary** (`critical`/`high`/`low`/`info`), a **near-miss category**
(`tests` for `testing`, `formatting` for `style`), a **stringly-typed number** (`"40"`),
**extra fields nobody asked for** (`confidence`, `reviewed_at`), and a **message that ran long**.

## 3. Self-repair

`prompts/code-review-repair.md` takes the broken output plus the validator text verbatim and
returns a corrected object. It is deliberately conservative: map to the nearest legal value,
never invent or delete a finding.

What it changed, and nothing else:

| Broken | Repaired | Rule applied |
|---|---|---|
| `"severity": "critical"` | `"blocker"` | nearest legal severity |
| `"severity": "high"` ×4 | `"major"` | nearest legal severity |
| `"severity": "low"` / `"info"` | `"minor"` / `"nit"` | nearest legal severity |
| `"category": "vulnerability"` | `"security"` | nearest legal category |
| `"category": "tests"` ×2 | `"testing"` | nearest legal category |
| `"category": "formatting"` | `"style"` | nearest legal category |
| `"line": "40"` | `40` | coerce type, do not invent |
| `"confidence": 0.95` | removed | `additionalProperties: false` |
| `"reviewed_at": "…"` | removed | `additionalProperties: false` |
| 511-char message | truncated at a sentence boundary (139 chars) | length limit, no paraphrase |

All seven findings survive, with their files, lines and wording intact. That is the property
worth having: the repair pass fixes the envelope, not the judgement.

```bash
python3 work/validate/validate.py work/library/runs/code-review-standard_run1_repaired.json
```

```
OK: response matches schema
```

## Note on severities after repair

`run1_repaired.json` grades the SQLAlchemy-2.x `ObjectNotExecutableError` finding as `major`
(mapped from `high`), while the accepted `run1.json` grades it `blocker`. That gap is real and
kept on purpose: the repair prompt is forbidden from re-judging severity, so a coarse input
vocabulary permanently loses that distinction. The fix belongs upstream — constrain the first
call — which is exactly why `code-review-standard` states the four-value vocabulary inline
instead of relying on the repair pass to clean up afterwards.
