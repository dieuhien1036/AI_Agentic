---
name: scaffold-migration
version: 0.1.0
description: |
  Generates a new append-only SQL database migration file in the project's
  migrations/ directory, numbered and named per house convention.
  Use when the user asks to add, create, or generate a database migration —
  including phrases like "add a migration", "create a migration for", "scaffold
  a schema change", "new migration to add a column/table/index".
  Do NOT use for running or applying existing migrations, writing ad-hoc SQL
  queries, editing application/ORM code, or explaining what a migration is.
license: Internal
---

# Scaffold Migration

## When to invoke

The user wants a *new migration file* written to disk in this repo's convention — not a
query run against a database, not a change to existing migrations, not application code.

## Steps

1. Locate the repo's migrations directory (usually `migrations/`). If none exists, stop
   and ask where migrations live — do not invent a directory.
2. Read the most recent 1–2 migration files to infer the current schema for the table(s)
   involved. If the referenced table/column doesn't appear to exist yet, say so instead of
   guessing.
3. Draft the SQL body for the requested change.
4. Check the body against `reference/destructive-operations.md`. If it matches a
   destructive pattern, stop per that file's process — do not proceed to step 5.
5. Run `scripts/scaffold_migration.py --migrations-dir <path> --name <slug> --body-file -`,
   piping the SQL body in. Let the script assign the number and write the file — do not
   hand-pick a filename or number.
6. If the request bundles a schema change with something else (e.g. "rename and update all
   references"), read `reference/conventions.md`'s "One concern per migration" section:
   scaffold only the schema half, and say explicitly what wasn't included and why.
7. Report the created file path back to the user. Do not run the migration against any
   database — this skill only writes the file.

## Conventions

- One concern per migration file (see `reference/conventions.md`).
- Never hand-edit an existing migration file — a fix is always a new file.
- Numbering and idempotency are handled by the script, not by hand.

## Failure modes

- Destructive SQL pattern detected → stop, explain exactly what matched, point to
  `reference/destructive-operations.md`. No file written.
- Migrations directory not found → stop and ask; do not create one speculatively.
- Referenced table doesn't appear in existing migrations → say so; don't guess a schema.
- Script exits non-zero for any other reason → surface its stderr verbatim; do not retry
  silently or fall back to writing the file by hand.

## Reference

- `reference/conventions.md` — naming, numbering, append-only policy, split-concern rule.
- `reference/destructive-operations.md` — what counts as destructive and the sign-off
  process required before scaffolding one.
