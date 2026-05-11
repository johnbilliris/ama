"""Spec-038 / T-C01 — Replay contract test."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    from app.services.evidence.kpi_ladder import router as kpi_router

    kpi_router._SEEDED = False
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_replay_returns_five_kpi_deltas(client):
    r = client.post(
        "/api/v1/evidence/scenarios/bushfire/replay",
        json={"seed": "S1", "run_pair_id": "qs-1", "repetitions": 3},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["kpi_deltas"]) == 5
    assert body["scenario_id"] == "bushfire"
    assert body["seed"] == "S1"
    assert body["advisory_only"] is True
    # Determinism check populated for repetitions ≥ 2
    assert body["determinism"] is not None
    assert body["determinism"]["repetition_count"] >= 1


def test_replay_unknown_scenario_404(client):
    r = client.post(
        "/api/v1/evidence/scenarios/unknown/replay",
        json={"seed": "X", "run_pair_id": "x"},
    )
    # Pydantic literal rejection → 422 from FastAPI.
    assert r.status_code in (404, 422)
