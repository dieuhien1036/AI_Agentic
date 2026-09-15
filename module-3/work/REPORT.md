# REPORT — scaffold-migration

**Task family:** migration-scaffold — generate a database migration file in the right
format.

**Platform:** Claude Code. Installed repo-scoped: `demo-repo/.claude/skills/scaffold-migration/`
(a copy of `scaffold-migration/`, installed exactly per that skill's own `README.md`
instructions, against a fixture repo — `demo-repo/` — built for this lab so the scripts
could be run against a real `migrations/` directory rather than described only in the
abstract).

## Scenario scoring

| Scenario | Result | Rationale |
|---|---|---|
| Happy path | **PASS** | Correct file (`0002_add_orders_notes.sql`), correct `ALTER TABLE`, correct number, `0001_initial.sql` untouched — matches `SCENARIOS.md` expectation exactly. See [runs/run1_happy.md](runs/run1_happy.md). |
| Edge case | **PASS** | Schema-only half (`RENAME COLUMN`) was scaffolded; the "update all references" half was explicitly named as out-of-scope and flagged back to the user for confirmation, rather than silently attempted or silently dropped — matches `SCENARIOS.md` expectation. See [runs/run2_edge.md](runs/run2_edge.md). |
| Failure case | **PASS** | `DROP TABLE users` was blocked before any file was written; the message named the exact pattern (`DROP TABLE`) and the exact reason it's dangerous (primary entity, referenced by `orders.user_id`) rather than a generic warning; confirmed zero files created (no crash, no partial state). See [runs/run3_failure.md](runs/run3_failure.md). |

## Discovery contract

6/6 positive and 6/6 negative on the required round; a second, harder adversarial round
(paraphrases without the word "migration," and prompts containing "migration" for the
wrong verb) also scored 4/4. **No description revision was needed** — see
[discovery-contract/ITERATION_LOG.md](discovery-contract/ITERATION_LOG.md) for the full
method (independent subagent judging on name+description alone, not self-graded) and every
prompt/result.

## What would make this fail in a real repo (known limitations, not covered by PASS above)

- The destructive-operation guard is pattern-based (`DROP TABLE`, `TRUNCATE`, etc.). A
  destructive change phrased to avoid those exact SQL keywords (e.g. an `UPDATE` that
  zeroes out every row's data) would not be caught mechanically — the skill instructions
  rely on the agent's own judgment for anything the script doesn't pattern-match, which is
  weaker than the mechanical guard demonstrated in Run 3.
- `find_existing_for_slug`'s idempotency check is a substring match on the rendered body,
  not a semantic diff — two SQL statements that are logically identical but formatted
  differently (extra whitespace, different statement order) would be treated as a conflict
  (exit 3) rather than recognized as the same change.
