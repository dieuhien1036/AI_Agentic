# Capstone — "Add a column" → reversible migration, verified

**Sample Task A** from the brief, built on the `payments-api` repo from Module 1.

A developer says *"add a notes column to orders, it's optional"*. The workflow:

1. **parses** the sentence into a structured spec (table, column, type, nullability, default),
   or asks clarifying questions if the request is vague;
2. **generates** `migrations/000N_add_<table>_<column>.sql` with the forward `ALTER` and an
   exact rollback in a commented `-- ROLLBACK` block, after checking against the real
   migration history that the table exists and the column **does not**, and that the
   change follows the house rules (no `NOT NULL` without a default on a live table, money is
   `NUMERIC(12, 2)`, `TIMESTAMPTZ`, `JSONB`, no destructive forward SQL);
3. **verifies** that the file is reversible, using a deterministic round-trip replay
   (before → forward → rollback must equal before) plus an independent verifier subagent on
   a different model, and returns **GO / NO-GO** with evidence.

It never applies a migration. It stops at a reviewable file and a verdict.

## Brief checklist

| Brief requirement | Where |
|---|---|
| Pillar 1: context file | [target-repo/CLAUDE.md](target-repo/CLAUDE.md) §9, [target-repo/AGENTS.md](target-repo/AGENTS.md) §9 |
| Pillar 2: reusable prompt + golden case | [prompts/parse-migration-request.md](prompts/parse-migration-request.md); primary golden [evals/goldens/add_orders_notes.json](evals/goldens/add_orders_notes.json) (+4 more); [evals/run_eval.py](evals/run_eval.py) |
| Pillar 3: custom skill (SKILL.md + supporting files) | [target-repo/.claude/skills/generate-migration/](target-repo/.claude/skills/generate-migration/SKILL.md) |
| Pillar 4: subagents (pipeline of 2) | [migration-request-parser](target-repo/.claude/agents/migration-request-parser.md) → skill → [migration-verifier](target-repo/.claude/agents/migration-verifier.md) |
| Driver / orchestration code | [driver/run_workflow.py](driver/run_workflow.py) |
| README: what / install / run | this file: sections Architecture, Install, Run |
| One-paragraph reflection | [Reflection](#reflection--what-id-build-next) at the end of this file |
| One-slide overview | [SLIDE.md](SLIDE.md) |
| Task A: file `migrations/000N_<name>.sql` with ALTER + rollback in a comment block | [templates/add_column.sql.tpl](target-repo/.claude/skills/generate-migration/templates/add_column.sql.tpl); real generated output: [examples/0002_add_orders_notes.sql](examples/0002_add_orders_notes.sql) |
| Task A: validate the column doesn't already exist | `rule_violations()` in [generate_migration.py](target-repo/.claude/skills/generate-migration/scripts/generate_migration.py); case `users_email_exists` |
| Task A: verifier confirms it's reversible | [check_reversible.py](target-repo/.claude/skills/generate-migration/scripts/check_reversible.py) + `migration-verifier`; cases `bad_rollback_injected`, `rubber_stamp_verifier` |
| Reuse of Modules 1–4 | [Reused from Modules 1–4](#reused-from-modules-14) |

## Architecture

```
 developer request
        │
        ▼
 ┌──────────────────────────┐  prompt: prompts/parse-migration-request.md   (pillar 2)
 │ migration-request-parser │  model: haiku · tools: Read, Glob             (pillar 4)
 │        subagent          │──► spec JSON ── validated against schemas/migration_spec.schema.json
 └──────────────────────────┘          │
        │ needs_clarification? ──► STOP, ask the developer
        ▼
 ┌──────────────────────────┐  .claude/skills/generate-migration/          (pillar 3)
 │ generate-migration skill │  generate_migration.py replays migrations/ (schema_state.py)
 │  (deterministic script)  │  exit 4 = column exists / rule broken ──► STOP, no file written
 └──────────────────────────┘──► migrations/000N_<slug>.sql  (forward + -- ROLLBACK block)
        │
        ▼
 ┌──────────────────────────┐  check_reversible.py: round-trip replay  ── deterministic GATE
 │   migration-verifier     │  + rule review against CLAUDE.md §9          (pillar 4)
 │       subagent           │  model: sonnet (≠ parser) · read-only
 └──────────────────────────┘──► GO / NO-GO JSON (schemas/verifier_verdict.schema.json)
                                  mechanical FAIL always wins over an LLM "GO"

 CLAUDE.md / AGENTS.md §9 route "add a column" requests into this pipeline and hold the rules
 that the skill and the verifier both enforce.                                 (pillar 1)
```

| Pillar | What carries it | Where |
|---|---|---|
| 1. Context file | `CLAUDE.md` + `AGENTS.md`, new §9 "Schema changes — the add-column workflow": routing, steps, migration rules | [target-repo/CLAUDE.md](target-repo/CLAUDE.md), [target-repo/AGENTS.md](target-repo/AGENTS.md) |
| 2. Reusable prompt + eval | Request → spec prompt, 5 goldens (primary: `add_orders_notes`), two-layer eval harness | [prompts/](prompts/), [evals/](evals/) |
| 3. Custom skill | `generate-migration`: SKILL.md, generator, round-trip checker, shared schema replayer, template, 3 reference docs | [target-repo/.claude/skills/generate-migration/](target-repo/.claude/skills/generate-migration/) |
| 4. Subagents | `migration-request-parser` (haiku) → skill → `migration-verifier` (sonnet) | [target-repo/.claude/agents/](target-repo/.claude/agents/) |
| Orchestration | Driver with schema-validated handoffs, offline/live modes, 7 regression cases | [driver/](driver/), [schemas/](schemas/), [runs/](runs/) |

### Key design choices

- **Deterministic where possible, LLM where necessary.** Language → spec is the LLM's job.
  Numbering, existence checks, rule checks and the reversibility proof are scripts. The LLM
  verifier can add blockers but **cannot overrule** a failed mechanical check (the
  `rubber_stamp_verifier` case proves this).
- **The parser records, it does not judge.** If a developer explicitly asks for `FLOAT` on a
  money column, the parser passes `FLOAT` through and the generator refuses with the reason.
  A parser that silently "fixed" it would hide the disagreement from the developer. A golden
  (`orders_discount_float`) protects this rule.
- **Existence is checked against the migrations, not against the model's memory.**
  `schema_state.py` replays every `migrations/*.sql` file into an in-memory schema, so
  "column already exists" comes from the real history.
- **The rollback is not covered by the destructive guard.** It sits in a commented block that
  only runs on an approved revert. The generator scans only the forward SQL. The verifier
  checks that the rollback drops *exactly* the added column.
- **Independent verification.** The verifier runs on a different model from the parser and
  sees only the file, the earlier migrations and the mechanical-check output. It never sees
  the parser's reasoning.
- **One source of truth for the prompt.** The subagent embeds the prompt verbatim.
  `driver/sync_agents.py` regenerates it, and the eval fails if the two drift apart.

### Reused from Modules 1–4

| From | Reused as |
|---|---|
| Module 1: `payments-api` + `CLAUDE.md` / `AGENTS.md` | Target repo and context files, extended with §9 |
| Module 2: prompt library + two-layer eval harness (prompt contract + output checks, offline fixtures) | Same design for `evals/run_eval.py` |
| Module 3: `scaffold-migration` skill (numbering, append-only, idempotency, destructive guard, `reference/` docs) | Grown into `generate-migration`. `conventions.md` and `destructive-operations.md` are carried over and updated |
| Module 4: verifier subagent + hardened driver (schema-validated handoffs, one repair retry, no partial output) | `migration-verifier` and `driver/run_workflow.py` |

## Install

Requirements: Python 3.9+. The skill scripts use only the standard library. If
`jsonschema` is installed, the driver and eval use it for full schema validation; otherwise
they fall back to a required-keys check.

**Claude Code (interactive):** open `target-repo/` as the project. The skill
(`.claude/skills/generate-migration/`) and both subagents (`.claude/agents/`) are already in
place, and `CLAUDE.md` §9 tells Claude when to use them. To use them in another repo, copy
`.claude/skills/generate-migration/` and `.claude/agents/migration-*.md` into that repo's
`.claude/` and add the §9 section to its `CLAUDE.md`.

**Copilot / other agents:** `AGENTS.md` §9 lists the same steps as plain script calls.

## Run

All commands are run from this folder (`work/capstone/`).

```bash
python driver/run_workflow.py --list
```

```bash
python driver/run_workflow.py --all
```

`--all` runs the regression suite: all 7 cases, each on a scratch copy of `migrations/`, with
the expected outcome checked. Traces are written to `runs/<case>.json`.

```bash
python driver/run_workflow.py --case add_orders_notes
```

This writes `target-repo/migrations/0002_add_orders_notes.sql` for real. Run it again and it
is a no-op. Delete the file to reset.

```bash
python evals/run_eval.py
```

This is the prompt eval: 5 goldens plus the agent-sync check.

**Inside Claude Code** (in `target-repo/`), just ask: *"Add a notes column to orders, optional
free text."* Claude follows §9 of `CLAUDE.md`: it calls the parser subagent, then the skill,
then the verifier subagent.

**Live mode** (needs the `claude` CLI on PATH). This calls the two subagents headless through
`claude -p`, using each agent's `model:`:

```bash
python driver/run_workflow.py --live --request "orders need a gift_message, optional text"
```

```bash
python evals/run_eval.py --live --record
```

### Cases

| Case | Shows | Expected |
|---|---|---|
| `add_orders_notes` | happy path, plain-English type | GO, `0002_add_orders_notes.sql` |
| `add_orders_cancelled_at` | camelCase → snake_case, inferred `TIMESTAMPTZ`, assumptions surfaced | GO |
| `users_email_exists` | **"validate the column doesn't already exist"** | stopped at generate, exit 4 |
| `orders_discount_float` | money-as-float + `NOT NULL` without default, both reasons listed | stopped at generate, exit 4 |
| `vague_request` | parser asks instead of guessing | stopped at parse |
| `bad_rollback_injected` | hand-written file whose rollback drops the wrong column | NO-GO |
| `rubber_stamp_verifier` | *simulated* lazy verifier says GO on that file; the mechanical gate overrules it | NO-GO |

### Demo script (≈5 min)

1. Lead with the trust story: `--case bad_rollback_injected`, then `--case rubber_stamp_verifier`.
   A plausible-looking migration is not reversible, and even a verifier that says "GO"
   cannot get it through.
2. Happy path: `--case add_orders_notes` and show the generated file with its rollback block.
   Run it again to show the no-op.
3. Refusals: `--case users_email_exists` and `--case orders_discount_float`.
4. The prompt has tests: `python evals/run_eval.py`.

## Honesty notes

- **The recorded LLM responses are not live model output.** These are
  `evals/fixtures/*.txt` and `driver/fixtures/verifier_*.txt`. The `claude` CLI was not
  installed on the build machine, so I wrote them in this session as the responses the prompts
  specify. `verifier_rubber_stamp_SIMULATED.txt` is deliberately wrong, as its name says. To
  replace the fixtures with real runs, use `--live --record`.
- **Live mode (`--live`) is implemented but has not been run here** for the same reason.
  Everything else ran for real: the skill scripts, the round-trip checker, the driver's
  schema validation, all 7 cases and the eval, including negative tests. Those tests showed
  that a weakened prompt, a drifted agent file and a fenced response each fail the eval.
- `schema_state.py` models only the DDL subset this repo uses: create/drop table, add/drop
  column, create/drop index. Any other statement is reported as *unsupported*, so no
  reversibility claim is made for it. It is not a SQL engine. The real check is still a
  dry run against Postgres in CI (see the reflection below).

## Layout

```
README.md                         this file (incl. reflection)
SLIDE.md                          one-slide overview
examples/0002_add_orders_notes.sql  a migration produced by the skill (golden request)
target-repo/                      payments-api (Module 1), the repo the workflow runs in
  CLAUDE.md, AGENTS.md            context files, §9 = this workflow
  migrations/0001_initial.sql
  .claude/skills/generate-migration/
    SKILL.md
    scripts/generate_migration.py  spec -> validated migration file
    scripts/check_reversible.py    deterministic round-trip check
    scripts/schema_state.py        migration replayer shared by both
    templates/add_column.sql.tpl
    reference/{conventions,type-rules,destructive-operations}.md
  .claude/agents/
    migration-request-parser.md    pillar-4 subagent #1 (embeds the prompt)
    migration-verifier.md          pillar-4 subagent #2
prompts/parse-migration-request.md the reusable prompt
evals/goldens/*.json               5 golden cases (primary: add_orders_notes)
evals/fixtures/*.txt               recorded parser responses
evals/run_eval.py                  prompt eval
schemas/*.schema.json              handoff contracts
driver/run_workflow.py             orchestrator
driver/contracts.py                shared validation + `claude -p` call
driver/sync_agents.py              prompt -> parser subagent sync
driver/cases.json, driver/fixtures/  demo/regression cases
runs/*.json                        traces from the last `--all` run
```

## Reflection — what I'd build next

With another session, I would first replace the in-memory replayer as the final authority with
a **real Postgres round trip in CI**: start `postgres:15` in a testcontainer, apply all
migrations, apply the new forward SQL, apply the rollback, and diff `pg_dump --schema-only`
against the "before" dump. The Python replayer would stay as the fast pre-check. Second, I would
record real fixtures with `--live --record` on two different models and add the parser eval
to CI, the same way Module 2 wired `--strict` into a workflow, so that prompt edits are
regression-tested. Third, I would widen the scope one operation at a time (add index, then add
a foreign key with `NOT VALID` + `VALIDATE`), each with its own golden and round-trip case.
I would also add a fourth subagent that drafts the *matching* `OrderRow` / `app.types.Order`
change as a separate PR, so the "one concern per migration" rule holds while the developer
still gets both halves of the change.
