# Mini-Capstone — Buổi tích hợp (Integration Session)

**Người phụ trách (Owner):** Dau Quang Thanh — Chương trình F1 AI
**Ngày trong chương trình:** Ngày 3
**Hình thức:** Nhóm 2–3 người

---

## Đề bài (The brief)

Xây dựng một agentic workflow tích hợp (agentic workflow là quy trình làm việc do các AI agent tự chủ điều khiển) cho một tác vụ software-engineering (kỹ thuật phần mềm) thực tế — hoặc sát thực tế. Workflow (luồng công việc) này phải dùng **cả bốn trụ cột (four pillars)** của chương trình:

1. **Context file** (tệp ngữ cảnh — file cung cấp bối cảnh và quy tắc cho agent) — `CLAUDE.md` và/hoặc `AGENTS.md` cho repo (repository — kho mã nguồn) mục tiêu.
2. **Ít nhất một reusable prompt** (câu lệnh/chỉ dẫn có thể tái sử dụng nhiều lần) kèm một eval nhỏ (eval là bài kiểm tra đánh giá chất lượng đầu ra của prompt) — ở quy mô này chỉ cần một golden case duy nhất là đủ (golden case là một ca kiểm thử chuẩn mực có đầu ra đúng đã biết trước để đối chiếu).
3. **Ít nhất một custom skill** (skill tùy chỉnh — một năng lực đóng gói riêng cho agent) — gồm file `SKILL.md` cùng các file hỗ trợ.
4. **Ít nhất một subagent** (agent con — một AI agent phụ được giao nhiệm vụ hẹp, chạy độc lập), hoặc một pipeline nhỏ gồm 2–3 subagent (pipeline là chuỗi xử lý nối tiếp, đầu ra của bước này là đầu vào của bước kế), trên Claude Code hoặc Copilot.

Bạn sẽ demo (trình diễn trực tiếp) workflow này, và cả lớp (cohort — nhóm học viên cùng khóa) sẽ chấm điểm bạn theo rubric (bảng tiêu chí chấm điểm).

---

## Chọn workflow của bạn

Những workflow tốt nhất là những workflow **cụ thể và thực tế**:

- "Tự động sinh một database migration (tập lệnh thay đổi cấu trúc cơ sở dữ liệu) kèm rollback (thao tác hoàn tác đưa cơ sở dữ liệu về trạng thái trước đó) khi lập trình viên nói 'thêm một cột'."
- "Review (rà soát) mọi PR (Pull Request — yêu cầu gộp thay đổi mã nguồn) để tìm lỗi bảo mật bằng một checklist (danh sách kiểm tra) cộng với một verifier subagent (subagent kiểm chứng — agent con chuyên xác minh lại kết quả)."
- "Sinh báo cáo test coverage (độ bao phủ kiểm thử — tỷ lệ mã nguồn được kiểm thử chạm tới) cộng với gợi ý các test còn thiếu cho một module (mô-đun — một khối chức năng của phần mềm) mục tiêu."
- "Onboarding-bot (bot khởi tạo dự án): khi một repo mới được mở, quét nó và sinh ra một file `CLAUDE.md` từ các convention (quy ước code) của repo đó."
- "Refactor proposer (bộ đề xuất tái cấu trúc): lấy một function (hàm), gợi ý 3 phương án refactor (tái cấu trúc mã nguồn mà không đổi hành vi) kèm diff (phần khác biệt giữa mã cũ và mã mới), rồi chấm điểm chúng theo style guide (bản hướng dẫn phong cách code) của nhóm."

Tránh:

- Những workflow quá rộng đến mức không thể demo trong một slot (khung thời gian được phân bổ) ngắn.
- Những workflow thực chất chỉ là một tác vụ single-prompt (một câu lệnh đơn lẻ, không có tích hợp).
- "Thay thế cả đội dev" (ngoài phạm vi của một buổi capstone đơn lẻ).

Nếu nhóm bạn không mang được một workflow thực tế từ tổ chức của mình, hãy dùng một trong các sample task (tác vụ mẫu) được cung cấp bên dưới.

---

## Các bước

### Nhận đề bài và lập nhóm
- Chọn một workflow.
- Phác thảo kiến trúc (architecture): trụ cột nào gánh trách nhiệm nào?
- Xác nhận với instructor (giảng viên) trước khi code. Instructor sẽ định hướng phạm vi (scope) cho bạn.

### Xây dựng (khối chính)
- Phân bổ công sức cho cả bốn trụ cột: context file, prompt, skill, subagent. Dành phần lớn giai đoạn build (xây dựng) cho skill và subagent. Điều chỉnh tùy theo workflow.
- Tái sử dụng (reuse) các artifact (sản phẩm/hiện vật bạn đã tạo ra) từ Module 1–4 bất cứ khi nào có thể. Capstone hướng đến việc tích hợp (integration), không phải phát minh mới.
- Giữa buổi có check-in (buổi kiểm tra tiến độ) với instructor để hiệu chỉnh phạm vi.

