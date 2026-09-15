# Combined M1+M2 Lab — Foundations

**Owner:** Dau Quang Thanh — F1 AI Program
**Module:** Combined Module 1 + Module 2
**Format:** paired
**Day in program:** Day 1

This is the only hands-on lab for Modules 1 and 2. There is no separate M1 or M2 lab.

> ### 🧭 Before we start — quick word on what we're actually doing here
>
> You've probably hit this before: you ask an AI to write some code, and it hands back something that *looks* fine but lands in the wrong place, ignores your conventions, and touches a file it had no business touching. Annoying. This whole lab is about fixing exactly that annoyance — **getting an AI to write code in your team's style, every time, in a way you can actually check instead of just hoping.**
>
> We'll go through 4 steps. Don't treat them as 4 disconnected exercises — they're one closed loop, each one untying a different knot:
>
> | Step | What you make | Which knot it unties |
> |---|---|---|
> | **1. Context files** | `CLAUDE.md` + `AGENTS.md` | "How does the agent learn the house rules?" |
> | **2. Prompt library + schema** | 5 reusable prompts + schema-constrained output | "How do prompts become shared, machine-checkable tools instead of throwaway one-liners?" |
> | **3. CI + regression** | Eval running in CI | "How do I stop a broken prompt before it sneaks into the main branch?" |
> | **4. Verification** | with-file vs without-file comparison | "How do I *know* the context file actually does something, and I'm not just imagining it?" |
>
> 👉 One piece of advice: after each Step, stop for five seconds and ask *"what real problem does this fix for me?"* before you start typing commands. Every Step below has a **🎯 Goal / 💡 Why it's worth it / ✅ What you walk away with** box so you don't get lost in the pile of commands.

---

## Setup

> 🎯 **Goal:** Spin up a `work/` copy you can mess around in freely, and leave `starter/` alone.  
> 💡 **Why it's worth it:** Sounds obvious, but "play in the copy, keep the original clean" is a genuine habit of the trade. Break something? Delete the copy, make a new one, start over. And the real payoff is Step 4: you'll need a pristine original to *put side by side and compare against* — edit the starter directly and you've thrown away your own measuring stick.  
> ✅ **What you walk away with:** A repo that builds cleanly + a library scaffold that's yours to break, no fear of wrecking anything.  

Pair up. Decide who drives first; switch driver and navigator at natural breaks.

1. Open a terminal in this folder: `labs/combined_m1_m2/`.
2. Copy the starter materials into a working directory you can edit:
   ```
   mkdir -p work
   cp -r starter/repo                work/repo
   cp     starter/verification_prompt.md  work/verification_prompt.md
   cp -r starter/library_template    work/library
   cp -r starter/structured_output   work/validate
   cp     starter/ci/eval.yml        work/eval.yml.template
   ```
3. Verify the repo builds:
   ```
   cd work/repo && make setup && make test && cd ../..
   ```
4. Open `work/` in your editor with Claude Code or GitHub Copilot active. Use one platform consistently for the lab.

You'll work inside `work/` for all four steps. The starter stays untouched.

---

## Step 1 — Author `CLAUDE.md` and `AGENTS.md` (paired)

Apply the eight-section anatomy from theory to the sample repo at `work/repo/`.

> 🎯 **Goal:** Write two "context files" — `CLAUDE.md` (for Claude Code) and `AGENTS.md` (the standard lots of agents can read) — that pack in everything someone new to the team, or an AI, needs to not make a mess in this repo: how to build, what the conventions are, which corners are off-limits.  
> 💡 **Why it's worth it:** If you only take one thing from today, make it this. By default the AI *knows nothing* about your team's unwritten rules — and when it doesn't know, it guesses. A context file is how you turn that guessing into knowing. The difference it makes is very real: one side is code you rewrite from scratch, the other side is code you merge straight in. That eight-part skeleton (overview, build/test, conventions, do-not, glossary, escalation, examples, pointers) isn't theory for its own sake — it's a checklist so you don't forget a section.  
> ✅ **What you walk away with:** You can "onboard" an AI into an unfamiliar codebase with a single text file — and you know which line produces which behavior (Step 4 is where you prove it yourself).  

### Steps
1. **Explore the repo.** Read these files:
   - `app/main.py`, `app/orders/routes.py`, `app/auth/handlers.py`, `app/types.py`, `app/db.py`
   - `tests/integration/test_orders.py`
   - `migrations/0001_initial.sql`
   - `docs/architecture.md`
   - `Makefile`, `pyproject.toml`, `README.md`

   List the conventions you notice: build commands, endpoint patterns, what's clearly off-limits.

