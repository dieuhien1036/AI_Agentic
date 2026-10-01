---
name: generate-migration
version: 0.2.0
description: |
  Writes a new add-column SQL migration — forward ALTER plus an exact rollback in a
  commented ROLLBACK block — into this repo's migrations/ directory, after checking the
  column does not already exist and the change follows the house schema rules.
  Use when a developer asks to add a column or field to a table ("add column X to table Y",
  "we need a notes field on orders", "store cancelled_at on orders"), normally with a spec
  from the migration-request-parser subagent.
  Do NOT use for dropping or renaming columns, creating tables or indexes, applying or
  running migrations, editing existing migration files, or changing ORM/application code.
license: Internal
---

# Generate migration (add column, with rollback)

Grown from the Module 3 `scaffold-migration` skill: same numbering, append-only and
destructive-operation rules, plus a structured spec as input, schema validation against the
existing migrations, and a mandatory rollback block.

## When to invoke

A developer wants one new column on one existing table, written as a migration file. Anything
else (drop, rename, new table, index, data backfill) is out of scope — say so and stop.

## Inputs

A spec JSON matching `../../../../schemas/migration_spec.schema.json` (in the capstone root),
normally produced by the `migration-request-parser` subagent:

```json
{"status": "ok", "operation": "add_column", "table": "orders", "column": "notes",
 "type": "TEXT", "nullable": true, "default": null, "slug": "add_orders_notes",
 "request": "Add a notes column to orders, optional free text"}
```

If you only have the developer's sentence, delegate to `migration-request-parser` first. If
the spec has `"status": "needs_clarification"`, ask the developer its questions — do not fill
the gaps yourself.

## Steps

1. Save the spec to a temp file (or pipe it on stdin with `--spec -`).
2. Preview: `python .claude/skills/generate-migration/scripts/generate_migration.py
   --migrations-dir migrations --spec <spec.json> --dry-run`.
3. Write: the same command without `--dry-run`. Let the script choose the number and file
   name. Never write or edit the `.sql` file by hand, and never retry with a modified spec
   that you invented to get past a refusal.
4. On exit code `0`, hand the created path to the `migration-verifier` subagent. Report its
   verdict to the developer as-is.
5. On any non-zero exit code, show the script's stderr verbatim and stop (see Failure modes).

## Rules the script enforces

Full text in `reference/type-rules.md` and `reference/conventions.md`:

- The table must exist and the column must not, judged by replaying `migrations/`.
- `NOT NULL` needs a `DEFAULT` on an existing table.
- Money-named columns are `NUMERIC(12, 2)`; timestamps `TIMESTAMPTZ`; blobs `JSONB`; the type
  must be on the allowlist.
- Forward SQL is `ADD COLUMN IF NOT EXISTS`; the rollback is `DROP COLUMN IF EXISTS` in a
  commented `-- ROLLBACK` block.
- No destructive statement in the forward SQL (`reference/destructive-operations.md`).

## Failure modes

| Exit | Meaning | What you do |
|---|---|---|
| 0 + `NO-OP:` | identical migration already exists | Tell the developer which file; nothing new. |
| 1 | malformed spec / missing dir | Show stderr. Fix the spec only if the fix is mechanical (e.g. JSON syntax); otherwise go back to the parser. |
| 2 | destructive SQL in forward body | Stop. Follow `reference/destructive-operations.md`. |
| 3 | slug used by a different migration | Stop. Ask the developer for a new name or whether the existing file covers it. |
| 4 | schema/rule conflict (column exists, NOT NULL w/o default, float money…) | Show every listed reason. Offer the compliant alternative as a *question* ("nullable, or NOT NULL DEFAULT 0?"). Do not pick for them. |

## Scripts

- `scripts/generate_migration.py` — validates the spec, writes the file.
- `scripts/check_reversible.py` — replays before → forward → rollback and checks the schema
  round-trips. The verifier subagent runs it; you can too.
- `scripts/schema_state.py` — the shared migration replayer (stdlib only).

## Reference

- `reference/conventions.md` — naming, numbering, append-only, one concern per file.
- `reference/type-rules.md` — type allowlist and the money / timestamp / NOT NULL rules.
- `reference/destructive-operations.md` — what is destructive and the sign-off it needs.
