# Module 4 — Lab Handout

**Owner:** Dau Quang Thanh — F1 AI Program
**Module:** Subagent Development
**Format:** paired
**Day in program:** Day 3

This is the only hands-on lab for Module 4. Single combined lab covering pipeline build and a hardening pass.

---

## Setup

Pair up. Switch driver/navigator at natural breaks.

1. Open a terminal in this folder: `labs/module4/`.
2. Copy starter:
   ```
   mkdir -p work
   cp -r starter/sample_pr work/sample_pr
   cp -r starter/pipeline    work/pipeline_template
   cp     starter/hardening/HARDENING.md.tpl work/HARDENING.md.tpl
   ```
3. Pick a platform: Claude Code or Copilot. Use it for the whole lab.

`work/sample_pr/` is the PR you'll review — a small diff against the Module 1 sample repo with eight seeded issues.

---

## Module 4 Lab — Build and harden a multi-subagent pipeline (paired)

### Learning objective
By the end of the lab, the pair has built a four-stage code-quality pipeline (planner → reviewer (parallel) → aggregator → verifier) running end-to-end on a sample PR, then run a single hardening pass that tightens tool allowlists and adds structured handoffs with validation.

### Steps

1. **Architecture sketch.** On paper or a doc, draw the pipeline. For each subagent: name, role, model (cheap/fast or capable?), tools (allowlist), input schema, output schema. **Confirm with the instructor before coding.** This step is mandatory — it's where the pipeline gets shaped.

2. **Build the four subagents.** Adapt the templates in `work/pipeline_template/`:
   - `planner.md` — takes a PR, returns a list of files to review.
   - `reviewer.md` — takes ONE file + diff, returns structured review for that file. (Multiple instances run in parallel, one per file.)
   - `aggregator.md` — takes N reviewer outputs, returns one combined review.
   - `verifier.md` — takes the combined review, returns approve | changes-requested.

   Install each subagent on your platform (`.claude/agents/<name>.md` for Claude Code, or the equivalent Copilot path).

3. **Wire the orchestration.** Adapt `work/pipeline_template/pipeline.py.tpl` into `work/pipeline.py`. The driver runs the four stages, dispatches reviewers in parallel, aggregates, runs the verifier.

4. **Run on the sample PR.** `python3 work/pipeline.py work/sample_pr/diff.patch`. Capture all stage traces under `work/runs/baseline/`.

5. **Hardening pass.**
   - **Tool allowlists.** Audit each subagent's `tools` list. Read-only roles (planner, reviewer, verifier) get only read tools. The aggregator gets ZERO tools (it just transforms input). Document each change in `work/HARDENING.md`.
   - **Structured handoffs.** Define a JSON schema for each parent → child task and each child → parent result. Validate at every boundary. On validation failure, retry once with a repair prompt before failing.

6. **Re-run and document.** Run the hardened pipeline on the sample PR again. Capture traces under `work/runs/hardened/`. Diff against baseline. One-paragraph note in `work/HARDENING.md`: what changed, what improved.

### Acceptance criteria

- Four subagents installed.
- `pipeline.py` runs end-to-end on the sample PR.
- All baseline stage outputs captured under `work/runs/baseline/`.
- Hardening pass complete: minimal allowlists documented, schemas at every handoff, repair flow on validation failure.
- Hardened-pipeline run captured under `work/runs/hardened/`.
- HARDENING.md describes the diff vs baseline.

### Submit

The whole `work/` directory plus an architecture diagram (any format — sketch, draw.io, ASCII) and a recorded demo (your platform's screen recording is fine).
