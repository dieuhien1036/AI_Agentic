# CLAUDE.md

Guidance for Claude Code (and any other coding agent) working in this repository.

## 1. Project overview

- `payments-api` — a single FastAPI process (see [app/main.py](app/main.py)) that handles two
  concerns: customer **authentication** (`app/auth/`) and **order** CRUD (`app/orders/`).
- Cross-cutting pieces (shared types, DB engine) live at the package root in `app/`.
- Data layer: Postgres 15 in production, SQLAlchemy 2.x with an async engine
  (`psycopg` driver). Schema changes ship as append-only SQL files in `migrations/`.
- Deeper design notes: @docs/architecture.md

## 2. Build & test

Always use the `Makefile` targets — do not invoke `pytest`/`ruff`/`mypy` directly unless a
target does not exist for what you need.

```
make setup            # uv sync — install deps
make lint              # ruff check .
make type              # mypy app (strict mode)
make test              # pytest -q (full suite)
make test-integration   # pytest tests/integration -q
make run                # uvicorn app.main:app --reload --port 8000
```

- Python >= 3.11, dependency-managed with `uv` (see `pyproject.toml`).
- Integration tests spin up a real Postgres via `testcontainers` (see `tests/conftest.py`).
  They do **not** use SQLite.
- Before reporting any task done, run `make lint` and `make test` and confirm both pass.

## 3. Conventions

- Every Python module starts with `from __future__ import annotations`.
- **Public types** — anything that crosses a module boundary — live in `app/types.py`
  (Pydantic v2 models). **Internal types** (ORM row models, etc.) stay private inside their
  own module, e.g. `OrderRow` in `app/orders/repository.py`, `UserRow` in
  `app/auth/queries.py`. Never move an internal type into `app/types.py` "just in case."
- Route handlers never contain business logic. They validate input, call a function in the
  same module (or a sibling repository module), and shape the response. Put logic in a
  repository/service function, not inline in the `@router` handler.
- New endpoint pattern (see `app/orders/routes.py` docstring for the canonical version):
  1. Define request/response models in `app/types.py`.
  2. Add the route in the relevant module (e.g. `app/orders/routes.py`).
  3. Delegate persistence to that module's repository function — never touch the ORM
     directly from a route.
  4. Add an integration test under `tests/integration/`.
- Repository modules (`app/orders/repository.py`, `app/auth/queries.py`) are internal to
  their package and are not imported from other modules' routes.
- All request/response models are Pydantic v2 (`from pydantic import BaseModel, Field`).
- Lint/type config is enforced, not aspirational: `ruff` selects `E, F, I, N, W, B, UP, C4`
  at line-length 100; `mypy --strict` on `app/`. Keep new code compliant rather than adding
  suppressions.

## 4. Do not

- **Do not modify `app/auth/*`** (token TTLs, signing keys, password verification, or any
  other auth logic) without explicit human review from the security lead. This code is
  security-sensitive by policy — see the warning at the top of
  [app/auth/handlers.py](app/auth/handlers.py).
- **Do not hand-edit files in `migrations/`.** Migrations are append-only. A schema change
  is always a *new* file `migrations/000N_<name>.sql` — never a diff to an existing one.
- **Do not switch `app/db.py` off Postgres** (e.g. to SQLite) for tests or anywhere else.
  The schema relies on Postgres-only features (`JSONB`, `TIMESTAMPTZ`, generated columns);
  swapping the database engine would silently break it. Do not propose this as a fix for
  "slow" or "flaky" tests.
- Do not put business logic in a route handler — delegate it (see Conventions).
- Do not invent ad-hoc build/test commands — use the `Makefile` targets in section 2.

## 5. Glossary

- **Order** — a customer's purchase intent. Created `pending`, moves `pending → paid →
  shipped`. Can be `cancelled` from any non-terminal state.
- **Order item** — one line on an order: SKU, quantity, unit price.
- **Token** — a JWT issued at login. TTL 24h, HS256-signed, secret from the `JWT_SECRET`
  env var.

## 6. Escalation

- Any change touching `app/auth/*` requires sign-off from the security lead before merge —
  raise this explicitly rather than merging silently.
- Schema changes go through a new migration file and the normal PR review process; the
  deploy pipeline (`.github/workflows/deploy.yml`) applies migrations in order.
- If a requirement is ambiguous (e.g. a new endpoint's URL shape or return type isn't
  specified), infer from the conventions above and existing sibling code rather than
  guessing something inconsistent — and say what you inferred and why in your response.
- For anything outside this file's scope (operational questions, on-call, incidents), see
  the pointers in section 8 rather than speculating.

## 7. Examples

Adding "get order count for a user" follows the same shape as the existing
`list_orders` endpoint:

```python
# app/types.py
class OrderCountResponse(BaseModel):
    user_id: int
    count: int

# app/orders/repository.py
async def count_orders_for_user(session: AsyncSession, *, user_id: int) -> int:
    stmt = select(func.count()).select_from(OrderRow).where(OrderRow.user_id == user_id)
    return (await session.execute(stmt)).scalar_one()

# app/orders/routes.py
@router.get("/count", response_model=OrderCountResponse)
async def get_order_count(user_id: int,
                          session: AsyncSession = Depends(get_session)) -> OrderCountResponse:
    count = await count_orders_for_user(session, user_id=user_id)
    return OrderCountResponse(user_id=user_id, count=count)
```

Plus a matching test in `tests/integration/test_orders.py` following the existing
arrange/act/assert pattern (realistic request shape, assert status then specific fields).

## 8. Imports / pointers

- Deeper design notes: @docs/architecture.md
- Operational runbook: internal wiki, "payments-api runbook".
- On-call rotation: PagerDuty service "payments-api".
- Deploy pipeline: GitHub Actions workflow `.github/workflows/deploy.yml`.
