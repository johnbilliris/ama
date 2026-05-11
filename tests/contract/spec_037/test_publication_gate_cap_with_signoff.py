"""T020 — publication gate test: cap > 0.5 with complete signoff passes.

Citations: FR-038, SC-011, CHK063.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_over_cap_with_signoff_passes_gate(tmp_path: Path):
    pytest.importorskip("evidence_pack_gate")
    from evidence_pack_gate.gate import enforce_cap

    artefact = {
        "metadata": {
            "manual_row_count": 8,
            "total_row_count": 10,
            "manual_row_ratio": 0.8,
            "link_check_status": "passed",
            "last_gate_run_utc": "2026-05-11T00:00:00Z",
            "auditor_signoff": {
                "name": "Jane Doe",
                "role": "Compliance Auditor",
                "signoff_date_utc": "2026-05-11T00:00:00Z",
                "basis": "ISO/IEC 23894 §7.4 risk evaluation under uncertainty",
            },
        }
    }
    file = tmp_path / "artefact.json"
    file.write_text(json.dumps(artefact), encoding="utf-8")
    result = enforce_cap(file)
    assert result.passed is True
