"""T018 — publication gate test: ratio recompute equals declared.

Citations: FR-037, RES-05, CHK061.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _make_artefact(rows_manual: int, rows_auto: int, declared_ratio: float | None = None):
    rows = []
    for i in range(rows_manual):
        rows.append({"provenance": {"tag": "manual"}})
    for i in range(rows_auto):
        rows.append({"provenance": {"tag": "automated"}})
    total = rows_manual + rows_auto
    if declared_ratio is None:
        declared_ratio = (rows_manual / total) if total else 0.0
    return {
        "artefact_id": "risk_register",
        "schema_version": "1.0.0",
        "publication_id": "00000000-0000-0000-0000-000000000100",
        "published_at_utc": "2026-05-11T00:00:00Z",
        "published_by": "test",
        "metadata": {
            "manual_row_count": rows_manual,
            "total_row_count": total,
            "manual_row_ratio": declared_ratio,
            "link_check_status": "passed",
            "last_gate_run_utc": "2026-05-11T00:00:00Z",
        },
        "rows": rows,
    }


def test_ratio_recompute_matches_declared(tmp_path: Path):
    pytest.importorskip("evidence_pack_gate")
    from evidence_pack_gate.gate import recompute_manual_row_ratio

    artefact = _make_artefact(2, 8)
    file = tmp_path / "artefact.json"
    file.write_text(json.dumps(artefact), encoding="utf-8")
    result = recompute_manual_row_ratio(file)
    assert result.manual_row_count == 2
    assert result.total_row_count == 10
    assert result.manual_row_ratio == pytest.approx(0.2)
    assert result.matches_declared is True


def test_ratio_mismatch_detected(tmp_path: Path):
    pytest.importorskip("evidence_pack_gate")
    from evidence_pack_gate.gate import recompute_manual_row_ratio

    # declare 0.5 but actual is 0.2
    artefact = _make_artefact(2, 8, declared_ratio=0.5)
    file = tmp_path / "artefact.json"
    file.write_text(json.dumps(artefact), encoding="utf-8")
    result = recompute_manual_row_ratio(file)
    assert result.matches_declared is False
