"""Spec-038 / T-C03 — Replay determinism (FR-016 / SC-004).

Reruns the same seed and asserts ≥95 % of per-KPI deltas reproduce within
±2 % relative OR ±1 absolute unit.
"""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from app.services.evidence.measurement.confidence import within_tolerance
from fastapi.testclient import TestClient

REPETITIONS = 5
TOLERANCE_REL_PCT = 2.0
TOLERANCE_ABS_UNIT = 1.0


@pytest.fixture()
def client():
    reset_registry()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_repeated_replay_reproduces_within_tolerance(client):
    runs = []
    for i in range(REPETITIONS):
        r = client.post(
            "/api/v1/evidence/scenarios/bushfire/replay",
            json={"seed": "S1", "run_pair_id": f"det-{i}", "repetitions": 1},
        )
        assert r.status_code == 200
        runs.append({d["kpi_id"]: float(d["ama_assisted_value"]) for d in r.json()["kpi_deltas"]})
    ref = runs[0]
    total = 0
    within = 0
    for r in runs[1:]:
        for kpi, v in r.items():
            total += 1
            if within_tolerance(v, ref[kpi], rel_pct=TOLERANCE_REL_PCT, abs_unit=TOLERANCE_ABS_UNIT):
                within += 1
    rate = within / total
    assert rate >= 0.95, f"reproduction rate {rate:.2%} below 95% (FR-016 / SC-004)"
