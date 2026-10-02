from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_ci_wires_feature_evidence_binding_and_p1_gate() -> None:
    text = _read(".github/workflows/ci.yml")
    assert "feature-evidence-binding-lint" in text
    assert "python tools/lint/check_feature_evidence_binding.py" in text
    assert "p1-training-release-gate" in text
    assert "python scripts/p1_release_training_gate.py" in text


def test_cd_wires_p1_gate_before_deploy() -> None:
    text = _read(".github/workflows/cd.yml")
    assert "Enforce P1 training release gate" in text
    assert "python scripts/p1_release_training_gate.py" in text


def test_dr_drill_includes_rpo_and_residency_inventory_steps() -> None:
    text = _read(".github/workflows/dr-drill.yml")
    assert "Write pre-failover sentinel records" in text
    assert "Validate sentinel recovery and RPO" in text
    assert "Probe real user workflow after failover" in text
    assert "Build residency inventory and fail non-AU resources" in text
    assert "scripts/dr_drill_residency_inventory.py" in text
