from __future__ import annotations

import base64
import json

import pytest
from app.core.auth import extract_principal_from_claims
from app.main import create_app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.spec007_isolation


def _forwarded_principal(claims: dict[str, object]) -> dict[str, str]:
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("ascii")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


@pytest.fixture(autouse=True)
def _auth_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.delenv("AMA_ALLOW_ANONYMOUS_SIMULATION", raising=False)
    monkeypatch.delenv("AMA_TRUST_FORWARDED_PRINCIPAL", raising=False)
    monkeypatch.delenv("AMA_TEST_SUPPORT", raising=False)
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)


def test_simulation_routes_reject_missing_principal() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/simulations")

    assert response.status_code == 401


def test_incident_routes_reject_missing_principal() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/incidents/incident-auth/declare")

    assert response.status_code == 401


def test_anonymous_simulation_requires_explicit_nonproduction_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_SIMULATION", "1")

    with TestClient(create_app()) as client:
        response = client.get("/api/simulations")

    assert response.status_code == 200


def test_forwarded_principal_is_rejected_without_trusted_test_gate() -> None:
    headers = _forwarded_principal(
        {
            "oid": "participant-1",
            "roles": ["SimulationUser"],
            "agency_id": "ses-nsw",
            "jurisdiction_ids": ["nsw"],
        }
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/simulations", headers=headers)

    assert response.status_code == 401


def test_authenticated_subject_prefers_entra_oid() -> None:
    principal = extract_principal_from_claims(
        {
            "oid": "entra-object-id",
            "sub": "application-subject",
            "roles": ["SimulationUser"],
        }
    )

    assert principal.subject == "entra-object-id"
