# Combined M1+M2 Lab — Foundations

**Owner:** Dau Quang Thanh — F1 AI Program  
**Module:** Combined Module 1 + Module 2  
**Format:** paired (làm theo cặp)  
**Day in program:** Day 1  

Đây là bài lab hands-on duy nhất cho Module 1 và Module 2. Không có lab M1 hay M2 riêng.

> ### 🧭 Trước khi bắt đầu — nói nhanh về việc mình đang làm gì ở đây
>
> Bạn chắc đã từng gặp cảnh này: nhờ một con AI viết code, nó trả về thứ trông thì ổn nhưng đặt sai chỗ, sai convention, đụng vào file lẽ ra không được đụng. Bực. Cả buổi lab hôm nay là để trị đúng cái bực đó — **làm sao để AI viết code đúng "kiểu" của team mình, lần nào cũng vậy, và mình kiểm chứng được chứ không phải đoán.**
>
> Mình sẽ đi qua 4 bước. Đừng nhìn chúng như 4 bài tập rời — nó là một vòng khép kín, mỗi bước gỡ một nút:
>
> | Step | Bạn làm ra cái gì | Nó gỡ nút nào |
> |---|---|---|
> | **1. Context files** | `CLAUDE.md` + `AGENTS.md` | "Làm sao agent biết luật chơi của dự án?" |
> | **2. Prompt library + schema** | 5 prompt dùng lại được + output có schema | "Làm sao prompt thành đồ dùng chung, máy kiểm được, chứ không phải gõ xong là quên?" |
> | **3. CI + regression** | Eval chạy trong CI | "Làm sao chặn một prompt bị làm hỏng trước khi nó lọt vào nhánh chính?" |
> | **4. Verification** | So sánh có-file / không-file | "Làm sao biết chắc context file thật sự có tác dụng, chứ không phải mình tưởng thế?" |
>
> 👉 Một lời khuyên: đọc mỗi Step xong, dừng 5 giây tự hỏi *"cái này gỡ vấn đề gì của mình ngoài đời?"* trước khi gõ lệnh. Mỗi Step dưới đây mình để sẵn một ô **🎯 Mục tiêu / 💡 Vì sao đáng làm / ✅ Xong rồi bạn được gì** để bạn không bị lạc giữa đống command.

---

## Setup

> 🎯 **Mục tiêu:** Dựng một bản `work/` để bạn tha hồ nghịch, còn `starter/` thì để yên đó.  
> 💡 **Vì sao đáng làm:** Nghe thì hiển nhiên, nhưng "nghịch ở bản copy, giữ bản gốc sạch" là một thói quen thật của dân làm nghề. Lỡ làm hỏng thì xoá đi copy lại, chạy lại từ đầu. Mà quan trọng nhất là ở Step 4 bạn sẽ cần một bản gốc nguyên vẹn để *đặt cạnh mà so* — sửa thẳng vào starter là tự cắt mất cái thước đo của chính mình.  
> ✅ **Xong rồi bạn được gì:** Một repo build chạy ngon + bộ khung library là của riêng bạn, nghịch thoải mái không sợ vỡ gì.  

Ghép cặp. Quyết định ai làm driver trước; đổi driver và navigator tại các điểm nghỉ tự nhiên.

1. Mở terminal trong folder này: `labs/combined_m1_m2/`.
2. Copy starter materials vào một thư mục làm việc mà bạn có thể chỉnh sửa:
   ```
   mkdir -p work
   cp -r starter/repo                work/repo
   cp     starter/verification_prompt.md  work/verification_prompt.md
   cp -r starter/library_template    work/library
   cp -r starter/structured_output   work/validate
   cp     starter/ci/eval.yml        work/eval.yml.template
   ```
3. Kiểm tra repo build được:
   ```
   cd work/repo && make setup && make test && cd ../..
   ```
4. Mở `work/` trong editor với Claude Code hoặc GitHub Copilot đang bật. Dùng một platform nhất quán trong suốt lab.

Bạn sẽ làm việc bên trong `work/` cho cả bốn bước. Phần starter giữ nguyên, không đụng vào.

---

## Step 1 — Author `CLAUDE.md` and `AGENTS.md` (paired)

Áp dụng eight-section anatomy (cấu trúc 8 phần) từ phần lý thuyết vào sample repo tại `work/repo/`.

