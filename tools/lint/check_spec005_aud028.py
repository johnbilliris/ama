#!/usr/bin/env python3
"""Feature-scoped static checks for spec 005 AUD-028 evidence integrity."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FEATURE_DIR = Path("specs/005-data-source-governance")
SPEC_PATH = FEATURE_DIR / "spec.md"
CHECKLIST_PATH = FEATURE_DIR / "checklists/requirements.md"
REVIEW_TASKS_PATH = FEATURE_DIR / "implementation-review-tasks.md"
HYP_PATH = FEATURE_DIR / "evidence/HYP-043.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)")
    match = pattern.search(text)
    return match.group("body") if match else ""


def _parse_checked_claims(text: str) -> list[str]:
    return [m.group(2).strip() for m in re.finditer(r"(?m)^- \[(x|X)\] (.+)$", text)]


def _parse_disposition_rows(text: str) -> dict[str, str]:
    body = _section(text, "Current Status Dispositions (2026-09-15)")
    rows: dict[str, str] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 3:
            continue
        if cols[0] in {"Claim", "---"}:
            continue
        if set(cols[0]) == {"-"}:
            continue
        rows[cols[0]] = cols[2]
    return rows


def _check_hyp_stub(path: Path, failures: list[str]) -> None:
    if not path.exists():
        failures.append(f"Missing hypothesis evidence file: {path.as_posix()}")
        return

    if path.name != "HYP-043.md":
        failures.append("HYP evidence filename must be HYP-043.md")

    text = _read(path)
    headings = [
        "## Hypothesis",
        "## Preconditions",
        "## Measurement Window",
        "## Falsification Criterion",
        "## Status",
        "## Linked",
    ]
    positions = [text.find(item) for item in headings]
    for idx, heading in enumerate(headings):
        if positions[idx] < 0:
            failures.append(f"HYP-043 evidence missing heading: {heading}")
    if all(pos >= 0 for pos in positions) and positions != sorted(positions):
        failures.append("HYP-043 required headings are out of order")

    preconditions = _section(text, "Preconditions")
    if len(re.findall(r"(?m)^- ", preconditions)) < 2:
        failures.append("HYP-043 Preconditions must contain at least two bullet items")

    falsification = _section(text, "Falsification Criterion")
    numeric_bullets = [
        line for line in falsification.splitlines() if line.strip().startswith("-") and re.search(r"\d", line)
    ]
    if not numeric_bullets:
        failures.append("HYP-043 Falsification Criterion must include a numeric threshold")

    status = _section(text, "Status").strip()
    if status != "Not tested":
        failures.append("HYP-043 Status must be exactly 'Not tested'")

    linked = _section(text, "Linked")
    if "Spec: `specs/005-data-source-governance/spec.md`" not in linked:
        failures.append("HYP-043 Linked section must include the owning spec path")


def _check_hyp_owner_uniqueness(specs_root: Path, failures: list[str]) -> None:
    owners = [path for path in specs_root.rglob("HYP-043.md") if path.parent.name == "evidence"]
    if len(owners) != 1:
        owner_list = ", ".join(path.as_posix() for path in owners) or "none"
        failures.append(f"HYP-043 must resolve to exactly one owner-scoped evidence file (found {owner_list})")


def _check_spec_claims(path: Path, failures: list[str]) -> None:
    text = _read(path)

    if "- **PER-007**" not in text or "`status:` unverified." not in text:
        failures.append("PER-007 must remain explicitly unverified")
    if "- **PER-008**" not in text or "`status:` unverified." not in text:
        failures.append("PER-008 must remain explicitly unverified")
    if "- **PER-009** [non-AU placeholder]" not in text or "`status:` placeholder." not in text:
        failures.append("PER-009 must remain placeholder with explicit status")

    asm_section = _section(text, "Assumptions")
    if "ASM-008" not in asm_section:
        failures.append("ASM-008 assumption entry is missing")
    if "consulted via the `agent` tool" in asm_section:
        failures.append("ASM-008 must not claim tool invocation as consultation evidence")
    if "do not count as human consultation or approval" not in asm_section:
        failures.append("ASM-008 must state that agent/tool invocation is not human consultation")

    if "HYP-HYP-" in text:
        failures.append("spec.md contains malformed speculative HYP path")
    if "specs/005-data-source-governance/evidence/HYP-043.md" not in text:
        failures.append("spec.md must link to specs/005-data-source-governance/evidence/HYP-043.md")


def _check_checklist(path: Path, failures: list[str]) -> None:
    text = _read(path)
    checked_claims = _parse_checked_claims(text)
    dispositions = _parse_disposition_rows(text)
    if not dispositions:
        failures.append("Checklist is missing Current Status Dispositions table")
        return

    required_claims = {
        "Feature meets measurable outcomes defined in Success Criteria",
        "Registry security and access control requirements are defined (FR-015, FR-016)",
    }
    for claim in required_claims:
        if claim not in checked_claims:
            failures.append(f"Checklist checked claim missing: {claim}")
        if claim not in dispositions:
            failures.append(f"Checklist disposition missing for checked claim: {claim}")


def _check_review_disposition(path: Path, failures: list[str]) -> None:
    text = _read(path)
    if not re.search(r"\|\s*T056\s*\|\s*\[X\]\s*\|\s*UNVERIFIED\s*\|", text):
        failures.append("implementation-review-tasks.md must retain T056 as historical [X] with UNVERIFIED status")
    if not re.search(r"\|\s*T057\s*\|\s*\[X\]\s*\|\s*UNVERIFIED\s*\|", text):
        failures.append("implementation-review-tasks.md must retain T057 as historical [X] with UNVERIFIED status")


def _check_readiness_manifest_linkage(feature_dir: Path, failures: list[str]) -> None:
    required_files = [
        feature_dir / "contracts/readiness-manifest.schema.json",
        feature_dir / "evidence/readiness-manifest.template.json",
        feature_dir / "evidence/quickstart-rehearsal-manifest.template.json",
        feature_dir / "evidence/readiness-snapshot.generated.json",
    ]
    for path in required_files:
        if not path.exists():
            failures.append(f"Missing readiness linkage artifact: {path.as_posix()}")

    if failures:
        return

    try:
        schema = json.loads((feature_dir / "contracts/readiness-manifest.schema.json").read_text(encoding="utf-8"))
        template = json.loads((feature_dir / "evidence/readiness-manifest.template.json").read_text(encoding="utf-8"))
        quickstart = json.loads(
            (feature_dir / "evidence/quickstart-rehearsal-manifest.template.json").read_text(encoding="utf-8")
        )
        snapshot = json.loads((feature_dir / "evidence/readiness-snapshot.generated.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"Readiness artifact JSON decode error: {exc}")
        return

    if schema.get("title") != "Spec005 Readiness Manifest":
        failures.append("readiness-manifest schema title mismatch")
    if template.get("status") != "UNVERIFIED":
        failures.append("readiness-manifest template default status must be UNVERIFIED")
    if quickstart.get("status") != "UNVERIFIED":
        failures.append("quickstart rehearsal template default status must be UNVERIFIED")
    if snapshot.get("schema_version") not in {"spec005-readiness-v1", "spec005-readiness-v2"}:
        failures.append("readiness snapshot schema version is missing or unexpected")


def run(feature_dir: Path = FEATURE_DIR, specs_root: Path = Path("specs")) -> list[str]:
    failures: list[str] = []
    feature_dir = feature_dir.resolve()
    specs_root = specs_root.resolve()

    paths = [
        feature_dir / "spec.md",
        feature_dir / "checklists/requirements.md",
        feature_dir / "implementation-review-tasks.md",
    ]
    for path in paths:
        if not path.exists():
            failures.append(f"Missing required file: {path.as_posix()}")
    if failures:
        return failures

    _check_hyp_stub(feature_dir / "evidence/HYP-043.md", failures)
    _check_hyp_owner_uniqueness(specs_root, failures)
    _check_spec_claims(feature_dir / "spec.md", failures)
    _check_checklist(feature_dir / "checklists/requirements.md", failures)
    _check_review_disposition(feature_dir / "implementation-review-tasks.md", failures)
    _check_readiness_manifest_linkage(feature_dir, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-dir", type=Path, default=FEATURE_DIR)
    parser.add_argument("--specs-root", type=Path, default=Path("specs"))
    args = parser.parse_args(argv)

    failures = run(feature_dir=args.feature_dir, specs_root=args.specs_root)
    if failures:
        print("spec005-aud028: FAIL")
        for item in failures:
            print(f" - {item}")
        return 1

    print("spec005-aud028: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
