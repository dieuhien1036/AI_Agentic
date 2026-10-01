# "Add a column" → reversible migration, verified  ·  payments-api

**Problem:** hand-written migrations miss the rollback, re-add columns that already exist, put
money in `FLOAT`, and add `NOT NULL` columns that fail on live tables.

```
"add a notes column to orders, optional"
   │
   ▼  [prompt + subagent]  migration-request-parser (haiku)  ──► spec JSON (schema-checked)
   │                        vague? → asks, stops
   ▼  [skill]               generate-migration: replays migrations/, refuses if column exists
   │                        or rule broken → 0002_add_orders_notes.sql  (+ -- ROLLBACK block)
   ▼  [subagent + script]   check_reversible.py (before→fwd→rollback == before)  = GATE
                            migration-verifier (sonnet, independent)              → GO / NO-GO
   [context]  CLAUDE.md / AGENTS.md §9 route the request and hold the rules all stages enforce
```

**Key choices**
- LLMs for language, scripts for facts: existence, numbering and reversibility are deterministic.
- The verifier can add blockers, never overrule a failed round-trip (demo: rubber-stamp case).
- The parser records what was asked; the skill says *why* it is refused (FLOAT money golden).
- Reuse: M1 repo + context file · M2 eval design · M3 migration skill · M4 verifier + driver.

**Evidence:** 7/7 regression cases · 5/5 prompt goldens · eval proven to fail on prompt
weakening, agent drift and fenced output.
