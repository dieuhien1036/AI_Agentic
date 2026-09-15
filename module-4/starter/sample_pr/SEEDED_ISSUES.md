# Seeded issues in sample_pr/diff.patch

Dành cho instructor tham khảo. Có bảy issue riêng biệt mà một bản review mạnh nên bắt được:

1. **Edited past migration** — `migrations/0001_initial.sql` lẽ ra không bao giờ được sửa. Thay đổi schema phải đi vào một file mới.
2. **No auth on admin endpoint** — `GET /orders/admin/all` đang là public; lẽ ra phải yêu cầu admin auth.
3. **Returns ALL orders unbounded** — `admin_list_all` không có pagination; sẽ OOM (cạn bộ nhớ) trên một database lớn.
4. **Raw SQL string** — `sql = "SELECT * FROM orders ORDER BY created_at DESC"` đi vòng qua ORM và type system.
5. **Missing return type annotation** trên `admin_list_all`.
6. **Refund corrupts the total** — `refund_order` set `order.total = amount`, làm thay đổi total của order thay vì ghi nhận khoản refund. Lẽ ra phải dùng cột `refund_amount` mới.
7. **Float for money** — `amount: float` lẽ ra phải là `Decimal`. Float làm mất độ chính xác.
8. **Returns dict instead of model** — `refund_order` trả về `{"error": ...}` hoặc `{"status": ...}` thay vì một typed response. Không nhất quán với phần còn lại của API.

Một reviewer subagent mạnh bắt được ít nhất 5 trong số này. Loại yếu bắt được 1–2 cái hiển nhiên (auth, raw SQL).

Module 4 Lab — kỳ vọng ở mỗi bước:
- Step 4 (chạy pipeline baseline): reviewer nên bắt được các issue hiển nhiên (auth gap, raw SQL, thiếu pagination, thiếu type annotation). Nó thường bỏ sót cái migration bị sửa, bug refund-làm-hỏng-total, và issue float-for-money.
- Step 5–6 (hardening pass + re-run): verifier đã được tăng cường nên bắt được ít nhất một issue mà reviewer baseline đã bỏ sót. Nếu không, thì lượt hardening đã không thực sự làm việc gì.
