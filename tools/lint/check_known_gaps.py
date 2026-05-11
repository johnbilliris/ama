#!/usr/bin/env python3
"""
check_known_gaps.py — Assert every row in docs/architecture/known-gaps.md has a valid Follow-up Task Ref.

Usage: python tools/lint/check_known_gaps.py [--root REPO_ROOT]

Exit 0: All rows valid.
Exit 1: One or more rows have empty or TBD Follow-up Task Ref.
"""

import argparse
from pathlib import Path
import re
import sys


TABLE_ROW_RE = re.compile(r"^\|.*\|$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current working directory).",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    known_gaps_path = root / "docs" / "architecture" / "known-gaps.md"
    if not known_gaps_path.exists():
        print(f"FAIL: docs/architecture/known-gaps.md not found at {known_gaps_path}")
        return 1

    failures: list[tuple[int, str]] = []
    checked_rows = 0
    text = known_gaps_path.read_text(encoding="utf-8")

    for row_number, line in enumerate(text.splitlines(), 1):
        if not TABLE_ROW_RE.match(line):
            continue
        if "Area/Spec" in line or "---|" in line or "--- |" in line:
            continue

        columns = [cell.strip() for cell in line.split("|")[1:-1]]
        area_spec = columns[0] if columns else ""
        if not area_spec or area_spec == "_(none yet)_" or area_spec.startswith("---"):
            continue

        follow_up_task_ref = columns[2] if len(columns) > 2 else ""
        checked_rows += 1
        if not follow_up_task_ref or follow_up_task_ref.lower() == "tbd":
            failures.append((row_number, line))

    if failures:
        for row_number, line in failures:
            print(
                f"FAIL: docs/architecture/known-gaps.md row {row_number}: "
                "Follow-up Task Ref is empty or 'TBD'"
            )
            print(f"  Row content: {line}")
        print(f"Total failures: {len(failures)}")
        return 1

    print(f"All {checked_rows} rows valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
