#!/usr/bin/env python3
"""Spec-007 AUD-029 — keep the required isolation gate honest.

The ``spec007_isolation`` marker is only a release gate if the dedicated CI job
actually selects every marked module and refuses to pass on an empty selection.
This check fails when:

* a test module carries ``pytest.mark.spec007_isolation`` but is missing from the
  job's pytest invocation (silently unenforced behaviour), or
* the job lists a module that no longer carries the marker (stale selector), or
* the job drops ``-m spec007_isolation`` / ``--strict-markers``, or
* the job stops asserting an explicit, positive minimum collected-case count.

Parsed as text so the isolation CI job stays dependency-light (pytest only).

Usage::

    python tools/lint/check_spec007_isolation_selector.py
    python tools/lint/check_spec007_isolation_selector.py --repo-root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MARKER = "spec007_isolation"
JOB_NAME = "simulation-tenant-isolation"
WORKFLOW = Path(".github/workflows/ci.yml")
TEST_ROOT = Path("tests")

_MARKED = re.compile(rf"pytest\.mark\.{MARKER}\b")
_TEST_PATH = re.compile(r"tests/[\w./-]+\.py")
_MIN_CASES = re.compile(r"SPEC007_MIN_CASES:\s*\"?(\d+)\"?")


def _job_block(workflow_text: str) -> str | None:
    match = re.search(
        rf"(?ms)^  {re.escape(JOB_NAME)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        workflow_text,
    )
    return match.group("body") if match else None


def _marked_modules(repo_root: Path) -> set[str]:
    found: set[str] = set()
    for path in sorted((repo_root / TEST_ROOT).rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _MARKED.search(text):
            found.add(path.relative_to(repo_root).as_posix())
    return found


def run(repo_root: Path) -> list[str]:
    failures: list[str] = []

    workflow_path = repo_root / WORKFLOW
    if not workflow_path.exists():
        return [f"Missing workflow: {WORKFLOW.as_posix()}"]

    block = _job_block(workflow_path.read_text(encoding="utf-8"))
    if block is None:
        return [f"Workflow job '{JOB_NAME}' not found in {WORKFLOW.as_posix()}"]

    selected = set(_TEST_PATH.findall(block))
    marked = _marked_modules(repo_root)

    for missing in sorted(marked - selected):
        failures.append(f"Module carries pytest.mark.{MARKER} but is absent from CI job '{JOB_NAME}': {missing}")
    for stale in sorted(selected - marked):
        failures.append(f"CI job '{JOB_NAME}' selects a module without pytest.mark.{MARKER}: {stale}")

    if f"-m {MARKER}" not in block:
        failures.append(f"CI job '{JOB_NAME}' no longer filters on '-m {MARKER}'")
    if "--strict-markers" not in block:
        failures.append(f"CI job '{JOB_NAME}' no longer runs pytest with --strict-markers")

    minimum = _MIN_CASES.search(block)
    if minimum is None:
        failures.append(f"CI job '{JOB_NAME}' does not declare SPEC007_MIN_CASES")
    elif int(minimum.group(1)) < 1:
        failures.append(f"CI job '{JOB_NAME}' declares a non-positive SPEC007_MIN_CASES={minimum.group(1)}")
    elif marked and int(minimum.group(1)) < len(marked):
        failures.append(
            f"CI job '{JOB_NAME}' expects only {minimum.group(1)} cases "
            f"for {len(marked)} marked modules; the gate could pass while modules contribute nothing"
        )

    if '"$SPEC007_MIN_CASES"' not in block or "exit 1" not in block:
        failures.append(f"CI job '{JOB_NAME}' does not fail when fewer than SPEC007_MIN_CASES cases are collected")
    if "--collect-only" not in block:
        failures.append(f"CI job '{JOB_NAME}' does not count collected cases before running the gate")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args(argv)

    failures = run(args.repo_root.resolve())
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"OK: spec-007 {MARKER} selector is complete and gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