2. **Draft `CLAUDE.md`.** Apply the eight-section anatomy:
   - Project overview · Build & test · Conventions · Do not · Glossary · Escalation · Examples · Imports / pointers

   Save as `work/repo/CLAUDE.md`.

3. **Draft `AGENTS.md`.** Same eight-section shape, single file (no `@`-imports). Save as `work/repo/AGENTS.md`.

4. **Quick verification.** Run a single short prompt from inside `work/repo/`: *"Add a new endpoint that returns the count of orders for a given user."* Note whether the agent followed your conventions (file location, type imports, integration test added, no auth changes). Don't spend long on this — Step 4 is the rigorous verification.

### Acceptance for Step 1
- `work/repo/CLAUDE.md` and `work/repo/AGENTS.md` exist.
- Both cover the eight-section anatomy in imperative bullets.
- No secrets in either file.

---

## Step 2 — Five-prompt library + schema-constrained output (paired)

Build a reusable prompt library targeting the same `work/repo/` you just authored context files for.

> 🎯 **Goal:** Take something you ask AI to do over and over (say, "write tests for this function") and turn it into **a versioned, reusable set of 5 prompts** — with at least one that forces its output into a hard schema, so a machine can check it instead of you eyeballing it.  
> 💡 **Why it's worth it:** Let's be honest — most of us use AI by typing one line, taking it if it works, and forgetting it. Next time we type it from scratch, and nobody remembers which prompt actually gave good results. This step trains you to treat prompts as **real tools**: named, versioned, reviewable like code. And "schema-constrained output" cures the single worst headache of shipping AI in a product: it answers differently every time — neat JSON one run, a rambling paragraph the next. Once you force a schema, run a validator, and keep a "repair prompt" ready so it fixes itself when it slips, *then* the code downstream can actually trust the AI. This is genuinely how people wire LLMs into systems that run for real.  
> 💡 **Why 5 prompts and not just 1?** Because a real task is never one situation — there's the happy path, the edge case, the time it errors out... Making yourself write 5 variations forces you to think through every way the task can go sideways, not just the pretty case.  
> ✅ **What you walk away with:** A prompt library a machine can check, plus the "constrain → validate → self-repair" reflex — take it back to the team and you can wire it straight into a real workflow.  

### Steps
1. **Pick a task family.** Choose one and confirm with the instructor:
   - test generation (write tests for a function)
   - refactor proposals (suggest a refactor with diff)
   - code review (against a checklist)
   - bug triage (categorize and rank from a stack trace)
   - doc generation (write a docstring for a function)

2. **Write five prompts.** Five distinct variations of the task — happy path, edge case, error case, and two more axes you pick. One file per prompt under `work/library/prompts/`. Each prompt has a small frontmatter header (`name`, `version`, `model`, `input_kind`, `output_kind`).

3. **Add schema-constrained output to one prompt.** Pick the most production-relevant of your five and make its output strictly schema-constrained:
   - Reuse `work/validate/review.schema.json` as a starting schema OR write your own `work/library/<name>.schema.json`.
   - Test the prompt; capture the response in `work/library/runs/<name>_run1.json`.
   - Run `python3 work/validate/validate.py work/library/runs/<name>_run1.json` to confirm.
   - If the response fails validation, write a one-shot repair prompt that takes the original output + validator complaint and returns a corrected response. Test it.

4. **Build a small golden set.** Six to ten input/expected pairs in `work/library/goldens/`. Expected outputs precise enough that a regression is a real regression.

5. **Run the harness.** `python3 work/library/harness/run_eval.py`. Iterate on goldens or prompts until pass rate is >80%.

### Acceptance for Step 2
- Five prompts in `work/library/prompts/`, distinct variations.
- At least one prompt uses schema-constrained output with a validator + repair flow.
- Golden set with ≥6 cases.
- Eval harness reports >80% pass rate.

---

## Step 3 — Eval harness in CI + regression catch (paired)

Wire the harness into CI and demonstrate it failing on a deliberate regression.

> 🎯 **Goal:** Drop the Step 2 eval harness into CI (GitHub Actions), then *deliberately* break a prompt to watch CI **go red and block it** — then fix it back to green.  
> 💡 **Why it's worth it:** A test suite that never catches anything is the same as no test suite. Prompts rot quietly, exactly like code: someone tweaks a line, the output gets a little worse, nobody notices — until a customer does. Putting eval in CI means **every time you touch a prompt, the machine checks it before it merges**, just like a unit test. And that "break it on purpose and see if CI catches it" bit sounds backwards but it's the best part: it tests *your golden set itself*. You break a prompt and CI stays green? Then your tests are just *for show* — they aren't holding any weight yet. Stings a little to realize, but it's one of the most valuable lessons of the day.  
> ✅ **What you walk away with:** You know how to string up an automated safety net for AI work — and, more to the point, how to *check the net actually catches something* instead of just hanging there looking nice.  

