#!/usr/bin/env python3
"""Generate an add-column migration, with its rollback, from a structured spec.

Usage:
  python generate_migration.py --migrations-dir <path> --spec <spec.json | ->  [--dry-run]

The spec is the JSON the migration-request-parser subagent produces:

  {"status": "ok", "operation": "add_column", "table": "orders", "column": "notes",
   "type": "TEXT", "nullable": true, "default": null, "slug": "add_orders_notes",
   "request": "<the developer's original words>"}

What it does, in order -- every check runs before any file I/O, so a refusal never leaves a
partial file behind:

  1. Validate the spec's shape (identifiers, default literal) and build the forward SQL and
     its exact inverse.
  2. Idempotency: same slug + same SQL already on disk -> no-op. Same slug, different SQL ->
     conflict (migrations are append-only).
  3. Replay migrations/ into a schema (scripts/schema_state.py) and check the table exists and
     the column does NOT already exist.
  4. Apply the house rules from reference/type-rules.md: type allowlist, no NOT NULL without
     DEFAULT on an existing table, money is NUMERIC(12, 2), TIMESTAMPTZ not TIMESTAMP, JSONB
     not JSON.
  5. Destructive-operation guard on the forward SQL (carried over from Module 3's
     scaffold-migration skill). The rollback block is comments only and is not scanned.
  6. Write migrations/NNNN_<slug>.sql (NNNN = max existing + 1) from
     templates/add_column.sql.tpl.

Exit codes:
  0 created, or identical migration already exists (no-op)
  1 usage / malformed spec
  2 blocked by the destructive-operation guard
  3 slug already used by a migration with different content
  4 spec conflicts with the current schema or a house rule (all violations are listed)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_state import ApplyError, load_schema, migration_files

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_DIR / "templates" / "add_column.sql.tpl"

IDENT_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Base types this repo allows for a new column. See reference/type-rules.md.
ALLOWED_TYPE_RES = [
    re.compile(p)
    for p in (
        r"^TEXT$", r"^VARCHAR\(\d{1,4}\)$", r"^BOOLEAN$", r"^SMALLINT$", r"^INTEGER$",
        r"^BIGINT$", r"^NUMERIC\(\d{1,2}, ?\d{1,2}\)$", r"^TIMESTAMPTZ$", r"^DATE$",
        r"^JSONB$", r"^UUID$", r"^REAL$", r"^DOUBLE PRECISION$",
    )
]
MONEY_NAME_RE = re.compile(r"(^|_)(amount|price|total|discount|fee)s?($|_)")
MONEY_TYPE = "NUMERIC(12, 2)"
DEFAULT_LITERAL_RE = re.compile(
    r"^(-?\d+(\.\d+)?|'[^'\\]*'|TRUE|FALSE|now\(\)|CURRENT_DATE|CURRENT_TIMESTAMP)$",
    re.IGNORECASE,
)

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "DROP DATABASE"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"\bALTER\s+TABLE\b[^;]*\bDROP\s+COLUMN\b", re.IGNORECASE | re.DOTALL),
     "ALTER TABLE ... DROP COLUMN"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;", re.IGNORECASE), "DELETE FROM <table> with no WHERE"),
]


class SpecError(Exception):
    pass


def normalise_type(raw: str) -> str:
    t = re.sub(r"\s+", " ", raw.strip().upper())
    t = re.sub(r"\s*\(\s*", "(", t)
    t = re.sub(r"\s*\)", ")", t)
    t = re.sub(r"\s*,\s*", ", ", t)
    return {"FLOAT": "FLOAT", "INT": "INTEGER", "BOOL": "BOOLEAN"}.get(t, t)


def load_spec(source: str) -> dict:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    raw = raw.lstrip("﻿")  # PowerShell pipes and Windows editors prepend a BOM
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"spec is not valid JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecError("spec must be a JSON object")
    if spec.get("status") == "needs_clarification":
        questions = "; ".join(spec.get("questions", [])) or "(none listed)"
        raise SpecError(f"spec still needs clarification from the developer: {questions}")
    if spec.get("operation") != "add_column":
        raise SpecError(f"operation must be 'add_column', got {spec.get('operation')!r}")
    for key in ("table", "column"):
        if not isinstance(spec.get(key), str) or not IDENT_RE.match(spec[key]):
            raise SpecError(f"{key} must be a lowercase snake_case identifier, got {spec.get(key)!r}")
    if not isinstance(spec.get("type"), str) or not spec["type"].strip():
        raise SpecError("type must be a non-empty string")
    if not isinstance(spec.get("nullable"), bool):
        raise SpecError("nullable must be true or false")
    default = spec.get("default")
    if default is not None and (not isinstance(default, str) or not DEFAULT_LITERAL_RE.match(default)):
        raise SpecError(
            f"default must be null or a simple SQL literal (number, 'string', TRUE/FALSE, now()), "
            f"got {default!r}"
        )
    slug = spec.get("slug") or f"add_{spec['table']}_{spec['column']}"
    if not SLUG_RE.match(slug):
        raise SpecError(f"slug must be lowercase snake_case, got {slug!r}")
    spec["slug"] = slug
    spec["type"] = normalise_type(spec["type"])
    return spec


def rule_violations(spec: dict, migrations_dir: Path) -> list[str]:
    problems: list[str] = []
    try:
        schema = load_schema(migrations_dir)
    except ApplyError as exc:
        return [f"could not replay existing migrations: {exc}"]

    table, column, col_type = spec["table"], spec["column"], spec["type"]
    if table not in schema.tables:
        known = ", ".join(sorted(schema.tables)) or "(none)"
        problems.append(f"table {table!r} does not exist in migrations/ (known tables: {known})")
    elif column in schema.tables[table]:
        problems.append(
            f"column {table}.{column} already exists ({schema.tables[table][column]}); "
            "nothing to add"
        )

    if col_type == "TIMESTAMP" or col_type.startswith("TIMESTAMP WITHOUT"):
        problems.append(f"type {col_type} is not allowed: timestamps are TIMESTAMPTZ")
    elif col_type == "JSON":
        problems.append("type JSON is not allowed: structured blobs are JSONB")
    elif MONEY_NAME_RE.search(column) and col_type != MONEY_TYPE:
        problems.append(
            f"{column!r} looks like a money column: type must be {MONEY_TYPE}, got {col_type}"
        )
    elif not any(r.match(col_type) for r in ALLOWED_TYPE_RES):
        problems.append(f"type {col_type} is not on the allowlist in reference/type-rules.md")

    if not spec["nullable"] and spec.get("default") is None and table in schema.tables:
        problems.append(
            f"NOT NULL with no DEFAULT on existing table {table!r} fails on any existing row; "
            "make it nullable or give it a DEFAULT"
        )
    return problems


def build_sql(spec: dict) -> tuple[str, str]:
    parts = [f"ALTER TABLE {spec['table']} ADD COLUMN IF NOT EXISTS {spec['column']} {spec['type']}"]
    if not spec["nullable"]:
        parts.append("NOT NULL")
    if spec.get("default") is not None:
        parts.append(f"DEFAULT {spec['default']}")
    forward = " ".join(parts) + ";"
    rollback = f"ALTER TABLE {spec['table']} DROP COLUMN IF EXISTS {spec['column']};"
    return forward, rollback


def render(filename: str, spec: dict, forward: str, rollback: str) -> str:
    request = re.sub(r"\s+", " ", str(spec.get("request") or "(not recorded)")).strip()[:200]
    return (
        TEMPLATE_PATH.read_text(encoding="utf-8")
        .replace("{FILENAME}", filename)
        .replace("{REQUEST}", request)
        .replace("{FORWARD_SQL}", forward)
        .replace("{ROLLBACK_SQL}", rollback)
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--migrations-dir", required=True)
    parser.add_argument("--spec", required=True, help="Path to the spec JSON, or - for stdin.")
    parser.add_argument("--dry-run", action="store_true", help="Print the file; write nothing.")
    args = parser.parse_args(argv[1:])

    migrations_dir = Path(args.migrations_dir)
    if not migrations_dir.is_dir():
        print(f"ERROR: migrations dir not found: {migrations_dir}", file=sys.stderr)
        return 1

    try:
        spec = load_spec(args.spec)
    except (SpecError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    forward, rollback = build_sql(spec)

    # Slug check first: re-running a request that already produced this exact file must be a
    # no-op, not a "column already exists" refusal caused by our own earlier run.
    slug = spec["slug"]
    for _, existing in migration_files(migrations_dir):
        if existing.name.split("_", 1)[1] == f"{slug}.sql":
            text = existing.read_text(encoding="utf-8")
            if forward in text and rollback in text:
                print(f"NO-OP: {existing.as_posix()} already contains this migration.")
                return 0
            print(
                f"CONFLICT: slug {slug!r} is already used by {existing.name} with different SQL. "
                "Migrations are append-only: pick a new slug or confirm the existing file "
                "covers this change.",
                file=sys.stderr,
            )
            return 3

    problems = rule_violations(spec, migrations_dir)
    if problems:
        print("REFUSED: the spec conflicts with the current schema or a house rule:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("No file was written.", file=sys.stderr)
        return 4

    hits = [label for pattern, label in DESTRUCTIVE_PATTERNS if pattern.search(forward)]
    if hits:
        print(f"BLOCKED: forward SQL matches destructive pattern(s): {', '.join(hits)}",
              file=sys.stderr)
        print("No file was written. See reference/destructive-operations.md.", file=sys.stderr)
        return 2

    existing_numbers = [n for n, _ in migration_files(migrations_dir)]
    number = (max(existing_numbers) if existing_numbers else 0) + 1
    filename = f"{number:04d}_{slug}.sql"
    content = render(filename, spec, forward, rollback)

    if args.dry_run:
        print(f"DRY-RUN: would write {(migrations_dir / filename).as_posix()}\n")
        print(content)
        return 0

    out_path = migrations_dir / filename
    out_path.write_text(content, encoding="utf-8")
    print(f"CREATED: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
