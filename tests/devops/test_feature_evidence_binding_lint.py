from __future__ import annotations

from pathlib import Path

from tools.lint.check_feature_evidence_binding import run


def _write_quickstart(root: Path, body: str) -> None:
    feature = root / "specs/001-disaster-response-hub"
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "quickstart.md").write_text(body, encoding="utf-8")


def test_evidence_binding_passes_with_pending_metadata(tmp_path: Path) -> None:
    _write_quickstart(
        tmp_path,
        "\n".join(
            [
                "## Validated Results",
                "Validation status: Unverified",
                "Revision: Pending",
                "Acceptance evidence artifact: Pending",
            ]
        ),
    )

    violations = run(tmp_path / "specs/001-disaster-response-hub")
    assert violations == []


def test_evidence_binding_fails_without_revision(tmp_path: Path) -> None:
    _write_quickstart(
        tmp_path,
        "\n".join(
            [
                "## Validated Results",
                "Validation status: Unverified",
                "Acceptance evidence artifact: Pending",
            ]
        ),
    )

    violations = run(tmp_path / "specs/001-disaster-response-hub")
    assert any("Revision" in v for v in violations)


def test_evidence_binding_fails_cross_feature_acceptance_link(tmp_path: Path) -> None:
    _write_quickstart(
        tmp_path,
        "\n".join(
            [
                "## Validated Results",
                "Validation status: Unverified",
                "Revision: Pending",
                "Acceptance evidence artifact: specs/003-rubric-gap-closure/evidence/rehearsal-results.md",
            ]
        ),
    )

    violations = run(tmp_path / "specs/001-disaster-response-hub")
    assert any("outside feature scope" in v for v in violations)


def test_evidence_binding_fails_validated_placeholder_evidence(tmp_path: Path) -> None:
    feature = tmp_path / "specs/001-disaster-response-hub"
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "quickstart.md").write_text(
        "\n".join(
            [
                "## Validated Results",
                "Validation status: Unverified",
                "Revision: Pending",
                "Acceptance evidence artifact: Pending",
            ]
        ),
        encoding="utf-8",
    )
    (feature / "evidence.md").write_text(
        "\n".join(
            [
                "---",
                "status: Validated",
                "revision: deadbeef",
                "method: rehearsal",
                "cohort: au-v1",
                "denominator: 30",
                "results: pass",
                "---",
                "## Evidence",
                "> To be populated",
            ]
        ),
        encoding="utf-8",
    )

    violations = run(feature)
    assert any("non-placeholder Evidence" in v for v in violations)
