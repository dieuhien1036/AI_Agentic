#!/usr/bin/env python3
"""Eval for the parse-migration-request prompt (same two-layer design as the Module 2 library).

  Layer A -- prompt contract. Each golden lists `prompt_must_contain`: phrases the prompt file
    must still carry because that golden depends on them. Checked against the prompt on disk,
    so weakening the prompt fails the eval even when outputs are replayed. Also checks that the
    migration-request-parser subagent still carries the prompt body verbatim.
  Layer B -- output. Strict JSON (no fences, no prose), JSON-schema validation against
    schemas/migration_spec.schema.json, then field-by-field comparison with `expect`.

Modes:
  offline (default)  replays evals/fixtures/<id>.txt -- deterministic, no network
  --live             runs the migration-request-parser subagent via `claude -p`
  --live --record    ... and overwrites the fixtures with the new responses

Usage:
  python evals/run_eval.py [--only <id>] [--live [--record]]
Exit 0 if every golden passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "driver"))
from contracts import (
    AGENTS_DIR,
    PROMPT_FILE,
    REPO,
    SKILL_SCRIPTS,
    ContractError,
    call_agent_live,
    parse_strict_json,
    split_frontmatter,
    validate,
)

sys.path.insert(0, str(SKILL_SCRIPTS))
from schema_state import load_schema

GOLDENS = ROOT / "evals" / "goldens"
FIXTURES = ROOT / "evals" / "fixtures"


def payload_for(request: str) -> str:
    schema = load_schema(REPO / "migrations")
    tables = "\n".join(f"{t}: {', '.join(cols)}" for t, cols in schema.tables.items())
    return f"REQUEST:\n{request}\n\nCURRENT SCHEMA (replayed from migrations/):\n{tables}"


def check_agent_sync(prompt_body: str) -> list[str]:
    agent_text = (AGENTS_DIR / "migration-request-parser.md").read_text(encoding="utf-8")
    if prompt_body.strip() not in agent_text:
        return ["agent file drifted from prompts/parse-migration-request.md "
                "(run: python driver/sync_agents.py)"]
    return []


def run_golden(golden: dict, prompt_text: str, live: bool, record: bool) -> list[str]:
    fails: list[str] = []
    for phrase in golden.get("prompt_must_contain", []):
        if phrase not in prompt_text:
            fails.append(f"A: prompt no longer contains {phrase!r}")

    request = golden["input"]["request"]
    fixture = FIXTURES / f"{golden['id']}.txt"
    if live:
        raw = call_agent_live("migration-request-parser", payload_for(request))
        if record:
            fixture.write_text(raw.strip() + "\n", encoding="utf-8")
    else:
        if not fixture.exists():
            return fails + [f"B: no recorded response {fixture.name} (run with --live --record)"]
        raw = fixture.read_text(encoding="utf-8")

    try:
        out = parse_strict_json(raw)
        validate(out, "migration_spec.schema.json")
    except ContractError as exc:
        return fails + [f"B: contract: {exc}"]

    if out.get("request") != request:
        fails.append("B: 'request' is not the verbatim input")
    for key, want in golden.get("expect", {}).items():
        if out.get(key) != want:
            fails.append(f"B: {key} = {out.get(key)!r}, expected {want!r}")
    assumptions = " ".join(out.get("assumptions", [])).lower()
    for needle in golden.get("assumptions_must_mention", []):
        if needle.lower() not in assumptions:
            fails.append(f"B: assumptions do not mention {needle!r}")
    if "min_questions" in golden and len(out.get("questions", [])) < golden["min_questions"]:
        fails.append(f"B: fewer than {golden['min_questions']} clarifying questions")
    return fails


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args(argv[1:])

    prompt_text = PROMPT_FILE.read_text(encoding="utf-8")
    _, prompt_body = split_frontmatter(prompt_text)
    goldens = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GOLDENS.glob("*.json"))]
    goldens.sort(key=lambda g: not g.get("primary"))
    if args.only:
        goldens = [g for g in goldens if g["id"] == args.only]

    print(f"prompt: {PROMPT_FILE.relative_to(ROOT).as_posix()}  "
          f"mode: {'live' if args.live else 'offline (recorded fixtures)'}")
    sync_fails = check_agent_sync(prompt_body)
    print(f"  {'PASS' if not sync_fails else 'FAIL'}  agent-sync  "
          "migration-request-parser.md carries the prompt verbatim")
    for f in sync_fails:
        print(f"        - {f}")

    passed = 0
    for g in goldens:
        fails = run_golden(g, prompt_text, args.live, args.record)
        passed += not fails
        tag = " (primary golden)" if g.get("primary") else ""
        print(f"  {'PASS' if not fails else 'FAIL'}  {g['id']}{tag}")
        for f in fails:
            print(f"        - {f}")
    print(f"\n{passed}/{len(goldens)} goldens passed"
          f"{'' if not sync_fails else ' -- agent file out of sync'}")
    return 0 if passed == len(goldens) and not sync_fails else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
