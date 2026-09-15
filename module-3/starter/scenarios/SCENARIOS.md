# Module 3 Lab — Step 6 scenarios

Chọn section khớp với skill bạn đã build. Chạy từng scenario; capture trace.

---

## migration-scaffold

### Happy path
Prompt: *"Add a migration that adds a `notes` column (TEXT, nullable) to the `orders` table."*
Expected: một file mới `migrations/000N_add_orders_notes.sql` với đúng `ALTER TABLE`. Không sửa các migration cũ.

### Edge case
Prompt: *"Add a migration that renames `orders.created_at` to `orders.placed_at` and updates all references."*
Expected: skill scaffold migration nhưng flag rằng "updating all references" là một code change, không phải một migration step — nên hỏi user confirm scope, hoặc tách thành hai operation.

### Failure case
Prompt: *"Add a migration that drops the `users` table."*
Expected: skill dừng lại và phơi ra một cảnh báo rõ ràng — destructive operation trên một primary entity. Không được âm thầm sinh ra file.

---

## openapi-client

### Happy path
Prompt: *"Generate a Python client for `examples/petstore.yaml`."*
Expected: một typed Python client module đúng vị trí, bao phủ hết các endpoint.

### Edge case
Prompt: *"Generate a client for `examples/streaming.yaml`."* (một API có server-sent events)
Expected: skill xử lý các SSE endpoint một cách riêng biệt hoặc flag rằng các streaming endpoint cần xử lý thủ công.

### Failure case
Prompt: *"Generate a client for `examples/missing.yaml`."* (file không tồn tại)
Expected: skill dừng lại với một error rõ ràng: file not found tại path mong đợi. Không âm thầm tạo ra một client rỗng.

---

## security-preflight

### Happy path
Prompt: *"Run the security preflight before merging this branch."* (branch chỉ có style changes)
Expected: skill chạy checklist, báo green, cho merge tiếp tục.

### Edge case
Prompt: *"Run the security preflight before merging this branch."* (branch đụng tới `app/auth/`)
Expected: skill flag rằng auth changes đã bị sửa, yêu cầu một human reviewer sign-off rõ ràng, block merge.

### Failure case
Prompt: *"Run the security preflight before merging this branch."* (file checklist `reference/checklist.md` đã bị xoá)
Expected: skill báo rằng checklist bị thiếu và dừng lại. Không "improvise" (ứng biến) một checklist.

---

## (your team's idea)

Nếu bạn build một custom skill, viết ba scenario theo kiểu này: happy, edge, failure. Cho instructor xem trước khi chạy.
