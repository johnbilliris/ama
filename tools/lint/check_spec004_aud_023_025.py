#!/usr/bin/env python3
"""Feature-scoped static checks for spec 004 AUD-023/AUD-024/AUD-025 remediations."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED_CONSTITUTION_HEADINGS = (
    "I. Primacy of Life and Harm Reduction",
    "II. National Emergency Management Principles",
    "III. Multi-Hazard, Multi-Agency Design",
    "IV. Transparency and Auditability",
    "V. Warning and Public Information",
    "VI. Evacuation Framework",
    "VII. Recovery Support",
    "VIII. Cloud Platform and Infrastructure",
    "NON-NEGOTIABLE #1 Human-in-the-loop",
    "NON-NEGOTIABLE #2 Data sovereignty (+ bounded Foundry carve-out)",
    "NON-NEGOTIABLE #3 Privacy by design",
    "NON-NEGOTIABLE #4 Interoperability",
    "NON-NEGOTIABLE #5 Graceful degradation",
)

DISPOSITION_PREFIXES = (
    "Supported with resolvable evidence",
    "Unverified",
    "Incorrect as written",
)


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


def check_all_hyp_refs_have_single_owner(specs_root: Path) -> list[str]:
    """Check that every HYP reference maps to exactly one evidence stub owner."""
    markdown_files = sorted(specs_root.rglob("*.md"))
    owners: dict[str, list[Path]] = {}
    refs: set[str] = set()

    for path in markdown_files:
        norm = path.as_posix()
        # Limit strict portfolio ownership checks to spec/evidence artefacts.
        if path.name != "spec.md" and "/evidence/" not in norm:
            continue

        for match in re.findall(r"\b(HYP-\d{3})\b", _read(path)):
            refs.add(match)

        if path.parent.name != "evidence":
            continue
        name = path.name
        if not re.fullmatch(r"HYP-\d{3}\.md", name):
            continue
        hyp_id = name[:-3]
        owners.setdefault(hyp_id, []).append(path)

    violations: list[str] = []
    for hyp_id in sorted(refs):
        owner_paths = owners.get(hyp_id, [])
        if len(owner_paths) != 1:
            owners_text = ", ".join(str(p).replace("\\", "/") for p in owner_paths) or "none"
            violations.append(f"{hyp_id} resolves to {len(owner_paths)} owners ({owners_text})")
    return violations


def _check_checklist(path: Path, failures: list[str]) -> None:
    text = _read(path)
    if re.search(r"(?i)all items pass(?:ed)?", text):
        failures.append("checklists/requirements.md contains a blanket all-pass claim")

    claims = _parse_checked_claims(text)
    dispositions = _parse_disposition_rows(text)
    if not dispositions:
        failures.append("checklists/requirements.md missing dated Current Status disposition rows")
        return

    for claim in claims:
        if claim not in dispositions:
            failures.append(f"checklists/requirements.md missing disposition row for checked claim: {claim}")
            continue
        value = dispositions[claim]
        if not value.startswith(DISPOSITION_PREFIXES):
            failures.append(f"checklists/requirements.md invalid disposition for '{claim}': {value}")

    measurable_claim = "Feature meets measurable outcomes defined in Success Criteria"
    if measurable_claim in dispositions:
        disposition = dispositions[measurable_claim]
        if not (disposition.startswith("Incorrect as written") or disposition.startswith("Unverified")):
            failures.append(
                "checklists/requirements.md measurable-outcome claim must be Incorrect as written or Unverified"
            )


def _check_plan(path: Path, failures: list[str]) -> None:
    text = _read(path)
    if "Historical Snapshot (2026-03-23)" not in text:
        failures.append("plan.md must retain a labelled historical snapshot section")
    if "not a current acceptance gate" not in text:
        failures.append("plan.md must label the historical pass table as non-current")

    for heading in REQUIRED_CONSTITUTION_HEADINGS:
        if heading not in text:
            failures.append(f"plan.md missing current constitution heading: {heading}")

    if "**Current Gate Result**: Unverified." not in text:
        failures.append("plan.md must report current gate as Unverified")


def _check_spec(path: Path, failures: list[str], hyp_id: str) -> None:
    text = _read(path)

    if "- **PER-004**" not in text or "`status:` unverified." not in text:
        failures.append("spec.md must downgrade PER-004 to unverified")
    if "- **PER-005**" not in text or "`status:` unverified." not in text:
        failures.append("spec.md must downgrade PER-005 to unverified")

    if re.search(r"\*\*PER-004\*\*:.*?`status:`\s*validated", text, flags=re.IGNORECASE):
        failures.append("spec.md PER-004 must not remain validated")
    if re.search(r"\*\*PER-005\*\*:.*?`status:`\s*validated", text, flags=re.IGNORECASE):
        failures.append("spec.md PER-005 must not remain validated")

    asm005_body = _section(text, "Assumptions")
    if "ASM-005" not in asm005_body:
        failures.append("spec.md must include ASM-005 in Assumptions")
    if "integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`)" in asm005_body:
        failures.append("spec.md ASM-005 must not self-reference spec.md as integration artefact")
    if "Human consultation evidence for this amendment is currently absent" not in asm005_body:
        failures.append("spec.md ASM-005 must state human consultation evidence is currently absent")
    if "do not count as human consultation or approval" not in asm005_body:
        failures.append("spec.md ASM-005 must state agent/tool invocation is not human consultation")

    if f"- **{hyp_id}**:" not in text:
        failures.append(f"spec.md must define {hyp_id} in Hypotheses")
    if "- **HYP-002**:" in text:
        failures.append("spec.md must not continue to use HYP-002 for this hypothesis")

    expected_stub = f"specs/004-actor-github-agents/evidence/{hyp_id}.md"
    if expected_stub not in text:
        failures.append(f"spec.md must link local owner-scoped evidence stub: {expected_stub}")
    hypotheses = _section(text, "Hypotheses")
    if "rubric-baseline.md" in hypotheses or "rubric-postfeature.md" in hypotheses:
        failures.append(
            "spec.md hypothesis measurement design must not use rubric baseline/postfeature as causal proxy"
        )


def _check_hyp_stub(path: Path, failures: list[str], hyp_id: str) -> None:
    if not path.exists():
        failures.append(f"Missing hypothesis stub: {path.as_posix()}")
        return

    if not re.fullmatch(r"HYP-\d{3}\.md", path.name):
        failures.append(f"Hypothesis stub filename must match HYP-###.md: {path.name}")

    text = _read(path)
    if f"# {hyp_id}" not in text:
        failures.append(f"{path.as_posix()} title must start with '# {hyp_id}'")

    headings = [
        "## Hypothesis",
        "## Preconditions",
        "## Measurement Window",
        "## Falsification Criterion",
        "## Status",
        "## Linked",
    ]
    positions: list[int] = []
    for heading in headings:
        pos = text.find(heading)
        if pos < 0:
            failures.append(f"{path.as_posix()} missing heading: {heading}")
        positions.append(pos)

    if all(p >= 0 for p in positions):
        if positions != sorted(positions):
            failures.append(f"{path.as_posix()} required headings are out of order")

    preconditions = _section(text, "Preconditions")
    precondition_bullets = re.findall(r"(?m)^- ", preconditions)
    if len(precondition_bullets) < 2:
        failures.append(f"{path.as_posix()} must contain at least 2 preconditions")

    falsification = _section(text, "Falsification Criterion")
    numeric_bullets = [
        line for line in falsification.splitlines() if line.strip().startswith("-") and re.search(r"\d", line)
    ]
    if not numeric_bullets:
        failures.append(f"{path.as_posix()} falsification criterion must include a numeric threshold")

    status = _section(text, "Status").strip()
    if status != "Not tested":
        failures.append(f"{path.as_posix()} status must be exactly 'Not tested'")

    linked = _section(text, "Linked")
    if "Spec: `specs/004-actor-github-agents/spec.md`" not in linked:
        failures.append(f"{path.as_posix()} Linked section must include owning spec")
    if "Owner:" not in linked:
        failures.append(f"{path.as_posix()} Linked section must include owner reference")


def _check_hyp_unique_owner(specs_root: Path, hyp_id: str, failures: list[str]) -> None:
    owners = [p for p in specs_root.rglob(f"{hyp_id}.md") if p.parent.name == "evidence" and p.name == f"{hyp_id}.md"]
    if len(owners) != 1:
        owner_list = ", ".join(p.as_posix() for p in owners) or "none"
        failures.append(f"{hyp_id} must resolve to exactly one owner-scoped evidence file (found {owner_list})")


def run(feature_dir: Path, specs_root: Path, hyp_id: str = "HYP-042") -> list[str]:
    failures: list[str] = []
    feature_dir = feature_dir.resolve()
    specs_root = specs_root.resolve()

    checklist = feature_dir / "checklists" / "requirements.md"
    plan = feature_dir / "plan.md"
    spec = feature_dir / "spec.md"
    hyp_stub = feature_dir / "evidence" / f"{hyp_id}.md"

    for path in (checklist, plan, spec):
        if not path.exists():
            failures.append(f"Missing required file: {path.as_posix()}")
    if failures:
        return failures

    _check_checklist(checklist, failures)
    _check_plan(plan, failures)
    _check_spec(spec, failures, hyp_id)
    _check_hyp_stub(hyp_stub, failures, hyp_id)
    _check_hyp_unique_owner(specs_root, hyp_id, failures)

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--feature-dir",
        type=Path,
        default=Path("specs/004-actor-github-agents"),
        help="Feature directory to validate.",
    )
    parser.add_argument(
        "--specs-root",
        type=Path,
        default=Path("specs"),
        help="Root specs directory used for ownership uniqueness checks.",
    )
    parser.add_argument(
        "--hyp-id",
        default="HYP-042",
        help="Hypothesis id to validate for owner-scoped stub checks.",
    )
    parser.add_argument(
        "--strict-portfolio",
        action="store_true",
        help="Also require every HYP reference in specs root to resolve to exactly one owner.",
    )
    args = parser.parse_args(argv)

    failures = run(args.feature_dir, args.specs_root, args.hyp_id)
    if args.strict_portfolio:
        failures.extend(check_all_hyp_refs_have_single_owner(args.specs_root))

    if failures:
        print("spec004-aud-023-025: FAIL")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("spec004-aud-023-025: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