> 🎯 **Mục tiêu:** Viết hai "context file" — `CLAUDE.md` (cho Claude Code) và `AGENTS.md` (chuẩn chung nhiều agent đọc được) — gói lại mọi thứ một người mới vào team, hay một con AI, cần biết để không làm bậy trong repo này: build kiểu gì, convention ra sao, chỗ nào cấm động vào.  
> 💡 **Vì sao đáng làm:** Nếu cả buổi bạn chỉ kịp học một thứ, thì là cái này. Mặc định con AI *chẳng biết gì* về luật ngầm của team bạn — và khi không biết, nó đoán. Context file chính là cách bạn biến "đoán" thành "biết". Khác biệt nó tạo ra rất thật: một bên là code nhận về phải sửa lại từ đầu, một bên là code merge thẳng. Cái khung 8 phần (overview, build/test, conventions, do-not, glossary, escalation, examples, pointers) không phải lý thuyết suông — nó là checklist để bạn khỏi quên mất phần nào.  
> ✅ **Xong rồi bạn được gì:** Bạn biết cách "onboard" một con AI vào một codebase lạ chỉ bằng một file text — và biết dòng nào trong file đẻ ra hành vi nào (Step 4 bạn sẽ tự tay chứng minh).  

### Steps
1. **Explore repo.** Đọc các file sau:
   - `app/main.py`, `app/orders/routes.py`, `app/auth/handlers.py`, `app/types.py`, `app/db.py`
   - `tests/integration/test_orders.py`
   - `migrations/0001_initial.sql`
   - `docs/architecture.md`
   - `Makefile`, `pyproject.toml`, `README.md`

   Liệt kê các convention bạn nhận thấy: build commands, endpoint patterns, những gì rõ ràng là off-limits (không được đụng tới).

2. **Draft `CLAUDE.md`.** Áp dụng eight-section anatomy:
   - Project overview · Build & test · Conventions · Do not · Glossary · Escalation · Examples · Imports / pointers

   Lưu thành `work/repo/CLAUDE.md`.

3. **Draft `AGENTS.md`.** Cùng cấu trúc 8 phần, một file duy nhất (không dùng `@`-imports). Lưu thành `work/repo/AGENTS.md`.

4. **Quick verification.** Chạy một prompt ngắn duy nhất từ bên trong `work/repo/`: *"Add a new endpoint that returns the count of orders for a given user."* Ghi lại xem agent có tuân theo convention của bạn không (file location, type imports, integration test được thêm vào, không thay đổi auth). Đừng dành quá nhiều thời gian ở đây — Step 4 mới là phần verification kỹ lưỡng.

### Acceptance for Step 1
- `work/repo/CLAUDE.md` và `work/repo/AGENTS.md` tồn tại.
- Cả hai bao quát đủ eight-section anatomy bằng các imperative bullet (gạch đầu dòng dạng mệnh lệnh).
- Không có secret nào trong cả hai file.

---

## Step 2 — Five-prompt library + schema-constrained output (paired)

Xây dựng một prompt library tái sử dụng được, nhắm vào cùng `work/repo/` mà bạn vừa author context files cho nó.

> 🎯 **Mục tiêu:** Lấy một việc bạn hay nhờ AI làm đi làm lại (vd "viết test cho function này") và biến nó thành **một bộ 5 prompt có version, dùng lại được** — trong đó ít nhất một cái ép output theo schema cứng, để máy tự kiểm chứ không phải bạn ngồi soi bằng mắt.  
> 💡 **Vì sao đáng làm:** Thú thật đi — đa số chúng ta xài AI kiểu gõ một câu, được thì dùng, xong quên luôn. Lần sau gõ lại từ đầu, chẳng ai biết prompt nào từng cho kết quả tốt. Bước này tập cho bạn coi prompt như **đồ nghề thật**: có tên, có version, review được như code. Còn "schema-constrained output" trị đúng cơn đau đầu lớn nhất khi đưa AI vào sản phẩm: nó trả về lúc thế này lúc thế kia, khi JSON gọn gàng khi lại lảm nhảm cả đoạn văn. Khi bạn ép schema, chạy validator, và thủ sẵn một "repair prompt" để nó tự sửa lúc lỗi — thì phần code phía sau mới dám tin con AI. Đây đúng là cách người ta thật sự cắm LLM vào hệ thống chạy thật.  
> 💡 **Sao phải 5 prompt mà không phải 1?** Vì một việc thật không bao giờ chỉ có một tình huống — có happy path, có edge case, có lúc lỗi... Bắt mình viết 5 biến thể là bắt mình nghĩ hết các ngả task có thể rẽ, thay vì chỉ lo mỗi trường hợp đẹp.  
> ✅ **Xong rồi bạn được gì:** Một prompt library máy kiểm được, cộng với cái phản xạ "ép schema → validate → tự sửa" — mang về team là cắm vào quy trình thật dùng được luôn.  

### Steps
1. **Pick a task family.** Chọn một và confirm với instructor:
   - test generation (write tests for a function)
   - refactor proposals (suggest a refactor with diff)
   - code review (against a checklist)
   - bug triage (categorize and rank from a stack trace)
   - doc generation (write a docstring for a function)

