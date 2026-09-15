# Module 3 — Lab Handout

**Owner:** Dau Quang Thanh — F1 AI Program
**Module:** Agent Skill Development
**Format:** paired (làm theo cặp)
**Day in program:** Day 2

Đây là bài lab hands-on duy nhất cho Module 3. Một lab gộp duy nhất, bao trùm authoring, install, iterate trên discovery contract, và scenario testing.

---

## Setup

Ghép cặp. Đổi driver/navigator tại các điểm nghỉ tự nhiên.

1. Mở terminal trong folder này: `labs/module3/`.
2. Copy starter materials:
   ```
   mkdir -p work
   cp -r starter/skill_template work/skill
   cp     starter/scenarios/SCENARIOS.md work/SCENARIOS.md
   ```
3. Đọc `starter/README.md` để nắm layout.

Bạn sẽ dùng platform tuỳ chọn (Claude Code hoặc Copilot). Chọn một và bám theo nó trong suốt lab.

---

## Module 3 Lab — Build a skill end-to-end and verify it triggers reliably (paired)

### Learning objective
Hết lab, cặp của bạn đã làm ra một skill cài được (installable) — trigger đáng tin trên đúng các prompt cần trigger, im lặng trên các prompt lân cận, và xử lý được ba scenario thực tế: happy path, edge case, và một failure case mà nó buộc phải fail loudly (fail rõ ràng, ồn ào).

### Steps

1. **Pick a task and set up.** Chọn một task family và confirm với instructor:
   - **migration-scaffold** — sinh ra một database migration file đúng format
   - **openapi-client** — sinh ra một typed Python client từ một OpenAPI spec
   - **security-preflight** — chạy một checklist trước khi merge các thay đổi đụng tới auth hoặc migrations
   - **(your team's idea)** — phải được instructor duyệt

   Đổi tên `work/skill/` thành `work/<your-skill-name>/` và `cp work/<your-skill-name>/SKILL.md.tpl work/<your-skill-name>/SKILL.md`.

2. **Author SKILL.md.** Frontmatter: `name`, `description` (một câu action + trigger phrases + negative scope), `version`. Body: imperative numbered steps (các bước đánh số dạng mệnh lệnh), conventions, failure modes, pointers trỏ tới các reference file. Giữ trong khoảng 50–100 dòng.

3. **Build supporting files.** Tuỳ task của bạn cần:
   - `scripts/` cho các executable mà agent gọi được (mỗi script một entry point duy nhất).
   - `templates/` cho các file scaffold có placeholder.
   - `reference/` cho các rule dài hơn mà agent fetch khi cần (on demand).

   Làm scripts idempotent. Dùng templates với `{PLACEHOLDERS}` rõ ràng.

4. **Install on your platform.**
   - **Claude Code:** `cp -r work/<your-skill-name>/ ~/.claude/skills/` (hoặc vào `<repo>/.claude/skills/` nếu scope theo repo).
   - **Copilot:** copy folder vào skills path đã cấu hình của workspace; register trong workspace settings.
   - Xác nhận agent load được nó (mở một session, nhắc tới mảng việc của skill).

5. **Iterate the discovery contract.** Chạy hai batch test prompts:
   - **5+ positive prompts** lẽ ra phải trigger skill. Ghi lại cái nào trigger, cái nào không.
   - **5+ negative prompts** lẽ ra KHÔNG được trigger (task lân cận, query chỉ-đọc, việc không liên quan). Ghi lại cái nào fire sai.
   - Tinh chỉnh description sau mỗi vòng. Siết trigger phrases cho các ca miss; thêm negative scope cho các ca false fire. Lặp cho tới khi 5/5 positive và 5/5 negative đều đúng.

6. **Drive through three scenarios.** Mở `work/SCENARIOS.md`. Với task type của bạn, chạy ba scenario:
   - **Happy path:** input sạch, thường gặp. Skill sinh ra đúng artifact mong đợi.
   - **Edge case:** input ở biên (rỗng / max-size / mơ hồ). Skill xử lý gọn gàng hoặc hỏi lại để làm rõ.
   - **Failure case:** input mà skill không thể hoàn thành. Skill buộc phải fail với một thông báo rõ ràng, cụ thể. Không crash. Không ứng biến (improvise). Không để lại partial state.

   Capture toàn bộ agent trace cho từng scenario vào `work/runs/run1_happy.md`, `run2_edge.md`, `run3_failure.md`.

7. **Document.** Thêm `work/<your-skill-name>/README.md`: task family nào, ai sẽ dùng, install instructions. Một trang.

### Acceptance criteria

- Một skill chạy được, đã cài trên ít nhất một platform.
- 5/5 positive prompts trigger; 5/5 negative prompts im lặng.
- Cả ba scenario trace đã được capture. Failure case fail một cách gracefully (thông báo rõ ràng, không crash, không có artifact dở dang).
- README.md nằm trong folder skill.

### Submit

Toàn bộ folder `work/<your-skill-name>/` cộng `work/runs/` và một `REPORT.md` ngắn, chấm mỗi scenario trong ba cái là pass / partial / fail kèm một dòng lý do.
