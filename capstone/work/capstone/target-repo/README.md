# payments-api (capstone target repo)

The Module 1 sample service (FastAPI + Postgres 15), used as the target repo for the capstone's
add-column workflow. See `../README.md` for the workflow itself.

```
app/                 FastAPI service (auth + orders)
migrations/          append-only SQL migrations, applied by the deploy pipeline
.claude/skills/      generate-migration skill (Claude Code)
.claude/agents/      migration-request-parser + migration-verifier subagents
CLAUDE.md            context file for Claude Code (§9 = the migration workflow)
AGENTS.md            the same rules for any other agent
docs/architecture.md deeper design notes
```