2. **Write five prompts.** Năm biến thể (variation) khác biệt của cùng một task — happy path, edge case, error case, và hai axis (trục) nữa do bạn chọn. Một file cho mỗi prompt dưới `work/library/prompts/`. Mỗi prompt có một frontmatter header nhỏ (`name`, `version`, `model`, `input_kind`, `output_kind`).

3. **Add schema-constrained output to one prompt.** Chọn prompt mang tính production nhất trong năm prompt và làm cho output của nó bị ràng buộc chặt theo schema (strictly schema-constrained):
   - Tái sử dụng `work/validate/review.schema.json` làm schema khởi đầu HOẶC tự viết `work/library/<name>.schema.json` của riêng bạn.
   - Test prompt; capture response vào `work/library/runs/<name>_run1.json`.
   - Chạy `python3 work/validate/validate.py work/library/runs/<name>_run1.json` để xác nhận.
   - Nếu response fail validation, viết một repair prompt one-shot: nhận output gốc + lời phàn nàn của validator và trả về response đã được sửa. Test nó.

4. **Build a small golden set.** Sáu đến mười cặp input/expected trong `work/library/goldens/`. Expected output đủ chính xác để một regression thật sự là một regression thật.

5. **Run harness.** `python3 work/library/harness/run_eval.py`. Lặp lại trên goldens hoặc prompts cho đến khi pass rate đạt >80%.

### Acceptance for Step 2
- Năm prompt trong `work/library/prompts/`, là các variation khác biệt.
- Ít nhất một prompt dùng schema-constrained output với validator + repair flow.
- Golden set với ≥6 case.
- Eval harness báo pass rate >80%.

---

## Step 3 — Eval harness in CI + regression catch (paired)

Tích hợp harness vào CI và minh hoạ nó fail trên một regression cố ý.

> 🎯 **Mục tiêu:** Nhét cái eval harness ở Step 2 vào CI (GitHub Actions), rồi *cố tình* làm hỏng một prompt để tận mắt thấy CI **báo đỏ và chặn lại** — xong sửa lại cho xanh.  
> 💡 **Vì sao đáng làm:** Một bộ test mà không bao giờ bắt được lỗi thì cũng như không. Prompt thì xuống cấp âm thầm y hệt code: ai đó sửa một dòng, output tệ đi tí, chẳng ai để ý — cho tới khi khách hàng kêu. Gắn eval vào CI nghĩa là **mỗi lần đụng vào prompt là máy tự kiểm trước khi merge**, đúng kiểu unit test cho code. Còn cái màn "cố ý phá xem CI có bắt không" nghe hơi ngược đời nhưng cực hay: nó kiểm tra chính golden set của bạn. Bạn phá prompt mà CI vẫn xanh lè? Vậy test của bạn đang *làm cảnh* thôi, chưa gánh được gì. Hơi đau khi nhận ra, nhưng đây là một trong những bài học đáng giá nhất buổi hôm nay.  
> ✅ **Xong rồi bạn được gì:** Bạn biết cách giăng một "lưới an toàn" tự động cho việc dùng AI — và quan trọng hơn, biết cách *thử xem cái lưới đó có thật sự đỡ được gì không* chứ không phải treo lên cho đẹp.  

### Steps
1. **Add workflow.** Copy `work/eval.yml.template` sang `work/library/.github/workflows/eval.yml`. Điều chỉnh paths và python version cho khớp với layout library của bạn.

2. **Run locally first.** `python3 work/library/harness/run_eval.py --strict` phải phản ánh đúng những gì CI sẽ làm. Xác nhận exit code 0.

3. **Demonstrate a regression.** Cố ý làm một trong các prompt của bạn tệ đi — bỏ một constraint, thêm wording mơ hồ. Commit. Chạy `--strict` lại. Xác nhận nó fail. Capture output vào `work/library/REGRESSION_LOG.md`.

4. **Restore.** Revert regression. Xác nhận `--strict` pass.

### Acceptance for Step 3
- CI workflow file hiện diện tại `work/library/.github/workflows/eval.yml`.
- `REGRESSION_LOG.md` cho thấy một failing run đã được capture với (các) golden cụ thể đã bắt được regression.
- Trạng thái cuối cùng pass `--strict`.

---

## Step 4 — Verify the context file is doing work (paired)

Chạy một verification prompt cố định hai lần và truy ngược các khác biệt về các rule cụ thể trong context file của bạn.

