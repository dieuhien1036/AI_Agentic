# Destructive operations (reference)

Fetched when a request looks like it might touch one of these. This is the definition of
"destructive" the skill uses, and what to do when a request matches.

## What counts as destructive here

- `DROP TABLE` — removes a whole entity, including all its data, irreversibly outside of a
  backup restore.
- `DROP DATABASE` — same, at the database level.
- `TRUNCATE` — deletes all rows in a table; usually not what "clean up some data" actually
  means.
- `ALTER TABLE ... DROP COLUMN` — irreversibly discards a column and its data.
- `DELETE FROM <table>` with no `WHERE` clause — deletes every row.

Renaming, adding a nullable column, adding an index, adding a `CHECK` constraint on new
data going forward — none of these are destructive in this sense, even though they're all
still schema changes that deserve normal review.

## What the skill does when a request matches

1. **Stop before writing anything.** `scripts/scaffold_migration.py` enforces this
   mechanically: it refuses to write a file for a body matching any pattern above unless
   `--allow-destructive` is passed. Treat a block from the script as a hard stop, not
   something to route around by hand-writing the file instead.
2. **Say exactly what triggered the block** — which pattern, on which table/entity — not a
   generic "this looks risky."
3. **Do not improvise a "safer" version on your own** (e.g. silently turning a `DROP TABLE`
   request into a `DELETE FROM` request, or scaffolding a soft-delete column instead of what
   was actually asked for). If a safer alternative genuinely exists, name it as a
   *suggestion* for the requester to confirm — don't substitute it silently.
4. **Require an explicit, named human sign-off** before ever passing
   `--allow-destructive`. "The user asked for it in the same message" is not sign-off — a
   destructive migration on a primary entity (a table other tables reference, or that
   clearly holds production data: `users`, `orders`, `payments`, and equivalents) needs a
   second, explicit confirmation turn, and ideally a named reviewer, before this skill
   proceeds.
5. **Never produce partial state.** If blocked, no migration file exists at all — not a
   half-written one, not a commented-out one. The repo is exactly as it was before the
   request.

## Primary entities in this repo (fill in per project)

Treat these as needing the extra confirmation step in addition to the pattern match above,
since a destructive change to them has outsized blast radius:

- `users`
- `orders`
- any table other tables have a foreign key into
