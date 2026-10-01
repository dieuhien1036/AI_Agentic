#!/usr/bin/env python3
"""Mechanically check that a migration's ROLLBACK block undoes its forward SQL.

Usage:
  python check_reversible.py --migrations-dir <path> <migration file>

Replays every migration numbered below the target to get the "before" schema, then:

  has_rollback_block     the file has a `-- ROLLBACK` marker with at least one statement
  forward_supported      every forward statement is DDL this checker models (schema_state.py)
  forward_changes_schema forward SQL applies cleanly and actually changes the schema
  forward_not_destructive  no DROP TABLE / DROP COLUMN / TRUNCATE / bare DELETE in forward SQL
  rollback_applies       rollback SQL applies cleanly on top of the forward result
  round_trip             before -> forward -> rollback == before   (the reversibility claim)
  forward_rerunnable     applying forward twice does not error (IF NOT EXISTS guards)
  rollback_rerunnable    applying rollback twice does not error (IF EXISTS guards)

Prints one JSON object to stdout. Exit 0 = every check passed, 5 = at least one failed,
1 = usage error. Deterministic and offline: the migration-verifier subagent runs this first
and cannot overrule a failure.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_state import (
    MIGRATION_FILE_RE,
    ApplyError,
    apply_statements,
    diff_schemas,
    load_schema,
    parse_migration_file,
)

DESTRUCTIVE_RE = re.compile(
    r"\bDROP\s+TABLE\b|\bDROP\s+DATABASE\b|\bTRUNCATE\b|\bDROP\s+COLUMN\b|\bDELETE\s+FROM\s+\w+\s*$",
    re.IGNORECASE,
)


def check(migrations_dir: Path, target: Path) -> dict:
    checks: list[dict] = []

    def record(name: str, passed: bool, detail: str) -> bool:
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    m = MIGRATION_FILE_RE.match(target.name)
    number = int(m.group(1)) if m else None
    before = load_schema(migrations_dir, before_number=number)
    parsed = parse_migration_file(target)
    result: dict = {"file": target.as_posix(), "checks": checks}

    record(
        "has_rollback_block",
        parsed.has_rollback_block and bool(parsed.rollback),
        f"{len(parsed.rollback)} rollback statement(s)"
        if parsed.has_rollback_block
        else "no '-- ROLLBACK' marker found",
    )
    destructive = [s for s in parsed.forward if DESTRUCTIVE_RE.search(s)]
    record(
        "forward_not_destructive",
        not destructive,
        "none" if not destructive else "; ".join(destructive),
    )

    after_up = before.clone()
    try:
        apply_statements(after_up, parsed.forward)
        forward_diff = diff_schemas(before, after_up)
        record("forward_supported", True, f"{len(parsed.forward)} statement(s) modelled")
        record(
            "forward_changes_schema",
            bool(forward_diff),
            "; ".join(forward_diff) if forward_diff else "forward SQL is a no-op on this schema",
        )
    except ApplyError as exc:
        record("forward_supported", "unsupported" not in str(exc), str(exc))
        record("forward_changes_schema", False, f"forward SQL failed: {exc}")
        result["reversible"] = False
        return result
    result["forward_diff"] = forward_diff

    after_down = after_up.clone()
    try:
        apply_statements(after_down, parsed.rollback)
        record("rollback_applies", True, f"{len(parsed.rollback)} statement(s) applied")
    except ApplyError as exc:
        record("rollback_applies", False, str(exc))
        result["reversible"] = False
        return result

    leftover = diff_schemas(before, after_down)
    record(
        "round_trip",
        not leftover,
        "schema after rollback == schema before"
        if not leftover
        else "rollback leaves: " + "; ".join(leftover),
    )

    for name, start, stmts in (
        ("forward_rerunnable", after_up, parsed.forward),
        ("rollback_rerunnable", after_down, parsed.rollback),
    ):
        again = start.clone()
        try:
            apply_statements(again, stmts)
            record(name, True, "second application is a no-op")
        except ApplyError as exc:
            record(name, False, f"second application fails: {exc} (add IF [NOT] EXISTS)")

    result["reversible"] = all(c["passed"] for c in checks)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--migrations-dir", required=True)
    parser.add_argument("migration")
    args = parser.parse_args(argv[1:])

    migrations_dir, target = Path(args.migrations_dir), Path(args.migration)
    if not migrations_dir.is_dir() or not target.is_file():
        print(f"ERROR: not found: {migrations_dir if not migrations_dir.is_dir() else target}",
              file=sys.stderr)
        return 1
    try:
        result = check(migrations_dir, target)
    except ApplyError as exc:
        print(f"ERROR: could not replay earlier migrations: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["reversible"] else 5


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
