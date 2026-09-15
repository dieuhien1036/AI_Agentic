# Rationale — code review against a checklist

## Task family

**Code review against a checklist**, targeting the `payments-api` repo from Step 1.

Picked over test generation and doc generation for three reasons:

1. **It has a natural hard schema.** A review is a list of findings with a severity, a category,
   a file, a line. That is a record, not prose — so `review.schema.json` constrains something
   real rather than being bolted onto free text to satisfy the exercise. Test generation outputs
   Python source; you can check it compiles, but "is this a *good* test" resists a schema.
2. **It closes the loop with Step 1.** The checklist inside every prompt *is* `CLAUDE.md` §3/§4,
   restated as review criteria. The context file tells the agent how to write the code; the
   prompt library tells it how to catch code that ignored the context file. Same rules, both
   directions.
3. **The failure modes are well known and easy to write goldens for.** Reviewers invent findings
   to look useful, inflate severity, hallucinate on truncated input, and drown blockers in nits.
   Four of the seven goldens exist specifically to pin one of those down.

## The five prompts

| # | Prompt | Axis | Covers |
|---|---|---|---|
| 1 | `code-review-standard` | happy path, full coverage | The reference reviewer. Whole checklist, all four severities, strict JSON. This is the schema-constrained one. |
| 2 | `code-review-clean-diff` | **negative case** | A diff with nothing wrong. Correct answer is `issues: []` and a `CLEAN:` summary. Guards the "invent a finding to look useful" failure. |
| 3 | `code-review-malformed-diff` | **error case** | Truncated / empty / unparsable input. Must refuse with `MALFORMED_INPUT:` instead of hallucinating findings about code it cannot see. |
| 4 | `code-review-security-focus` | **scope narrowing** | Security only, with the repo's protected-path rule wired in: any `app/auth/` change is a blocker and the summary must start `ESCALATE:`. |
| 5 | `code-review-blockers-only` | **precision over recall** | Merge gate on a release branch. Only `blocker`/`major` — every nit dropped, no severity inflation, summary starts `BLOCK:` or `MERGE:`. |

Plus `code-review-repair` — the sixth file, not one of the five. It takes an invalid output and
the validator's complaint and returns a corrected object.

**Why these five axes.** They are not five phrasings of the same request; they are the five
situations the same task lands in. 1 is "it works". 2 and 3 are the two ways the *input* can be
unusual (nothing to report / nothing readable). 4 and 5 are the two ways the *caller's needs*
can be unusual (I only care about one category / I only care above one severity). Writing them
forced two rules into the library I would not have thought of from the happy path alone: that an
empty result must be first-class, and that a refusal must still be valid JSON.

## The golden set

- **7 cases**, one per prompt plus three extra on `code-review-standard`, which carries the most
  production traffic and deserves the most coverage.
- **Source: synthetic, modelled on real failure modes.** Every diff is a plausible PR against
  this repo, and each one violates rules `CLAUDE.md` actually states. `review_standard_sample_diff`
  embeds the lab's own `starter/structured_output/sample.diff` verbatim.
- **Seeded with distractors on purpose.** `review_blockers_only_mixed_severity` contains a typo
  in a docstring, an import in the wrong place, and a long line — all irrelevant to a merge gate.
  A prompt that surfaces them fails the golden, because noise in a merge gate is a defect.
- **What a regression looks like here:** the clean-diff prompt starts returning a "consider
  caching this" suggestion. Nothing is *wrong* in the output — it is well-formed, schema-valid,
  and superficially helpful. It is a regression because the reviewer no longer distinguishes
  "this diff is fine" from "this diff has issues", and a caller downstream that gates on
  `len(issues) == 0` silently stops merging anything. Demonstrated in `REGRESSION_LOG.md` §2.

## What the harness measures

Two layers, both required to pass:

**Layer A — prompt contract** (`prompt_must_contain` in each golden, checked against the prompt
file on disk): frontmatter completeness, the `{INPUT}` placeholder, and the specific constraints
that golden exists to protect. A prompt edit that removes a constraint fails here.

**Layer B — output**: JSON Schema validation (draft-07, `review.schema.json`), plus
`expected_substrings`, `forbidden_substrings`, and structural `json_checks` —
`issues_count_exactly` / `_at_least` / `_at_most`, `severities_only`, `categories_only`,
`severities_include`, `categories_include`, `summary_startswith`, `summary_contains`, and
`issue_must_match` for "there must be a blocker in *this* file about *that*".

**Why layer A exists at all.** The harness runs offline by default: `call_agent()` replays the
recorded response in `fixtures/<id>.txt`, so CI is deterministic, needs no API key, and cannot
be flaked by a model update. The cost of that choice is that editing a prompt does not move the
recorded output — so with layer B alone, CI would stay green through an arbitrarily bad prompt
edit. Layer A is what makes offline replay honest. `REGRESSION_LOG.md` demonstrates both layers
firing.

**Pass threshold: 100% under `--strict`**, with the 80% rate printed as a dashboard number.
The lab asks for >80%; the harness reports it, but CI gates on `--strict` (every golden passes).
`REGRESSION_LOG.md` §1 is the argument: the regression run scored **86%** — comfortably over the
threshold — with a real defect in it. A percentage is a trend line, not a gate.

**Current state: 7/7 (100%), `--strict` exit 0.**

## What's not yet good enough

- **Offline replay is not a live eval.** Fixtures are recorded outputs; `call_agent_live()` is
  deliberately unimplemented so CI cannot depend on a model. That means the suite verifies
  "the prompt still carries its constraints and the recorded output still satisfies the golden",
  not "the current model still produces that output". Layer A narrows the gap; it does not close it.
- **Substring and structural checks, no semantic scoring.** A finding worded well and a finding
  worded badly score the same if both contain `"f-string"`. An LLM-judge rubric over the
  `message` field is the obvious next move, and its own reliability problem.
- **Seven goldens is thin.** One case per prompt is enough to catch a gross regression, not a
  subtle drift in tone or severity calibration.
- **The `nit`/`minor` boundary is undefined.** `code-review-blockers-only` drops both, so the
  distinction is untested — two prompts could disagree about it forever and the suite stays green.
- **No cost or latency budget.** Nothing in the harness notices if a prompt doubles in length.

## What I'd do next

One concrete step: wire `call_agent_live()` to the Anthropic SDK behind `EVAL_MODE=live`, run it
nightly on a schedule (not on PRs), and diff the live output against the recorded fixture. PRs
stay fast and deterministic; the nightly job answers the question replay cannot — "did the model
drift under a prompt nobody touched?" — and opens a PR with the regenerated fixture when it did,
so a model change arrives as a reviewable diff instead of a surprise.

---

## Reflection — what I'd do differently with another session

I built the golden set after writing the prompts, and it shows: the goldens mostly assert what
the prompts already said, which is a comfortable way to score 7/7 and a weak way to find bugs.
Next time I would write the goldens **first**, from real reviews the team has already argued
about — including the ones where two reviewers disagreed — and let the prompts be whatever makes
those pass. I would also spend the time I put into a sixth prompt variation on running each
existing prompt five times instead of once, because a single sampled run told me nothing about
variance, and variance is the thing that actually bites in production. The most useful thing I
learned came from the part of the lab I nearly rushed: the regression at **86%** sailing over an
80% threshold. I had written that threshold myself, an hour earlier, believing it meant
something. Step 4 taught the same lesson from the other side — the one dimension where the
with/without runs came out identical (test location) is a line in `CLAUDE.md` that is pure
decoration, and I would not have known which line to delete without running the comparison.
Both halves of the day came down to the same habit: **check that the thing you built to catch
problems can actually catch one.**
