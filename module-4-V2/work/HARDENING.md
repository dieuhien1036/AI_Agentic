# Hardening pass — Module 4 Lab Step 5

## Pass 1: Tool allowlists

Với mỗi subagent (`.claude/agents/`):

- **pr-planner**
  - Before: `Read, Bash`
  - After: `Read`
  - Justification: driver đưa nguyên diff vào task (`{"diff": ...}`), nên planner không cần
    chạy `git diff --stat`. Planner là role read-only, `Bash` cho phép chạy lệnh tùy ý mà không
    cần dùng tới.

- **file-reviewer**
  - Before: `Read, Grep`
  - After: `Read, Grep` (không đổi)
  - Justification: cần `Read` để đọc cả file trong `repo_root` lấy context, `Grep` để tìm
    usage/call site (ví dụ `OrderStatus`, `_row_to_order`). Cả hai đều read-only.

- **review-aggregator**
  - Before: `[]`
  - After: `[]` (không đổi — đã là zero tools)
  - Justification: aggregator chỉ biến đổi input JSON nó nhận được; không cần đọc file hay chạy gì.

- **review-verifier**
  - Before: `Read, Grep`
  - After: `Read, Grep` (không đổi)
  - Justification: cần đọc code gốc để kiểm tra từng claim của reviewer (false positive) và tìm
    issue bị bỏ sót. Cả hai đều read-only.

## Pass 2: Verifier strengthening

- Thay đổi đối với verifier prompt: không đổi phần hướng dẫn. Chỉ thêm phần "Output contract"
  (JSON Schema) mà driver gắn vào prompt của mọi subagent (xem Pass 3).
- Model khác? **Yes** — `claude-opus-4-6`, khác reviewer (`claude-sonnet-4-5`).
- Bổ sung vào output schema: `schemas/verifier_output.schema.json` — `verdict` là enum
  `approved | changes-requested`; `missed_issues[]` có cùng ràng buộc như issue của reviewer
  (severity/category enum, `line >= 1`, `message` ≤ 280 ký tự); không cho field lạ.
- Một issue mà verifier bắt được mà reviewer đã bỏ sót (hardened run, `runs/hardened/04_verifier.json`):
  - *blocker, app/orders/routes.py:64* — "Setting status='refunded' persists a value OrderStatus
    lacks (pending/paid/shipped/cancelled). The existing list_orders -> _row_to_order calls
    OrderStatus(row.status), so it raises ValueError (HTTP 500) for any user with a refunded order."
- False positive bị flag: không có (`false_positives: []` ở cả hai lần chạy; verifier đã kiểm từng
  claim với repo gốc).

## Pass 3: Structured handoffs

- Schema được thêm vào (`schemas/`):
  - parent → planner: `planner_input.schema.json`
  - planner → parent: `planner_output.schema.json`
  - parent → reviewer: `reviewer_input.schema.json`
  - reviewer → parent / aggregator: `review.schema.json` (từ starter)
  - parent → aggregator: `aggregator_input.schema.json`
  - aggregator → parent: `review.schema.json`
  - parent → verifier: `verifier_input.schema.json`
  - verifier → parent: `verifier_output.schema.json`
- Validation hook trong driver: `call_with_validation()` trong `pipeline.py` bọc mọi lần gọi
  subagent. Nó validate task gửi đi theo input schema, rồi parse response bằng `json.loads`
  (không còn tự gỡ code fence như baseline) và validate theo output schema (`jsonschema`, Draft 7).
  Output schema cũng được gắn vào prompt dưới mục "Output contract".
- Repair flow: nếu output không phải JSON hợp lệ hoặc sai schema, driver gọi lại subagent **một lần**
  với repair prompt (prompt gốc + output cũ + danh sách lỗi validate, yêu cầu chỉ sửa cho đúng
  schema). Nếu vẫn sai thì raise `PipelineError`, log `pipeline_failed`, exit 1, không in kết quả.
  Task gửi đi sai input schema thì dừng ngay (lỗi của driver, không repair).
  - Trong hardened run mọi output đều qua ngay lần đầu, nên repair không bị kích hoạt.
  - Đã kiểm tra repair flow bằng output thật của reviewer baseline (`message` quá 280 ký tự):
    (1) repair trả về bản đúng → `validated attempts=2`; (2) repair vẫn sai → `PipelineError`.

