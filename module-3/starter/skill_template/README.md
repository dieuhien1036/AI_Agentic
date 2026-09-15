# Skill template

Fork folder này. Đổi tên thành tên skill của bạn.

```
SKILL.md             # the contract (rename SKILL.md.tpl)
scripts/             # executables the agent can call (one per file)
templates/           # file scaffolds with placeholders
reference/           # longer rules the agent fetches on demand
```

## Steps to start

1. `cp SKILL.md.tpl SKILL.md` và điền vào.
2. Bỏ scripts vào `scripts/`. Làm chúng idempotent.
3. Bỏ templates với `{PLACEHOLDERS}` vào `templates/`.
4. Dùng `reference/` cho nội dung quá dài để inline.
5. Install:
   - **Claude Code:** `cp -r . .claude/skills/<your-skill-name>/`
   - **Copilot:** copy folder vào skills path đã cấu hình của workspace; register trong workspace settings.

## Test trigger reliability

Viết 5 prompt lẽ ra phải trigger skill, 5 prompt lẽ ra không. Chạy chúng.
Skill nên fire trên 5/5 và im lặng trên 5/5. Iterate description
cho tới khi đạt.
