"""Spec-038 / T-C02 — All 7 scenarios × 5 capstone KPIs (SC-003)."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from app.services.evidence.simulation.scenarios import SCENARIOS
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_replay_covers_5_capstone_kpis(client, scenario):
    r = client.post(
        f"/api/v1/evidence/scenarios/{scenario}/replay",
        json={"seed": "S1", "run_pair_id": f"int-{scenario}", "repetitions": 2},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["kpi_deltas"]) == 5
    expected_kpis = {
        "lives_saved_lagging",
        "response_time_p1",
        "evac_lead_lagging",
        "logistics_efficiency",
        "econ_loss_lagging",
    }
    assert {d["kpi_id"] for d in body["kpi_deltas"]} == expected_kpis