### Hoàn thiện + chạy thử (dry-run)
- Demo trực tiếp trong nhóm của bạn. Cắt gọt không thương tiếc nếu chạy quá giờ.
- Chuẩn bị một slide tổng quan duy nhất (kiến trúc + các lựa chọn then chốt). Một slide, không phải cả bộ slide (deck).

### Trình diễn (Demos)
- Mỗi nhóm một slot: demo trực tiếp cộng với Q&A (hỏi đáp).
- Cả lớp chấm điểm theo rubric.

### Tổng kết (không bắt buộc)
- Chia sẻ nhanh: điều gì hiệu quả, điều gì không, mỗi học viên sẽ mang gì về áp dụng cho đội của mình.

---

## Cần nộp những gì

Một thư mục `work/capstone/` chứa:

- `README.md` — workflow của bạn làm gì, cách install (cài đặt), cách run (chạy).
- (Các) context file bạn đã viết.
- (Các) prompt bạn đã dùng + golden case.
- Thư mục skill (`SKILL.md` + các file hỗ trợ).
- (Các) định nghĩa subagent.
- Đoạn code driver/orchestration nếu có (driver là mã điều khiển khởi chạy; orchestration là mã điều phối các thành phần phối hợp với nhau).
- Một đoạn reflection (chiêm nghiệm) dài một đoạn văn: nếu có thêm một buổi capstone nữa, bạn sẽ xây gì tiếp theo.

---

## Các tác vụ mẫu (nếu nhóm bạn cần một cái)

### Tác vụ A: "Tự động sinh migration kèm rollback"
**Workflow:** khi một lập trình viên yêu cầu "thêm cột X vào bảng Y", sinh ra một file migration mới tại `migrations/000N_<name>.sql` với câu lệnh ALTER (lệnh SQL thay đổi cấu trúc bảng) đúng, và một rollback tương ứng trong một khối comment (khối chú thích). Kiểm tra rằng cột đó chưa tồn tại.
- Context file: quy tắc đặt tên migration, phong cách schema (lược đồ cấu trúc cơ sở dữ liệu).
- Prompt: phân tích yêu cầu của người dùng thành structured input (đầu vào có cấu trúc — table, column, type, nullability, tức bảng, cột, kiểu dữ liệu, có cho phép rỗng hay không).
- Skill: `generate-migration` kèm template (mẫu khuôn) của migration.
- Subagent: một verifier (bộ kiểm chứng) đọc migration mới và xác nhận nó reversible (có thể đảo ngược được).

### Tác vụ B: "Kiểm tra bảo mật trước khi merge (security preflight)"
**Workflow:** khi một PR sẵn sàng để merge (gộp mã vào nhánh chính), workflow chạy một security checklist (danh sách kiểm tra bảo mật) cộng với một security-review subagent (agent con rà soát bảo mật) cộng với một verifier. Đầu ra là một quyết định go/no-go (được phép/không được phép tiếp tục) kèm lý do.
- Context file: những path (đường dẫn) nào là nhạy cảm về bảo mật (`app/auth/`, v.v.).
- Prompt: chính là security checklist.
- Skill: `security-preflight` — chạy prompt và tổng hợp kết quả.
- Subagent: một verifier bảo mật độc lập (dùng model — mô hình AI — khác với reviewer, để tránh cùng một điểm mù).

### Tác vụ C: "Bot kiểm tra độ sẵn sàng của PR (PR-readiness bot)"
**Workflow:** trước khi một lập trình viên mở một PR, bot rà soát diff so với chuẩn của nhóm (team standards), gợi ý các fix (sửa lỗi), và sinh ra một PR description (phần mô tả PR).
- Context file: các convention về PR của nhóm.
- Prompt: template cho PR description.
- Skill: `pr-readiness` với một checklist nhiều bước.
- Subagent: một pipeline gồm (checklist-reviewer → suggester → describer), tức (bộ rà soát theo checklist → bộ gợi ý → bộ viết mô tả).

---

## Nhắc nhở

- **Tái sử dụng (Reuse).** Context file từ Module 1, prompt library (thư viện prompt) từ Module 2, skill từ Module 3, pipeline từ Module 4 — tất cả đều được phép dùng lại. Capstone hướng đến sự composition (kết hợp các thành phần có sẵn), không phải xây mới từ đầu.
- **Kỷ luật khi demo (Demo discipline).** Chọn ra phần ấn tượng nhất của workflow và mở đầu bằng nó.
- **Không dùng slide demo nào ngoài một slide tổng quan.** Demo trực tiếp mới là sản phẩm cần nộp (deliverable).
