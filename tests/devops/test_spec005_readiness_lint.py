from __future__ import annotations

import json
from pathlib import Path

from tools.lint.check_spec005_readiness import (
    SCHEMA_VERSION,
    _snapshot_hashes,
    _tool_source_hash,
    replay_snapshot,
    validate_snapshot,
)


def _write_valid_snapshot(path: Path) -> None:
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "generator": {
            "tool": "tools/lint/check_spec005_readiness.py",
            "version": "2026-09-16",
            "source_sha256": _tool_source_hash(),
        },
        "revision": "abcdef1234567890",
        "generated_at": "2026-09-16T00:00:00+00:00",
        "tenant_scope": {"tenant_id": "live", "agency_id": "nsw-ses"},
        "sources": [],
        "assessments": [],
        "assignments": [],
        "chains": [],
        "gaps": {"by_source": {}, "total": 0},
        "audit": [],
        "readiness": {
            "catalogue_source": "packages/domain/src/domain/seed/data_sources_australia.json",
            "required_source_ids": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
            "covered_source_ids": ["a", "b", "c", "d", "e", "f", "g", "h", "i"],
            "source_coverage_ratio": 0.9,
            "unresolved_gap_total": 0,
            "human_protocol": {
                "roles": {
                    "governance_lead": "required",
                    "qa_observer": "required",
                    "sme_panel": "required",
                    "ux_researcher": "required",
                },
                "start_event": "manual_start",
                "end_event": "manual_end",
                "tested_user_count": 10,
                "successful_user_count": 9,
                "workflow_seconds": 1800,
                "gap_identification_seconds": 120,
                "approval_decision": "PASS",
                "deactivated_history_considered": True,
                "notes": "recorded",
            },
        },
        "replay_validation": {
            "audit_entries": [],
            "replayed_state": {"sources": [], "assessments": [], "assignments": [], "chains": []},
            "unsupported_events": [],
            "exact_diff": {},
        },
    }
    hashes = _snapshot_hashes(snapshot)
    hashes["snapshot"] = "placeholder"
    snapshot["hashes"] = hashes
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def test_validate_snapshot_passes_at_exact_boundaries(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    _write_valid_snapshot(snapshot)
    result = validate_snapshot(snapshot)
    assert result.ok
    assert result.metrics["source_coverage_ratio"] == 0.9


def test_validate_snapshot_fails_with_generator_hash_mismatch(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    _write_valid_snapshot(snapshot)
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    payload["generator"]["source_sha256"] = "0" * 64
    payload["hashes"] = _snapshot_hashes(payload)
    snapshot.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = validate_snapshot(snapshot)
    assert not result.ok
    assert any("generator hash" in item for item in result.errors)


def test_replay_snapshot_reports_exact_diff(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    _write_valid_snapshot(snapshot)
    payload = json.loads(snapshot.read_text(encoding="utf-8"))
    payload["sources"] = [{"data_source_id": "ds-1"}]
    payload["hashes"] = _snapshot_hashes(payload)
    snapshot.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    replay = replay_snapshot(snapshot)
    assert "sources" in replay["exact_diff"]
