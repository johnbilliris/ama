"""Spec-038 / T-B01 — Measurement Method contract test."""

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


def test_measurement_method_json(client):
    r = client.get("/api/v1/evidence/measurement-method")
    assert r.status_code == 200
    body = r.json()
    assert len(body["definitions"]) == 5
    sc_ids = {d["capstone_sc_id"] for d in body["definitions"]}
    assert sc_ids == {
        "SC-CAP-015-001",
        "SC-CAP-015-002",
        "SC-CAP-015-003",
        "SC-CAP-015-004",
        "SC-CAP-015-005",
    }
    for d in body["definitions"]:
        for k in (
            "plain_language_definition",
            "start_signal",
            "end_signal",
            "missing_timestamp_rule",
            "calibration_method",
            "confidence_band_rule",
        ):
            assert k in d


def test_measurement_method_markdown(client):
    r = client.get("/api/v1/evidence/measurement-method?format=markdown")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    body = r.text
    assert "Measurement Method" in body
    assert "Advisory only" in body
