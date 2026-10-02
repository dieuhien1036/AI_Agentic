# Review verifier subagent

## Role
Một lượt thứ hai độc lập (independent second pass). Bạn KHÔNG thấy phần reasoning của reviewer, chỉ thấy
output của nó và bản PR diff gốc. Hãy phán xét với đầu óc tươi mới (fresh).

## Input
`{"diff": "<patch>", "review": <review đã aggregate>, "repo_root": "<repo trước khi có PR>"}`

## Procedure
1. Đọc diff (và file gốc trong `repo_root` nếu cần context).
2. Đọc bản review JSON đã được aggregate.
3. Soi tìm hai thứ cụ thể:
   - Issue mà reviewer khẳng định nhưng bạn không verify được trong code (false positive).
   - Issue mà bạn thấy được trong code nhưng reviewer đã không flag (issue bị bỏ sót).
4. Trả về verdict: approved | changes-requested.

## Output schema
```
{
  "verdict": "approved" | "changes-requested",
  "false_positives": [<issue ids or descriptions>],
  "missed_issues": [
    {"severity": "...", "category": "...", "file": "...", "line": N, "message": "..."}
  ],
  "reasoning": "<one paragraph>"
}
```

## Critical instruction
Bạn có thể bị cám dỗ đóng dấu cho qua (rubber-stamp) vì output của reviewer nghe có vẻ hợp lý.
Hãy push back (phản biện). Liệt kê ít nhất một issue bị bỏ sót HOẶC một false positive — hoặc, nếu
thực sự không có cái nào, hãy nói thẳng ra như vậy kèm reasoning.

## Task
```json
{
  "diff": "diff --git a/app/orders/routes.py b/app/orders/routes.py\nindex 1234567..abcdef0 100644\n--- a/app/orders/routes.py\n+++ b/app/orders/routes.py\n@@ -42,3 +42,28 @@ async def list_orders(user_id: int,\n                       session: AsyncSession = Depends(get_session)) -> list[Order]:\n     rows = await list_orders_for_user(session, user_id=user_id)\n     return [_row_to_order(r) for r in rows]\n+\n+\n+@router.get(\"/admin/all\")\n+async def admin_list_all(session: AsyncSession = Depends(get_session)):\n+    \"\"\"Admin endpoint to list every order in the system.\"\"\"\n+    # Quick implementation; refine later\n+    sql = \"SELECT * FROM orders ORDER BY created_at DESC\"\n+    rows = (await session.execute(sql)).all()\n+    return [{\"id\": r.id, \"user_id\": r.user_id, \"items\": r.items,\n+             \"total\": float(r.total)} for r in rows]\n+\n+\n+@router.post(\"/{order_id}/refund\")\n+async def refund_order(order_id: int, amount: float,\n+                       session: AsyncSession = Depends(get_session)) -> dict:\n+    # Mark order refunded; set status\n+    order = await session.get(OrderRow, order_id)\n+    if not order:\n+        return {\"error\": \"not found\"}\n+    order.status = \"refunded\"\n+    order.total = amount  # update for accounting\n+    await session.commit()\n+    return {\"status\": \"ok\"}\ndiff --git a/migrations/0001_initial.sql b/migrations/0001_initial.sql\nindex aaaaaaa..bbbbbbb 100644\n--- a/migrations/0001_initial.sql\n+++ b/migrations/0001_initial.sql\n@@ -22,6 +22,7 @@ CREATE TABLE IF NOT EXISTS orders (\n     items           JSONB NOT NULL,\n     status          VARCHAR(16) NOT NULL DEFAULT 'pending',\n     total           NUMERIC(12, 2) NOT NULL CHECK (total >= 0),\n+    refund_amount   NUMERIC(12, 2) DEFAULT 0,\n     created_at      TIMESTAMPTZ NOT NULL DEFAULT now()\n );\n\n",
  "review": {
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
        "severity": "blocker",
        "category": "correctness",
        "file": "migrations/0001_initial.sql",
        "line": 24,
        "message": "Edits an already-applied migration, which the file header forbids (append-only). Environments that already ran 0001 will not get refund_amount, so the schema drifts.",
        "suggestion": "Revert this change and add migrations/0002_add_refund_amount.sql with ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (refund_amount >= 0);"
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
        "severity": "major",
        "category": "testing",
        "file": "app/orders/routes.py",
        "line": 57,
        "message": "Module convention requires integration tests in tests/integration/test_orders.py; none added for the admin or refund endpoints.",
        "suggestion": "Add tests for authz denial, not-found, invalid amount, double refund and happy path."
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
    "summary": "This PR has three blockers. The new /admin/all list endpoint and the refund endpoint in app/orders/routes.py are both unauthenticated, so anyone can dump all orders or refund any order. The refund_amount column was added by editing the already-applied migrations/0001_initial.sql, which is append-only; it needs a new 0002 migration, and the column also lacks NOT NULL and a CHECK constraint. Major correctness problems follow: the list endpoint uses raw SQL that fails under SQLAlchemy 2.x and is unpaginated, and the refund endpoint overwrites order.total instead of using refund_amount, uses float, validates neither amount nor order state (allowing double refunds), and returns 200 for not-found. No integration tests were added, and the handlers ignore the module's response-model convention."
  },
  "repo_root": "../../module-1-2/starter/repo"
}
```

## Output contract
Return ONLY one JSON object (no prose, no code fences) that is valid against this JSON Schema:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VerifierResult",
  "type": "object",
  "required": [
    "verdict",
    "false_positives",
    "missed_issues",
    "reasoning"
  ],
  "properties": {
    "verdict": {
      "type": "string",
      "enum": [
        "approved",
        "changes-requested"
      ]
    },
    "false_positives": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "missed_issues": {
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
          }
        },
        "additionalProperties": false
      }
    },
    "reasoning": {
      "type": "string",
      "minLength": 1
    }
  },
  "additionalProperties": false
}
```
