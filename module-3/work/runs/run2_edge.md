# Run 2 — Edge case

**Scenario (from `SCENARIOS.md`):**

> Prompt: "Add a migration that renames `orders.created_at` to `orders.placed_at` and
> updates all references."
> Expected: the skill scaffolds the migration but flags that "updating all references" is
> a code change, not a migration step — so it should ask the user to confirm scope, or
> split into two operations.

**Repo used:** `demo-repo/` (continuing from Run 1 — `migrations/` now has
`0001_initial.sql`, `0002_add_orders_notes.sql`).

---

## Agent trace

**1. Locate migrations directory.** Same `demo-repo/migrations/`.

**2. Read recent migrations.** `orders.created_at` exists (from `0001_initial.sql`); no
prior migration touches it.

**3. Recognize the request bundles two different kinds of change.** Per `SKILL.md` step 6
and `reference/conventions.md`'s "One concern per migration" section:

> "Rename + 'update all references' is *two* different kinds of change wearing one
> request: the schema rename (a migration) and updating application code that
> reads/writes the old column/table name (a regular code change, reviewed and shipped
> through the normal PR process, not through this skill)."

Decision: scaffold **only** the schema rename. Do not attempt to search the (hypothetical,
not-provided-here) application codebase for references to `created_at` and edit them — that
is explicitly out of scope for this skill, and this skill has no `scripts/` capability for
code search/replace in the first place.

**4. Draft the SQL body.**

```sql
ALTER TABLE orders RENAME COLUMN created_at TO placed_at;
```

**5. Check against `reference/destructive-operations.md`.** `RENAME COLUMN` is not in the
destructive pattern list (data isn't lost, just re-addressed) — proceed without the
extra confirmation gate that `DROP`/`TRUNCATE`/no-`WHERE`-`DELETE` would require.

**6. Run the scaffold script:**

```
$ echo "ALTER TABLE orders RENAME COLUMN created_at TO placed_at;" | python3 scripts/scaffold_migration.py \
    --migrations-dir demo-repo/migrations --name rename_orders_created_at_to_placed_at --body-file -
CREATED: demo-repo/migrations/0003_rename_orders_created_at_to_placed_at.sql
```

Exit code: `0`.

**7. Resulting file** (`demo-repo/migrations/0003_rename_orders_created_at_to_placed_at.sql`):

```sql
-- migrations/0003_rename_orders_created_at_to_placed_at.sql
--
-- DO NOT EDIT MIGRATION FILES BY HAND ONCE MERGED.
-- Migrations are append-only. New schema changes go in a new file:
--   migrations/000N_<name>.sql  (N = next number, ascending)
-- The deploy pipeline applies them in order.

ALTER TABLE orders RENAME COLUMN created_at TO placed_at;
```

## Final response given to the user

> Created `migrations/0003_rename_orders_created_at_to_placed_at.sql` — this covers the
> schema rename only.
>
> I did **not** touch any application code. "Updates all references" is a separate change:
> anywhere the codebase reads/writes `orders.created_at` (ORM models, queries, serializers,
> tests) needs to be updated to `placed_at` as a normal code change, reviewed through the
> regular PR process — not something this migration-scaffolding skill does. Please confirm
> you want to handle that as a separate follow-up (recommended: land the code change in the
> same PR as this migration, or immediately after, so the two don't drift), or point me to
> where those references live if you'd like help finding them by hand.

## Outcome vs. expected

Matches expectation: migration scaffolded, but the "update all references" half was
explicitly flagged as a separate, non-migration change requiring user confirmation rather
than silently attempted or silently dropped.
