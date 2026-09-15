# Module 3 — Lab Handout

**Owner:** Dau Quang Thanh — F1 AI Program
**Module:** Agent Skill Development
**Format:** paired
**Day in program:** Day 2

This is the only hands-on lab for Module 3. Single combined lab covering authoring, install, iteration on the discovery contract, and scenario testing.

---

## Setup

Pair up. Switch driver/navigator at natural breaks.

1. Open a terminal in this folder: `labs/module3/`.
2. Copy starter materials:
   ```
   mkdir -p work
   cp -r starter/skill_template work/skill
   cp     starter/scenarios/SCENARIOS.md work/SCENARIOS.md
   ```
3. Read `starter/README.md` for layout.

You'll use the platform of your choice (Claude Code or Copilot). Pick one and stick with it for the whole lab.

---

## Module 3 Lab — Build a skill end-to-end and verify it triggers reliably (paired)

### Learning objective
By the end of the lab, the pair has produced an installable skill that triggers reliably on the right prompts, stays silent on adjacent prompts, and handles three realistic scenarios — happy path, edge case, and a failure case where it must fail loudly.

### Steps

1. **Pick a task and set up.** Choose one task family and confirm with the instructor:
   - **migration-scaffold** — generate a database migration file in the right format
   - **openapi-client** — generate a typed Python client from an OpenAPI spec
   - **security-preflight** — run a checklist before merging changes that touch auth or migrations
   - **(your team's idea)** — instructor approval required

   Rename `work/skill/` to `work/<your-skill-name>/` and `cp work/<your-skill-name>/SKILL.md.tpl work/<your-skill-name>/SKILL.md`.

2. **Author SKILL.md.** Frontmatter: `name`, `description` (one-sentence action + trigger phrases + negative scope), `version`. Body: imperative numbered steps, conventions, failure modes, pointers to reference files. Keep it 50–100 lines.

3. **Build supporting files.** As needed for your task:
   - `scripts/` for executables the agent can call (one entry point per script).
   - `templates/` for file scaffolds with placeholders.
   - `reference/` for longer rules the agent fetches on demand.

   Make scripts idempotent. Use templates with explicit `{PLACEHOLDERS}`.

4. **Install on your platform.**
   - **Claude Code:** `cp -r work/<your-skill-name>/ ~/.claude/skills/` (or to `<repo>/.claude/skills/` if scoped to a repo).
   - **Copilot:** copy folder under your workspace's configured skills path; register in workspace settings.
   - Confirm the agent loads it (start a session, mention the skill area).

5. **Iterate the discovery contract.** Run two batches of test prompts:
   - **5+ positive prompts** that should trigger the skill. Capture which trigger and which don't.
   - **5+ negative prompts** that should NOT trigger (adjacent tasks, read-only queries, unrelated work). Capture which fire incorrectly.
   - Refine the description after each round. Tighten trigger phrases for misses; add negative scope for false fires. Repeat until 5/5 positive and 5/5 negative are correct.

6. **Drive through three scenarios.** Open `work/SCENARIOS.md`. For your task type, run the three scenarios:
   - **Happy path:** clean, common input. Skill produces the expected artifact.
   - **Edge case:** boundary input (empty / max-size / ambiguous). Skill handles it cleanly or asks for clarification.
   - **Failure case:** input the skill cannot complete. Skill must fail with a clear, specific message. No crash. No improvising. No partial state.

   Capture the full agent trace for each scenario in `work/runs/run1_happy.md`, `run2_edge.md`, `run3_failure.md`.

7. **Document.** Add `work/<your-skill-name>/README.md`: what task family, who'd use it, install instructions. One page.

### Acceptance criteria

- Working skill installed on at least one platform.
- 5/5 positive prompts trigger; 5/5 negative prompts stay silent.
- All three scenario traces captured. Failure case fails gracefully (clear message, no crash, no partial artifact).
- README.md in the skill folder.

### Submit

The whole `work/<your-skill-name>/` folder plus `work/runs/` and a short `REPORT.md` scoring each of the three scenarios as pass / partial / fail with one-line rationale.
