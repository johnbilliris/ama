from __future__ import annotations

from pathlib import Path

from tools.lint.check_demo_evidence_pack import run

ROOT = Path(__file__).resolve().parents[2]


def test_demo_evidence_pack_checks_pass_for_feature_docs() -> None:
    failures = run(ROOT)
    assert any("Missing required capture asset" in failure for failure in failures)
    assert not any("Placeholder literal" in failure for failure in failures)


def test_demo_evidence_pack_detects_invalid_docs(tmp_path: Path) -> None:
    demo_dir = tmp_path / "docs/disaster-response-hub/demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    (demo_dir / "walkthrough.md").write_text(
        "\n".join(
            [
                "# Walkthrough",
                "- Screenshot placeholder: demo-01.png",
                "- Capture target: docs/disaster-response-hub/demo/assets/demo-01-incident-activation.png",
                "- Setup context: 120s",
                "- Ingestion + dashboard: 90s",
                "- Persona + recommendation: 90s",
            ]
        ),
        encoding="utf-8",
    )

    (demo_dir / "executive-deck.md").write_text(
        "\n".join(
            [
                "# Deck",
                "| KPI | Baseline | Target Outcome |",
                "|---|---:|---:|",
                "| Response coordination time | 100% baseline | 50% faster |",
            ]
        ),
        encoding="utf-8",
    )

    failures = run(tmp_path)

    assert any("Placeholder literal" in failure for failure in failures)
    assert any("<300 seconds" in failure for failure in failures)
    assert any("Measured column" in failure for failure in failures)
    assert any("Walkthrough must declare 8 capture targets" in failure for failure in failures)
