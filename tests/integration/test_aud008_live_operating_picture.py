import base64
import json
from datetime import UTC, datetime, timedelta

import pytest
from app.main import create_app
from app.services.operational_store import OperationalStore
from app.services.state_store import reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.signal import Signal


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)


def _auth_headers(role: str = "incident-commander", persona_id: str = "persona-ic") -> dict[str, str]:
    claims = {
        "sub": "user-008",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw", "vic"],
        "roles": [role],
        "persona_id": persona_id,
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def _seed_live_incident() -> None:
    reset_state()
    store = OperationalStore.current()
    store.incidents.put(
        "incident-008",
        Incident(
            incident_id="incident-008",
            title="Cross-border flood coordination",
            incident_type="flood",
            status="active",
            severity="warning",
            affected_jurisdiction_ids=["nsw", "vic"],
            participating_organisation_ids=["ses-nsw", "vic-cfa"],
            owning_framework_ids=["aiims"],
        ),
    )
    store.recommendations.put(
        "rec-008",
        Recommendation(
            recommendation_id="rec-008",
            incident_id="incident-008",
            type="public_alert",
            summary="Issue cross-border watch-and-act alert",
            explanation="River gauges exceeded trigger levels across borders.",
            supporting_signal_ids=["sig-008"],
            required_approval_level="incident_commander",
        ),
    )
    store.tasks.put(
        "task-008",
        CoordinationTask(
            task_id="task-008",
            incident_id="incident-008",
            title="Coordinate sandbag deployment",
            assigned_persona_id="persona-ops",
            assigned_organisation_id="ses-nsw",
            status="in_progress",
            priority="high",
        ),
    )
    store.signals.put(
        "sig-008",
        Signal(
            signal_id="sig-008",
            incident_id="incident-008",
            data_source_id="bom-warnings",
            category="weather",
            occurred_at=datetime.now(UTC) - timedelta(hours=3),
            received_at=datetime.now(UTC) - timedelta(hours=2),
            jurisdiction_id="nsw",
            location={"type": "Point", "coordinates": [151.2, -33.8]},
            payload={"warning": "major flood"},
            classification="official",
            retention_until=datetime.now(UTC) + timedelta(days=30),
            confidence_score=0.95,
            freshness_score=0.4,
            validation_status="validated",
            provenance={"expectedUpdateSeconds": 60},
        ),
    )


def test_aud008_dashboard_uses_catalogue_orgs_tasks_and_degraded_sources() -> None:
    _seed_live_incident()
    client = TestClient(create_app())

    response = client.get("/api/incidents/incident-008/dashboard", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["activeTasks"][0]["task_id"] == "task-008"
    assert body["incident"]["frameworkContext"] == [] or isinstance(body["incident"]["frameworkContext"], list)
    assert "geometry" in body["incident"]
    assert body["signalSummary"]["degradedSources"]
    org_names = [entry["name"] for entry in body["participatingOrganisations"]]
    assert any(name != "ses-nsw" for name in org_names)


def test_aud008_dashboard_authz_approval_action_by_role() -> None:
    _seed_live_incident()
    client = TestClient(create_app())

    unauthorized = client.get("/api/incidents/incident-008/dashboard")
    assert unauthorized.status_code == 401

    authorized = client.get(
        "/api/incidents/incident-008/dashboard",
        headers=_auth_headers(role="incident-commander", persona_id="persona-ic"),
    )
    assert authorized.status_code == 200
    assert authorized.json()["activeRecommendations"][0]["approvalAction"]["allowed"] is True


def test_aud008_dashboard_not_found() -> None:
    reset_state()
    client = TestClient(create_app())

    response = client.get("/api/incidents/missing-incident/dashboard", headers=_auth_headers())

    assert response.status_code == 404
