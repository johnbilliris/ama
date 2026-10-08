from __future__ import annotations

from pathlib import Path

from tools.lint.check_aud025_consistency import run

ROOT = Path(__file__).resolve().parents[2]


def test_aud025_consistency_passes_for_feature_003() -> None:
    failures = run(ROOT / "specs/003-rubric-gap-closure")
    assert failures == []


def test_checker_scopes_to_003_and_ignores_004_content(tmp_path: Path) -> None:
    feature_003 = tmp_path / "specs/003-rubric-gap-closure"
    feature_004 = tmp_path / "specs/004-rubric-gap-closure"
    (feature_003 / "contracts").mkdir(parents=True, exist_ok=True)
    (feature_003 / "checklists").mkdir(parents=True, exist_ok=True)
    feature_004.mkdir(parents=True, exist_ok=True)

    (feature_003 / "spec.md").write_text(
        "\n".join(
            [
                "Runtime uses attempt_count and retry_count.",
                "Delivery is attempted up to 3 total times.",
                "Non-AU model endpoints require Foundry carve-out approvals.",
                "status:` unverified",
            ]
        ),
        encoding="utf-8",
    )
    (feature_003 / "plan.md").write_text(
        "two logical edges (Monitoring→Risk and Risk→Communication)",
        encoding="utf-8",
    )
    (feature_003 / "tasks.md").write_text(
        "T027 uses 3 total attempts and up to 2 retries.",
        encoding="utf-8",
    )
    (feature_003 / "data-model.md").write_text(
        "attemptCount and maxRetries: integer, default 2 and retryCount`: integer, retries after the initial call (0–2)",  # noqa: E501
        encoding="utf-8",
    )
    (feature_003 / "quickstart.md").write_text(
        "\n".join(
            [
                "exactly 2 logical handoff edges",
                "authorized staging environment",
                "locust --headless -u 1000",
                ">=50,000 signals/hour",
                "QAC-08 Real resolved media/evidence package",
                "QAC-11 Controlled breach-to-receipt evidence",
            ]
        ),
        encoding="utf-8",
    )
    (feature_003 / "contracts/openapi-addendum.yaml").write_text(
        "Wire field convention: camelCase. attemptCount retryCount maxRetries:",
        encoding="utf-8",
    )
    (feature_003 / "checklists/requirements.md").write_text(
        "Historical snapshot\nCurrent status",
        encoding="utf-8",
    )

    (feature_004 / "spec.md").write_text(
        "all 3 handoffs and HYP-HYP-001 and acceptable latency",
        encoding="utf-8",
    )

    failures = run(feature_003)
    assert failures == []
