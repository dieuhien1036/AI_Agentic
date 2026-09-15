---
name: write-pytest
version: 1.0.0
model: claude-sonnet-4-5
input_kind: function_source
output_kind: pytest_module
---

Write pytest tests for the function below.

Constraints:
- Use pytest. No other framework.
- Each test function name starts with `test_`.
- Cover: happy path, one edge case (empty/zero/None as appropriate), one boundary.
- Type hints in test signatures: keep them.
- No mocks unless the function makes network or I/O calls.
- Keep it short — one assertion per test where possible.

Output format: Python source code only. No prose. No markdown fences.

Function:

<input>
{INPUT}
</input>
