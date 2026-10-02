# Module 4 — Lab Handout

**Owner:** Dau Quang Thanh — F1 AI Program
**Module:** Subagent Development
**Format:** paired (làm theo cặp)
**Day in program:** Day 3

Đây là bài lab hands-on duy nhất của Module 4. Một lab gộp duy nhất, bao trùm cả phần build pipeline lẫn một lượt hardening.

---

## Setup

Ghép cặp. Đổi driver/navigator tại các điểm nghỉ tự nhiên.

1. Mở terminal trong folder này: `labs/module4/`.
2. Copy starter:
   ```
   mkdir -p work
   cp -r starter/sample_pr work/sample_pr
   cp -r starter/pipeline    work/pipeline_template
   cp     starter/hardening/HARDENING.md.tpl work/HARDENING.md.tpl
   ```
3. Chọn một platform: Claude Code hoặc Copilot. Dùng nó cho cả lab.

`work/sample_pr/` là cái PR bạn sẽ review — một diff nhỏ so với sample repo của Module 1, có tám issue được cài sẵn (seeded).

---

## Module 4 Lab — Build and harden a multi-subagent pipeline (paired)

### Learning objective
Hết lab, cặp của bạn đã build xong một code-quality pipeline bốn tầng (planner → reviewer (parallel) → aggregator → verifier) chạy end-to-end trên một sample PR, rồi chạy thêm một lượt hardening duy nhất để siết chặt tool allowlist và thêm các structured handoff có validation.

### Steps

1. **Architecture sketch.** Trên giấy hoặc trong một doc, vẽ ra pipeline. Với mỗi subagent: name, role, model (cheap/fast hay capable?), tools (allowlist), input schema, output schema. **Confirm với instructor trước khi code.** Bước này bắt buộc — đây là chỗ pipeline được định hình.

2. **Build bốn subagent.** Chỉnh lại các template trong `work/pipeline_template/`:
   - `planner.md` — nhận một PR, trả về danh sách file cần review.
   - `reviewer.md` — nhận MỘT file + diff, trả về review có cấu trúc cho file đó. (Nhiều instance chạy parallel, mỗi file một cái.)
   - `aggregator.md` — nhận N output của reviewer, trả về một review gộp.
   - `verifier.md` — nhận review gộp, trả về approve | changes-requested.

   Cài mỗi subagent lên platform của bạn (`.claude/agents/<name>.md` cho Claude Code, hoặc path tương đương bên Copilot).

3. **Wire orchestration (ráp nối điều phối).** Chỉnh `work/pipeline_template/pipeline.py.tpl` thành `work/pipeline.py`. Driver chạy bốn tầng, dispatch các reviewer chạy parallel, aggregate, rồi chạy verifier.

4. **Run trên sample PR.** `python3 work/pipeline.py work/sample_pr/diff.patch`. Capture toàn bộ trace của các tầng vào `work/runs/baseline/`.

5. **Hardening pass.**
   - **Tool allowlists.** Audit danh sách `tools` của từng subagent. Các role read-only (planner, reviewer, verifier) chỉ được cấp tool đọc. Aggregator được cấp ZERO tool (nó chỉ transform input). Document từng thay đổi vào `work/HARDENING.md`.
   - **Structured handoffs.** Định nghĩa một JSON schema cho mỗi task parent → child và mỗi result child → parent. Validate ở mọi boundary. Khi validation fail, retry một lần với một repair prompt trước khi báo fail.

6. **Re-run và document.** Chạy lại pipeline đã hardened trên sample PR. Capture trace vào `work/runs/hardened/`. Diff lại so với baseline. Một đoạn note trong `work/HARDENING.md`: cái gì đã đổi, cái gì cải thiện.

### Acceptance criteria

- Bốn subagent đã được cài.
- `pipeline.py` chạy end-to-end trên sample PR.
- Toàn bộ output baseline của các tầng được capture vào `work/runs/baseline/`.
- Hardening pass hoàn tất: allowlist tối thiểu đã được document, có schema ở mọi handoff, có repair flow khi validation fail.
- Lần chạy pipeline đã hardened được capture vào `work/runs/hardened/`.
- HARDENING.md mô tả phần diff so với baseline.

### Submit

Toàn bộ thư mục `work/` cộng với một architecture diagram (định dạng nào cũng được — sketch tay, draw.io, ASCII) và một bản demo có ghi hình (quay màn hình bằng platform của bạn là ổn).
