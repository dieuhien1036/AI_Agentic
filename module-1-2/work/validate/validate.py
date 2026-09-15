"""Validate a code-review JSON response against review.schema.json.

Usage:
  python3 validate.py <path_to_response.json>

Exit code 0 = valid; non-zero = invalid (with a printed error).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate.py <response.json>", file=sys.stderr)
        return 2
    response_path = Path(argv[1])
    schema_path = Path(__file__).parent / "review.schema.json"

    schema = json.loads(schema_path.read_text())
    try:
        instance = json.loads(response_path.read_text())
    except json.JSONDecodeError as e:
        print(f"NOT VALID JSON: {e}", file=sys.stderr)
        return 1

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if not errors:
        print("OK: response matches schema")
        return 0

    print("VALIDATION FAILED:", file=sys.stderr)
    for err in errors:
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        print(f"  {path}: {err.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
