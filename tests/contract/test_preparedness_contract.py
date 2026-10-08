import base64
import json

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _trusted_forwarded_principal_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "local")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.setenv("MANAGEMENT_API_KEY", "test-key")


def _auth_headers(persona_id: str = "planning-officer") -> dict[str, str]:
    claims = {
        "sub": "user-prepare-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": ["planning-officer"],
        "persona_id": persona_id,
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def test_preparedness_catalog_and_replay_contract() -> None:
    client = TestClient(create_app())

    organisations_response = client.get("/api/organisations?jurisdictionId=nsw")
    assert organisations_response.status_code == 200
    assert any(item["organisation_id"] == "ses-nsw" for item in organisations_response.json())

    frameworks_response = client.get("/api/frameworks?jurisdictionId=nsw")
    assert frameworks_response.status_code == 200
    assert any(item["framework_id"] == "aiims-national" for item in frameworks_response.json())

    queued_response = client.post(
        "/api/scenarios/scenario-001/runs",
        json={"requestedByPersonaId": "persona-planner-001"},
        headers=_auth_headers("persona-planner-001"),
    )
    assert queued_response.status_code == 202
    assert queued_response.json()["status"] == "queued"

    scenario_response = client.post(
        "/api/scenarios/replay",
        json={
            "scenarioName": "NSW Flood Rehearsal",
            "scenarioType": "flood",
            "jurisdictionIds": ["nsw"],
        },
        headers=_auth_headers(),
    )
    assert scenario_response.status_code == 200
    scenario_run = scenario_response.json()
    assert scenario_run["scenario_type"] == "flood"
    assert scenario_run["jurisdiction_ids"] == ["nsw"]
    assert scenario_run["status"] == "completed"
    assert scenario_run["mode"] == "rehearsal"


def test_preparedness_management_routes_require_auth() -> None:
    client = TestClient(create_app())

    unauthorized = client.post(
        "/api/frameworks/management",
        json={
            "framework_id": "fw-local-1",
            "name": "Local Framework",
            "framework_type": "agency_specific",
            "status": "active",
            "version": 1,
        },
    )
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/api/frameworks/management",
        headers={"X-API-Key": "test-key"},
        json={
            "framework_id": "fw-local-1",
            "name": "Local Framework",
            "framework_type": "agency_specific",
            "status": "active",
            "version": 1,
        },
    )
    assert authorized.status_code == 200
