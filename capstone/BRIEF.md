# Mini-Capstone — Integration Session

**Owner:** Dau Quang Thanh — F1 AI Program
**Day in program:** Day 3
**Format:** Teams of 2–3

---

## The brief

Build one integrated agentic workflow for a real (or realistic) software-engineering task. The workflow must use **all four pillars** from the program:

1. **Context file** — `CLAUDE.md` and/or `AGENTS.md` for the target repo.
2. **At least one reusable prompt** with a small eval (a single golden case is enough at this scale).
3. **At least one custom skill** — `SKILL.md` plus supporting files.
4. **At least one subagent** (or a small pipeline of 2–3) on Claude Code or Copilot.

You'll demo the workflow live, with the cohort scoring you against the rubric.

---

## Picking your workflow

Best workflows are **specific and real**:

- "Auto-generate a database migration with rollback when a developer says 'add a column'."
- "Review every PR for security issues using a checklist + verifier subagent."
- "Generate test coverage reports + suggested missing tests for a target module."
- "Onboarding-bot: when a new repo is opened, scan it and generate a CLAUDE.md from its conventions."
- "Refactor proposer: take a function, suggest 3 refactor options with diffs, score against the team's style guide."

Avoid:

- Workflows so broad they can't be demoed in a short live slot.
- Workflows that are really just a single-prompt task (no integration).
- "Replace the dev team" (out of scope for a single capstone session).

If your team can't bring a real workflow from your org, use one of the provided sample tasks below.

---

## Steps

### Brief and team formation
- Pick a workflow.
- Sketch the architecture: which pillar carries which responsibility?
- Confirm with the instructor before coding. The instructor will steer scope.

### Build (main block)
- Allocate effort across the four pillars: context file, prompt, skill, subagent. Spend the bulk of the build phase on the skill and subagent. Adjust per workflow.
- Reuse artifacts you built in Modules 1–4 wherever possible. The capstone is about integration, not invention.
- Mid-session check-in with the instructor for scope correction.

### Polish + dry-run
- Live demo in your team. Trim ruthlessly if it runs long.
- Prepare a one-slide overview (architecture + key choices). One slide, not a deck.

### Demos
- One slot per team: live demo plus Q&A.
- Cohort scores using the rubric.

### Wrap (optional)
- Quick share-out: what worked, what didn't, what each trainee will take back to their team.

---

## What to submit

A folder `work/capstone/` containing:

- `README.md` — what your workflow does, how to install, how to run.
- The context file(s) you authored.
- The prompt(s) you used + the golden case.
- The skill folder (SKILL.md + supporting files).
- The subagent definition(s).
- The driver / orchestration code if any.
- A one-paragraph reflection: what you'd build next if you had another capstone session.

---

## Sample tasks (if your team needs one)

### Task A: "Auto-generate a migration with rollback"
**Workflow:** when a developer asks to "add column X to table Y", produce a new migration file in `migrations/000N_<name>.sql` with the right ALTER and a corresponding rollback in a comment block. Validate that the column doesn't already exist.
- Context file: rules for migration naming, schema style.
- Prompt: parses the user's request into structured input (table, column, type, nullability).
- Skill: `generate-migration` with the migration template.
- Subagent: a verifier that reads the new migration and confirms it's reversible.

### Task B: "Security preflight before merge"
**Workflow:** when a PR is ready to merge, the workflow runs a security checklist + a security-review subagent + a verifier. Output is a go/no-go with reasons.
- Context file: which paths are security-sensitive (`app/auth/`, etc.).
- Prompt: the security checklist.
- Skill: `security-preflight` that runs the prompt and aggregates results.
- Subagent: independent security verifier (different model from the reviewer).

### Task C: "PR-readiness bot"
**Workflow:** before a developer opens a PR, the bot reviews the diff against team standards, suggests fixes, and produces a PR description.
- Context file: team's PR conventions.
- Prompt: PR description template.
- Skill: `pr-readiness` with a multi-step checklist.
- Subagent: pipeline of (checklist-reviewer → suggester → describer).

---

## Reminders

- **Reuse.** The context file from Module 1, the prompt library from Module 2, the skill from Module 3, the pipeline from Module 4 — all fair game. The capstone is about composition, not net-new building.
- **Demo discipline.** Pick the one most impressive part of the workflow and lead with it.
- **No demo slides beyond one overview slide.** Live demo is the deliverable.
