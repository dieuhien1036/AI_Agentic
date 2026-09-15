#!/usr/bin/env python3
"""Scaffold a new append-only SQL migration file.

Usage:
  python3 scaffold_migration.py --migrations-dir <path> --name <slug> --body-file <path> [--allow-destructive]
  python3 scaffold_migration.py --migrations-dir <path> --name <slug> --body-file -           # read body from stdin

Behavior:
  - Finds the next migration number by scanning <migrations-dir> for files matching
    NNNN_*.sql and taking max(N) + 1 (4-digit, zero-padded). An empty directory starts
    at 0001.
  - Writes <migrations-dir>/NNNN_<slug>.sql from templates/migration.sql.tpl next to
    this script.
  - Idempotent: if a migration file already exists for <slug> with byte-identical SQL
    body, does nothing and exits 0 (re-running the same request does not create a
    duplicate file or bump the number). If a migration exists for <slug> with a
    *different* body, that's a conflict — refuses and exits 3 rather than silently
    overwriting or silently creating a second file for the same slug.
  - Refuses to scaffold a migration whose body matches a destructive-operation pattern
    (DROP TABLE, TRUNCATE, DELETE without WHERE, DROP COLUMN, DROP DATABASE) unless
    --allow-destructive is passed explicitly. This is a mechanical safety net, not a
    judgment call — the skill's own instructions are what decide whether a destructive
    op is ever appropriate to scaffold at all.
  - Never writes a partial file: validation happens before any file I/O.

Exit codes: 0 = created or no-op idempotent match, 1 = usage/input error,
  2 = blocked by destructive-operation guard, 3 = slug conflict (existing file, different body).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "migration.sql.tpl"

MIGRATION_FILE_RE = re.compile(r"^(\d{4})_.*\.sql$")
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "DROP DATABASE"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"\bALTER\s+TABLE\b[^;]*\bDROP\s+COLUMN\b", re.IGNORECASE | re.DOTALL), "ALTER TABLE ... DROP COLUMN"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*;", re.IGNORECASE), "DELETE FROM <table> with no WHERE clause"),
]


def find_next_number(migrations_dir: Path) -> int:
    max_n = 0
    for p in migrations_dir.glob("*.sql"):
        m = MIGRATION_FILE_RE.match(p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def find_existing_for_slug(migrations_dir: Path, slug: str) -> Path | None:
    for p in migrations_dir.glob(f"*_{slug}.sql"):
        if MIGRATION_FILE_RE.match(p.name):
            return p
    return None


def check_destructive(body: str) -> list[str]:
    hits = []
    for pattern, label in DESTRUCTIVE_PATTERNS:
        if pattern.search(body):
            hits.append(label)
    return hits


def render(number: int, slug: str, body: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    filename = f"{number:04d}_{slug}.sql"
    return template.replace("{FILENAME}", filename).replace("{SQL_BODY}", body.strip() + "\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--migrations-dir", required=True, help="Path to the repo's migrations/ directory.")
    parser.add_argument("--name", required=True, help="Slug for the migration, e.g. add_orders_notes.")
    parser.add_argument("--body-file", required=True, help="Path to a file containing the SQL body, or - for stdin.")
    parser.add_argument("--allow-destructive", action="store_true",
                        help="Bypass the destructive-operation guard. Use only after explicit human sign-off.")
    args = parser.parse_args(argv[1:])

    migrations_dir = Path(args.migrations_dir)
    if not migrations_dir.is_dir():
        print(f"ERROR: migrations dir not found: {migrations_dir}", file=sys.stderr)
        return 1

    slug = args.name.strip()
    if not SLUG_RE.match(slug):
        print(f"ERROR: --name must be lowercase snake_case (e.g. add_orders_notes), got: {slug!r}", file=sys.stderr)
        return 1

    if args.body_file == "-":
        body = sys.stdin.read()
    else:
        body_path = Path(args.body_file)
        if not body_path.is_file():
            print(f"ERROR: --body-file not found: {body_path}", file=sys.stderr)
            return 1
        body = body_path.read_text(encoding="utf-8")

    if not body.strip():
        print("ERROR: SQL body is empty. Refusing to scaffold an empty migration.", file=sys.stderr)
        return 1

    hits = check_destructive(body)
    if hits and not args.allow_destructive:
        print("BLOCKED: this migration body matches destructive-operation pattern(s):", file=sys.stderr)
        for h in hits:
            print(f"  - {h}", file=sys.stderr)
        print(
            "No file was written. See reference/destructive-operations.md for the "
            "required sign-off process, then re-run with --allow-destructive if this "
            "is genuinely intended and approved.",
            file=sys.stderr,
        )
        return 2

    existing = find_existing_for_slug(migrations_dir, slug)
    if existing is not None:
        existing_body = existing.read_text(encoding="utf-8")
        new_content_body = body.strip() + "\n"
        if new_content_body in existing_body:
            print(f"NO-OP: {existing.name} already contains this exact migration body. Nothing written.")
            return 0
        print(
            f"ERROR: a migration already exists for slug {slug!r} ({existing.name}) with "
            "different content. Migrations are append-only and never edited in place — "
            "pick a different --name for this new change, or confirm the existing file "
            "already covers it.",
            file=sys.stderr,
        )
        return 3

    number = find_next_number(migrations_dir)
    content = render(number, slug, body)
    out_path = migrations_dir / f"{number:04d}_{slug}.sql"
    out_path.write_text(content, encoding="utf-8")
    print(f"CREATED: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
