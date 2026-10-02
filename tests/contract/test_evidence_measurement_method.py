# Contract tests for the canonical Measurement Method.

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
    with TestClient(app) as test_client:
        yield test_client


def test_measurement_method_json_has_one_canonical_definition_source(client):
    response = client.get("/api/v1/evidence/measurement-method")
    assert response.status_code == 200
    body = response.json()
    assert len(body["definitions"]) == 5
    definitions = {definition["kpi_id"]: definition for definition in body["definitions"]}
    assert set(definitions) == {
        "lives_saved_lagging",
        "response_time_p1",
        "evac_lead_lagging",
        "logistics_efficiency",
        "econ_loss_lagging",
    }
    assert "annual_operational_tempo_scale" in definitions["lives_saved_lagging"]["formula"]
    assert definitions["response_time_p1"]["start_signal"] == "call_received_at"
    assert definitions["response_time_p1"]["end_signal"] == "controlled_at"
    assert definitions["evac_lead_lagging"]["target_value"] == "24"
    assert "baseline_efficiency_pct" in definitions["logistics_efficiency"]["formula"]
    assert "baseline.modelled_economic_loss_aud" in definitions["econ_loss_lagging"]["formula"]
    for definition in definitions.values():
        assert definition["formula_version"]
        assert definition["unit"]
        assert definition["calibration_reference"]
        assert definition["prototype_disclaimer"]
        assert definition["confidence_band_rule"]["min_resamples"] >= 1000


def test_measurement_method_markdown_matches_json_definitions(client):
    response = client.get("/api/v1/evidence/measurement-method?format=markdown")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    body = response.text
    assert "Measurement Method" in body
    assert "annual_operational_tempo_scale" in body
    assert "call_received_at" in body and "controlled_at" in body
    assert "Formula version" in body
    assert "Calibration reference" in body
    assert "Prototype disclaimer" in body
    assert "Advisory only" in body
