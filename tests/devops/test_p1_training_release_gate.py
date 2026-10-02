from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
import yaml

from scripts.p1_release_training_gate import run_gate


def _write_inventory(root: Path, *, last_reviewed: str = "2026-09-15", signed_at: str = "2026-09-15") -> Path:
    (root / "docs/disaster-response-hub").mkdir(parents=True, exist_ok=True)
    (root / "apps/api/app/services").mkdir(parents=True, exist_ok=True)
    (root / "docs/disaster-response-hub/operator-runbooks.md").write_text("runbook", encoding="utf-8")
    (root / "docs/disaster-response-hub/evaluation").mkdir(parents=True, exist_ok=True)
    (root / "docs/disaster-response-hub/evaluation/baseline-metrics.md").write_text("baseline", encoding="utf-8")

    doc = {
        "version": 1,
        "feature_id": "001-disaster-response-hub",
        "last_reviewed": "2026-09-15",
        "flows": [
            {
                "flow_id": "p1-shared-operating-picture",
                "source_paths": ["apps/api/app/services/dashboard_service.py"],
                "training_pack": {
                    "path": str(root / "docs/disaster-response-hub/operator-runbooks.md"),
                    "version": "v1",
                    "locale": ["en-AU"],
                },
                "operator_notes": {
                    "path": str(root / "docs/disaster-response-hub/evaluation/baseline-metrics.md"),
                    "version": "v1",
                    "locale": ["en-AU"],
                },
                "owner": "product-owner-ba",
                "last_reviewed": last_reviewed,
                "signed_by": "training-lead",
                "signed_at": signed_at,
            }
        ],
    }
    inventory = root / "docs/disaster-response-hub/p1-flow-inventory.yaml"
    inventory.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return inventory


def test_p1_gate_passes_with_fresh_signed_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path)
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["apps/api/app/services/dashboard_service.py"],
        base_sha=None,
        head_sha=None,
        waiver_path=None,
    )

    assert passed is True
    assert summary["errors"] == []
    assert "p1-shared-operating-picture" in summary["matched_flows"]


def test_p1_gate_fails_unclassified_change_without_waiver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path)
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["README.md"],
        base_sha=None,
        head_sha=None,
        waiver_path=None,
    )

    assert passed is False
    assert any("unclassified changed files" in err for err in summary["errors"])


def test_p1_gate_fails_stale_review_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path, last_reviewed="2026-09-01", signed_at="2026-09-01")
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["apps/api/app/services/dashboard_service.py"],
        base_sha=None,
        head_sha=None,
        waiver_path=None,
    )

    assert passed is False
    assert any("stale" in err for err in summary["errors"])


def test_p1_gate_honors_not_p1_waiver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path)
    waiver = tmp_path / "waiver.yaml"
    waiver.write_text(
        "\n".join(
            [
                "type: not-p1",
                "owner: incident-commander",
                "reason: docs-only release",
                "expires_on: 2026-09-20",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["README.md"],
        base_sha=None,
        head_sha=None,
        waiver_path=waiver,
    )

    assert passed is True
    assert summary["waiver_valid"] is True


def test_p1_gate_rejects_expired_waiver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path)
    waiver = tmp_path / "waiver.yaml"
    waiver.write_text(
        "\n".join(
            [
                "type: emergency",
                "owner: incident-commander",
                "reason: active incident recovery",
                "expires_on: 2026-09-10",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["README.md"],
        base_sha=None,
        head_sha=None,
        waiver_path=waiver,
    )

    assert passed is False
    assert summary["waiver_valid"] is False
