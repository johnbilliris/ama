"""Existing dashboards regression test (T060b, FR-017, SC-009).

Reads the pre-cutover snapshot captured by T024b
(``tests/contract/snapshots/existing_dashboard_fields.json``) and asserts no
field has been removed by MAF code paths. New fields are allowed; removals or
renames fail the test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO_ROOT / "tests" / "contract" / "snapshots" / "existing_dashboard_fields.json"


def _load_snapshot() -> dict[str, list[str]]:
    if not SNAPSHOT.exists():
        return {}
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return payload.get("fields_by_file", {})


def test_no_dashboard_field_removed() -> None:
    snapshot = _load_snapshot()
    if not snapshot:
        pytest.skip(
            "Snapshot missing — run apps/agents/maf_runtime/equivalence/dashboard_snapshot.py first."
        )
    # Re-collect current fields.
    from apps.agents.maf_runtime.equivalence.dashboard_snapshot import (
        DASHBOARDS_DIR,
        collect_fields,
    )

    current = collect_fields([DASHBOARDS_DIR])
    deltas: list[str] = []
    for file_path, fields in snapshot.items():
        cur = set(current.get(file_path, []))
        missing = sorted(set(fields) - cur)
        if missing:
            deltas.append(f"{file_path}: removed {missing}")
    assert not deltas, "FR-017 / SC-009 regression:\n  " + "\n  ".join(deltas)
