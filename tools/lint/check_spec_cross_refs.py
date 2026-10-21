#!/usr/bin/env python3
"""
check_spec_cross_refs.py — Assert every shipped spec (001–037) is cited in docs/architecture/**/*.md.

Usage: python tools/lint/check_spec_cross_refs.py [--root REPO_ROOT]

Exit 0: All spec numbers cited (or excluded via known-gaps Resolved entries).
Exit 1: One or more spec numbers missing citations.
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.lint._architecture_docs_common import (  # noqa: E402
    MARKDOWN_LINK_RE,
    is_resolvable_reference,
    parse_known_gaps_rows,
    split_local_ref,
)

SPEC_DIR_RE = re.compile(r"^(\d{3})-")
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_MAX_TRACKED_SPEC = 37
SPEC_DOC_RE = re.compile(r"(?:^|[\\/])specs[\\/](\d{3})-[^\\/]+[\\/]spec\.md$", re.IGNORECASE)
SPEC_GAP_ID_RE = re.compile(r"^SPEC-(\d{3})$", re.IGNORECASE)


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
            spec_number = int(match.group(1))
            if 1 <= spec_number <= _MAX_TRACKED_SPEC:
                spec_inventory.add(match.group(1))
    return spec_inventory


def build_exclusion_set(root: Path) -> tuple[set[str], list[str]]:
    known_gaps_path = root / "docs" / "architecture" / "known-gaps.md"
    exclusion_set: set[str] = set()
    failures: list[str] = []
    if not known_gaps_path.exists():
        return exclusion_set, failures

    rows, _ = parse_known_gaps_rows(known_gaps_path)
    for row in rows:
        match = SPEC_GAP_ID_RE.match(row.area_spec.strip()) if row.area_spec else None
        if not match:
            continue

        spec_id = match.group(1)
        if row.status.strip() != "Resolved":
            continue

        reason = row.gap_description.lower()
        if "archive" not in reason and "supersed" not in reason:
            failures.append(
                f"known-gaps row {row.line_number}: SPEC-{spec_id} exclusions require archive/superseded evidence"
            )
            continue
        if not is_resolvable_reference(row.follow_up_task_ref, root, known_gaps_path):
            failures.append(f"known-gaps row {row.line_number}: SPEC-{spec_id} exclusion follow-up is not resolvable")
            continue
        exclusion_set.add(spec_id)

    return exclusion_set, failures


def build_cited_set(root: Path) -> set[str]:
    architecture_dir = root / "docs" / "architecture"
    cited_set: set[str] = set()
    if not architecture_dir.exists():
        return cited_set

    for markdown_file in architecture_dir.rglob("*.md"):
        if markdown_file.name == "known-gaps.md":
            continue
        text = markdown_file.read_text(encoding="utf-8")
        text = _CODE_FENCE_RE.sub("", text)
        text = _HTML_COMMENT_RE.sub("", text)
        for target in MARKDOWN_LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not is_resolvable_reference(
                target,
                root,
                markdown_file,
                allow_repo_root_relative=False,
            ):
                continue

            local_target, _ = split_local_ref(target)
            resolved = (markdown_file.parent / local_target).resolve()
            if not resolved.exists():
                continue

            rel = resolved.relative_to(root).as_posix()
            match = SPEC_DOC_RE.search(rel)
            if match:
                cited_set.add(match.group(1))
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
    specs_dir = root / "specs"
    architecture_dir = root / "docs" / "architecture"
    if not specs_dir.exists():
        print(f"FAIL: specs directory not found at {specs_dir}")
        return 1
    if not architecture_dir.exists():
        print(f"FAIL: architecture docs directory not found at {architecture_dir}")
        return 1

    spec_inventory = build_spec_inventory(root)
    if not spec_inventory:
        print("FAIL: no tracked specs found in specs/ (expected 001-037 feature folders)")
        return 1
    exclusion_set, exclusion_failures = build_exclusion_set(root)
    if exclusion_failures:
        print("FAIL: invalid known-gaps exclusions")
        for failure in exclusion_failures:
            print(f"  - {failure}")
        return 1
    required = spec_inventory - exclusion_set
    cited_set = build_cited_set(root)
    missing = sorted(required - cited_set)

    if missing:
        print("FAIL: The following spec numbers are not cited in any docs/architecture/**/*.md page:")
        for spec_number in missing:
            print(f"  spec-{spec_number} (no citation found)")
        print(f"Total missing: {len(missing)}")
        print()
        print("To fix: add a resolvable local markdown link to the relevant specs/NNN-*/spec.md page")
        print("from at least one docs/architecture page, or mark SPEC-NNN as Resolved in")
        print("docs/architecture/known-gaps.md with archive/superseded evidence and a resolvable reference.")
        return 1

    print(f"All {len(required)} spec numbers cited via resolvable local spec links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
