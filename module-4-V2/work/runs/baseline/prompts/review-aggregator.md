# Review aggregator subagent

## Role
Bạn nhận N JSON review per-file và tạo ra MỘT review gộp duy nhất.

## Input
`{"reviews": [<review per-file>, ...]}`

## Procedure
1. Nối (concatenate) `issues` từ tất cả các per-file review. Giữ nguyên thứ tự.
2. De-duplicate (khử trùng lặp) bất kỳ issue nào xuất hiện ở hơn một file (hiếm, nhưng có thể).
3. Viết một đoạn summary cấp-PR dẫn chiếu tới các issue nghiêm trọng
   nhất.

## Output schema
Cùng hình dạng với reviewer per-file (khớp `schemas/review.schema.json`):
```
{
  "issues": [...],   // de-duped, ordered by severity
  "summary": "<one paragraph>"
}
```

## Failure modes
- Input rỗng: trả về `{"issues": [], "summary": "no issues found"}`.
- Severity không nhất quán giữa các file cho cùng một issue: chọn mức
  severity cao hơn.

## Task
```json
{
  "reviews": [
    {
      "issues": [
        {
          "severity": "blocker",
          "category": "security",
          "file": "app/orders/routes.py",
          "line": 53,
          "message": "The admin endpoint GET /admin/all has no authentication or authorization. Any caller can list every order in the system, including user_id and items (PII and business data).",
          "suggestion": "Add an auth dependency that enforces an admin role (for example Depends(require_admin)). Add a test that a non-admin gets 401/403."
        },
        {
          "severity": "blocker",
          "category": "security",
          "file": "app/orders/routes.py",
          "line": 63,
          "message": "POST /{order_id}/refund has no authentication or authorization. Anyone can refund any order and overwrite its total.",
          "suggestion": "Require an authenticated admin or support role. Ideally also check that the caller is allowed to act on this order."
        },
        {
          "severity": "blocker",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 71,
          "message": "The refund handler overwrites order.total with the refund amount. This destroys the original order total, so the accounting data is wrong. The migration adds a refund_amount column in this same PR, but it is never used. A refund amount larger than the total, or a negative one, is also accepted (a negative amount violates the CHECK (total >= 0) constraint and raises a 500).",
          "suggestion": "Leave total unchanged. Set order.refund_amount = amount and order.status = 'refunded'. Validate 0 < amount <= total (for example with Decimal and Field(gt=0)). Also add refund_amount to OrderRow."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 57,
          "message": "session.execute() is given a raw SQL string. In SQLAlchemy 2.x this raises ObjectNotExecutableError; it must be wrapped in text() or written as a select(). The endpoint will fail at runtime. It also uses SELECT * and has no LIMIT.",
          "suggestion": "Use select(OrderRow).order_by(OrderRow.created_at.desc()).limit(...).offset(...) with (await session.execute(stmt)).scalars().all()."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 69,
          "message": "A missing order returns HTTP 200 with {\"error\": \"not found\"}. This contradicts the module's existing error pattern (HTTPException).",
          "suggestion": "raise HTTPException(status_code=404, detail=\"order not found\")."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 70,
          "message": "The refund has no state checks and is not idempotent. An already refunded or cancelled order can be refunded again, and there is no concurrency control, so two simultaneous refunds can race.",
          "suggestion": "Reject refunds for orders already in refunded/cancelled state (409). Use SELECT ... FOR UPDATE (with_for_update) or an atomic conditional UPDATE. Use OrderStatus.REFUNDED rather than a magic string, and add the value to the enum if it is missing."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 65,
          "message": "amount is typed as float, but money is Decimal elsewhere in this module and in the NUMERIC(12,2) column. This risks rounding errors. The /admin/all response also converts total with float(r.total).",
          "suggestion": "Use Decimal for amount and total in request and response models."
        },
        {
          "severity": "minor",
          "category": "style",
          "file": "app/orders/routes.py",
          "line": 53,
          "message": "The module docstring requires request/response models in app/types.py and no business logic in handlers. The new handlers have no response_model, return hand-built dicts, and put refund logic inline. They also skip the existing _row_to_order mapping. The '# Quick implementation; refine later' comment indicates unfinished work.",
          "suggestion": "Define Refund request and response models in app/types.py. Move the refund logic into a function in repository.py or a sibling module. Use response_model=list[Order] and _row_to_order."
        },
        {
          "severity": "minor",
          "category": "performance",
          "file": "app/orders/routes.py",
          "line": 58,
          "message": "The admin endpoint loads all orders in the system into memory with no pagination, which will degrade and eventually exhaust memory as the table grows.",
          "suggestion": "Add limit/offset (or keyset) pagination parameters with a maximum page size."
        },
        {
          "severity": "minor",
          "category": "testing",
          "file": "app/orders/routes.py",
          "line": 53,
          "message": "The module docstring requires an integration test under tests/integration/test_orders.py for every new endpoint. None is included in this PR for either endpoint (auth, 404, invalid amount, double refund, ordering).",
          "suggestion": "Add integration tests covering the success path and the failure cases for both endpoints."
        },
        {
          "severity": "nit",
          "category": "style",
          "file": "app/orders/routes.py",
          "line": 66,
          "message": "The comment '# Mark order refunded; set status' only restates the code, and the 'update for accounting' comment on the total line is misleading.",
          "suggestion": "Remove it, or explain why the refund is recorded the way it is."
        }
      ],
      "summary": "The two new endpoints are not mergeable. Both the admin listing and the refund endpoint are unauthenticated, so anyone can read all orders or refund any order. The refund overwrites the order total instead of using the new refund_amount column, has no amount validation, and has no state or idempotency checks. It also returns 200 for a missing order. The admin listing passes a raw SQL string to session.execute, which fails on SQLAlchemy 2.x, and it has no pagination or response model. Both endpoints break the module's conventions (types in app/types.py, logic outside handlers, an integration test per endpoint, Decimal for money). The migration change (a nullable refund_amount with default 0) is fine in itself, but it is unused and lacks a CHECK (refund_amount >= 0 AND refund_amount <= total). That file is outside this review."
    },
    {
      "issues": [
        {
          "severity": "blocker",
          "category": "correctness",
          "file": "migrations/0001_initial.sql",
          "line": 25,
          "message": "The diff edits an existing migration in place (adds refund_amount to the CREATE TABLE of orders). The file header says migrations are append-only and must not be edited by hand. Also, CREATE TABLE IF NOT EXISTS is a no-op on environments where orders already exists, so refund_amount will never be added there. Code that reads or writes refund_amount will then fail with 'column does not exist' on existing databases, while fresh databases get the column. This leaves schemas inconsistent across environments.",
          "suggestion": "Revert the change to 0001_initial.sql. Add a new migration, e.g. migrations/0002_add_orders_refund_amount.sql, containing: ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (refund_amount >= 0 AND refund_amount <= total);"
        },
        {
          "severity": "minor",
          "category": "correctness",
          "file": "migrations/0001_initial.sql",
          "line": 25,
          "message": "The new refund_amount column is nullable (DEFAULT 0 but no NOT NULL) and has no CHECK constraint. NULL values and negative or over-total refunds are possible, so the data is inconsistent with the total column, which has NOT NULL and CHECK (total >= 0).",
          "suggestion": "Declare it NOT NULL DEFAULT 0 with CHECK (refund_amount >= 0 AND refund_amount <= total), in the new migration."
        },
        {
          "severity": "minor",
          "category": "testing",
          "file": "migrations/0001_initial.sql",
          "line": 25,
          "message": "No test or migration check covers the schema change. The accompanying refund endpoint in routes.py overwrites order.total instead of using refund_amount, which suggests the new column is not yet wired in or verified.",
          "suggestion": "Add a migration test that applies migrations in order on an existing database and checks that refund_amount exists with the expected constraints. Add a test that the refund flow populates refund_amount rather than mutating total."
        }
      ],
      "summary": "The only change to this file adds a refund_amount column directly to the orders CREATE TABLE in 0001_initial.sql. This breaks the file's append-only rule: databases that already ran the migration never receive the column because of IF NOT EXISTS, so fresh and existing environments diverge. The change should be reverted and moved into a new numbered migration (ALTER TABLE ... ADD COLUMN). The new column should also be NOT NULL with a CHECK bounding it between 0 and total, and migration tests should cover it."
    }
  ]
}
```
