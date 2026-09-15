# Hardening pass — Module 4 Lab Step 5

## Pass 1: Tool allowlists

Với mỗi subagent:

- **pr-planner**
  - Before: [list]
  - After: [list]
  - Justification: [vì sao mỗi tool là cần thiết]

- **file-reviewer**
  - Before: [list]
  - After: [list]
  - Justification:

- **review-aggregator**
  - Before: [list]
  - After: [list]
  - Justification:

- **review-verifier**
  - Before: [list]
  - After: [list]
  - Justification:

## Pass 2: Verifier strengthening

- Thay đổi đối với verifier prompt:
  - [list]
- Model khác? [yes/no — model nào]
- Bổ sung vào output schema: [list]
- Một issue mà verifier mới bắt được mà reviewer trước đó đã bỏ sót:
  - [dán issue cụ thể vào đây]
- Hoặc: false positive bị flag:
  - [dán vào đây]

## Pass 3: Structured handoffs

- Schema được thêm vào:
  - [parent → planner: schema]
  - [planner → reviewer: schema]
  - [reviewer → aggregator: schema]
  - [aggregator → verifier: schema]
- Validation hook trong driver: [chỗ nào + cách nào]
- Repair flow: [nếu validation fail, chuyện gì xảy ra]

## Comparison vs baseline run (Step 4)

- Issue bắt được ở lần chạy baseline: [số lượng và danh sách]
- Issue bắt được sau hardening: [số lượng và danh sách]
- Issue bị lật (false positive bị loại bỏ, catch bị sót được thêm vào): [list]
- Khác biệt về cost: [tokens / dollars]
- Khác biệt về latency: [seconds]

## One-paragraph reflection

Cái gì được hardened nhiều nhất? Bạn đổ công sức vào đâu và nó có đáng không?
