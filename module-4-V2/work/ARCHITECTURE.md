# Architecture — code-quality review pipeline (Module 4 Lab, Step 1)

Platform: **Claude Code** (subagents in `.claude/agents/`).

```
 sample_pr/diff.patch
        |
        v
 +---------------------+
 | 1. pr-planner       |  haiku (cheap/fast)
 +---------------------+
        | {files:[{path, lines_changed, complexity, sensitive}]}
        v
 +---------------------+   +---------------------+
 | 2. file-reviewer    |   | 2. file-reviewer    |   sonnet (capable)
 |    (file 1)         |...|    (file N)         |   one instance per file,
 +---------------------+   +---------------------+   run in PARALLEL
        | {issues, summary}        | {issues, summary}
        +-----------+--------------+
                    v
 +---------------------+
 | 3. review-aggregator|  sonnet, ZERO tools (pure transform)
 +---------------------+
        | {issues, summary}  (de-duped, ordered by severity)
        v
 +---------------------+
 | 4. review-verifier  |  opus (different model from reviewer)
 +---------------------+
        |
        v
 {verdict: approved | changes-requested, false_positives, missed_issues, reasoning}
```

`pipeline.py` is the driver: planner once → one reviewer per planned file
(`asyncio.gather`) → aggregator once → verifier once.

| Subagent | Role | Model | Tools (allowlist) | Input | Output |
|---|---|---|---|---|---|
| `pr-planner` | List the files changed in the PR, with complexity and sensitivity flags. No code judgment. | `claude-haiku-4-5` | baseline `Read, Bash` → hardened `Read` | `{diff}` | `{files: [{path, lines_changed, complexity, sensitive}], groups?}` |
| `file-reviewer` | Review ONE file's changes against the checklist. | `claude-sonnet-4-5` | `Read, Grep` | `{file, diff, repo_root}` | `{issues: [...], summary}` (`review.schema.json`) |
| `review-aggregator` | Merge N per-file reviews into one: concatenate, de-dup, order by severity, PR-level summary. | `claude-sonnet-4-5` | none | `{reviews: [review, ...]}` | `{issues: [...], summary}` (`review.schema.json`) |
| `review-verifier` | Independent second pass: find false positives and missed issues, give the verdict. | `claude-opus-4-6` | `Read, Grep` | `{diff, review, repo_root}` | `{verdict, false_positives, missed_issues, reasoning}` |

`repo_root` points at the pre-PR Module 1 sample repo (`labs/module-1-2/starter/repo`), so
the reviewer and verifier can read whole files for context, not only the diff.

The JSON Schemas for every handoff are in `schemas/` (added in the hardening pass, Step 5).
