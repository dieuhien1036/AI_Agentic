# Column type rules (reference)

Enforced by `scripts/generate_migration.py` (exit 4) and re-checked by the
`migration-verifier` subagent. Source of truth: `CLAUDE.md` §3 and §9.

## Allowlist

| Type | Use for |
|---|---|
| `TEXT` | free text of any length (default for "string" / "notes" / "comment") |
| `VARCHAR(n)` | short codes with a real length limit (`n` ≤ 9999) |
| `BOOLEAN` | flags |
| `SMALLINT`, `INTEGER`, `BIGINT` | counts; `BIGINT` for ids / foreign keys (ids are `BIGSERIAL`) |
| `NUMERIC(p, s)` | exact decimals; money is always `NUMERIC(12, 2)` |
| `TIMESTAMPTZ` | points in time |
| `DATE` | calendar dates without time |
| `JSONB` | structured blobs |
| `UUID` | external identifiers |
| `REAL`, `DOUBLE PRECISION` | measurements only — never money |

Anything else is refused. Add a type here (and to `ALLOWED_TYPE_RES` in the script) through a
normal reviewed change, not by passing it in a spec.

## Rules

- **Money.** A column whose name contains `amount`, `price`, `total`, `discount` or `fee` as a
  snake_case word (`discount_amount`, `unit_price`, `shipping_fee`, `total`) must be
  `NUMERIC(12, 2)`. The app uses `Decimal`; a float column silently loses cents.
- **Timestamps.** `TIMESTAMPTZ`, never `TIMESTAMP` / `TIMESTAMP WITHOUT TIME ZONE`.
- **JSON.** `JSONB`, never `JSON`.
- **NOT NULL on an existing table** needs a `DEFAULT`. Postgres rejects `ADD COLUMN … NOT NULL`
  with no default on a table that has rows, and `users` / `orders` always have rows in
  production.
- **Defaults** are simple literals only: a number, a single-quoted string, `TRUE`/`FALSE`,
  `now()`, `CURRENT_DATE`, `CURRENT_TIMESTAMP`. No expressions, no sub-selects.
