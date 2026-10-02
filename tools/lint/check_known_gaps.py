#!/usr/bin/env python3
"""
check_known_gaps.py — Assert every row in docs/architecture/known-gaps.md has a valid Follow-up Task Ref.

Usage: python tools/lint/check_known_gaps.py [--root REPO_ROOT]

Exit 0: All rows valid.
Exit 1: One or more rows have empty or TBD Follow-up Task Ref.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.lint._architecture_docs_common import (  # noqa: E402
    is_resolvable_reference,
    is_valid_iso_date,
    parse_known_gaps_rows,
    strip_inline_markdown,
)

PLACEHOLDER_RE = re.compile(r"^(?:tbd|todo|n/a|none|pending|placeholder)$", re.IGNORECASE)
AREA_SPEC_RE = re.compile(r"^[A-Z0-9-]+$")
STATUS_ALLOWED = {"Open", "In Progress", "Resolved"}

# Explicit empty-state markers. An arbitrary empty file is still rejected.
NO_GAP_MARKERS = {"_(none yet)_", "(none yet)", "none yet", "-", "\u2014"}


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

    failures: list[str] = []
    checked_rows = 0
    rows, has_header = parse_known_gaps_rows(known_gaps_path)
    seen_area_specs: set[str] = set()
    explicit_no_gap_marker = False

    for row in rows:
        if not row.area_spec and not row.gap_description and not row.follow_up_task_ref:
            failures.append(f"row {row.line_number}: malformed table row; expected 5 columns")
            continue

        area_spec = strip_inline_markdown(row.area_spec)
        if area_spec in NO_GAP_MARKERS:
            explicit_no_gap_marker = True
            continue
        if area_spec == "":
            continue

        follow_up_task_ref = strip_inline_markdown(row.follow_up_task_ref)
        date_identified = strip_inline_markdown(row.date_identified)
        status = strip_inline_markdown(row.status)
        checked_rows += 1

        if area_spec in seen_area_specs:
            failures.append(f"row {row.line_number}: duplicate Area/Spec identifier '{area_spec}'")
        seen_area_specs.add(area_spec)

        if not AREA_SPEC_RE.match(area_spec):
            failures.append(f"row {row.line_number}: Area/Spec '{area_spec}' must be uppercase alnum/hyphen")

        if not follow_up_task_ref or PLACEHOLDER_RE.match(follow_up_task_ref):
            failures.append(
                f"row {row.line_number}: Follow-up Task Ref is empty or placeholder ('{row.follow_up_task_ref}')"
            )
            continue
        if "issues/new?" in follow_up_task_ref:
            failures.append(
                f"row {row.line_number}: Follow-up Task Ref must point to a concrete issue, not issue-creation URL"
            )
            continue
        if not is_resolvable_reference(follow_up_task_ref, root, known_gaps_path):
            failures.append(f"row {row.line_number}: Follow-up Task Ref is not resolvable ('{row.follow_up_task_ref}')")

        if not is_valid_iso_date(date_identified):
            failures.append(f"row {row.line_number}: Date Identified must be ISO yyyy-mm-dd ('{row.date_identified}')")
            continue
        if status not in STATUS_ALLOWED:
            failures.append(f"row {row.line_number}: Status must be one of {sorted(STATUS_ALLOWED)} ('{row.status}')")

    if not has_header:
        print("FAIL: docs/architecture/known-gaps.md is missing the required table header")
        return 1

    if checked_rows == 0:
        if explicit_no_gap_marker and not failures:
            print("All 0 rows valid (explicit no-gap state).")
            return 0
        print("FAIL: docs/architecture/known-gaps.md has no actionable data rows")
        return 1

    if failures:
        for failure in failures:
            print(f"FAIL: docs/architecture/known-gaps.md {failure}")
        print(f"Total failures: {len(failures)}")
        return 1

    print(f"All {checked_rows} rows valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
