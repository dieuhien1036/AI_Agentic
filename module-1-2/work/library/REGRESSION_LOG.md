# Regression log — Step 3

Purpose: prove the golden set has teeth. Break a prompt on purpose, watch `--strict` go red,
name the golden that caught it, restore, confirm green.

Environment: Windows 10, Python 3.9.0, `pyyaml` + `jsonschema`, `EVAL_MODE=offline`.
All commands run from `work/library/`.

---

## 0. Baseline — green

```
$ python3 harness/run_eval.py --strict -v
eval mode: offline  |  goldens: 7

[PASS] review_blockers_only_mixed_severity    ok
[PASS] review_clean_diff_no_issues            ok
[PASS] review_malformed_diff_truncated        ok
[PASS] review_security_focus_auth_change      ok
[PASS] review_standard_multiple_files         ok
[PASS] review_standard_sample_diff            ok
[PASS] review_standard_style_issue            ok

7/7 passed (100%); threshold 80%
EXIT=0
```

---

## 1. Regression A — strip a constraint from a prompt (layer A)

**The change.** In `prompts/code-review-clean-diff.md`, deleted the rule that makes an empty
finding list a first-class answer and replaced it with plausible-sounding, ambiguous wording —
the kind of edit that arrives in a real PR titled "make the reviewer more helpful":

```diff
-version: 1.0.0
+version: 1.1.0-regression
@@
-- **Returning an empty `issues` array is correct and expected when the diff follows the
-  checklist.** Do not manufacture a finding, a "consider…" suggestion, or a hypothetical
-  future problem to fill the list.
+- Be thorough and helpful. Surface anything a reviewer might want to think about,
+  including suggestions and possible future concerns.
```

Nothing else was touched. The output contract, the checklist, and the `CLEAN:` rule all stayed.

**Result — red:**

```
$ python3 harness/run_eval.py --strict -v
eval mode: offline  |  goldens: 7

[PASS] review_blockers_only_mixed_severity    ok
[FAIL] review_clean_diff_no_issues            prompt lost constraint: 'empty `issues` array is correct and expected'
                                              prompt lost constraint: 'Do not manufacture a finding'
[PASS] review_malformed_diff_truncated        ok
[PASS] review_security_focus_auth_change      ok
[PASS] review_standard_multiple_files         ok
[PASS] review_standard_sample_diff            ok
[PASS] review_standard_style_issue            ok

6/7 passed (86%); threshold 80%
STRICT: 1 golden(s) failing — blocking.
EXIT=1
```

**Caught by:** `goldens/review_clean_diff_no_issues.yaml`, via its `prompt_must_contain` entries
`empty \`issues\` array is correct and expected` and `Do not manufacture a finding`.

**The uncomfortable bit worth writing down.** 86% is *above* the 80% threshold. A pass-rate gate
alone would have waved this through. What blocked it was `--strict`, which requires every golden
to pass. That is why CI runs `--strict` and the percentage is only a dashboard number.

---

## 2. Regression B — the degraded output itself (layer B)

Layer A catches a prompt edit even in offline replay mode, because it reads the prompt file.
But replay means the recorded output does not move when the prompt does, so layer A on its own
would let a *live* degradation through unnoticed. Regression B checks the other half: with
regression A still in place, `fixtures/review_clean_diff_no_issues.txt` was replaced with what
the weakened prompt actually produces — two manufactured findings (a speculative Redis cache, a
missing docstring) and a summary that no longer commits to anything.

**Result — red, and louder:**

```
$ python3 harness/run_eval.py --strict -v
eval mode: offline  |  goldens: 7

[PASS] review_blockers_only_mixed_severity    ok
[FAIL] review_clean_diff_no_issues            prompt lost constraint: 'empty `issues` array is correct and expected'
                                              prompt lost constraint: 'Do not manufacture a finding'
                                              missing substring: 'CLEAN:'
                                              forbidden substring present: '"severity"'
                                              expected exactly 0 issues, got 2
                                              summary does not start with 'CLEAN:'
[PASS] review_malformed_diff_truncated        ok
[PASS] review_security_focus_auth_change      ok
[PASS] review_standard_multiple_files         ok
[PASS] review_standard_sample_diff            ok
[PASS] review_standard_style_issue            ok

6/7 passed (86%); threshold 80%
STRICT: 1 golden(s) failing — blocking.
EXIT=1
```

**Caught by:** the same golden, now on four independent output checks — `expected_substrings`,
`forbidden_substrings`, `json_checks.issues_count_exactly`, `json_checks.summary_startswith`.

Four checks firing on one behavioural change is redundancy on purpose. One of them could be
loosened by a future edit and the golden would still hold.

---

## 3. Restore — green again

Both files reverted from their `.orig` copies (prompt back to `version: 1.0.0`, fixture back to
the empty-issues response).

```
$ python3 harness/run_eval.py --strict -v
eval mode: offline  |  goldens: 7

[PASS] review_blockers_only_mixed_severity    ok
[PASS] review_clean_diff_no_issues            ok
[PASS] review_malformed_diff_truncated        ok
[PASS] review_security_focus_auth_change      ok
[PASS] review_standard_multiple_files         ok
[PASS] review_standard_sample_diff            ok
[PASS] review_standard_style_issue            ok

7/7 passed (100%); threshold 80%
EXIT=0
```

Final state: **7/7, exit 0**. No `.orig` files remain in the tree.

---

## What this exercise actually taught

1. **A percentage threshold is not a gate.** 86% passed the threshold and still had a real
   regression in it. Gate on `--strict`; report the percentage.
2. **Offline replay needs a prompt-contract layer.** With fixtures replayed, editing a prompt
   changes nothing the output checks can see. Without `prompt_must_contain`, regression A would
   have been completely invisible — green CI on a genuinely worse prompt, which is the exact
   "tests that are just for show" failure the lab warns about.
3. **The negative case is the one that rots.** `review_clean_diff_no_issues` — the golden whose
   expected answer is *nothing* — is the one that caught this. A golden set made only of
   "find the bug" cases would have stayed green through both regressions.
