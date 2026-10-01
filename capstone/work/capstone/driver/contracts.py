"""Shared helpers for the driver and the eval harness: paths, JSON contracts, agent calls."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # capstone/
REPO = ROOT / "target-repo"
AGENTS_DIR = REPO / ".claude" / "agents"
SKILL_SCRIPTS = REPO / ".claude" / "skills" / "generate-migration" / "scripts"
SCHEMAS = ROOT / "schemas"
PROMPT_FILE = ROOT / "prompts" / "parse-migration-request.md"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

try:
    from jsonschema import Draft7Validator
except ImportError:  # the driver still runs; validation falls back to a key check
    Draft7Validator = None


class ContractError(Exception):
    pass


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    m = FRONTMATTER_RE.match(text.lstrip("﻿"))
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, text[m.end():]


def parse_strict_json(raw: str) -> dict:
    """The prompts demand ONLY a JSON object: fences or surrounding prose are a contract break."""
    text = raw.lstrip("﻿").strip()  # a BOM from a Windows editor is not a contract break
    if text.startswith("```"):
        raise ContractError("response is wrapped in a markdown code fence")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"response is not a single JSON object: {exc}") from exc
    if not isinstance(obj, dict):
        raise ContractError("response JSON is not an object")
    return obj


def validate(obj: dict, schema_name: str) -> None:
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    if Draft7Validator is None:
        required = schema.get("required") or []
        missing = [k for k in required if k not in obj]
        if missing:
            raise ContractError(f"{schema_name}: missing keys {missing}")
        return
    errors = sorted(Draft7Validator(schema).iter_errors(obj), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        where = "/".join(str(p) for p in e.path) or "<root>"
        raise ContractError(f"{schema_name}: {where}: {e.message}")


def call_agent_live(
    agent_name: str, payload: str, cwd: Path | None = None, timeout: int = 300
) -> str:
    """Run a subagent definition headless through the Claude Code CLI (`claude -p`).

    The agent file's body is sent as the instructions and its `model:` front matter picks the
    model, so the parser (haiku) and the verifier (sonnet) stay on different models.
    """
    exe = shutil.which("claude")
    if exe is None:
        raise RuntimeError("live mode needs the Claude Code CLI ('claude') on PATH")
    meta, body = split_frontmatter((AGENTS_DIR / f"{agent_name}.md").read_text(encoding="utf-8"))
    cmd = [exe, "-p", "--output-format", "text"]
    if meta.get("model"):
        cmd += ["--model", meta["model"]]
    proc = subprocess.run(
        cmd,
        input=f"{body}\n\n---\n\n# Input\n\n{payload}\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd or REPO),
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed ({proc.returncode}): {proc.stderr.strip()[:500]}")
    return proc.stdout
