#!/usr/bin/env python3
"""Validate feature-003 demo docs for evidence-pack quality gates (AUD-022)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
TIMING_RE = re.compile(r"^-\s+[^:\n]+:\s*(\d+)s\s*$", re.MULTILINE)
CENTERED_CAPTURE_TARGET_RE = re.compile(r"^\s*-\s+Capture target:\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_LITERALS = (
    "Screenshot placeholder:",
    "TODO screenshot",
    "placeholder image",
    "pending capture",
)

REQUIRED_CAPTURE_FILES: tuple[str, ...] = (
    "docs/disaster-response-hub/demo/assets/demo-01-incident-activation.png",
    "docs/disaster-response-hub/demo/assets/demo-02-signal-ingestion.png",
    "docs/disaster-response-hub/demo/assets/demo-03-dashboard.png",
    "docs/disaster-response-hub/demo/assets/demo-04-persona-workspace.png",
    "docs/disaster-response-hub/demo/assets/demo-05-recommendation-review.png",
    "docs/disaster-response-hub/demo/assets/demo-06-alert-drafting.png",
    "docs/disaster-response-hub/demo/assets/demo-07-alert-publish.png",
    "docs/disaster-response-hub/demo/assets/demo-08-replay.png",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_kpi_table(deck_text: str) -> list[list[str]]:
    lines = deck_text.splitlines()
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        if line.startswith("| KPI "):
            in_table = True
        if in_table:
            if not line.startswith("|"):
                break
            table_lines.append(line)
    rows: list[list[str]] = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and set(cells[0]) == {"-"}:
            continue
        rows.append(cells)
    return rows


def _extract_capture_targets(walkthrough_text: str) -> list[str]:
    return [
        match.group(1).strip().replace("\\", "/") for match in CENTERED_CAPTURE_TARGET_RE.finditer(walkthrough_text)
    ]


def run(root: Path) -> list[str]:
    failures: list[str] = []

    walkthrough = root / "docs/disaster-response-hub/demo/walkthrough.md"
    deck = root / "docs/disaster-response-hub/demo/executive-deck.md"

    if not walkthrough.exists():
        failures.append("Missing walkthrough.md")
        return failures
    if not deck.exists():
        failures.append("Missing executive-deck.md")
        return failures

    walkthrough_text = _read(walkthrough)
    deck_text = _read(deck)

    for literal in PLACEHOLDER_LITERALS:
        if literal in walkthrough_text or literal in deck_text:
            failures.append(f"Placeholder literal still present: {literal}")

    targets = _extract_capture_targets(walkthrough_text)
    if len(targets) != 8:
        failures.append(f"Walkthrough must declare 8 capture targets, found {len(targets)}")
    expected = set(REQUIRED_CAPTURE_FILES)
    actual = set(targets)
    if actual != expected:
        missing_targets = sorted(expected - actual)
        extra_targets = sorted(actual - expected)
        if missing_targets:
            failures.append("Missing required capture targets: " + ", ".join(missing_targets))
        if extra_targets:
            failures.append("Unexpected capture targets: " + ", ".join(extra_targets))

    for target in REQUIRED_CAPTURE_FILES:
        if not (root / target).exists():
            failures.append(f"Missing required capture asset: {target}")

    for doc_path, text in ((walkthrough, walkthrough_text), (deck, deck_text)):
        for match in IMAGE_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith("http://") or target.startswith("https://"):
                continue
            resolved = (doc_path.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"Unresolved image reference in {doc_path.name}: {target}")

    durations = [int(value) for value in TIMING_RE.findall(walkthrough_text)]
    if not durations:
        failures.append("No demo timing entries found in walkthrough.md")
    else:
        total = sum(durations)
        if total >= 300:
            failures.append(f"Demo timing must be <300 seconds, found {total}")

    rows = _extract_kpi_table(deck_text)
    if len(rows) < 2:
        failures.append("KPI table missing or empty in executive-deck.md")
        return failures

    header = rows[0]
    if "Measured" not in header:
        failures.append("KPI table must include a Measured column")
        return failures

    target_idx = header.index("Target Outcome") if "Target Outcome" in header else -1
    measured_idx = header.index("Measured")
    if target_idx < 0:
        failures.append("KPI table must include Target Outcome column")
        return failures

    for row in rows[2:]:
        if max(target_idx, measured_idx) >= len(row):
            failures.append("KPI data row has missing columns")
            continue
        target = row[target_idx].strip()
        measured = row[measured_idx].strip()
        if not measured:
            failures.append("Measured value cannot be blank")
            continue
        if measured.lower() == "not measured":
            continue
        if "run:" not in measured.lower() and "http" not in measured.lower() and "artifact" not in measured.lower():
            failures.append("Measured values must be 'Not measured' or include linked run evidence")
            continue
        if measured == target:
            failures.append("Measured value must not copy target outcome")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root containing docs/disaster-response-hub/demo.",
    )
    args = parser.parse_args(argv)

    failures = run(args.root.resolve())
    if failures:
        print("FAIL: demo evidence-pack checks failed")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS: demo evidence-pack checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
