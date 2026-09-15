# Run 1 — Happy path

**Scenario (from `SCENARIOS.md`, migration-scaffold section):**

> Prompt: "Add a migration that adds a `notes` column (TEXT, nullable) to the `orders`
> table."
> Expected: a new file `migrations/000N_add_orders_notes.sql` with the correct
> `ALTER TABLE`. No existing migration edited.

**Repo used:** `demo-repo/` (fixture repo built for this lab; `migrations/0001_initial.sql`
defines `users` and `orders`).

**Working directory for every command below:** `work/demo-repo/`. The script is invoked
through its *installed* path (`.claude/skills/scaffold-migration/scripts/…`), not from the
source folder — so this run exercises exactly what a user of the installed skill gets.

```
$ cd work/demo-repo
```

---

## Agent trace

**1. Locate migrations directory.** `migrations/` exists, containing `0001_initial.sql`.

**2. Read the most recent migration to infer current schema.** `0001_initial.sql` shows
`orders` has `id, user_id, status, total, created_at`. No `notes` column yet — the request
is additive and doesn't conflict with anything existing.

**3. Draft the SQL body.**

```sql
ALTER TABLE orders ADD COLUMN notes TEXT;
```

(Nullable is Postgres's default for a new column with no `NOT NULL` — matches "TEXT,
nullable" from the request without needing an explicit `NULL` keyword.)

**4. Check against `reference/destructive-operations.md`.** No match — `ADD COLUMN` isn't
in the destructive pattern list. Proceed.

**5. Run the scaffold script**, letting it assign the number:

```
$ echo "ALTER TABLE orders ADD COLUMN notes TEXT;" \
    | python3 .claude/skills/scaffold-migration/scripts/scaffold_migration.py \
        --migrations-dir migrations --name add_orders_notes --body-file -
CREATED: migrations/0002_add_orders_notes.sql
```

Exit code: `0`.

**6. Resulting file** (`migrations/0002_add_orders_notes.sql`):

```sql
-- migrations/0002_add_orders_notes.sql
--
-- DO NOT EDIT MIGRATION FILES BY HAND ONCE MERGED.
-- Migrations are append-only. New schema changes go in a new file:
--   migrations/000N_<name>.sql  (N = next number, ascending)
-- The deploy pipeline applies them in order.

ALTER TABLE orders ADD COLUMN notes TEXT;
```

**7. `0001_initial.sql` untouched** — confirmed by `ls migrations/`:
`0001_initial.sql`, `0002_add_orders_notes.sql`. Nothing else modified.

## Final response given to the user

> Created `migrations/0002_add_orders_notes.sql` — adds a nullable `notes TEXT` column to
> `orders`. `0001_initial.sql` was not touched. This only writes the file; it doesn't run
> the migration against any database.

## Outcome vs. expected

Matches expectation exactly: correctly-numbered new file, correct `ALTER TABLE`, no
existing migration edited.