## Comparison vs baseline run (Step 4)

Đối chiếu với 8 issue trong `sample_pr/SEEDED_ISSUES.md` (tính cả reviewer + verifier):

| # | Seeded issue | Baseline | Hardened |
|---|---|---|---|
| 1 | Edited past migration | ✅ | ✅ |
| 2 | No auth on admin endpoint | ✅ | ✅ |
| 3 | Unbounded query (no pagination) | ✅ | ✅ |
| 4 | Raw SQL string | ✅ | ✅ |
| 5 | Missing return type annotation | ❌ | ❌ |
| 6 | Refund corrupts the total | ✅ | ✅ |
| 7 | Float for money | ✅ | ✅ |
| 8 | Returns dict instead of model | ✅ | ✅ |

- Issue bắt được ở lần chạy baseline: **7/8** (thiếu #5). Verifier thêm 2 issue ngoài danh sách:
  `'refunded'` không có trong `OrderStatus` (làm `GET /orders` lỗi 500), và `amount` bị bind
  từ query string.
- Issue bắt được sau hardening: **7/8** (thiếu #5). Verifier thêm: lỗi `'refunded'`/`OrderStatus`
  (blocker), và thiếu regression test cho `GET /orders`.
- Issue bị lật: không có issue nào bị lật. Khác biệt nằm ở tính hợp lệ của handoff:
  - Baseline: **4/5 output vi phạm schema mà không ai phát hiện** (reviewer routes.py: 2 lỗi,
    reviewer migration: 1, aggregator: 3, verifier: 1 — tất cả là `message` dài hơn 280 ký tự).
  - Hardened: **5/5 output hợp lệ**, và giờ driver bắt buộc kiểm tra.
- Khác biệt về cost (tokens của các subagent call, gồm cả overhead của harness):
  baseline ≈ 271k, hardened ≈ 273k (+0.7%, do output schema được gắn vào prompt).
- Khác biệt về latency (planner + max(reviewer) + aggregator + verifier):
  baseline ≈ 103 s, hardened ≈ 106 s — gần như không đổi.

**Tóm tắt diff vs baseline:** hardening thay đổi ba thứ: planner mất `Bash` (giờ mọi role
read-only chỉ có tool đọc, aggregator có zero tools); mọi handoff giữa parent và subagent đều có
JSON Schema và được validate ở cả hai chiều; output sai schema được repair một lần trước khi
pipeline fail. Chất lượng review gần như giữ nguyên (7/8 seeded issue ở cả hai lần, verifier
đều bắt được lỗi `OrderStatus` mà reviewer bỏ sót), nhưng độ tin cậy của handoff thì cải thiện
rõ: ở baseline 4/5 output âm thầm vi phạm contract và vẫn được truyền xuống stage sau; sau
hardening, output nào sai contract đều bị phát hiện, được repair hoặc làm pipeline dừng, với chi
phí token và latency tăng không đáng kể.

## One-paragraph reflection

Phần được harden nhiều nhất là handoff giữa các stage, không phải prompt. Allowlist gần như đã
gọn từ template (chỉ planner thừa `Bash`). Kết quả review cũng không đổi nhiều vì reviewer và
verifier đã được đọc cả file trong repo gốc. Cái đáng giá nhất là validation: không có nó,
baseline đã chuyển 4 output sai schema xuống stage sau mà không ai biết, vì model thường trả
JSON "nhìn đúng" nhưng vi phạm ràng buộc như độ dài `message`. Gắn schema vào prompt giúp model
tự tuân thủ ngay lần đầu, còn validate + repair ở driver là lưới an toàn khi nó không tuân thủ.
Issue #5 (thiếu return type annotation) bị bỏ sót ở cả hai lần; đó là việc cho một lượt
strengthening prompt tiếp theo, ngoài phạm vi pass này.