> 🎯 **Mục tiêu:** Chạy *đúng một prompt* hai lần — một lần CÓ context file, một lần KHÔNG — rồi chỉ ra ít nhất 3 chỗ agent cư xử khác nhau, và với mỗi chỗ, lần ra được dòng nào trong `CLAUDE.md`/`AGENTS.md` đã gây ra nó.  
> 💡 **Vì sao đáng làm:** Đây là cái khoảnh khắc "à, ra thế" của cả buổi. Ở Step 1 bạn *tin* là context file có ích; tới đây bạn **tận mắt thấy** nó bằng một thí nghiệm có đối chứng đàng hoàng — đổi đúng một biến, giữ nguyên phần còn lại, xem ra kết quả gì. Và nó cũng phơi ra một sự thật hơi phũ: nếu hai lần chạy ra y chang nhau, thì context file của bạn *chẳng làm gì cả*, chỉ là chữ trang trí. Cái kỹ năng lần ngược "hành vi này ← từ rule kia" chính xác là cách sau này bạn debug và mài giũa context file ngoài đời, thay vì ngồi sửa mò.  
> ✅ **Xong rồi bạn được gì:** Bạn không chỉ *viết* được context file, mà còn *đo* được nó có ăn thua không — và khi agent làm sai, bạn biết ngay phải sửa dòng nào.  

### Steps
1. **Run with file.** Mở `work/verification_prompt.md` và chạy prompt đó trong `work/repo/` với `CLAUDE.md` và `AGENTS.md` đang có mặt. Lưu toàn bộ response của agent vào `work/verification/run_with.md`.

2. **Run without file.** Đổi tên các context file thành `.bak` (`mv CLAUDE.md CLAUDE.md.bak` và tương tự cho AGENTS.md). Chạy cùng prompt. Lưu vào `work/verification/run_without.md`. Khôi phục lại các context file.

3. **Annotate diff.** Trong `work/verification/REPORT.md`, liệt kê ít nhất 3 khác biệt bạn quan sát được giữa hai lần chạy. Với mỗi khác biệt, chỉ ra (các) dòng cụ thể trong `CLAUDE.md` hoặc `AGENTS.md` của bạn đã tạo ra nó.

### Acceptance for Step 4
- `run_with.md` và `run_without.md` được capture đầy đủ.
- `REPORT.md` chú thích ≥3 khác biệt với khả năng truy ngược (traceability) về các rule cụ thể trong context file.

---

## Submission

Nộp toàn bộ thư mục `work/`. Nó phải chứa:

```
work/
├── repo/
│   ├── CLAUDE.md
│   └── AGENTS.md
├── library/
│   ├── prompts/                 (5 prompts)
│   ├── goldens/                 (≥6 cases)
│   ├── harness/run_eval.py
│   ├── runs/<name>_run1.json    (validated output)
│   ├── REGRESSION_LOG.md
│   ├── RATIONALE.md             (one page: choices and trade-offs)
│   └── .github/workflows/eval.yml
└── verification/
    ├── run_with.md
    ├── run_without.md
    └── REPORT.md
```

Kèm theo một đoạn reflection (một paragraph) ở cuối `RATIONALE.md`: nếu có thêm một buổi lab nữa thì bạn sẽ làm gì khác đi?

---

## Acceptance criteria (overall)

- Cả `CLAUDE.md` và `AGENTS.md` đều hiện diện và được "tập dượt" (exercised) qua Step 4.
- Năm prompt khác biệt; ít nhất một dùng schema-constrained output.
- Eval harness chạy trên goldens với pass rate được ghi lại.
- CI workflow hiện diện; đã minh hoạ một failing run trên một regression cố ý.
- Verification report xác định ít nhất ba khác biệt giữa run with-vs-without, mỗi cái truy ngược về một rule cụ thể.

Lab được chấm như một artifact duy nhất (xem `RUBRIC.md`). Trọng số đánh giá tổng hợp: **25 %** điểm chương trình.

---

## 🎓 Hết buổi, bạn cầm về được gì?

Nếu chỉ nhớ một điều thôi, thì nhớ cái này: **bạn vừa đi trọn một vòng của việc đưa AI vào một codebase thật** — dạy nó (Step 1), gói lại cách dùng thành đồ chung cho cả team (Step 2), giăng lưới giữ chất lượng cho khỏi tụt (Step 3), rồi chứng minh nó thật sự ăn thua (Step 4).

Không phải mấy thứ học cho biết rồi để đó đâu. Mỗi bước đổi thẳng ra một việc bạn sẽ làm khi mang AI về team:

- **Context file** → onboard agent vào mọi dự án mới, khỏi phải giải thích lại từ đầu mỗi lần.
- **Prompt library + schema** → gom mấy lần xài AI lẻ tẻ thành một quy trình lặp lại được, tin được.
- **CI eval** → giữ cho chất lượng AI khỏi âm thầm tụt dốc theo thời gian.
- **Tư duy verification** → quen miệng hỏi "*làm sao mình biết cái này thật sự chạy được?*" thay vì tin vào cảm giác.

Mang được bốn thói quen này về cho team là bạn đã chạm đúng đích của Module 1 + 2 rồi.
