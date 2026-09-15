# Discovery contract — trigger reliability testing

Tests whether `scaffold-migration`'s `name`+`description` alone (the only thing a skill
router sees before invoking it) fires on the right prompts and stays silent on the wrong
ones.

**Method:** rather than judge this myself (I wrote the description, so I'm the worst judge
of whether it reads unambiguously to someone who didn't), each round was scored by a fresh
subagent given *only* the frontmatter block below and the candidate prompts — no knowledge
of which prompts were "meant" to pass, no access to the rest of `SKILL.md`. This mirrors
what an actual skill router does: it sees name+description, not the skill's internals.

## Description under test (v1 — unchanged through both rounds)

```yaml
name: scaffold-migration
description: |
  Generates a new append-only SQL database migration file in the project's
  migrations/ directory, numbered and named per house convention.
  Use when the user asks to add, create, or generate a database migration —
  including phrases like "add a migration", "create a migration for", "scaffold
  a schema change", "new migration to add a column/table/index".
  Do NOT use for running or applying existing migrations, writing ad-hoc SQL
  queries, editing application/ORM code, or explaining what a migration is.
```

## Round 1 — required 5+/5+ positive, 5+/5+ negative

| ID | Prompt | Intended | Router said | Correct? |
|----|--------|----------|-------------|----------|
| P1 | "Add a migration that adds a `notes` column (TEXT, nullable) to the `orders` table." | fire | yes | ✅ |
| P2 | "I need a new migration to add an index on orders.status." | fire | yes | ✅ |
| P3 | "Create a migration file that adds a `shipped_at` timestamp column to orders." | fire | yes | ✅ |
| P4 | "Scaffold a new schema migration for adding a `discount_code` column to orders." | fire | yes | ✅ |
| P5 | "We need to add a `cancelled_reason` column via a new migration — can you generate it?" | fire | yes | ✅ |
| P6 | "Generate the next migration to add a unique constraint on users.email." | fire | yes | ✅ |
| N1 | "What does the `orders` table's schema currently look like?" | silent | no | ✅ |
| N2 | "Can you write a SQL query to find all pending orders older than 30 days?" | silent | no | ✅ |
| N3 | "Refactor the `list_orders_for_user` function to use pagination." | silent | no | ✅ |
| N4 | "Run the existing migrations against my local dev database." | silent | no | ✅ |
| N5 | "Explain what a database migration is and why we use append-only migration files." | silent | no | ✅ |
| N6 | "Fix the bug where order totals are calculated incorrectly." | silent | no | ✅ |

**Result: 6/6 positive, 6/6 negative — bar cleared on the first attempt, no revision made
to the description at this point.**

## Round 2 — adversarial stress test (beyond the acceptance bar)

Passing round 1 cleanly is a weaker signal than it looks: the round-1 prompts were mostly
close paraphrases of the description's own trigger phrases. Before declaring the contract
done, I ran a second, harder round designed to probe exactly where a description like this
is *expected* to fail — recall without the literal word "migration," and precision when
"migration" appears but the verb is wrong.

| ID | Prompt | Probes | Router said | Correct? |
|----|--------|--------|-------------|----------|
| P7 | "Our orders table needs a boolean `is_gift` flag — can you set that up?" | recall without the word "migration" or "add a column" | yes | ✅ |
| P8 | "Bump the schema so orders has a `refunded_at` timestamp." | recall with unusual phrasing ("bump the schema") | yes | ✅ |
| N7 | "Apply migration 0002 to the staging database." | precision — contains "migration" but the verb is apply/run, not create | no | ✅ |
| N8 | "Can you review this migration file I already wrote for mistakes?" | precision — contains "migration" but the verb is review, not create | no | ✅ |

**Result: 4/4 correct. No revision needed.**

## Outcome

**No description changes were made.** Across both rounds — 16 total classifications — the
v1 description scored 16/16. The two design choices that most plausibly account for this:

1. The description states the action *and* explicit trigger phrases *and* explicit negative
   scope in the same short block, rather than leaving negative scope implicit — this is
   exactly the anatomy the lab material teaches, and skipping the negative-scope half is the
   most common way a description under-specifies.
2. The negative-scope list names the *specific adjacent actions* on the same nouns
   ("running or applying existing migrations," not just "don't do database stuff") —
   which is what made N4/N7 (both about *running*, not creating, a migration) resolve
   correctly instead of over-firing just because the word "migration" is present.

If a future prompt did surface a miss, the fix path is: for a false negative, add the
missed phrasing to the trigger-phrase list; for a false positive, add the specific
adjacent action to the negative-scope list — never make either list vaguer to "cover more
ground," since vagueness is what caused the ambiguity in the first place.
