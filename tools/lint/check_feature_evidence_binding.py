"""Fail-closed evidence-binding checks for spec-001 acceptance statements.

Rules enforced:
1. Any markdown file with a "## Validated Results" section must include:
   - Validation status
   - Revision
   - Acceptance evidence artifact
2. Any "Validation status: Validated" or frontmatter "status: Validated"
   must include method/cohort/denominator/results metadata and non-placeholder
   evidence text.
3. Acceptance evidence for spec-001 must point at spec-001/disaster-hub
   artefacts. Cross-feature links are allowed only as supplemental evidence.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FEATURE_ROOT = Path("specs/001-disaster-response-hub")

_PLACEHOLDER_PATTERNS = (
    "to be populated",
    "pending evidence",
    "tbd",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)")
    match = pattern.search(text)
    return match.group("body") if match else ""


def _is_cross_feature(path_value: str) -> bool:
    norm = path_value.replace("\\", "/").lower()
    if "specs/001-disaster-response-hub/" in norm:
        return False
    if "docs/disaster-response-hub/" in norm:
        return False
    return "specs/" in norm or "docs/" in norm


def _contains_placeholder(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in _PLACEHOLDER_PATTERNS)


def _check_validated_results(path: Path, violations: list[str]) -> None:
    text = _read(path)
    body = _section(text, "Validated Results")
    if not body:
        return

    status_match = re.search(r"(?im)^Validation status:\s*(.+)$", body)
    revision_match = re.search(r"(?im)^Revision:\s*(.+)$", body)
    acceptance_match = re.search(r"(?im)^Acceptance evidence artifact:\s*(.+)$", body)

    if not status_match:
        violations.append(f"{path}: Validated Results is missing 'Validation status:'")
    if not revision_match:
        violations.append(f"{path}: Validated Results is missing 'Revision:'")
    if not acceptance_match:
        violations.append(f"{path}: Validated Results is missing 'Acceptance evidence artifact:'")

    status_value = status_match.group(1).strip() if status_match else ""
    acceptance_value = acceptance_match.group(1).strip() if acceptance_match else ""
    if acceptance_value and acceptance_value.lower() != "pending":
        if _is_cross_feature(acceptance_value):
            violations.append(f"{path}: acceptance evidence points outside feature scope: {acceptance_value}")
        elif not Path(acceptance_value).exists():
            violations.append(f"{path}: acceptance evidence artifact does not exist: {acceptance_value}")

    if status_value.lower() == "validated":
        for field in ("Method", "Cohort", "Denominator", "Results"):
            if not re.search(rf"(?im)^\s*{re.escape(field)}:\s*.+$", body):
                violations.append(f"{path}: Validated status requires '{field}:' in Validated Results")


def _check_validated_frontmatter(path: Path, violations: list[str]) -> None:
    text = _read(path)
    if not re.search(r"(?im)^status:\s*Validated\s*$", text):
        return

    if not re.search(r"(?im)^revision:\s*[0-9a-f]{7,40}\s*$", text):
        violations.append(f"{path}: status Validated requires frontmatter revision SHA")

    for field in ("method", "cohort", "denominator", "results"):
        if not re.search(rf"(?im)^\s*{field}:\s*.+$", text):
            violations.append(f"{path}: status Validated requires '{field}' metadata")

    evidence = _section(text, "Evidence")
    if not evidence.strip() or _contains_placeholder(evidence):
        violations.append(f"{path}: status Validated requires populated non-placeholder Evidence section")


def run(root: Path) -> list[str]:
    violations: list[str] = []

    quickstart = root / "quickstart.md"
    if quickstart.exists():
        _check_validated_results(quickstart, violations)
    else:
        violations.append(f"{quickstart}: missing file")

    for file_path in sorted(root.rglob("*.md")):
        _check_validated_frontmatter(file_path, violations)

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate spec-001 evidence-binding metadata")
    parser.add_argument("--feature-root", type=Path, default=FEATURE_ROOT)
    args = parser.parse_args(argv)

    violations = run(args.feature_root)
    if violations:
        print("feature-evidence-binding: FAIL")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("feature-evidence-binding: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
