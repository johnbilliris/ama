#!/usr/bin/env python3
"""
check_spec_cross_refs.py — Assert every shipped spec (001–037) is cited in docs/architecture/**/*.md.

Usage: python tools/lint/check_spec_cross_refs.py [--root REPO_ROOT]

Exit 0: All spec numbers cited (or excluded via known-gaps Resolved entries).
Exit 1: One or more spec numbers missing citations.
"""

import argparse
from pathlib import Path
import re
import sys


SPEC_DIR_RE = re.compile(r"^(\d{3})-")
KNOWN_GAPS_ROW_RE = re.compile(r"^\|.*\|$")
EXCLUSION_RE = re.compile(r"^spec-(\d{3})")
CITATION_RE = re.compile(r"spec[- ]?(\d{3})", re.IGNORECASE)


def build_spec_inventory(root: Path) -> set[str]:
    specs_dir = root / "specs"
    spec_inventory: set[str] = set()
    if not specs_dir.exists():
        return spec_inventory

    for entry in specs_dir.iterdir():
        if not entry.is_dir():
            continue
        match = SPEC_DIR_RE.match(entry.name)
        if match:
            spec_inventory.add(match.group(1))
    return spec_inventory


def build_exclusion_set(root: Path) -> set[str]:
    known_gaps_path = root / "docs" / "architecture" / "known-gaps.md"
    exclusion_set: set[str] = set()
    if not known_gaps_path.exists():
        return exclusion_set

    text = known_gaps_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not KNOWN_GAPS_ROW_RE.match(line):
            continue
        if "Area/Spec" in line or "---|" in line or "--- |" in line:
            continue

        columns = [cell.strip() for cell in line.split("|")[1:-1]]
        area_spec = columns[0] if columns else ""
        status = columns[4] if len(columns) > 4 else ""
        match = EXCLUSION_RE.match(area_spec)
        if match and status == "Resolved":
            exclusion_set.add(match.group(1))

    return exclusion_set


def build_cited_set(root: Path) -> set[str]:
    architecture_dir = root / "docs" / "architecture"
    cited_set: set[str] = set()
    if not architecture_dir.exists():
        return cited_set

    for markdown_file in architecture_dir.rglob("*.md"):
        text = markdown_file.read_text(encoding="utf-8")
        cited_set.update(CITATION_RE.findall(text))
    return cited_set


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
    spec_inventory = build_spec_inventory(root)
    exclusion_set = build_exclusion_set(root)
    required = spec_inventory - exclusion_set
    cited_set = build_cited_set(root)
    missing = sorted(required - cited_set)

    if missing:
        print("FAIL: The following spec numbers are not cited in any docs/architecture/**/*.md page:")
        for spec_number in missing:
            print(f"  spec-{spec_number} (no citation found)")
        print(f"Total missing: {len(missing)}")
        print()
        print("To fix: add a citation (e.g., <!-- spec-cross-ref: spec-003 -->) to at least one")
        print("architecture page, or add the spec to docs/architecture/known-gaps.md with a")
        print("non-empty Follow-up Task Ref and Status = 'Resolved' if it is archived/superseded.")
        return 1

    print(f"All {len(required)} spec numbers cited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
