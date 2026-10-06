from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.p1_release_training_gate import _resolve_git_range, run_gate


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _make_git_history(root: Path) -> tuple[str, str]:
    _git(root, "init")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    (root / "README.md").write_text("initial", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "initial")
    base_sha = _git(root, "rev-parse", "HEAD")
    (root / "README.md").write_text("updated", encoding="utf-8")
    _git(root, "commit", "-am", "update")
    return base_sha, _git(root, "rev-parse", "HEAD")


def test_git_range_is_inferred_from_local_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_sha, head_sha = _make_git_history(tmp_path)
    monkeypatch.chdir(tmp_path)
    for name in ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "GITHUB_SHA", "GITHUB_REF_NAME"):
        monkeypatch.delenv(name, raising=False)

    assert _resolve_git_range() == (base_sha, head_sha)


def test_git_range_uses_push_event_shas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base_sha, head_sha = _make_git_history(tmp_path)
    monkeypatch.chdir(tmp_path)
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"before": base_sha}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_SHA", head_sha)
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

    assert _resolve_git_range() == (base_sha, head_sha)


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
        waiver_path=None,
    )

    assert passed is False
    assert any("unclassified changed files" in err for err in summary["errors"])


def test_p1_gate_ignores_root_coverage_report_as_generated_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory = _write_inventory(tmp_path)
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["coverage.xml"],
        waiver_path=None,
    )

    assert passed is True
    assert summary["generated_artifact_files"] == ["coverage.xml"]
    assert summary["unclassified_files"] == []


def test_p1_gate_does_not_ignore_nested_coverage_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory = _write_inventory(tmp_path)
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["reports/coverage.xml"],
        waiver_path=None,
    )

    assert passed is False
    assert summary["generated_artifact_files"] == []
    assert summary["unclassified_files"] == ["reports/coverage.xml"]


def test_p1_gate_fails_stale_review_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path, last_reviewed="2026-09-01", signed_at="2026-09-01")
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["apps/api/app/services/dashboard_service.py"],
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
                "not_p1_paths:",
                "  - README.md",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["README.md"],
        waiver_path=waiver,
    )

    assert passed is True
    assert summary["waiver_valid"] is True
    assert summary["not_p1_classified_files"] == ["README.md"]


def test_p1_gate_rejects_unlisted_path_in_not_p1_waiver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inventory = _write_inventory(tmp_path)
    waiver = tmp_path / "waiver.yaml"
    waiver.write_text(
        "\n".join(
            [
                "type: not-p1",
                "owner: incident-commander",
                "reason: scoped non-P1 documentation",
                "expires_on: 2026-09-20",
                "not_p1_paths:",
                "  - README.md",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    passed, summary = run_gate(
        inventory_path=inventory,
        release_date=dt.date(2026, 9, 15),
        changed_files=["README.md", "docs/other.md"],
        waiver_path=waiver,
    )

    assert passed is False
    assert any("docs/other.md" in err for err in summary["errors"])


def test_p1_gate_rejects_stale_or_wildcard_not_p1_classifications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inventory = _write_inventory(tmp_path)
    waiver = tmp_path / "waiver.yaml"
    waiver.write_text(
        "\n".join(
            [
                "type: not-p1",
                "owner: incident-commander",
                "reason: scoped non-P1 documentation",
                "expires_on: 2026-09-20",
                "not_p1_paths:",
                "  - docs/**",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="exact repository-relative paths"):
        run_gate(
            inventory_path=inventory,
            release_date=dt.date(2026, 9, 15),
            changed_files=["README.md"],
            waiver_path=waiver,
        )


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
        waiver_path=waiver,
    )

    assert passed is False
    assert summary["waiver_valid"] is False
