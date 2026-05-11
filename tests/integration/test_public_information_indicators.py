"""Spec-038 / T-A11 — Public Information indicators (US7)."""

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


def test_public_information_indicators_present(client):
    r = client.get("/api/v1/evidence/kpi-ladder")
    assert r.status_code == 200
    flat = []
    for g in r.json()["groups"]:
        flat.extend(g["leading"])
        flat.extend(g["lagging"])
    pi_rows = [i for i in flat if i["aiims_function"] == "PublicInformation"]
    assert len(pi_rows) >= 3, "expected reach + behavioural-impact + multilingual indicators"
    kpi_ids = {i["kpi_id"] for i in pi_rows}
    assert {
        "public_info_alert_reach",
        "public_info_behavioural_impact",
        "public_info_multilingual_coverage",
    } <= kpi_ids
    # FR-002 nine attributes present
    for ind in pi_rows:
        for attr in (
            "formula",
            "unit",
            "owner_role",
            "refresh_cadence",
            "target_value",
            "alert_threshold",
            "baseline_source",
            "provenance",
            "confidence_band_rule",
        ):
            assert attr in ind
