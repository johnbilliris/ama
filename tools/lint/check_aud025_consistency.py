#!/usr/bin/env python3
"""Static consistency checks for AUD-025 documentation reconciliation.

This checker is intentionally scoped to specs/003-rubric-gap-closure and does
not inspect sibling feature folders such as specs/004-rubric-gap-closure.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED_FILES = [
    "spec.md",
    "plan.md",
    "tasks.md",
    "data-model.md",
    "quickstart.md",
    "contracts/openapi-addendum.yaml",
    "checklists/requirements.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run(feature_dir: Path) -> list[str]:
    feature_dir = feature_dir.resolve()
    failures: list[str] = []

    if not feature_dir.name.startswith("003-"):
        return [f"AUD-025 checker expects a 003 feature directory, got: {feature_dir.name}"]

    for rel in REQUIRED_FILES:
        path = feature_dir / rel
        if not path.exists():
            failures.append(f"Missing required file: {rel}")

    if failures:
        return failures

    spec = _read(feature_dir / "spec.md")
    plan = _read(feature_dir / "plan.md")
    tasks = _read(feature_dir / "tasks.md")
    data_model = _read(feature_dir / "data-model.md")
    quickstart = _read(feature_dir / "quickstart.md")
    contract = _read(feature_dir / "contracts/openapi-addendum.yaml")
    checklist = _read(feature_dir / "checklists/requirements.md")

    if "attempt_count" not in spec or "retry_count" not in spec:
        failures.append("spec.md must define attempt_count and retry_count semantics")
    if "up to 3 total times" not in spec:
        failures.append("spec.md FR-014 must use total-attempt wording")
    if re.search(r"retried up to\s+3\s+times", spec, flags=re.IGNORECASE):
        failures.append("spec.md must not use ambiguous 'retried up to 3 times' wording")

    if "or a region with acceptable latency" in spec:
        failures.append("spec.md must not include acceptable-latency residency escape")
    if "Foundry carve-out" not in spec:
        failures.append("spec.md must require named Foundry carve-out for non-AU model endpoints")

    if "HYP-HYP-001" in spec:
        failures.append("spec.md contains dangling HYP-HYP-001 evidence reference")
    if "status:` validated" in spec or "`status:` validated" in spec:
        failures.append("spec.md persona status must not claim validated without linked evidence")
    if "status:` unverified" not in spec and "`status:` unverified" not in spec:
        failures.append("spec.md must label unresolved persona/hypothesis evidence as unverified")

    if "two logical edges (Monitoring→Risk and Risk→Communication)" not in plan:
        failures.append("plan.md must state two logical handoff edges")

    if "3 total attempts" not in tasks or "up to 2 retries" not in tasks:
        failures.append("tasks.md must align T027/T031 to total attempts and retries")

    if "attemptCount" not in data_model or not re.search(r"maxRetries`?:\s*integer,\s*default\s*2", data_model):
        failures.append("data-model.md must define attemptCount and maxRetries default 2")
    if not re.search(
        r"retryCount`?:\s*integer,\s*retries after the initial call\s*\(0[–-]2\)",
        data_model,
    ):
        failures.append("data-model.md must define retryCount as retries-after-initial semantics")

    if "exactly 2 logical handoff edges" not in quickstart:
        failures.append("quickstart.md scenario must use two logical handoff edges")
    if "all 3 handoffs" in quickstart:
        failures.append("quickstart.md must not claim three handoffs for a two-edge chain")
    if "authorized staging environment" not in quickstart:
        failures.append("quickstart.md Phase G must require authorized staging")
    if "-u 1000" not in quickstart or ">=50,000 signals/hour" not in quickstart:
        failures.append("quickstart.md Phase G must require 1,000 users and >=50,000 signals/hour")
    if "QAC-08" not in quickstart or "Real resolved media/evidence package" not in quickstart:
        failures.append("quickstart.md QAC-08 must require real resolved media/evidence")
    if "QAC-11" not in quickstart or "Controlled breach-to-receipt evidence" not in quickstart:
        failures.append("quickstart.md QAC-11 must require breach-to-receipt evidence")

    if "Wire field convention: camelCase." not in contract:
        failures.append("contracts/openapi-addendum.yaml must declare camelCase wire field convention")
    if "attemptCount" not in contract or "maxRetries:" not in contract:
        failures.append("contracts/openapi-addendum.yaml must define attemptCount/retryCount fields")

    if "All items pass" in checklist:
        failures.append("checklists/requirements.md must not contain blanket all-pass claim")
    if "Current status" not in checklist or "Historical snapshot" not in checklist:
        failures.append("checklists/requirements.md must preserve history via dated status addendum")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--feature-dir",
        type=Path,
        default=Path("specs/003-rubric-gap-closure"),
        help="Feature directory to validate (default: specs/003-rubric-gap-closure).",
    )
    args = parser.parse_args(argv)

    failures = run(args.feature_dir)
    if failures:
        print("FAIL: AUD-025 consistency checks failed")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("PASS: AUD-025 consistency checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
