# payments-api

> 🎯 **Repo này là gì, mình làm gì với nó?** Một codebase "mồi" — FastAPI service giả lập một dịch vụ như ngoài đời. Bạn KHÔNG phải sửa nghiệp vụ của nó. Việc của bạn là *ngắm* nó như một người mới vừa join team, rồi viết `CLAUDE.md`/`AGENTS.md` để tả lại cái convention của nó (Step 1).  
> 💡 **Sao phải repo thật, không lấy ví dụ đồ chơi cho nhanh?** Vì context file chỉ có nghĩa khi có thứ thật để mà tả: vùng cấm thật (`migrations/`, `app/auth/`), convention thật (`from __future__ import annotations`, public type nằm ở `app/types.py`), lệnh build thật (`make`). Ví dụ đồ chơi không dạy bạn được mấy cái đó. Cứ đọc repo này như thể mai bạn phải bàn giao nó cho một con AI làm tiếp.  

Một FastAPI service nhỏ để xử lý customer orders và xác thực (authenticate) customer. Dùng làm lab repo cho F1 AI Program — Module 1.

## What's here

```
app/
  main.py             # FastAPI entry point and route registration
  auth/handlers.py    # login + token-issuing endpoints
  orders/routes.py    # order CRUD endpoints
  types.py            # public Pydantic models shared across modules
  db.py               # SQLAlchemy engine + session helpers
tests/
  conftest.py
  integration/        # integration tests; one per route module
migrations/
  0001_initial.sql    # schema bootstrap; do not edit by hand
docs/
  architecture.md     # deeper design notes
```

## How to use it for the lab

Đây là một snapshot của một service có hình hài như ngoài đời thực (real-world-shaped). Bạn sẽ viết một `CLAUDE.md` và một `AGENTS.md` để nắm bắt các convention mà một developer mới (hoặc một agent) cần biết.

Đừng thay đổi code trong `starter/` — copy nó sang một folder `work/` mà bạn có thể chỉnh sửa.
