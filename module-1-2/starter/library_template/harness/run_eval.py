"""Five-prompt library eval harness.

Walks goldens/, runs each golden's prompt with the golden's input, scores the
output. The "agent call" is left as a function trainees fill in for their
chosen platform — it could call Claude Code via CLI, Copilot, an API, or a
fixture file for offline runs.

Usage:
  python3 harness/run_eval.py            # normal run
  python3 harness/run_eval.py --strict   # exit non-zero if any golden fails

The strict mode is what you wire into CI in Step 3 of the Combined M1+M2 Lab.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPTS = ROOT / "prompts"
GOLDENS = ROOT / "goldens"


def call_agent(prompt_body: str, input_text: str) -> str:
    """Run the prompt with the given input. Trainees: implement this for your platform.

    Three options, easiest to hardest:
    - OFFLINE: read a fixture file with the expected output (good for first runs).
    - CLI: shell out to `claude --prompt ...` or equivalent.
    - API: call the Anthropic / OpenAI SDK.

    The default below is the OFFLINE shim: it reads `goldens/<id>.fixture.txt`
    if present and returns it; otherwise raises.
    """
    raise NotImplementedError(
        "Implement call_agent() for your platform. See the docstring for options."
    )


def load_prompt(name: str) -> tuple[dict, str]:
    """Read a prompt file. Returns (frontmatter, body)."""
    for ext in (".md", ".yaml"):
        p = PROMPTS / f"{name}{ext}"
        if p.exists():
            text = p.read_text()
            if text.startswith("---"):
                _, fm, body = text.split("---", 2)
                return yaml.safe_load(fm), body.strip()
            return {"name": name}, text.strip()
    # Try to find any file with matching frontmatter
    for p in PROMPTS.glob("*.md"):
        text = p.read_text()
        if text.startswith("---"):
            _, fm, body = text.split("---", 2)
            meta = yaml.safe_load(fm)
            if meta.get("name") == name:
                return meta, body.strip()
    raise FileNotFoundError(f"prompt not found: {name}")


def load_goldens() -> list[dict]:
    out = []
    for path in sorted(GOLDENS.glob("*.yaml")):
        out.append(yaml.safe_load(path.read_text()))
    return out


def score(output: str, golden: dict) -> tuple[bool, str]:
    """Return (passed, reason)."""
    for needle in golden.get("expected_substrings", []):
        if needle not in output:
            return False, f"missing substring: {needle!r}"
    n = golden.get("expected_count_at_least")
    if n is not None:
        # Count "def test_" by default; trainees can swap to a regex.
        count = len(re.findall(r"def\s+test_", output))
        if count < n:
            return False, f"expected at least {n} test funcs, got {count}"
    return True, "ok"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on any failure (for CI).")
    args = parser.parse_args(argv[1:])

    goldens = load_goldens()
    if not goldens:
        print("no goldens found in", GOLDENS)
        return 0 if not args.strict else 1

    fails = 0
    for g in goldens:
        try:
            meta, body = load_prompt(g["prompt"])
        except FileNotFoundError as e:
            print(f"[ERROR] {g['id']}: {e}")
            fails += 1
            continue

        prompt_text = body.replace("{INPUT}", g["input"])
        try:
            output = call_agent(prompt_text, g["input"])
        except NotImplementedError as e:
            print(f"[SKIP]  {g['id']}: {e}")
            continue

        passed, reason = score(output, g)
        marker = "[PASS]" if passed else "[FAIL]"
        print(f"{marker} {g['id']:30s} -> {reason}")
        if not passed:
            fails += 1

    print(f"\n{len(goldens) - fails}/{len(goldens)} passed")
    if fails and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
