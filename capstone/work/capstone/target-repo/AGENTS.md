# AGENTS.md — payments-api

Self-contained context file for any coding agent (Copilot, Cursor, Codex, Claude Code, …).
No `@`-imports: everything an agent needs is in this one file. Kept in sync with `CLAUDE.md`.

## 1. Project overview

- `payments-api` v0.3.1 — a single-process **FastAPI** service on Python 3.11+, backed by **Postgres 15**.
- Two top-level concerns:
  - `app/auth/` — login and JWT issuance. Security-sensitive; no business logic.
  - `app/orders/` — order CRUD over a thin repository layer.
- Shared, cross-module code sits at the package root:
  - `app/types.py` — public Pydantic models.
  - `app/db.py` — SQLAlchemy 2.x async engine and `get_session` dependency.
  - `app/main.py` — app object and router registration.
- Layout:
  ```
  app/main.py            app/types.py         app/db.py
  app/auth/handlers.py   app/auth/queries.py
  app/orders/routes.py   app/orders/repository.py
  tests/conftest.py      tests/integration/test_orders.py
  migrations/0001_initial.sql
  docs/architecture.md   Makefile   pyproject.toml   README.md
  ```
- Treat the service as deployed against live data. Prefer additive changes over rewrites.

## 2. Build & test

Use `make`. Do not invent command lines.

| Command | What it does |
|---|---|
| `make setup` | `uv sync` — install dependencies. Run first in a fresh checkout. |
| `make lint` | `ruff check .` — line length 100, rules `E,F,I,N,W,B,UP,C4`. |
| `make type` | `mypy app` — **strict**, with the pydantic plugin. |
| `make test` | `uv run pytest -q` — full suite. |
| `make test-integration` | `tests/integration` only. |
| `make run` | `uvicorn app.main:app --reload --port 8000`. |
| `make migrate-dry-run` | Prints migrations. Never applies them. |

- Run `make lint && make type && make test` before reporting a task done, and paste the real output.
- Integration tests need a real Postgres via testcontainers (Docker). If it is unavailable, say so — do not claim a suite passed that you did not run.

## 3. Conventions

- Begin every Python file with `from __future__ import annotations`.
- Any type crossing a module boundary goes in `app/types.py`. Module-internal types stay in their module.
- Pydantic v2 models for every request and response body. No bare scalars, bare dicts, or ad-hoc JSON from a route.
- Every route declares `response_model=` and an annotated return type.
- No business logic in route handlers — delegate to a function in the same module.
- Routes never touch the ORM directly; go through `repository.py` / `queries.py`.
- Routers are registered in `app/main.py` with `prefix=` and `tags=`. In-module paths are relative to that prefix: `@router.get("")`, `@router.get("/count")`.
- Money is `Decimal`, never `float`. Totals are `Numeric(12, 2)`.
- Use SQLAlchemy `select()` with bound parameters. Never interpolate values into SQL strings.
- Every new endpoint gets an integration test in `tests/integration/test_<module>.py` using the `client` fixture from `tests/conftest.py`.
- Assert the status code first, then specific fields. Avoid full-payload equality where ids/timestamps make tests brittle.
- Lines ≤ 100 chars; imports sorted (ruff `I`); names follow PEP 8 (ruff `N`).

## 4. Do not

- **Do not modify anything under `app/auth/`.** Security-sensitive, owner: security lead. Token TTLs, signing keys, algorithms, and password verification need explicit human approval.
- **Do not edit existing files in `migrations/`.** Append-only: new schema changes go in `migrations/000N_<name>.sql`, next number ascending.
- **Do not apply migrations.** The deploy pipeline does. `make migrate-dry-run` is the only migration command to run.
- **Do not replace Postgres with SQLite** anywhere — `app/db.py`, test fixtures, or as a "faster tests" suggestion. The schema uses `JSONB` and `TIMESTAMPTZ`.
- Do not add dependencies silently — call it out and justify it.
- Do not hardcode secrets. `JWT_SECRET` and `DATABASE_URL` come from the environment.
- Do not reformat or reorganise files outside the scope of the task.
- Do not weaken or delete existing tests to make a suite pass.
- Do not silence lint/type errors with `# noqa` or `# type: ignore` — fix the cause.

## 5. Glossary

- **Order** — a customer's purchase intent. Created `pending`, moves `paid` → `shipped`; `cancelled` from any non-terminal state. Model: `app.types.Order`.
- **Order item** — one line on an order: `sku`, `quantity`, `unit_price`. Model: `app.types.OrderItem`.
- **Order status** — `OrderStatus` StrEnum: `pending | paid | shipped | cancelled`.
- **Token** — JWT issued at login. 24h TTL, HS256, secret from the `JWT_SECRET` env var. Model: `app.types.TokenResponse`.
- **Repository** — module-internal persistence layer (`app/orders/repository.py`, `app/auth/queries.py`). Not exported across modules.
- **Row type** — `OrderRow`, `UserRow`: SQLAlchemy ORM models. Internal; convert to a Pydantic type before returning from a route.

