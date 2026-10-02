"""Pipeline driver — Module 4 Lab starting point.

Runs four stages: planner -> reviewers (parallel) -> aggregator -> verifier.
Adapt the `invoke_subagent()` function to your platform's invocation
mechanism (Claude Code subagent dispatch, Copilot custom-agent invocation,
or a fixture-based offline shim).

Usage:
  python3 pipeline.py path/to/diff.patch
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path


def invoke_subagent(name: str, task: dict) -> dict:
    """Dispatch to a subagent. Returns its parsed JSON output.

    Implement this against your platform. Three options:
      1. Shell out to your platform's CLI with the subagent name + task JSON.
      2. Use the platform's SDK to invoke the named subagent.
      3. FIXTURE: read a pre-recorded response from `fixtures/<name>.json`.

    The fixture path is recommended for first runs and for CI-friendly tests.
    """
    raise NotImplementedError(
        "Implement invoke_subagent() for your platform. See the docstring."
    )


def log(stage: str, **fields) -> None:
    """Structured log line for observability. Optional in v2.0 (was a separate lab in v1.x); useful if you want to instrument the pipeline."""
    record = {"stage": stage, "ts": time.time(), **fields}
    print(json.dumps(record))


async def run_reviewers_parallel(plan: dict, diff_path: Path) -> list[dict]:
    """Dispatch one reviewer per file in parallel."""
    async def _one(file_entry: dict) -> dict:
        task = {"file": file_entry["path"], "diff": diff_path.read_text()}
        # The 'await asyncio.to_thread' lets a sync invoke_subagent run concurrently.
        return await asyncio.to_thread(invoke_subagent, "file-reviewer", task)
    return await asyncio.gather(*[_one(f) for f in plan["files"]])


async def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: pipeline.py <diff_path>", file=sys.stderr)
        return 2
    diff_path = Path(argv[1])

    # Stage 1: planner
    log("planner_start")
    plan = invoke_subagent("pr-planner", {"diff": diff_path.read_text()})
    log("planner_done", files=len(plan.get("files", [])))

    # Stage 2: reviewers in parallel
    log("reviewers_start")
    per_file = await run_reviewers_parallel(plan, diff_path)
    log("reviewers_done", count=len(per_file))

    # Stage 3: aggregator
    log("aggregator_start")
    combined = invoke_subagent("review-aggregator", {"reviews": per_file})
    log("aggregator_done", issues=len(combined.get("issues", [])))

    # Stage 4: verifier
    log("verifier_start")
    verdict = invoke_subagent("review-verifier",
                              {"diff": diff_path.read_text(), "review": combined})
    log("verifier_done", verdict=verdict.get("verdict"))

    print(json.dumps({"plan": plan, "combined_review": combined,
                      "verdict": verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv)))
