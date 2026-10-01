"""Replay the repo's migrations/ directory into an in-memory schema.

Shared by generate_migration.py (does the table exist? does the column already exist?) and
check_reversible.py (does forward-then-rollback return the schema to where it started?).

It understands the small DDL subset this repo's migrations use:

  CREATE TABLE [IF NOT EXISTS] t (...)        DROP TABLE [IF EXISTS] t
  ALTER TABLE [IF EXISTS] t ADD COLUMN [IF NOT EXISTS] c <definition>
  ALTER TABLE [IF EXISTS] t DROP COLUMN [IF EXISTS] c
  CREATE [UNIQUE] INDEX [IF NOT EXISTS] i ON t (...)
  DROP INDEX [IF EXISTS] i

Anything else is reported as "unsupported", never silently ignored, so a caller can refuse to
make a safety claim about SQL it did not model.

Migration file layout (see templates/add_column.sql.tpl):

  forward SQL                 plain SQL; whole-line `--` comments are ignored
  -- ROLLBACK                 marker line, exactly this text
  -- <rollback SQL>           every line after the marker, with the leading `-- ` removed
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from pathlib import Path

MIGRATION_FILE_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")
ROLLBACK_MARKER_RE = re.compile(r"^--\s*ROLLBACK\s*$", re.IGNORECASE)
IDENT = r"([A-Za-z_][A-Za-z0-9_]*)"

CREATE_TABLE_RE = re.compile(
    rf"^CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?{IDENT}\s*\((.*)\)$", re.IGNORECASE | re.DOTALL
)
DROP_TABLE_RE = re.compile(rf"^DROP\s+TABLE\s+(IF\s+EXISTS\s+)?{IDENT}$", re.IGNORECASE)
ADD_COLUMN_RE = re.compile(
    rf"^ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?{IDENT}\s+ADD\s+(?:COLUMN\s+)?"
    rf"(IF\s+NOT\s+EXISTS\s+)?{IDENT}\s+(.+)$",
    re.IGNORECASE | re.DOTALL,
)
DROP_COLUMN_RE = re.compile(
    rf"^ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?{IDENT}\s+DROP\s+(?:COLUMN\s+)?"
    rf"(IF\s+EXISTS\s+)?{IDENT}$",
    re.IGNORECASE,
)
CREATE_INDEX_RE = re.compile(
    rf"^CREATE\s+(?:UNIQUE\s+)?INDEX\s+(IF\s+NOT\s+EXISTS\s+)?{IDENT}\s+ON\s+{IDENT}\b",
    re.IGNORECASE,
)
DROP_INDEX_RE = re.compile(rf"^DROP\s+INDEX\s+(IF\s+EXISTS\s+)?{IDENT}$", re.IGNORECASE)
TABLE_CONSTRAINT_RE = re.compile(
    r"^(PRIMARY\s+KEY|UNIQUE|CONSTRAINT|CHECK|FOREIGN\s+KEY|EXCLUDE)\b", re.IGNORECASE
)


@dataclass
class Schema:
    # table -> {column -> normalised definition}; dicts keep column order
    tables: dict[str, dict[str, str]] = field(default_factory=dict)
    # index -> table
    indexes: dict[str, str] = field(default_factory=dict)

    def clone(self) -> Schema:
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return {"tables": self.tables, "indexes": self.indexes}


@dataclass
class ParsedMigration:
    path: Path
    forward: list[str]
    rollback: list[str]
    has_rollback_block: bool


class ApplyError(Exception):
    pass


def _norm(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


def split_statements(sql: str) -> list[str]:
    """Split on semicolons that are outside parentheses and single-quoted strings."""
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    in_str = False
    for ch in sql:
        if ch == "'":
            in_str = not in_str
        elif not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == ";" and depth == 0:
                stmt = "".join(buf).strip()
                if stmt:
                    out.append(stmt)
                buf = []
                continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


def _split_top_level_commas(body: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf).strip())
    return parts


def parse_migration_text(text: str, path: Path | None = None) -> ParsedMigration:
    forward_lines: list[str] = []
    rollback_lines: list[str] = []
    in_rollback = False
    for line in text.splitlines():
        stripped = line.strip()
        if ROLLBACK_MARKER_RE.match(stripped):
            in_rollback = True
            continue
        if in_rollback:
            if stripped.startswith("--"):
                rollback_lines.append(stripped[2:].strip())
            elif stripped:
                # Live SQL after the marker would run on every deploy -- keep it visible
                # as a forward statement so the checks see it.
                forward_lines.append(line)
            continue
        if stripped.startswith("--"):
            continue
        forward_lines.append(line)
    return ParsedMigration(
        path=path or Path("<text>"),
        forward=split_statements("\n".join(forward_lines)),
        rollback=split_statements("\n".join(rollback_lines)),
        has_rollback_block=in_rollback,
    )


def parse_migration_file(path: Path) -> ParsedMigration:
    return parse_migration_text(path.read_text(encoding="utf-8"), path)


def apply_statement(schema: Schema, stmt: str) -> None:
    """Apply one DDL statement in place. Raises ApplyError the way Postgres would."""
    s = stmt.strip()

    m = CREATE_TABLE_RE.match(s)
    if m:
        if_not_exists, table, body = m.group(1), m.group(2).lower(), m.group(3)
        if table in schema.tables:
            if if_not_exists:
                return
            raise ApplyError(f"relation {table!r} already exists")
        cols: dict[str, str] = {}
        for item in _split_top_level_commas(body):
            if TABLE_CONSTRAINT_RE.match(item):
                continue
            name, _, definition = item.partition(" ")
            cols[name.lower()] = _norm(definition)
        schema.tables[table] = cols
        return

    m = DROP_TABLE_RE.match(s)
    if m:
        if_exists, table = m.group(1), m.group(2).lower()
        if table not in schema.tables:
            if if_exists:
                return
            raise ApplyError(f"table {table!r} does not exist")
        del schema.tables[table]
        schema.indexes = {i: t for i, t in schema.indexes.items() if t != table}
        return

    m = ADD_COLUMN_RE.match(s)
    if m:
        table, if_not_exists, column, definition = (
            m.group(1).lower(), m.group(2), m.group(3).lower(), _norm(m.group(4))
        )
        if table not in schema.tables:
            raise ApplyError(f"relation {table!r} does not exist")
        if column in schema.tables[table]:
            if if_not_exists:
                return
            raise ApplyError(f"column {column!r} of relation {table!r} already exists")
        schema.tables[table][column] = definition
        return

    m = DROP_COLUMN_RE.match(s)
    if m:
        table, if_exists, column = m.group(1).lower(), m.group(2), m.group(3).lower()
        if table not in schema.tables:
            raise ApplyError(f"relation {table!r} does not exist")
        if column not in schema.tables[table]:
            if if_exists:
                return
            raise ApplyError(f"column {column!r} of relation {table!r} does not exist")
        del schema.tables[table][column]
        return

    m = CREATE_INDEX_RE.match(s)
    if m:
        if_not_exists, index, table = m.group(1), m.group(2).lower(), m.group(3).lower()
        if index in schema.indexes:
            if if_not_exists:
                return
            raise ApplyError(f"relation {index!r} already exists")
        if table not in schema.tables:
            raise ApplyError(f"relation {table!r} does not exist")
        schema.indexes[index] = table
        return

    m = DROP_INDEX_RE.match(s)
    if m:
        if_exists, index = m.group(1), m.group(2).lower()
        if index not in schema.indexes:
            if if_exists:
                return
            raise ApplyError(f"index {index!r} does not exist")
        del schema.indexes[index]
        return

    raise ApplyError(f"unsupported statement (not modelled): {_norm(s)[:80]}")


def apply_statements(schema: Schema, stmts: list[str]) -> None:
    for stmt in stmts:
        apply_statement(schema, stmt)


def migration_files(migrations_dir: Path) -> list[tuple[int, Path]]:
    found = []
    for p in migrations_dir.glob("*.sql"):
        m = MIGRATION_FILE_RE.match(p.name)
        if m:
            found.append((int(m.group(1)), p))
    return sorted(found)


def load_schema(migrations_dir: Path, before_number: int | None = None) -> Schema:
    """Replay the forward SQL of every migration (optionally only those numbered < N)."""
    schema = Schema()
    for number, path in migration_files(migrations_dir):
        if before_number is not None and number >= before_number:
            continue
        try:
            apply_statements(schema, parse_migration_file(path).forward)
        except ApplyError as exc:
            raise ApplyError(f"{path.name}: {exc}") from exc
    return schema


def diff_schemas(before: Schema, after: Schema) -> list[str]:
    lines: list[str] = []
    for table in sorted(set(before.tables) | set(after.tables)):
        b, a = before.tables.get(table), after.tables.get(table)
        if b is None:
            lines.append(f"+ table {table}")
            continue
        if a is None:
            lines.append(f"- table {table}")
            continue
        for col in b:
            if col not in a:
                lines.append(f"- {table}.{col} {b[col]}")
            elif a[col] != b[col]:
                lines.append(f"~ {table}.{col} {b[col]} -> {a[col]}")
        for col in a:
            if col not in b:
                lines.append(f"+ {table}.{col} {a[col]}")
    for idx in sorted(set(before.indexes) | set(after.indexes)):
        if idx not in before.indexes:
            lines.append(f"+ index {idx}")
        elif idx not in after.indexes:
            lines.append(f"- index {idx}")
    return lines
