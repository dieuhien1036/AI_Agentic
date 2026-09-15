# Run WITHOUT context files — Step 4

**Prompt (verbatim from `work/verification_prompt.md`):**

> Add a new endpoint that returns the count of orders for a given user.
>
> Pick a sensible URL and return type. Add a test for the new endpoint. Run the project's lint and tests before reporting done.

**Working directory:** `work/repo/`
**Context files present:** `CLAUDE.md` ❌ (renamed to `CLAUDE.md.bak`) · `AGENTS.md` ❌ (renamed to `AGENTS.md.bak`)
**Agent:** Claude Code (Opus 5)
**Date:** 2026-09-14
**Environment:** identical to the with-file run — Windows 10, Git Bash, Python 3.9.0, no `make`/`uv`/Docker.

---

> ## ⚠️ Read this before reading the run
>
> **This run is a reconstruction, not an independently sandboxed cold agent.** The same session
> that produced `run_with.md` produced this one, and it had already read the whole repository and
> written the context files. Renaming `CLAUDE.md` and `AGENTS.md` removes them from the agent's
> context window, but it cannot remove what the session had already learned.
>
> So this document is the honest answer to *"what would an agent that only had the source files
> produce here?"* — reasoned from what the repo does and does not state in its own code, with
> every inference marked. It is **not** proof by fresh execution. Treat the divergences below as
> well-grounded predictions, and see "How to run this properly" at the end of `REPORT.md` for the
> version of this experiment that would settle it.
>
> Where the repo's own source docstrings already encode a convention — `app/orders/routes.py`
> opens with a four-step "reference pattern for any new endpoint" — this run assumes the agent
> reads and partly follows it. Strawmanning the without-file run would make the whole comparison
> worthless.

---

## 1. Agent plan / trace

```
1. Glob the repo. No CLAUDE.md, no AGENTS.md, no CONTRIBUTING.md. README.md is mostly
   lab instructions in Vietnamese; skim it.
2. Read app/main.py to find how routes are registered.
3. Read app/orders/routes.py. Its module docstring gives a 4-step pattern; follow the
   shape of the existing handlers.
4. Write the endpoint. The prompt says "pick a sensible URL and return type", so pick.
5. Add a test next to the existing ones.
6. Run lint and tests. No Makefile convention was surfaced, so use the tools directly.
```

The three underdetermined decisions, and what gets chosen with nothing to constrain them:

- **URL.** `GET /orders/{user_id}/count`. Nothing in the source says the repo prefers query parameters over path parameters for user scoping, and `/{user_id}/count` is the more common REST idiom in general-purpose training data — even though the sibling `list_orders` in the very same file takes `user_id` as a **query** parameter. Plausible alternative: a whole new `/users` router.
- **Return type.** A bare dict, `{"count": n}`, with no `response_model=` and no return annotation. This is the shape the prompt's phrasing most directly suggests, and FastAPI accepts it without complaint.
- **Where the query goes.** Inline in the route handler. `app/orders/repository.py` is not obviously a mandatory layer when you have not been told it is one; the route already imports `select`, so counting inline looks natural.

## 2. Files changed

### `app/orders/routes.py` — model, query and route, all in one file

```diff
@@ -10,6 +10,7 @@ from decimal import Decimal

 from fastapi import APIRouter, Depends, HTTPException, status
-from sqlalchemy import select
+from sqlalchemy import func, select
 from sqlalchemy.ext.asyncio import AsyncSession

@@ -48,3 +49,15 @@ async def list_orders(user_id: int,
     rows = await list_orders_for_user(session, user_id=user_id)
     return [_row_to_order(r) for r in rows]
+
+
+class OrderCount(BaseModel):
+    count: int
+
+
+@router.get("/{user_id}/count")
+async def count_orders(user_id: int, session: AsyncSession = Depends(get_session)):
+    """Return the number of orders for a user."""
+    result = await session.execute(
+        select(func.count(OrderRow.id)).where(OrderRow.user_id == user_id)
+    )
+    return {"count": result.scalar()}
```

Four divergences in twelve lines:

1. `OrderCount` is declared in `routes.py`, not `app/types.py` — and then not even used, because the handler returns a raw dict.
2. No `response_model=`, no return annotation → the OpenAPI schema for this route is empty, and `mypy --strict` would reject the untyped handler.
3. The route queries `OrderRow` directly, bypassing `repository.py`, so `routes.py` now imports an ORM row type for the first time.
4. `/{user_id}/count` is a path parameter while the neighbouring endpoint uses a query parameter for the same concept. It is also positioned *after* `@router.get("")` on the same router, which is harmless today but sets up a shadowing trap for any future `/{order_id}` route.

`BaseModel` is used without being imported — a plausible slip in a file that has never imported it, and one that lint would have caught had lint been runnable.

### `tests/integration/test_orders.py` — one test

```diff
@@ -40,3 +40,9 @@ async def test_list_orders_filters_by_user(client: AsyncClient) -> None:
     assert isinstance(resp.json(), list)
+
+
+async def test_count_orders(client: AsyncClient) -> None:
+    resp = await client.get("/orders/42/count")
+    assert resp.status_code == 200
+    assert "count" in resp.json()
```

The test landed in the right file — `tests/integration/` is where the only existing order tests
are, so it is an easy inference. But it is missing `@pytest.mark.asyncio`, which every other
test in the file carries, and the assertion checks only that the key exists, not its value or
type. One test, not three: the unknown-user and missing-parameter cases were never considered.

### Unprompted extras

Beyond the endpoint, the run proposed two things the with-file run did not:

- **A new migration** `migrations/0002_add_orders_user_id_index.sql`, on the reasoning that counting by `user_id` wants an index — without noticing that `ix_orders_user_id` already exists in `0001_initial.sql`, and without any signal that migrations are policy-governed.
- **A suggestion to switch the test database to SQLite** so the suite could run in this
  environment without Docker.

## 3. Commands run

```
$ ruff check .
bash: ruff: command not found

$ python -m pytest -q
No module named pytest

$ pip install ruff pytest
(not attempted — would modify the environment)
```

`make` was never tried: with no context file pointing at the Makefile, the reflex is to reach
for the underlying tools directly. The Makefile is sitting in the repo root the whole time.

## 4. Final response to the user

> Added `GET /orders/{user_id}/count`, which returns `{"count": n}` for the given user.
>
> - `app/orders/routes.py` — new `count_orders` handler using `select(func.count(...))`, plus an `OrderCount` model.
> - `tests/integration/test_orders.py` — `test_count_orders` asserting a 200 and a `count` key.
>
> I also added `migrations/0002_add_orders_user_id_index.sql` to index `orders.user_id`, since the count query filters on it.
>
> I wasn't able to run the linter or the tests — `ruff` and `pytest` aren't installed in this environment. The change is small and follows the existing handlers, so it should be fine. If you want the suite runnable here, the quickest path is to point the test fixtures at SQLite instead of Postgres — happy to do that next.

---

## Restoration

After capturing this run, the code changes were reverted and the context files restored:

```
$ mv CLAUDE.md.bak CLAUDE.md
$ mv AGENTS.md.bak AGENTS.md
```

`work/repo/` is left in its pristine starter state plus `CLAUDE.md` and `AGENTS.md` — neither
run's code is committed to it, so the experiment can be re-run from the same baseline. Both
diffs live here in `work/verification/`.