### Steps
1. **Add the workflow.** Copy `work/eval.yml.template` to `work/library/.github/workflows/eval.yml`. Adjust paths and python version to match your library layout.

2. **Run locally first.** `python3 work/library/harness/run_eval.py --strict` should mirror what CI will do. Confirm exit code 0.

3. **Demonstrate a regression.** Make one of your prompts deliberately worse — strip a constraint, add ambiguous wording. Commit. Run `--strict` again. Confirm it fails. Capture the output in `work/library/REGRESSION_LOG.md`.

4. **Restore.** Revert the regression. Confirm `--strict` passes.

### Acceptance for Step 3
- CI workflow file present at `work/library/.github/workflows/eval.yml`.
- `REGRESSION_LOG.md` shows a captured failing run with specific golden(s) that caught the regression.
- Final state passes `--strict`.

---

## Step 4 — Verify the context file is doing work (paired)

Run a fixed verification prompt twice and trace the differences back to specific rules in your context file.

> 🎯 **Goal:** Run the *exact same prompt* twice — once WITH your context files, once WITHOUT — then point out at least 3 places the agent behaved differently, and for each one, track down the line in your `CLAUDE.md`/`AGENTS.md` that caused it.  
> 💡 **Why it's worth it:** This is the "oh, *that's* what it does" moment of the whole day. In Step 1 you *believed* the context file helps; here you get to see it with your own eyes, in a proper controlled experiment — change one variable, hold the rest still, watch what comes out. It also drags a slightly uncomfortable truth into the light: if the two runs come out identical, your context file is *doing nothing* — it's decoration. And that skill of tracing "this behavior ← came from that rule" is exactly how you'll debug and sharpen a context file out in the real world, instead of editing it blind.  
> ✅ **What you walk away with:** You can not just *write* a context file but actually *measure* whether it's pulling its weight — and when the agent does something dumb, you know which line to go fix.  

### Steps
1. **Run with file.** Open `work/verification_prompt.md` and run that prompt in `work/repo/` with your `CLAUDE.md` and `AGENTS.md` in place. Save the agent's full response to `work/verification/run_with.md`.

2. **Run without file.** Rename your context files to `.bak` (`mv CLAUDE.md CLAUDE.md.bak` and same for AGENTS.md). Run the same prompt. Save to `work/verification/run_without.md`. Restore your context files.

3. **Annotate the diff.** In `work/verification/REPORT.md`, list at least 3 differences you observe between the two runs. For each difference, point to the specific line(s) in your `CLAUDE.md` or `AGENTS.md` that produced it.

### Acceptance for Step 4
- `run_with.md` and `run_without.md` captured in full.
- `REPORT.md` annotates ≥3 differences with traceability to specific context-file rules.

---

## Submission

Submit the entire `work/` directory. It should contain:

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

Plus a one-paragraph reflection at the end of `RATIONALE.md`: what would you do differently if you had another lab session?

---

## Acceptance criteria (overall)

- Both `CLAUDE.md` and `AGENTS.md` present and exercised by Step 4.
- Five distinct prompts; at least one uses schema-constrained output.
- Eval harness runs on the goldens with a documented pass rate.
- CI workflow present; demonstrated failing run on a deliberate regression.
- Verification report identifies at least three differences between with-vs-without runs, each traced to a specific rule.

The lab is graded as a single artifact (see `RUBRIC.md`). Combined assessment weight: **25 %** of the program score.

---

## 🎓 What you take home

If you remember only one thing, make it this: **you just walked a full loop of bringing AI into a real codebase** — teaching it (Step 1), packaging how it's used into something the whole team can share (Step 2), stringing up a net to keep the quality from slipping (Step 3), then proving it actually pulls its weight (Step 4).

None of this is learn-it-and-forget-it stuff. Each step turns straight into something you'll do when you bring AI back to your team:

- **Context file** → onboard an agent into every new project, instead of re-explaining everything each time.
- **Prompt library + schema** → gather your scattered one-off AI use into a workflow that repeats and that you can trust.
- **CI eval** → keep AI quality from quietly sliding over time.
- **Verification mindset** → get in the habit of asking "*how do I actually know this works?*" instead of going on a gut feeling.

Carry those four habits back to your team and you've hit exactly what Modules 1 + 2 were aiming for.
