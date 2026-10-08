# KPI ladder contract tests for filtering and meaningful definitions.

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


def test_kpi_ladder_returns_five_complete_groups(client):
    response = client.get("/api/v1/evidence/kpi-ladder")
    assert response.status_code == 200, response.text
    groups = response.json()["groups"]
    assert len(groups) == 5
    assert {group["capstone_sc_id"] for group in groups} == {
        "SC-CAP-015-001",
        "SC-CAP-015-002",
        "SC-CAP-015-003",
        "SC-CAP-015-004",
        "SC-CAP-015-005",
    }
    indicators = [indicator for group in groups for indicator in group["leading"] + group["lagging"]]
    assert {indicator["aiims_function"] for indicator in indicators} == {
        "Control",
        "Intelligence",
        "Planning",
        "Operations",
        "Logistics",
        "PublicInformation",
    }
    assert {indicator["incident_level"] for indicator in indicators} == {1, 2, 3}
    for group in groups:
        assert group["leading"] and group["lagging"]
        for indicator in group["leading"] + group["lagging"]:
            for attribute in (
                "formula",
                "formula_version",
                "unit",
                "owner_role",
                "refresh_cadence",
                "target_value",
                "alert_threshold",
                "baseline_source",
                "calibration_reference",
                "provenance",
                "confidence_band_rule",
            ):
                assert indicator[attribute]
            assert indicator["formula"] != "value"


def test_kpi_ladder_correlation_id_echoed(client):
    response = client.get("/api/v1/evidence/kpi-ladder", headers={"x-ama-correlation-id": "test-cid"})
    assert response.headers.get("x-ama-correlation-id") == "test-cid"


def test_kpi_ladder_filter_returns_exactly_one_group(client):
    response = client.get("/api/v1/evidence/kpi-ladder?capstone_sc_id=SC-CAP-015-001")
    assert response.status_code == 200
    groups = response.json()["groups"]
    assert len(groups) == 1
    assert groups[0]["capstone_sc_id"] == "SC-CAP-015-001"


def test_legacy_missing_matrix_is_promoted_to_manual_three_by_three():
    from app.services.evidence.kpi_ladder import router as kpi_router
    from app.services.evidence.kpi_ladder.repository import get_version, publish
    from app.services.evidence.kpi_ladder.seed import _make

    reset_registry()
    kpi_router._SEEDED = True
    publish(_make(kpi_id="x_lead", name="x leading", kind="leading", sc="SC-CAP-015-001", risk=None))
    publish(_make(kpi_id="x_lag", name="x lagging", kind="lagging", sc="SC-CAP-015-001", risk=None))
    app = create_app()
    with TestClient(app) as test_client:
        response = test_client.get(
            "/api/v1/evidence/kpi-ladder?capstone_sc_id=SC-CAP-015-001&include_risk_adjusted=true"
        )
        assert response.status_code == 200, response.text
        for kpi_id in ("x_lead", "x_lag"):
            promoted = get_version(kpi_id, 2)
            assert promoted is not None
            assert promoted.provenance == "manual"
            assert promoted.risk_adjustment is not None
            assert (promoted.risk_adjustment.likelihood, promoted.risk_adjustment.consequence) == (3, 3)
            assert promoted.risk_adjustment.provenance == "manual"