## 6. Escalation — stop and ask a human when

- The change touches `app/auth/`, tokens, hashing, or credentials.
- The change needs a new table, column, index, or constraint — propose the new migration file and wait for approval. For "add column X to table Y", follow §9: it writes the file and stops for review.
- The change implies a different database engine, async driver, or test strategy.
- The change alters an existing endpoint's URL, status code, or response shape — that breaks clients.
- A requirement conflicts with a rule here — name the rule, present both options, let the human decide.
- `make lint`, `make type`, or `make test` cannot be run at all in the current environment.

## 7. Examples

**Reference flow for adding an endpoint (this exact order):**

1. `app/types.py` — the response model:
   ```python
   class OrderCountResponse(BaseModel):
       user_id: int
       count: int
   ```
2. `app/orders/repository.py` — the query:
   ```python
   async def count_orders_for_user(session: AsyncSession, *, user_id: int) -> int:
       stmt = select(func.count()).select_from(OrderRow).where(OrderRow.user_id == user_id)
       return int((await session.execute(stmt)).scalar_one())
   ```
3. `app/orders/routes.py` — the route, path relative to the `/orders` prefix:
   ```python
   @router.get("/count", response_model=OrderCountResponse)
   async def count_orders(user_id: int,
                          session: AsyncSession = Depends(get_session)) -> OrderCountResponse:
       total = await count_orders_for_user(session, user_id=user_id)
       return OrderCountResponse(user_id=user_id, count=total)
   ```
4. `tests/integration/test_orders.py` — the test:
   ```python
   @pytest.mark.asyncio
   async def test_count_orders_returns_count_for_user(client: AsyncClient) -> None:
       resp = await client.get("/orders/count", params={"user_id": 42})
       assert resp.status_code == 200
       assert resp.json()["user_id"] == 42
   ```
5. `make lint && make type && make test`.

**Good:** `select(OrderRow).where(OrderRow.id == order_id)` — bound parameter, via the repository.

**Bad:** `await session.execute(f"DELETE FROM orders WHERE id = {order_id}")` — SQL injection, bypasses the repository layer, and a raw string is not executable in SQLAlchemy 2.x.

## 8. Pointers

- `README.md` — repo layout and lab instructions.
- `docs/architecture.md` — service shape, data layer, glossary, protected paths. Read before any non-trivial change.
- `Makefile` — the authoritative list of build/test commands.
- `pyproject.toml` — dependency pins and ruff/mypy/pytest configuration.
- `CLAUDE.md` — the Claude Code version of this file (uses `@`-imports). Keep both in sync.
- Operational runbook: internal wiki, "payments-api runbook".
- On-call: PagerDuty service "payments-api".
- Deploy: GitHub Actions workflow `.github/workflows/deploy.yml`.

## 9. Schema changes — the add-column workflow

When a developer asks to add a column, do not hand-write the migration. Run these steps
(Claude Code wires them to subagents and a skill under `.claude/`; any other agent can run the
same scripts directly):

1. **Parse** the request into a spec using the prompt in `.claude/agents/migration-request-parser.md`.
   Output: JSON with `table`, `column`, `type`, `nullable`, `default`, `slug` — or
   `needs_clarification` with questions. Ask the developer the questions; do not guess.
2. **Generate** the file:
   `python .claude/skills/generate-migration/scripts/generate_migration.py --migrations-dir migrations --spec <spec.json>`
   Exit codes: `0` created / identical file already exists, `1` bad input, `2` destructive SQL
   blocked, `3` slug already used with different content, `4` spec conflicts with the current
   schema or a rule below. On non-zero, show stderr verbatim and stop.
3. **Verify** reversibility:
   `python .claude/skills/generate-migration/scripts/check_reversible.py --migrations-dir migrations <new file>`
   then review the file against the rules below. Report `GO` or `NO-GO` with reasons.
4. **Stop.** Do not apply the migration or change ORM code in the same change.

Migration rules:

- File name `migrations/NNNN_<snake_case_slug>.sql`, NNNN = previous max + 1, zero-padded to 4.
- One `ALTER TABLE … ADD COLUMN` per add-column migration.
- Every migration ends with a `-- ROLLBACK` block of commented-out SQL that exactly undoes the
  forward SQL (`ADD COLUMN IF NOT EXISTS x` ↔ `DROP COLUMN IF EXISTS x`).
- `users` and `orders` hold live data: new columns are nullable, or `NOT NULL` with a `DEFAULT`.
- Money columns (`*_amount`, `*_price`, `total`, `*_total`, `discount*`, `fee*`) are
  `NUMERIC(12, 2)` — never `REAL` / `FLOAT` / `DOUBLE PRECISION`.
- Timestamps are `TIMESTAMPTZ`; structured blobs are `JSONB`.
- No destructive statement in the forward SQL. The `DROP COLUMN` inside the commented rollback
  block is expected.
