from __future__ import annotations

from pathlib import Path

from tools.lint.check_spec004_aud_023_025 import (
    check_all_hyp_refs_have_single_owner,
    run,
)

ROOT = Path(__file__).resolve().parents[2]


def _write_minimal_valid_feature(root: Path, hyp_id: str = "HYP-042") -> tuple[Path, Path]:
    feature = root / "specs/004-actor-github-agents"
    (feature / "checklists").mkdir(parents=True, exist_ok=True)
    (feature / "evidence").mkdir(parents=True, exist_ok=True)

    (feature / "checklists/requirements.md").write_text(
        "\n".join(
            [
                "## Content Quality",
                "- [x] No implementation details (languages, frameworks, APIs)",
                "## Feature Readiness",
                "- [x] Feature meets measurable outcomes defined in Success Criteria",
                "## Current Status Dispositions (2026-09-15)",
                "| Claim | Historical state | Current disposition |",
                "| --- | --- | --- |",
                "| No implementation details (languages, frameworks, APIs) | [x] | Incorrect as written - delivery format is implementation-specific. |",  # noqa: E501
                "| Feature meets measurable outcomes defined in Success Criteria | [x] | Unverified - no measured run evidence. |",  # noqa: E501
            ]
        ),
        encoding="utf-8",
    )

    (feature / "plan.md").write_text(
        "\n".join(
            [
                "### Historical Snapshot (2026-03-23)",
                "This is not a current acceptance gate.",
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
                "**Current Gate Result**: Unverified.",
            ]
        ),
        encoding="utf-8",
    )

    (feature / "spec.md").write_text(
        "\n".join(
            [
                "## Assumptions",
                "- **ASM-005** [DECISION]: deliverables integrate with `.github/agents/AGENTS.md`; Human consultation evidence for this amendment is currently absent; agent/tool invocation records do not count as human consultation or approval.",  # noqa: E501
                "## Personas",
                "- **PER-004**: cross-ref. `status:` unverified. `preconditions:` persona-validation gate pending (`validated_by` must include SME/practitioner + date + evidence link + authority_scope unilateral/countersign).",  # noqa: E501
                "- **PER-005**: cross-ref. `status:` unverified. `preconditions:` persona-validation gate pending (`validated_by` must include SME/practitioner + date + evidence link + authority_scope unilateral/countersign).",  # noqa: E501
                "## Hypotheses",
                f"- **{hyp_id}**: hypothesis text. **Measurement design**: compare consultation-log entries against merged change history for this spec (change-link parity + required fields), not portfolio structural rubric scores. **Evidence stub**: `specs/004-actor-github-agents/evidence/{hyp_id}.md`.",  # noqa: E501
            ]
        ),
        encoding="utf-8",
    )

    (feature / f"evidence/{hyp_id}.md").write_text(
        "\n".join(
            [
                f"# {hyp_id} - title",
                "",
                "## Hypothesis",
                "Text.",
                "",
                "## Preconditions",
                "- condition 1",
                "- condition 2",
                "",
                "## Measurement Window",
                "Monthly.",
                "",
                "## Falsification Criterion",
                "- threshold < 90%.",
                "",
                "## Status",
                "Not tested",
                "",
                "## Linked",
                "- Spec: `specs/004-actor-github-agents/spec.md`",
                "- Owner: `specs/004-actor-github-agents/spec.md` ASM-005",
            ]
        ),
        encoding="utf-8",
    )

    return feature, root / "specs"


def test_spec004_aud_023_025_passes_for_repository_feature() -> None:
    failures = run(ROOT / "specs/004-actor-github-agents", ROOT / "specs")
    assert failures == []


def test_hyp_reference_collision_fixture_fails(tmp_path: Path) -> None:
    tmp = tmp_path / "collision"
    (tmp / "specs/001-a/evidence").mkdir(parents=True, exist_ok=True)
    (tmp / "specs/004-b/evidence").mkdir(parents=True, exist_ok=True)
    (tmp / "specs/001-a/spec.md").write_text("Reference HYP-042", encoding="utf-8")
    (tmp / "specs/001-a/evidence/HYP-042.md").write_text("# HYP-042", encoding="utf-8")
    (tmp / "specs/004-b/evidence/HYP-042.md").write_text("# HYP-042", encoding="utf-8")

    failures = check_all_hyp_refs_have_single_owner(tmp / "specs")
    assert any("HYP-042 resolves to 2 owners" in item for item in failures)


def test_validated_persona_claim_fails_without_downgrade(tmp_path: Path) -> None:
    feature, specs_root = _write_minimal_valid_feature(tmp_path)
    spec = feature / "spec.md"
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("`status:` unverified.", "`status:` validated.", 1),
        encoding="utf-8",
    )

    failures = run(feature, specs_root)
    assert any("PER-004" in item for item in failures)
