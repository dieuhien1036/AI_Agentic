# Five-prompt library — template

> 🎯 **Folder này là gì?** Bộ khung dựng sẵn cho cái prompt library bạn sẽ làm ở Step 2. Thư mục đã chia sẵn theo chuẩn để bạn khỏi phải ngồi nghĩ từ đầu — cứ đổi tên, điền vào, rồi lặp.  
> 💡 **Sao lại tách `prompts/` + `goldens/` + `harness/`?** Để ý mà xem, nó chính là hình dáng của một bộ test bình thường, chỉ là đem áp lên prompt:  
> - `prompts/` = "code" của bạn (thứ đem ra kiểm),
> - `goldens/` = "test case" (input + cái output bạn mong nó ra),
> - `harness/run_eval.py` = "test runner" (chạy mọi prompt với mọi golden rồi báo pass/fail).
>
> Tách ra ba phần như vậy là để gài vào đầu bạn một ý: **prompt là thứ phải đem ra kiểm thử, không phải gõ một phát rồi quăng.** Khi prompt nằm trong cái khung thế này, cả team review được, dùng lại được, và giữ cho nó khỏi xuống cấp (cái đó để Step 3 lo).

Dùng trong **Step 2** của Combined M1+M2 Lab. Setup script copy folder này sang `work/library/`. Rename, điền vào, và iterate.

## Layout

```
prompts/                # one .md or .yaml per prompt; metadata + body
goldens/                # one .yaml per golden; input + expected output
harness/run_eval.py     # runs every prompt against every golden
RATIONALE.md            # why these prompts, this golden set
```

## Prompt format (dùng một trong các convention này một cách nhất quán)

Mỗi prompt là một file trong `prompts/` với một header nhỏ:

```
---
name: write-pytest
version: 1.0.0
model: claude-sonnet-4-5
input_kind: function_source
output_kind: pytest_module
---
[the prompt body]
```

## Golden format

Mỗi golden trong `goldens/` là YAML:

```yaml
id: simple_function
prompt: write-pytest
input: |
  def add(a, b):
      return a + b
expected_substrings:
  - "def test_add"
  - "assert add"
expected_count_at_least: 2  # at least 2 test functions
```

Harness dùng `expected_substrings` (tất cả phải xuất hiện trong output) và tuỳ chọn
`expected_count_at_least` (số dòng `def test_`). Điều chỉnh cho phù hợp với task của bạn.

## Running

```
python3 harness/run_eval.py
```

In ra pass/fail cho mỗi golden. Nhắm tới >80% pass.

## Adding goldens

Golden thật tốt hơn golden tổng hợp (synthetic). Nếu bạn log lại vài cặp prompt+output thật
từ công việc hằng ngày của team và gán nhãn cho chúng, bạn có một test set trung thực.
