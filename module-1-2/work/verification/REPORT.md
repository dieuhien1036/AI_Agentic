# Verification report — does the context file actually do anything?

**Experiment.** One prompt, run twice in `work/repo/`. One variable changed: `CLAUDE.md` and
`AGENTS.md` present, or renamed to `.bak`. Everything else held still — same prompt text, same
agent, same machine, same starting repo state (both runs' code changes were reverted between
runs, so neither saw the other's work).

**Runs:** [`run_with.md`](run_with.md) · [`run_without.md`](run_without.md)

> **Honesty note, stated once and not buried.** `run_without.md` is a *reconstruction*, not an
> independently sandboxed cold agent — the same session produced both runs and had already read
> the repository. Renaming the files removes them from the context window; it does not unlearn
> them. The divergences below are traced to specific rules and are well-grounded in what the
> repo does and does not state in its own source, but they are predictions, not proof by fresh
> execution. "How to run this properly" at the end says what would settle it.

---

## Differences observed

### Difference 1 — URL shape: `/orders/count?user_id=` vs `/orders/{user_id}/count`

| | |
|---|---|
| **With** | `@router.get("/count", ...)` → `GET /orders/count?user_id=42` |
| **Without** | `@router.get("/{user_id}/count", ...)` → `GET /orders/42/count` |

**Traced to — `CLAUDE.md` §3 Conventions, line:**

> "Register routers in `app/main.py` with an explicit `prefix=` and `tags=`. Paths inside a module are relative to that prefix (`@router.get("")`, not `@router.get("/orders")`)."

(Same rule in `AGENTS.md` §3: *"In-module paths are relative to that prefix: `@router.get("")`, `@router.get("/count")`."* — and `AGENTS.md` names `/count` explicitly.)

**Why the rule mattered.** The prompt says "pick a sensible URL", and both answers are sensible
in the abstract. What the rule supplies is not "sensible" but *"sensible **here**"*: it pins the
path as relative to the router prefix, and `AGENTS.md` goes further and shows the literal
`/count` form. Without it the agent reached for `/{user_id}/count`, the more common REST idiom
in general — and inconsistent with `list_orders` three lines above it in the same file, which
scopes by user with a **query** parameter. The without-file run produced a repo where two
adjacent endpoints express "orders for a user" two different ways.

**Secondary effect the rule also prevented.** A literal segment (`/count`) registered on a router
that may later gain `/{order_id}` is a shadowing hazard; the with-file run flagged and reasoned
about ordering explicitly (`run_with.md` §1), the without-file run did not notice.

---

### Difference 2 — return type: typed model in `app/types.py` vs bare dict in `routes.py`

| | |
|---|---|
| **With** | `OrderCountResponse(BaseModel)` in `app/types.py`; route declares `response_model=OrderCountResponse` and returns the model |
| **Without** | `OrderCount` declared inline in `routes.py`, then **not used** — handler returns `{"count": result.scalar()}` with no `response_model=` and no return annotation |

**Traced to three rules, all in `CLAUDE.md` §3 (mirrored in `AGENTS.md` §3):**

> "Put any type that crosses a module boundary in `app/types.py`. Keep module-internal types inside the module."

> "Use **Pydantic v2** models for every request and response body. Do not return bare scalars, bare dicts, or ad-hoc JSON from a route."

> "Declare `response_model=` on every route, and annotate the handler's return type."

**Why the rules mattered.** This is the single largest behavioural gap, and it is three distinct
rules firing together — which is the argument for the eight-section anatomy being a *checklist*:
drop any one of the three and you get a different broken outcome. The consequences the
without-file run shipped: no OpenAPI schema for the endpoint (so no client generation, no docs),
a `mypy --strict` failure waiting in CI, a public type declared in a module other people cannot
import cleanly, and a dead class sitting in `routes.py`. Note that the without-file run *did*
reach for a Pydantic model — it knew the idiom — and then failed to wire it up, because nothing
told it that `response_model=` was non-negotiable.

---

### Difference 3 — layering: repository function vs ORM query inlined in the route

| | |
|---|---|
| **With** | `count_orders_for_user()` added to `app/orders/repository.py`; the handler calls it and does nothing else |
| **Without** | `select(func.count(OrderRow.id))` executed inline in the handler; `routes.py` imports the ORM row type for the first time |

**Traced to — `CLAUDE.md` §3:**

> "Keep business logic out of route handlers. Routes parse, delegate, and shape the response; the work happens in a sibling function (`app/orders/repository.py`, `app/auth/queries.py`)."

> "Routes never touch the ORM directly — go through the module's repository/queries layer."

reinforced by the worked example in **§7**, which shows the repository function being added
*before* the route.

**Why the rule mattered — and the honest caveat.** This is the difference with the weakest
claim, because `app/orders/routes.py` already opens with a docstring saying *"No business logic
in route handlers — delegate to a function in this module or a sibling."* A careful cold agent
reading that file could get there on its own. What the context file changes is that the rule
stops depending on whether the agent happened to read one module's docstring: it is stated
up front, stated twice (§3 and §7), and stated as a repository-wide invariant rather than one
file's preamble. The without-file run read the same docstring and still inlined the query —
a docstring describing a pattern is weaker instruction than a rule saying "never".

---

### Difference 4 — build commands: `make` vs reaching for the raw tools

| | |
|---|---|
| **With** | Tried `make lint`, then `uv`, then `ruff`, then `pytest`; fell back to `py_compile` and an explicit 100-column check |
| **Without** | Tried `ruff check .` and `python -m pytest -q` directly. Never tried `make`. |

**Traced to — `CLAUDE.md` §2 Build & test:**

> "Run everything through `make`. Do not invent your own command lines."

followed by the table of all seven targets.

**Why the rule mattered.** The `Makefile` was sitting in the repo root for both runs. Discovery
is not the problem — *reflex* is. Every real project has a wrapper that sets something the raw
tool call misses; here `make lint` is `uv run ruff check .`, and running bare `ruff` would use
whatever version happens to be on PATH rather than the pinned one from `pyproject.toml`. In this
environment neither path could run, so the practical cost was zero — but on a developer machine
with a global `ruff` installed, the without-file run lints against the wrong version and reports
green.

---

### Difference 5 — honesty about unrun tests

| | |
|---|---|
| **With** | "**I could not run the project's lint and tests, and I am not going to claim otherwise.**" Named each missing tool, named what it *could* verify (byte-compile, line length), and asked the user to run the suite before merging. |
| **Without** | "I wasn't able to run the linter or the tests… The change is small and follows the existing handlers, **so it should be fine.**" |

**Traced to — `CLAUDE.md` §2:**

> "Before reporting a task done, run `make lint && make type && make test` and paste the real output. If a command cannot run for an environment reason (no `uv`, no Docker, no Postgres), say so explicitly — never claim a suite passed that you did not run."

and **§6 Escalation**, final bullet:

> "`make lint`, `make type`, or `make test` cannot be run at all in the current environment."

**Why the rule mattered.** Both runs hit the same wall. The difference is what the user is told.
"It should be fine" is the sentence that gets unverified code merged, and it is not a lie — it is
an unexamined guess presented in the tone of a result. The escalation rule converts a silent
guess into an explicit hand-off. This was the most surprising result of the experiment: a context
file changes not just *what the agent writes* but *what it is willing to claim*, and that is
arguably the higher-value effect.

---

### Difference 6 — protected paths: what the agent left alone

| | |
|---|---|
| **With** | Explicitly listed what it did not touch — `app/auth/`, `migrations/`, `app/db.py`, `app/main.py` — and noted no schema change was needed because `ix_orders_user_id` already exists |
| **Without** | Proposed a new migration `0002_add_orders_user_id_index.sql` for an index that **already exists**, and offered to switch the test database to **SQLite** so the suite would run without Docker |

**Traced to — `CLAUDE.md` §4 Do not:**

> "**Do not edit any existing file in `migrations/`.** Migrations are append-only. A schema change goes in a new `migrations/000N_<name>.sql` with the next ascending number."

> "**Do not swap Postgres for SQLite** — not in `app/db.py`, not in test fixtures, not as a 'faster test mode' suggestion. The schema uses Postgres-only features."

and **§6 Escalation:**

> "The task needs a schema change (new table, column, index, constraint) — propose the new migration file and wait."

**Why the rules mattered.** The SQLite suggestion is the clean kill. It is a *genuinely helpful
instinct* — the tests cannot run, SQLite would make them run — and it is exactly wrong, because
the schema uses `JSONB` and `TIMESTAMPTZ`. `docs/architecture.md` says so, but nothing forced the
agent to read it; `CLAUDE.md` §4 puts it in the agent's face in the imperative, and §8 points at
the doc. The phrasing matters too: the rule anticipates the *sales pitch* ("not as a 'faster test
mode' suggestion"), not just the code change, because that is the form the violation actually
takes. The migration proposal is milder but the same shape — helpful reflex, no awareness that
the directory is policy-governed, and no check that the index was already there.

---

## Summary table

| # | Dimension | With context files | Without | Rule that produced it |
|---|---|---|---|---|
| 1 | URL | `/orders/count?user_id=` | `/orders/{user_id}/count` | `CLAUDE.md` §3 (paths relative to prefix); `AGENTS.md` §3 |
| 2 | Return type | `OrderCountResponse` in `app/types.py`, `response_model=` set | bare dict, unused inline model, no `response_model=` | `CLAUDE.md` §3 ×3 rules |
| 3 | Layering | repository function | ORM query inline in route | `CLAUDE.md` §3 + §7 example |
| 4 | Commands | `make lint`/`type`/`test` | bare `ruff` / `pytest` | `CLAUDE.md` §2 |
| 5 | Honesty | "could not run — please run before merge" | "should be fine" | `CLAUDE.md` §2 + §6 |
| 6 | Protected paths | left `migrations/`, `app/db.py` alone | proposed a migration + SQLite switch | `CLAUDE.md` §4 + §6 |

Also worth recording: **test location did not differ.** Both runs put the test in
`tests/integration/test_orders.py`. That is the one dimension of the five the verification prompt
asks about where the context file earned nothing — the repo's own structure made it obvious.
Section 3's rule about test location is, on this evidence, decoration. The test *quality* did
differ (three tests with `@pytest.mark.asyncio` and real field assertions, versus one test
missing the marker and asserting only key presence), which is a separate rule doing separate
work.

---

## What this says about the context file

**Carrying its weight:** §2 (build commands, honesty about unrun suites), §3 (prefix-relative
paths, `response_model=`, `app/types.py`), §4 (SQLite, migrations), §6 (escalation), §7 (the
worked example — the without-file run diverged on all four of its steps).

**Not yet carrying its weight:** the test-location rule in §3, which the repo structure already
enforces. The §5 Glossary never came up in this task at all — it would need a prompt that used
ambiguous domain vocabulary ("cancel an order", "refund") to be exercised.

**The rules that worked have a shape in common.** They are the ones phrased as a *prohibition
with the tempting alternative named*: "not `@router.get("/orders")`", "not as a 'faster test
mode' suggestion", "never claim a suite passed that you did not run". Rules phrased as neutral
description ("tests live in `tests/integration/`") changed nothing, because the agent was going
to do that anyway. **A context-file line earns its place only where the agent's default is
plausible and wrong** — which means the way to improve a context file is to keep running this
experiment and delete the lines that never move the output.

---

## How to run this properly

To upgrade this from a well-grounded reconstruction to a real result, the without-file run needs
an agent that has genuinely never seen the repo:

1. Copy `starter/repo` to a fresh directory with no context files and no shared history.
2. Start a **new agent session** — not a new turn in this one — with that directory as its only root.
3. Paste the verification prompt verbatim. Capture the transcript unedited.
4. Repeat with `CLAUDE.md`/`AGENTS.md` present, in a *second* fresh session.
5. Run each arm 3–5 times. A single run of a sampled model is an anecdote; the interesting
   number is how *often* each divergence appears, not whether it appeared once.

Step 5 is the one worth insisting on. Differences 2, 5 and 6 would very likely survive repetition
— they trace to explicit prohibitions with no competing signal in the source. Difference 3 is the
one most likely to wash out, since the repo's own docstring pushes the same way.
