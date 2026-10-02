"""Pipeline driver — Module 4 Lab (hardened).

Runs four stages: planner -> reviewers (parallel) -> aggregator -> verifier.

Structured handoffs: every parent -> child task and every child -> parent result is
validated against a JSON Schema in schemas/. On a validation failure the driver retries
ONCE with a repair prompt (the subagent's own output + the validator errors). If the
repaired output is still invalid, the pipeline stops with an error and no result.

invoke_subagent() uses the FIXTURE option from the starter template: for every call it
writes the exact prompt (subagent definition from .claude/agents/<name>.md + task JSON +
output schema) to runs/<RUN>/prompts/<key>.md, then reads the subagent's recorded
response from fixtures/<RUN>/<key>.txt. Each fixture is the raw response of a real
subagent call made with that prompt.

Every stage's task, raw output, validation errors and parsed output is written to
runs/<RUN>/.

Usage:
  python3 pipeline.py path/to/diff.patch
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

from jsonschema import Draft7Validator

RUN = "hardened"

HERE = Path(__file__).resolve().parent
AGENTS_DIR = HERE / ".claude" / "agents"
SCHEMAS_DIR = HERE / "schemas"
FIXTURES_DIR = HERE / "fixtures" / RUN
RUN_DIR = HERE / "runs" / RUN
# Pre-PR Module 1 sample repo, so reviewer/verifier can read whole files for context.
REPO_ROOT = "../../module-1-2/starter/repo"


class PipelineError(Exception):
    """A handoff failed validation (after one repair attempt for subagent outputs)."""


def _slug(path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")


def _inline_refs(node):
    if isinstance(node, dict):
        if set(node) == {"$ref"}:
            ref = load_schema(node["$ref"])
            ref.pop("$schema", None)
            return ref
        return {k: _inline_refs(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_inline_refs(v) for v in node]
    return node


def load_schema(filename: str) -> dict:
    return _inline_refs(json.loads((SCHEMAS_DIR / filename).read_text(encoding="utf-8")))


def validate(instance, schema: dict) -> list[str]:
    errors = sorted(Draft7Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in errors]


def _agent_body(name: str) -> str:
    text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return text.split("---", 2)[2].strip()


def build_prompt(name: str, task: dict, output_schema: dict) -> str:
    return (f"{_agent_body(name)}\n\n## Task\n```json\n"
            f"{json.dumps(task, indent=2, ensure_ascii=False)}\n```\n\n"
            "## Output contract\n"
            "Return ONLY one JSON object (no prose, no code fences) that is valid against "
            "this JSON Schema:\n```json\n"
            f"{json.dumps(output_schema, indent=2)}\n```\n")


def build_repair_prompt(name: str, task: dict, output_schema: dict,
                        raw: str, errors: list[str]) -> str:
    error_lines = "\n".join(f"- {e}" for e in errors)
    return (f"{build_prompt(name, task, output_schema)}\n"
            "## Repair\n"
            "Your previous output failed validation against the output contract.\n\n"
            f"Previous output:\n```\n{raw}\n```\n\n"
            f"Validation errors:\n{error_lines}\n\n"
            "Return the corrected JSON only. Keep the same findings; change only what is "
            "needed to satisfy the schema.\n")


def invoke_subagent(key: str, prompt: str) -> str:
    """Dispatch to a subagent (FIXTURE mode). Returns its RAW text response."""
    prompt_path = RUN_DIR / "prompts" / f"{key}.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    fixture = FIXTURES_DIR / f"{key}.txt"
    if not fixture.exists():
        raise NotImplementedError(f"No recorded response at {fixture} (prompt: {prompt_path})")
    return fixture.read_text(encoding="utf-8")


def _parse_and_validate(raw: str, schema: dict) -> tuple[dict | None, list[str]]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, [f"<root>: not valid JSON ({e})"]
    errors = validate(parsed, schema)
    return (None if errors else parsed), errors


def call_with_validation(trace_name: str, name: str, key: str, task: dict,
                         input_schema: dict, output_schema: dict) -> dict:
    """Validate the task, call the subagent, validate the result; repair once on failure."""
    record = {"task": task, "attempts": []}
    in_errors = validate(task, input_schema)
    if in_errors:
        raise PipelineError(f"{key}: task failed its input schema: {in_errors}")

    raw = invoke_subagent(key, build_prompt(name, task, output_schema))
    parsed, errors = _parse_and_validate(raw, output_schema)
    record["attempts"].append({"raw_output": raw, "errors": errors})
    if errors:
        log("validation_failed", subagent=key, attempt=1, errors=errors)
        repair = build_repair_prompt(name, task, output_schema, raw, errors)
        raw = invoke_subagent(f"{key}__repair", repair)
        parsed, errors = _parse_and_validate(raw, output_schema)
        record["attempts"].append({"raw_output": raw, "errors": errors})
        if errors:
            log("validation_failed", subagent=key, attempt=2, errors=errors)
            _write_trace(trace_name, record)
            raise PipelineError(f"{key}: output still invalid after one repair: {errors}")
    log("validated", subagent=key, attempts=len(record["attempts"]))
    record["output"] = parsed
    _write_trace(trace_name, record)
    return parsed


def _write_trace(trace_name: str, record: dict) -> None:
    (RUN_DIR / f"{trace_name}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")


def log(stage: str, **fields) -> None:
    """Structured log line for observability."""
    record = {"stage": stage, "ts": time.time(), **fields}
    line = json.dumps(record)
    print(line)
    with open(RUN_DIR / "pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


async def run_reviewers_parallel(plan: dict, diff_path: Path, schemas: dict) -> list[dict]:
    """Dispatch one reviewer per file in parallel."""
    async def _one(file_entry: dict) -> dict:
        task = {"file": file_entry["path"], "diff": diff_path.read_text(),
                "repo_root": REPO_ROOT}
        slug = _slug(task["file"])
        # The 'await asyncio.to_thread' lets a sync subagent call run concurrently.
        return await asyncio.to_thread(
            call_with_validation, f"02_reviewer__{slug}", "file-reviewer",
            f"file-reviewer__{slug}", task, schemas["reviewer_input"], schemas["review"])
    return await asyncio.gather(*[_one(f) for f in plan["files"]])


async def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: pipeline.py <diff_path>", file=sys.stderr)
        return 2
    diff_path = Path(argv[1])
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "pipeline.log").write_text("", encoding="utf-8")
    schemas = {n: load_schema(f"{n}.schema.json") for n in (
        "planner_input", "planner_output", "reviewer_input", "review",
        "aggregator_input", "verifier_input", "verifier_output")}

    try:
        # Stage 1: planner
        log("planner_start")
        plan = call_with_validation("01_planner", "pr-planner", "pr-planner",
                                    {"diff": diff_path.read_text()},
                                    schemas["planner_input"], schemas["planner_output"])
        log("planner_done", files=len(plan["files"]))

        # Stage 2: reviewers in parallel
        log("reviewers_start")
        per_file = await run_reviewers_parallel(plan, diff_path, schemas)
        log("reviewers_done", count=len(per_file))

        # Stage 3: aggregator
        log("aggregator_start")
        combined = call_with_validation("03_aggregator", "review-aggregator",
                                        "review-aggregator", {"reviews": per_file},
                                        schemas["aggregator_input"], schemas["review"])
        log("aggregator_done", issues=len(combined["issues"]))

        # Stage 4: verifier
        log("verifier_start")
        verdict = call_with_validation(
            "04_verifier", "review-verifier", "review-verifier",
            {"diff": diff_path.read_text(), "review": combined, "repo_root": REPO_ROOT},
            schemas["verifier_input"], schemas["verifier_output"])
        log("verifier_done", verdict=verdict["verdict"])
    except PipelineError as e:
        log("pipeline_failed", error=str(e))
        print(f"PIPELINE FAILED: {e}", file=sys.stderr)
        return 1

    result = {"plan": plan, "combined_review": combined, "verdict": verdict}
    (RUN_DIR / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                         encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv)))
