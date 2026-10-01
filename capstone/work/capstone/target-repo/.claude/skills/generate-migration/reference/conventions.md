# Migration conventions (reference)

Fetched by the skill when it needs the full rules, rather than inlining all of this in
`SKILL.md`.

## Naming and numbering

- Filename: `NNNN_<snake_case_description>.sql`, `NNNN` zero-padded to 4 digits, strictly
  ascending, no gaps introduced on purpose.
- The number is derived by scanning the existing `migrations/` directory — never
  hand-picked. If two people scaffold a migration on parallel branches, the number
  collision is expected to surface as a merge conflict on the migrations directory
  listing, not be silently resolved by the tool.
- The slug describes the *change*, not the table alone: `add_orders_notes`, not `orders`.

## Append-only

- Once a migration file is merged, it is never edited again — not even to fix a typo in a
  comment. A mistake gets corrected by a *new* migration.
- A migration file scaffolded in this session but not yet merged can still be safely
  regenerated (that's what the idempotency check in `scripts/generate_migration.py` is
  for) — "append-only" is a merged-history guarantee, not a local-working-tree one.

## Rollback block (added for the capstone)

- Every migration ends with a marker line `-- ROLLBACK` followed by commented-out SQL that
  undoes the forward SQL exactly. For an add-column migration that is one line:
  `-- ALTER TABLE <t> DROP COLUMN IF EXISTS <c>;`
- The block stays commented out. The deploy pipeline never runs it; an operator runs it on an
  approved revert. That is why its `DROP COLUMN` is not a destructive-operation violation.
- Both directions carry `IF [NOT] EXISTS` so a half-applied deploy or revert can be re-run.
- `scripts/check_reversible.py` proves the claim mechanically: replaying
  before → forward → rollback must return the exact "before" schema.
- Do not put prose comment lines after the marker — every commented line after it is read as
  rollback SQL. Explanations go above the marker.

## One concern per migration

A migration should do one schema-shaped thing. Two situations come up often enough to name
explicitly:

- **Pure rename** (`RENAME COLUMN` / `RENAME TABLE`) is fine as a single migration on its
  own — it's a schema-only operation.
- **Rename + "update all references"** is *two* different kinds of change wearing one
  request: the schema rename (a migration) and updating application code that reads/writes
  the old column/table name (a regular code change, reviewed and shipped through the normal
  PR process, not through this skill). When a request bundles both, scaffold only the
  schema half and say explicitly that the code-reference update is a separate, non-migration
  change the requester still needs to make.

## What this skill does not do

- It does not run migrations against any database. It only writes the `.sql` file.
- It does not modify ORM models, application code, or existing migration files.
- It does not decide *whether* a schema change is a good idea — it scaffolds the file in
  the house format and applies the mechanical safety checks in
  `reference/destructive-operations.md`. A DBA/reviewer still reviews the actual SQL.

## Sanity checks before scaffolding

- Does the table referenced in the request exist in the current schema (visible from the
  most recent migration file, or from an ORM model if the repo has one)? If not, say so
  instead of guessing a schema that doesn't exist yet.
- Is the requested column type/nullability internally consistent with the request (e.g. "a
  required column with no default" on a table that already has rows is a real production
  hazard — flag it, don't silently add `NOT NULL` with no `DEFAULT`).
