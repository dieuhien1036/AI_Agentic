# payments-api — architecture notes

> 🎯 **Đọc file này để làm gì?** Đây là mỏ vàng cho Step 1. README mới cho bạn cái khung thôi; file này mới là chỗ chứa mấy convention sâu mà bạn cần bê vào `CLAUDE.md`/`AGENTS.md` — nhất là phần **Glossary** (bê thẳng vào mục Glossary) và phần **"Things you should not change"** (bê thẳng vào mục "Do not"). Instructor sẽ nhắc bạn đào ở đây chứ đừng có paste lại README cho xong.  
> 💡 **Mẹo nhỏ:** Cứ đọc một dòng ở đây thì tự hỏi luôn "*một con AI mà không biết cái này thì nó sẽ làm hỏng chỗ nào?*" — trả lời được câu đó là bạn có ngay một bullet cho context file.  

## Service shape

Một process FastAPI duy nhất. Hai concern (mối quan tâm) cấp cao nhất:

- **auth/** — login và token issuance. Security-sensitive (nhạy cảm về bảo mật); phạm vi chặt chẽ, không chứa business logic.
- **orders/** — order CRUD. CRUD tiêu chuẩn với một repository layer nhỏ.

Các cross-module concern (types, db engine) nằm ở package root trong `app/`.

## Data layer

- Postgres 15 ở production. Tests dùng Postgres qua testcontainers — không bao giờ dùng SQLite. Schema dựa vào `JSONB` và `TIMESTAMPTZ` mà SQLite không hỗ trợ.
- SQLAlchemy 2.x với async engine (kiểu `asyncpg` qua `psycopg`).
- Migrations là các SQL file append-only (chỉ thêm, không sửa) trong `migrations/`. Deploy pipeline áp dụng chúng.
- Repositories là nội bộ của từng module (`app/orders/repository.py`, `app/auth/queries.py`). Routes không đụng trực tiếp vào ORM.

## Conventions worth knowing

- Tất cả Python file bắt đầu bằng `from __future__ import annotations`.
- Public types (bất cứ thứ gì băng qua một module boundary) nằm trong `app/types.py`. Internal types giữ private trong module của chúng.
- Pydantic v2 cho tất cả request/response model.
- Routes không bao giờ chứa business logic — delegate (uỷ thác) sang một function trong cùng module.
- Endpoint mới nhận được một integration test dưới `tests/integration/`.

## Glossary

- **Order** — một ý định mua hàng của customer (purchase intent). Tạo ở trạng thái `pending`, chuyển qua `paid` → `shipped`. Có thể `cancelled` từ bất kỳ trạng thái non-terminal nào.
- **Order item** — một dòng trên một order: SKU, quantity, unit price.
- **Token** — JWT phát hành lúc login. TTL 24h. Ký HS256 (HS256-signed). Secret lấy từ env var `JWT_SECRET`.

## Things you should not change without explicit human review

- `app/auth/*` — security-sensitive. Owner: security lead.
- `migrations/*` — append-only theo policy. Thay đổi schema nằm trong một file mới.
- `app/db.py` — chuyển từ Postgres sang database khác sẽ làm hỏng schema; đừng đề xuất việc đó.

## Where to find more

- Operational runbook: internal wiki, "payments-api runbook".
- On-call rotation: PagerDuty service "payments-api".
- Deploy pipeline: GitHub Actions workflow `.github/workflows/deploy.yml`.
