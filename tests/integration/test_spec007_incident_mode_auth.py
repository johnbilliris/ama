from __future__ import annotations

import base64
import json

import pytest
from app.main import create_app
from app.repositories.incident_mode_repository import IncidentModeRepository
from fastapi.testclient import TestClient

pytestmark = pytest.mark.spec007_isolation


def _headers(role: str, subject: str = "operator-1") -> dict[str, str]:
    claims = {
        "oid": subject,
        "roles": [role],
        "agency_id": "nema",
        "jurisdiction_ids": ["nsw"],
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("ascii")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> None:
    IncidentModeRepository.reset_for_tests()
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)


def test_only_administrator_can_declare_and_resolve_incident_mode() -> None:
    with TestClient(create_app()) as client:
        denied = client.post("/api/incidents/declare", headers=_headers("SimulationUser"))
        declared = client.post("/api/incidents/declare", headers=_headers("system-administrator", "admin-1"))
        duplicate = client.post("/api/incidents/declare", headers=_headers("system-administrator", "admin-1"))
        resolved = client.post("/api/incidents/resolve", headers=_headers("system-administrator", "admin-1"))

    assert denied.status_code == 403
    assert declared.status_code == 200
    assert duplicate.status_code == 200
    assert resolved.status_code == 200
    assert IncidentModeRepository._memory_document["version"] == 2
