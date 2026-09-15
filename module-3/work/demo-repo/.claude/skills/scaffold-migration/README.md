# scaffold-migration

## Task family

Generates a new, correctly-numbered, append-only SQL migration file in a project's
`migrations/` directory, in that project's house format. It does **not** run migrations,
edit existing ones, touch application/ORM code, or answer general SQL questions — see
`SKILL.md`'s negative scope.

## Who'd use it

Anyone adding a schema change to a repo that follows an append-only, numbered-SQL-file
migration convention (the pattern used by this lab's `payments-api`-style repos, and common
across many backend teams: Rails-style, Alembic-adjacent-but-raw-SQL, etc.). Saves the
"what's the next number, what's the exact header comment, did I typo the filename pattern"
busywork, and — more importantly — enforces two safety rules mechanically instead of relying
on the requester to remember them:

- a request that bundles a schema change with an application-code change gets split, not
  silently done in full or silently done half-right;
- a destructive operation (`DROP TABLE`, `TRUNCATE`, unconditional `DELETE`, `DROP COLUMN`)
  never gets scaffolded without an explicit, separate human sign-off.

## Install

**Claude Code**, repo-scoped (recommended, so the skill's `reference/` conventions can
reasonably assume "the current repo"):

```bash
mkdir -p .claude/skills
cp -r scaffold-migration/ .claude/skills/scaffold-migration/
```

**Claude Code**, user-scoped (available in every project):

```bash
cp -r scaffold-migration/ ~/.claude/skills/scaffold-migration/
```

**Copilot:** copy the `scaffold-migration/` folder into your workspace's configured skills
path and register it in workspace settings (path varies by Copilot configuration).

After installing, start a new session in the target repo and confirm it's picked up by
mentioning a migration task — see `discovery-contract/ITERATION_LOG.md` in the lab
submission for the exact prompts used to verify trigger reliability.

## Requirements

- Python 3 on PATH (for `scripts/scaffold_migration.py`; standard library only, no
  dependencies to install).
- A `migrations/` directory (or equivalent — point `--migrations-dir` at it) containing
  `NNNN_*.sql` files.

## Layout

```
SKILL.md                          # the contract: when to invoke, steps, failure modes
scripts/scaffold_migration.py     # idempotent: numbers, writes, and safety-checks the file
templates/migration.sql.tpl       # the house header format, with {FILENAME}/{SQL_BODY}
reference/conventions.md          # naming, numbering, append-only policy, split-concern rule
reference/destructive-operations.md   # what's destructive, and the required sign-off flow
```
