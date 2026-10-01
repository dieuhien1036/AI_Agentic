#!/usr/bin/env python3
"""Regenerate target-repo/.claude/agents/migration-request-parser.md from the reusable prompt.

The prompt in prompts/parse-migration-request.md is the single source of truth. The Claude
Code subagent needs it inline, so this script copies the prompt body (everything after its
front matter) under the subagent's own front matter. evals/run_eval.py fails if they drift.

Usage: python driver/sync_agents.py
"""
from __future__ import annotations

from contracts import AGENTS_DIR, PROMPT_FILE, split_frontmatter

HEADER = """---
name: migration-request-parser
description: |
  Parses a developer's natural-language request to add a database column ("add column X to
  table Y", "we need a notes field on orders") into a structured add-column migration spec
  (JSON), or returns clarifying questions. Use as the first step of the add-column workflow,
  before the generate-migration skill. Read-only; never writes files.
tools: Read, Glob
model: haiku
---

<!-- Body below is a verbatim copy of prompts/parse-migration-request.md (after its front
     matter). Edit the prompt file, then re-sync; evals/run_eval.py fails if they drift. -->

Before answering, build CURRENT SCHEMA yourself if the caller did not supply it: read the files
in `migrations/` in number order and list each table with its columns.

"""


def main() -> None:
    _, body = split_frontmatter(PROMPT_FILE.read_text(encoding="utf-8"))
    out = AGENTS_DIR / "migration-request-parser.md"
    out.write_text(HEADER + body.lstrip("\n"), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
