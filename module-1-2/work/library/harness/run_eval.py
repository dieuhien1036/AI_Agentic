"""Five-prompt library eval harness — code-review task family.

Walks goldens/, runs each golden's prompt with the golden's input, and scores
the result on two layers:

  Layer A — prompt contract.  Each golden declares `prompt_must_contain`: the
    constraints the prompt file itself must still carry (output format, the
    checklist rules that golden exists to protect, the required summary prefix).
    These are checked against the prompt file on disk, so weakening a prompt
    fails the eval even when the recorded output is replayed.

  Layer B — output.  JSON Schema validation plus substring, forbidden-substring
    and structural checks against the agent's response.

Two execution modes:

  offline (default)  Replays the recorded response in fixtures/<golden id>.txt.
    Deterministic, no API key, no network — this is what CI runs.
  live (EVAL_MODE=live)  Calls a real agent. Not wired up here; implement
    call_agent_live() for your platform and record new fixtures from it.

Usage:
  python3 harness/run_eval.py                 # normal run
  python3 harness/run_eval.py --strict        # exit non-zero if any golden fails
  python3 harness/run_eval.py --only <id>     # run a single golden
  python3 harness/run_eval.py -v              # print every failing check

`--strict` is what Step 3 wires into CI.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPTS = ROOT / "prompts"
GOLDENS = ROOT / "goldens"
FIXTURES = ROOT / "fixtures"

PASS_THRESHOLD = 0.80  # documented in RATIONALE.md


# --------------------------------------------------------------------------- #
# Agent invocation
# --------------------------------------------------------------------------- #

def call_agent_live(prompt_body, input_text):
    """Call a real agent. Implement for your platform, then re-record fixtures.

    Left unimplemented on purpose: CI must not depend on a live model. To
    refresh the recorded outputs, implement this (Anthropic SDK, `claude -p`,
    or your platform's CLI), run with EVAL_MODE=live --record, and commit the
    regenerated fixtures/ files as a reviewable diff.
    """
    raise NotImplementedError(
        "EVAL_MODE=live requires call_agent_live() to be implemented for your platform."
    )


def call_agent(prompt_body, input_text, golden_id):
    """Return the agent's response for this golden."""
    if os.environ.get("EVAL_MODE") == "live":
        return call_agent_live(prompt_body, input_text)
    fixture = FIXTURES / (golden_id + ".txt")
    if not fixture.exists():
        raise FileNotFoundError(
            "no recorded fixture: {} (run with EVAL_MODE=live to generate one)".format(fixture)
        )
    return fixture.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_prompt(name):
    """Read a prompt file. Returns (frontmatter, body)."""
    for ext in (".md", ".yaml"):
        p = PROMPTS / (name + ext)
        if p.exists():
            return _split_frontmatter(p, name)
    for p in sorted(PROMPTS.glob("*.md")):
        meta, body = _split_frontmatter(p, name)
        if meta.get("name") == name:
            return meta, body
    raise FileNotFoundError("prompt not found: {}".format(name))


def _split_frontmatter(path, fallback_name):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        return yaml.safe_load(fm) or {}, body.strip()
    return {"name": fallback_name}, text.strip()


def load_goldens():
    out = []
    for path in sorted(GOLDENS.glob("*.yaml")):
        g = yaml.safe_load(path.read_text(encoding="utf-8"))
        g["_path"] = str(path.relative_to(ROOT))
        out.append(g)
    return out


def load_schema(rel_name):
    """Resolve a golden's `schema:` path, relative to the library root.

    Single source of truth: the goldens point at ../validate/review.schema.json,
    the same file work/validate/validate.py loads. Keeping one copy means the
    harness and the validator can never disagree about what is valid.
    """
    path = (ROOT / rel_name).resolve()
    if not path.exists():
        raise FileNotFoundError("schema not found: {}".format(path))
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Layer A — prompt contract
# --------------------------------------------------------------------------- #

REQUIRED_FRONTMATTER = ("name", "version", "model", "input_kind", "output_kind")


def check_prompt(meta, body, golden):
    """Return a list of failure strings for the prompt file itself."""
    failures = []
    for key in REQUIRED_FRONTMATTER:
        if not meta.get(key):
            failures.append("prompt frontmatter missing {!r}".format(key))
    if "{INPUT}" not in body:
        failures.append("prompt body has no {INPUT} placeholder")
    for needle in golden.get("prompt_must_contain", []):
        if needle not in body:
            failures.append("prompt lost constraint: {!r}".format(needle))
    return failures


# --------------------------------------------------------------------------- #
# Layer B — output
# --------------------------------------------------------------------------- #

def check_output(output, golden, schema):
    """Return a list of failure strings for the agent's response."""
    failures = []

    for needle in golden.get("expected_substrings", []):
        if needle not in output:
            failures.append("missing substring: {!r}".format(needle))
    for needle in golden.get("forbidden_substrings", []):
        if needle in output:
            failures.append("forbidden substring present: {!r}".format(needle))

    checks = golden.get("json_checks")
    if schema is None and not checks:
        return failures

    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        failures.append("output is not valid JSON: {}".format(exc))
        return failures

    if schema is not None:
        for err in sorted(Draft7Validator(schema).iter_errors(data), key=lambda e: list(e.path)):
            where = ".".join(str(p) for p in err.absolute_path) or "<root>"
            failures.append("schema: {}: {}".format(where, err.message))

    if checks:
        failures.extend(_check_json(data, checks))
    return failures


def _check_json(data, checks):
    failures = []
    issues = data.get("issues", []) if isinstance(data, dict) else []
    summary = data.get("summary", "") if isinstance(data, dict) else ""

    n = checks.get("issues_count_at_least")
    if n is not None and len(issues) < n:
        failures.append("expected >= {} issues, got {}".format(n, len(issues)))
    n = checks.get("issues_count_at_most")
    if n is not None and len(issues) > n:
        failures.append("expected <= {} issues, got {}".format(n, len(issues)))
    n = checks.get("issues_count_exactly")
    if n is not None and len(issues) != n:
        failures.append("expected exactly {} issues, got {}".format(n, len(issues)))

    severities = [i.get("severity") for i in issues]
    categories = [i.get("category") for i in issues]

    for sev in checks.get("severities_include", []):
        if sev not in severities:
            failures.append("no issue at severity {!r}".format(sev))
    allowed = checks.get("severities_only")
    if allowed is not None:
        extra = sorted(set(s for s in severities if s not in allowed))
        if extra:
            failures.append("severities outside {}: {}".format(allowed, extra))
    for cat in checks.get("categories_include", []):
        if cat not in categories:
            failures.append("no issue in category {!r}".format(cat))
    allowed = checks.get("categories_only")
    if allowed is not None:
        extra = sorted(set(c for c in categories if c not in allowed))
        if extra:
            failures.append("categories outside {}: {}".format(allowed, extra))

    prefix = checks.get("summary_startswith")
    if prefix is not None and not summary.startswith(prefix):
        failures.append("summary does not start with {!r}".format(prefix))
    needle = checks.get("summary_contains")
    if needle is not None and needle not in summary:
        failures.append("summary missing {!r}".format(needle))

    for want in checks.get("issue_must_match", []):
        if not any(_issue_matches(i, want) for i in issues):
            failures.append("no issue matching {}".format(want))
    return failures


def _issue_matches(issue, want):
    for key, value in want.items():
        if key == "message_contains":
            if value.lower() not in str(issue.get("message", "")).lower():
                return False
        elif key == "suggestion_contains":
            if value.lower() not in str(issue.get("suggestion") or "").lower():
                return False
        elif key == "text_contains":
            blob = "{} {}".format(issue.get("message", ""), issue.get("suggestion") or "")
            if value.lower() not in blob.lower():
                return False
        elif str(issue.get(key)) != str(value):
            return False
    return True


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #

def run_golden(golden, verbose):
    gid = golden["id"]
    try:
        meta, body = load_prompt(golden["prompt"])
    except FileNotFoundError as exc:
        return False, [str(exc)]

    failures = check_prompt(meta, body, golden)

    prompt_text = body.replace("{INPUT}", golden.get("input", ""))
    try:
        output = call_agent(prompt_text, golden.get("input", ""), gid)
    except (FileNotFoundError, NotImplementedError) as exc:
        return False, failures + [str(exc)]

    schema = load_schema(golden["schema"]) if golden.get("schema") else None
    failures.extend(check_output(output, golden, schema))
    return (not failures), failures


def main(argv):
    parser = argparse.ArgumentParser(description="Run the code-review prompt library eval.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on any failure (for CI).")
    parser.add_argument("--only", metavar="ID", help="Run a single golden by id.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print every failing check, not just the first.")
    args = parser.parse_args(argv[1:])

    goldens = load_goldens()
    if args.only:
        goldens = [g for g in goldens if g["id"] == args.only]
    if not goldens:
        print("no goldens found in {}".format(GOLDENS))
        return 1 if args.strict else 0

    mode = os.environ.get("EVAL_MODE", "offline")
    print("eval mode: {}  |  goldens: {}\n".format(mode, len(goldens)))

    passed = 0
    for g in goldens:
        ok, failures = run_golden(g, args.verbose)
        if ok:
            passed += 1
            print("[PASS] {:38s} ok".format(g["id"]))
        else:
            print("[FAIL] {:38s} {}".format(g["id"], failures[0]))
            if args.verbose:
                for f in failures[1:]:
                    print("       {:38s} {}".format("", f))
            elif len(failures) > 1:
                print("       {:38s} (+{} more; rerun with -v)".format("", len(failures) - 1))

    rate = passed / float(len(goldens))
    print("\n{}/{} passed ({:.0%}); threshold {:.0%}".format(
        passed, len(goldens), rate, PASS_THRESHOLD))

    if args.strict and passed != len(goldens):
        print("STRICT: {} golden(s) failing — blocking.".format(len(goldens) - passed))
        return 1
    if rate < PASS_THRESHOLD:
        print("Below threshold.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
