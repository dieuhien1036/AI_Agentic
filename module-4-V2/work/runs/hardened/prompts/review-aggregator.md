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
          "line": 47,
          "message": "/admin/all has no authentication or authorization; any caller can dump every order (user_id, items, totals) in the system.",
          "suggestion": "Add an admin-only dependency (e.g. Depends(require_admin)) and return 401/403 for non-admins."
        },
        {
          "severity": "blocker",
          "category": "security",
          "file": "app/orders/routes.py",
          "line": 57,
          "message": "Refund endpoint has no auth or ownership/role check; anyone can refund any order and alter its total.",
          "suggestion": "Require an authenticated admin/finance role via a dependency before mutating the order."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 51,
          "message": "Raw SQL string passed to session.execute; SQLAlchemy 2.x requires text() and this raises ArgumentError at runtime. Also uses SELECT * and r.items/r.total access is brittle.",
          "suggestion": "Use select(OrderRow).order_by(OrderRow.created_at.desc()) with scalars().all(), or wrap in text()."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 65,
          "message": "Refund overwrites order.total with the refund amount, destroying original order total; the new refund_amount column is never used.",
          "suggestion": "Set order.refund_amount = amount and keep total unchanged (add the column to OrderRow)."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 58,
          "message": "No validation of refund amount: negative, zero, or greater than total is accepted (negative violates the total >= 0 CHECK). amount is a float, causing money precision errors.",
          "suggestion": "Use Decimal, validate 0 < amount <= order.total, reject otherwise with HTTP 400/422."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 62,
          "message": "No state check: already-refunded, cancelled or unpaid orders can be refunded again (not idempotent), enabling double refunds.",
          "suggestion": "Verify current status is refundable and return 409 if already refunded; lock row with with_for_update()."
        },
        {
          "severity": "major",
          "category": "correctness",
          "file": "app/orders/routes.py",
          "line": 63,
          "message": "Not-found returns HTTP 200 with {\"error\": ...} instead of a 404, inconsistent with module's HTTPException usage; the status string 'refunded' is also a raw literal not in OrderStatus.",
          "suggestion": "raise HTTPException(status_code=404, detail=\"order not found\") and use OrderStatus.REFUNDED (add if missing)."
        },
        {
          "severity": "major",
          "category": "performance",
          "file": "app/orders/routes.py",
          "line": 52,
          "message": "Admin endpoint loads every order in the table into memory with no pagination or limit.",
          "suggestion": "Add limit/offset (or keyset) pagination parameters with a sane max."
        },
        {
          "severity": "minor",
          "category": "style",
          "file": "app/orders/routes.py",
          "line": 48,
          "message": "Violates module's stated pattern: no response_model/types in app/types.py, hand-built dicts, float(r.total) loses Decimal precision, business logic inline in handlers.",
          "suggestion": "Define response models in app/types.py, return Order via _row_to_order, and delegate to repository functions."
        },
        {
          "severity": "minor",
          "category": "style",
          "file": "app/orders/routes.py",
          "line": 50,
          "message": "'Quick implementation; refine later' comment signals unfinished code merged into production path.",
          "suggestion": "Finish the implementation or remove the TODO-style comment."
        },
        {
          "severity": "major",
          "category": "testing",
          "file": "app/orders/routes.py",
          "line": 57,
          "message": "Module convention requires integration tests in tests/integration/test_orders.py; none added for the admin or refund endpoints.",
          "suggestion": "Add tests for authz denial, not-found, invalid amount, double refund and happy path."
        }
      ],
      "summary": "The PR adds an admin list endpoint and a refund endpoint to app/orders/routes.py that are both unauthenticated, which is a blocker. The list endpoint uses raw SQL that will fail under SQLAlchemy 2.x and is unpaginated. The refund endpoint overwrites the order total instead of using the new refund_amount column, uses float, validates nothing about the amount or order state, allows double refunds, and returns 200 for not-found. Neither endpoint follows the module's response-model convention, and no tests were added."
    },
    {
      "issues": [
        {
          "severity": "blocker",
          "category": "correctness",
          "file": "migrations/0001_initial.sql",
          "line": 24,
          "message": "Edits an already-applied migration, which the file header forbids (append-only). Environments that already ran 0001 will not get refund_amount, so the schema drifts.",
          "suggestion": "Revert this change and add migrations/0002_add_refund_amount.sql with ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (refund_amount >= 0);"
        },
        {
          "severity": "minor",
          "category": "correctness",
          "file": "migrations/0001_initial.sql",
          "line": 24,
          "message": "refund_amount is nullable and has no CHECK constraint. It can be NULL or negative, or exceed total, unlike the total column's guard.",
          "suggestion": "Declare it NOT NULL DEFAULT 0 with CHECK (refund_amount >= 0 AND refund_amount <= total)."
        },
        {
          "severity": "minor",
          "category": "testing",
          "file": "migrations/0001_initial.sql",
          "line": 24,
          "message": "The new column is not used by the accompanying refund_order route, which overwrites total instead. No test or code covers refund_amount.",
          "suggestion": "Have refund_order write refund_amount (validated against total) and keep total unchanged. Add a test for it."
        }
      ],
      "summary": "The only change to this file adds a refund_amount column directly to the existing 0001_initial.sql. That file's header says migrations are append-only and must not be edited, because environments that already ran it would never receive the column. The change should be moved into a new numbered migration (0002). The column definition also lacks NOT NULL and a CHECK constraint, so it can hold NULL or negative values. The refund route in the same PR does not populate the column, so it is currently unused."
    }
  ]
}
```

## Output contract
Return ONLY one JSON object (no prose, no code fences) that is valid against this JSON Schema:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReviewResult",
  "type": "object",
  "required": [
    "issues",
    "summary"
  ],
  "properties": {
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "severity",
          "category",
          "file",
          "line",
          "message"
        ],
        "properties": {
          "severity": {
            "type": "string",
            "enum": [
              "blocker",
              "major",
              "minor",
              "nit"
            ]
          },
          "category": {
            "type": "string",
            "enum": [
              "correctness",
              "security",
              "performance",
              "style",
              "testing"
            ]
          },
          "file": {
            "type": "string"
          },
          "line": {
            "type": "integer",
            "minimum": 1
          },
          "message": {
            "type": "string",
            "minLength": 1,
            "maxLength": 280
          },
          "suggestion": {
            "type": [
              "string",
              "null"
            ]
          }
        },
        "additionalProperties": false
      }
    },
    "summary": {
      "type": "string",
      "minLength": 1
    }
  },
  "additionalProperties": false
}
```
