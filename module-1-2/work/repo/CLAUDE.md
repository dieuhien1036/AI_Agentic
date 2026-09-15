# CLAUDE.md — payments-api

Context file for Claude Code. Read this before touching anything in this repo.

## 1. Project overview

- `payments-api` is a single-process **FastAPI** service (Python 3.11+, version 0.3.1) with exactly two top-level concerns.
- `app/auth/` issues JWTs at login. Security-sensitive, tightly scoped, holds no business logic.
- `app/orders/` is order CRUD over a thin repository layer.
- Cross-module concerns live at the package root: `app/types.py` (public models), `app/db.py` (engine/session), `app/main.py` (router registration).
- Persistence is **Postgres 15** via SQLAlchemy 2.x async. The schema depends on `JSONB` and `TIMESTAMPTZ`.
- Assume this service is deployed against live data. Prefer additive changes over rewrites.

## 2. Build & test

Run everything through `make`. Do not invent your own command lines.

- `make setup` — install dependencies (`uv sync`). Run this first in a fresh checkout.
- `make lint` — `ruff check .` (line length 100; rules `E,F,I,N,W,B,UP,C4`).
- `make type` — `mypy app` in **strict** mode with the pydantic plugin.
- `make test` — full pytest suite (`uv run pytest -q`).
- `make test-integration` — `tests/integration` only.
- `make run` — local server on port 8000.
- `make migrate-dry-run` — prints migrations; never applies them.

Before reporting a task done, run **`make lint && make type && make test`** and paste the real output. If a command cannot run for an environment reason (no `uv`, no Docker, no Postgres), say so explicitly — never claim a suite passed that you did not run.

## 3. Conventions

- Start every Python file with `from __future__ import annotations`.
- Put any type that crosses a module boundary in `app/types.py`. Keep module-internal types inside the module.
- Use **Pydantic v2** models for every request and response body. Do not return bare scalars, bare dicts, or ad-hoc JSON from a route.
- Declare `response_model=` on every route, and annotate the handler's return type.
- Keep business logic out of route handlers. Routes parse, delegate, and shape the response; the work happens in a sibling function (`app/orders/repository.py`, `app/auth/queries.py`).
- Routes never touch the ORM directly — go through the module's repository/queries layer.
- Register routers in `app/main.py` with an explicit `prefix=` and `tags=`. Paths inside a module are relative to that prefix (`@router.get("")`, not `@router.get("/orders")`).
- Represent money as `Decimal`, never `float`. Totals are `Numeric(12, 2)`.
- Use SQLAlchemy `select()` constructs with bound parameters. Never build SQL by string interpolation or f-string.
- Every new endpoint gets an integration test in `tests/integration/test_<module>.py`, using the `client` fixture from `tests/conftest.py`.
- Assert the status code first, then specific fields. Do not assert on whole payloads containing ids or timestamps.
- Keep lines ≤ 100 characters; keep imports sorted (ruff `I`).

## 4. Do not

- **Do not modify anything under `app/auth/`.** Security-sensitive, owned by the security lead. Token TTLs, signing keys, algorithms, and password verification change only with explicit human approval.
- **Do not edit any existing file in `migrations/`.** Migrations are append-only. A schema change goes in a new `migrations/000N_<name>.sql` with the next ascending number.
- **Do not apply migrations yourself.** The deploy pipeline does that. `make migrate-dry-run` is the only migration command you run.
- **Do not swap Postgres for SQLite** — not in `app/db.py`, not in test fixtures, not as a "faster test mode" suggestion. The schema uses Postgres-only features.
- Do not add a dependency without saying so and explaining why in your summary.
- Do not commit secrets. `JWT_SECRET` and `DATABASE_URL` come from the environment; never hardcode a value or write one into a test.
- Do not reformat, re-sort, or "clean up" files you were not asked to change.
- Do not weaken or delete an existing test to make a suite go green.
- Do not silence lint/type errors inline (`# noqa`, `# type: ignore`) — fix the cause.

## 5. Glossary

- **Order** — a customer's purchase intent. Created `pending`, moves `paid` → `shipped`. Can be `cancelled` from any non-terminal state. Model: `app.types.Order`.
- **Order item** — one line on an order: `sku`, `quantity`, `unit_price`. Model: `app.types.OrderItem`.
- **Order status** — the `OrderStatus` StrEnum: `pending | paid | shipped | cancelled`.
- **Token** — the JWT issued at login. 24h TTL, HS256-signed, secret read from the `JWT_SECRET` env var. Model: `app.types.TokenResponse`.
- **Repository** — the module-internal persistence layer (`repository.py` / `queries.py`). Not exported across module boundaries.
- **Row type** — `OrderRow`, `UserRow`: SQLAlchemy ORM models. Internal; convert to a Pydantic type before returning from a route.
- **Golden** — in the lab's prompt library, an input/expected pair used as a regression test for a prompt.

## 6. Escalation — stop and ask a human when

- The task needs a change under `app/auth/`, or to anything about tokens, hashing, or credentials.
- The task needs a schema change (new table, column, index, constraint) — propose the new migration file and wait.
- The task implies changing the database engine, the async driver, or the test strategy in `tests/conftest.py`.
- The task would change an existing endpoint's URL, status code, or response shape — that breaks clients.
- A requirement conflicts with a rule in this file. Name the rule, propose both options, let the human choose.
- `make lint`, `make type`, or `make test` cannot be run at all in the current environment.

## 7. Examples

**Adding an endpoint — follow this order exactly:**

1. Define the response model in `app/types.py`:
   ```python
   class OrderCountResponse(BaseModel):
       user_id: int
       count: int
   ```
2. Add the query to the module's repository (`app/orders/repository.py`):
   ```python
   async def count_orders_for_user(session: AsyncSession, *, user_id: int) -> int:
       stmt = select(func.count()).select_from(OrderRow).where(OrderRow.user_id == user_id)
       return int((await session.execute(stmt)).scalar_one())
   ```
3. Add the route in `app/orders/routes.py` — path relative to the `/orders` prefix:
   ```python
   @router.get("/count", response_model=OrderCountResponse)
   async def count_orders(user_id: int,
                          session: AsyncSession = Depends(get_session)) -> OrderCountResponse:
       total = await count_orders_for_user(session, user_id=user_id)
       return OrderCountResponse(user_id=user_id, count=total)
   ```
4. Add the integration test in `tests/integration/test_orders.py`:
   ```python
   @pytest.mark.asyncio
   async def test_count_orders_returns_count_for_user(client: AsyncClient) -> None:
       resp = await client.get("/orders/count", params={"user_id": 42})
       assert resp.status_code == 200
       assert resp.json()["user_id"] == 42
   ```
5. Run `make lint && make type && make test`.

**Good:** parameterised query — `select(OrderRow).where(OrderRow.id == order_id)`

**Bad:** `await session.execute(f"DELETE FROM orders WHERE id = {order_id}")` — SQL injection, bypasses the repository layer, and a raw string is not executable in SQLAlchemy 2.x.

## 8. Imports / pointers

- @README.md — repo layout and how the lab uses it.
- @docs/architecture.md — service shape, data layer, glossary, protected paths. Read before any non-trivial change.
- @Makefile — the authoritative list of build/test commands.
- @pyproject.toml — dependency pins, ruff/mypy/pytest configuration.
- `AGENTS.md` — the same rules in one self-contained file, for agents that do not read `CLAUDE.md`. Keep the two in sync: change a rule here, change it there.
- Operational runbook: internal wiki, "payments-api runbook".
- On-call: PagerDuty service "payments-api".
- Deploy: GitHub Actions workflow `.github/workflows/deploy.yml`.
