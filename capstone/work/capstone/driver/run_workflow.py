#!/usr/bin/env python3
"""Add-column workflow driver: parse -> generate -> verify -> GO / NO-GO.

  Stage 1  PARSE     migration-request-parser subagent  (prompt: prompts/parse-migration-request.md)
  Stage 2  GENERATE  generate-migration skill script    (deterministic, writes migrations/NNNN_*.sql)
  Stage 3  VERIFY    check_reversible.py (deterministic gate)  +  migration-verifier subagent

Every LLM handoff is validated against a JSON schema in schemas/. The verifier can only add
blockers: if the mechanical round-trip check fails, the result is NO-GO whatever it says.

Modes:
  offline (default)  LLM stages replay recorded responses (evals/fixtures/, driver/fixtures/).
                     Skill scripts and the mechanical check always run for real.
  --live             LLM stages call the subagents through the Claude Code CLI (`claude -p`).
                     One repair retry on a contract violation, then abort (Module 4 pattern).

Usage:
  python driver/run_workflow.py --list
  python driver/run_workflow.py --case add_orders_notes            # writes into target-repo/migrations
  python driver/run_workflow.py --case add_orders_notes --scratch  # works on a temp copy
  python driver/run_workflow.py --all                              # every case, scratch, checks expectations
  python driver/run_workflow.py --live --request "add a nullable notes text column to orders"
  python driver/run_workflow.py --live --case add_orders_notes --record   # refresh fixtures

Exit codes: 0 = workflow finished as expected (GO, or a correct stop), 1 = usage error,
2 = a contract was broken / a case did not match its expectation.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    REPO,
    ROOT,
    SKILL_SCRIPTS,
    ContractError,
    call_agent_live,
    parse_strict_json,
    validate,
)

sys.path.insert(0, str(SKILL_SCRIPTS))
from schema_state import load_schema

CASES_FILE = ROOT / "driver" / "cases.json"
RUNS_DIR = ROOT / "runs"
MIGRATION_PLACEHOLDER = "{MIGRATION_FILE}"


def banner(text: str) -> None:
    print(f"\n=== {text} " + "=" * max(0, 70 - len(text)))


def schema_summary(migrations_dir: Path) -> str:
    schema = load_schema(migrations_dir)
    return "\n".join(f"{t}: {', '.join(cols)}" for t, cols in schema.tables.items())


def run_script(script: str, args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL_SCRIPTS / script), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )


class Workflow:
    def __init__(self, repo_root: Path, live: bool, record: bool, case: dict) -> None:
        self.repo_root = repo_root
        self.migrations = repo_root / "migrations"
        self.live = live
        self.record = record
        self.case = case
        self.trace: dict = {"case": case.get("id"), "mode": "live" if live else "offline",
                            "request": case.get("request"), "stages": []}

    # -- LLM handoff -------------------------------------------------------------------------
    def ask_agent(self, agent: str, payload: str, schema: str, fixture_key: str,
                  substitutions: dict[str, str] | None = None) -> dict:
        fixture = ROOT / self.case[fixture_key] if self.case.get(fixture_key) else None
        if self.live:
            raw = call_agent_live(agent, payload, cwd=self.repo_root)
        else:
            if fixture is None or not fixture.exists():
                raise ContractError(f"offline mode: no recorded response for {agent} ({fixture_key})")
            raw = fixture.read_text(encoding="utf-8")
            for key, value in (substitutions or {}).items():
                raw = raw.replace(key, value)
        try:
            obj = parse_strict_json(raw)
            validate(obj, schema)
        except ContractError as exc:
            if not self.live:
                raise
            print(f"  ! {agent} broke its contract ({exc}); one repair attempt")
            raw = call_agent_live(
                agent,
                f"{payload}\n\nYour previous answer was rejected:\n{exc}\n\nPrevious answer:\n"
                f"{raw}\n\nReturn ONLY the corrected JSON object.",
                cwd=self.repo_root,
            )
            obj = parse_strict_json(raw)
            validate(obj, schema)
        if self.live and self.record and fixture is not None:
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(raw.strip() + "\n", encoding="utf-8")
        return obj

    # -- stages ------------------------------------------------------------------------------
    def parse(self) -> dict | None:
        banner("1/3 PARSE  (migration-request-parser subagent)")
        request = self.case["request"]
        payload = (f"REQUEST:\n{request}\n\nCURRENT SCHEMA (replayed from migrations/):\n"
                   f"{schema_summary(self.migrations)}")
        print(f"  request : {request}")
        spec = self.ask_agent("migration-request-parser", payload,
                              "migration_spec.schema.json", "parser_fixture")
        if spec["request"] != request:
            raise ContractError("parser echoed a different request than it was given")
        self.trace["stages"].append({"stage": "parse", "output": spec})
        if spec["status"] == "needs_clarification":
            print("  result  : NEEDS CLARIFICATION -- workflow stops, ask the developer:")
            for q in spec["questions"]:
                print(f"            ? {q}")
            return None
        print(f"  spec    : {spec['table']}.{spec['column']} {spec['type']} "
              f"nullable={spec['nullable']} default={spec['default']}")
        for a in spec["assumptions"]:
            print(f"  assumed : {a}")
        return spec

    def generate(self, spec: dict) -> str | None:
        banner("2/3 GENERATE  (generate-migration skill)")
        proc = run_script("generate_migration.py",
                          ["--migrations-dir", str(self.migrations), "--spec", "-"],
                          stdin=json.dumps(spec))
        out, err = proc.stdout.strip(), proc.stderr.strip()
        self.trace["stages"].append({"stage": "generate", "exit_code": proc.returncode,
                                     "stdout": out, "stderr": err})
        for line in (out + "\n" + err).strip().splitlines():
            print(f"  {line}")
        if proc.returncode != 0:
            print(f"  result  : STOPPED by the skill (exit {proc.returncode}); no file written")
            return None
        path = Path(out.split(":", 1)[1].split(" already")[0].strip())
        rel = f"migrations/{path.name}"
        print(f"  result  : {rel}")
        print("\n" + "\n".join("    | " + l for l in (self.repo_root / rel).read_text(
            encoding="utf-8").splitlines()))
        return rel

    def verify(self, rel: str) -> str:
        banner("3/3 VERIFY  (check_reversible.py + migration-verifier subagent)")
        target = self.repo_root / rel
        proc = run_script("check_reversible.py",
                          ["--migrations-dir", str(self.migrations), str(target)])
        if proc.returncode not in (0, 5):
            raise ContractError(f"check_reversible.py failed: {proc.stderr.strip()}")
        mech = json.loads(proc.stdout)
        failed = [c["name"] for c in mech["checks"] if not c["passed"]]
        for c in mech["checks"]:
            print(f"  [{'ok' if c['passed'] else 'FAIL'}] {c['name']:<24} {c['detail']}")

        earlier = "\n\n".join(
            f"--- {p.name}\n{p.read_text(encoding='utf-8')}"
            for p in sorted(self.migrations.glob("*.sql")) if p.name < target.name
        )
        payload = (f"migration_file: {rel}\n\nFILE CONTENT:\n{target.read_text(encoding='utf-8')}\n\n"
                   f"MECHANICAL CHECK (already run, exit {proc.returncode}):\n{proc.stdout}\n\n"
                   f"EARLIER MIGRATIONS:\n{earlier}")
        verdict = self.ask_agent("migration-verifier", payload, "verifier_verdict.schema.json",
                                 "verifier_fixture", {MIGRATION_PLACEHOLDER: rel})
        if verdict["migration_file"] != rel:
            raise ContractError(f"verifier reviewed {verdict['migration_file']}, expected {rel}")
        for r in verdict["rule_checks"]:
            print(f"  [{'ok' if r['passed'] else 'FAIL'}] {r['rule']:<24} {r['evidence']}")
        for i in verdict["issues"]:
            print(f"  {i['severity'].upper():<8} {i['message']}")

        final = verdict["verdict"]
        if not mech["reversible"] and final == "GO":
            final = "NO-GO"
            print("  ! verifier said GO but the mechanical check failed -> overruled to NO-GO")
        self.trace["stages"].append({"stage": "verify", "mechanical": mech,
                                     "verifier": verdict, "final": final})
        print(f"\n  VERDICT : {final} -- {verdict['summary']}")
        if failed:
            print(f"  failed mechanical checks: {', '.join(failed)}")
        return final

    def run(self) -> dict:
        outcome: dict = {"stopped_at": None, "verdict": None, "file": None}
        if self.case.get("inject_file"):
            # verify-only case: drop a hand-written migration in and check it
            src = ROOT / self.case["inject_file"]
            shutil.copy(src, self.migrations / src.name)
            rel = f"migrations/{src.name}"
            print(f"  injected hand-written migration: {rel}")
        else:
            spec = self.parse()
            if spec is None:
                outcome["stopped_at"] = "parse"
                return self._finish(outcome)
            rel = self.generate(spec)
            if rel is None:
                outcome["stopped_at"] = "generate"
                outcome["exit_code"] = self.trace["stages"][-1]["exit_code"]
                return self._finish(outcome)
        outcome["file"] = rel
        outcome["verdict"] = self.verify(rel)
        return self._finish(outcome)

    def _finish(self, outcome: dict) -> dict:
        self.trace["outcome"] = outcome
        return outcome


def load_cases() -> list[dict]:
    return json.loads(CASES_FILE.read_text(encoding="utf-8"))


def run_case(case: dict, live: bool, record: bool, scratch: bool) -> tuple[dict, dict]:
    tmp = None
    repo_root = REPO
    if scratch:
        tmp = Path(tempfile.mkdtemp(prefix="capstone_"))
        shutil.copytree(REPO / "migrations", tmp / "migrations")
        repo_root = tmp
    try:
        wf = Workflow(repo_root, live, record, case)
        outcome = wf.run()
        return outcome, wf.trace
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


def matches(expect: dict, outcome: dict) -> bool:
    return all(outcome.get(k) == v for k, v in expect.items())


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", help="id of a case in driver/cases.json")
    ap.add_argument("--request", help="free-text request (live mode only)")
    ap.add_argument("--all", action="store_true", help="run every case on scratch copies")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--live", action="store_true", help="call subagents via `claude -p`")
    ap.add_argument("--record", action="store_true", help="with --live: overwrite fixtures")
    ap.add_argument("--scratch", action="store_true",
                    help="work on a temp copy of migrations/ instead of target-repo/migrations")
    args = ap.parse_args(argv[1:])

    cases = load_cases()
    if args.list:
        for c in cases:
            print(f"{c['id']:<28} expect {json.dumps(c['expect'])}\n{'':<28} {c.get('request') or c.get('inject_file')}")
        return 0

    if args.request:
        if not args.live:
            print("ERROR: --request needs --live (offline mode only has recorded cases)", file=sys.stderr)
            return 1
        selected = [{"id": "adhoc", "request": args.request, "expect": {}}]
    elif args.all:
        selected = cases
        args.scratch = True
    elif args.case:
        selected = [c for c in cases if c["id"] == args.case]
        if not selected:
            print(f"ERROR: unknown case {args.case!r}; try --list", file=sys.stderr)
            return 1
    else:
        ap.print_help()
        return 1

    RUNS_DIR.mkdir(exist_ok=True)
    results = []
    for case in selected:
        print(f"\n##### case: {case['id']}  ({'live' if args.live else 'offline'}"
              f"{', scratch' if args.scratch else ''})")
        try:
            outcome, trace = run_case(case, args.live, args.record, args.scratch)
        except (ContractError, RuntimeError) as exc:
            print(f"  ABORTED: {exc}")
            outcome, trace = {"aborted": str(exc)}, {"case": case["id"], "aborted": str(exc)}
        ok = matches(case["expect"], outcome) if case["expect"] else "aborted" not in outcome
        trace["expected"], trace["matched"] = case["expect"], ok
        (RUNS_DIR / f"{case['id']}.json").write_text(json.dumps(trace, indent=2) + "\n",
                                                     encoding="utf-8")
        results.append((case["id"], outcome, ok))

    banner("SUMMARY")
    for cid, outcome, ok in results:
        shown = {k: v for k, v in outcome.items() if v is not None}
        print(f"  {'PASS' if ok else 'FAIL'}  {cid:<28} {json.dumps(shown)}")
    print(f"  traces in {RUNS_DIR.relative_to(ROOT).as_posix()}/")
    return 0 if all(ok for _, _, ok in results) else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
