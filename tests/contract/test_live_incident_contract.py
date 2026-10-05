import base64
import json

import pytest
from app.api.dependencies.governance_composition import get_governance_composition
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.main import create_app
from app.services.state_store import ALERTS, INCIDENTS, RECOMMENDATIONS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


@pytest.fixture(autouse=True)
def _trusted_forwarded_principal_fixture(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)

    async def _no_active_simulations(self, user_oid: str):  # type: ignore[no-untyped-def]
        return []

    monkeypatch.setattr(
        "app.repositories.simulation_repository.SimulationRepository.get_by_participant",
        _no_active_simulations,
    )
    token = set_current_tenant(TenantContext(agency_id="ses-nsw", jurisdiction_ids=("nsw",), tenant_id="live"))
    try:
        yield
    finally:
        reset_current_tenant(token)


def _auth_headers(persona_id: str = "persona-incident-commander") -> dict[str, str]:
    claims = {
        "sub": "user-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": ["incident-commander"],
        "persona_id": persona_id,
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def test_signal_ingestion_dashboard_and_alert_contracts() -> None:
    reset_state()
    INCIDENTS["incident-001"] = Incident(
        incident_id="incident-001",
        title="NSW Flood Response",
        incident_type="flood",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["nsw"],
        participating_organisation_ids=["ses-nsw"],
        owning_framework_ids=["aiims-nsw"],
    )
    RECOMMENDATIONS["rec-001"] = Recommendation(
        recommendation_id="rec-001",
        incident_id="incident-001",
        type="public_alert",
        summary="Issue prepare-to-evacuate alert",
        explanation="River gauge and field reports indicate escalating risk.",
        supporting_signal_ids=[],
        required_approval_level="incident_commander",
    )
    ALERTS["alert-rec-001"] = PublicAlert(
        alert_id="alert-rec-001",
        incident_id="incident-001",
        status="approved",
        audience_segments=["community"],
        languages=["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
        channel_set=["sms"],
        content_blocks={
            "headline": "Prepare to evacuate.",
            "body": "Follow emergency service instructions.",
            "en-AU": "Prepare to evacuate.",
            "zh-Hans": "准备疏散。",
            "ar": "استعد للإخلاء.",
            "vi": "Chuẩn bị sơ tán.",
            "el": "Ετοιμαστείτε για εκκένωση.",
            "it": "Prepararsi all'evacuazione.",
        },
        content_safety_result="passed",
    )

    client = TestClient(create_app())

    data_source = get_governance_composition(client.app).registry.register_source(
        DataSource(
            data_source_id="ds-test-bom",
            name="BoM Official Feed",
            kind="authoritative",
            trust_tier="tier_1_authoritative_government",
        ),
        actor_id="test-suite",
    )

    ingest_response = client.post(
        "/api/signals",
        json={
            "source": {"dataSourceId": data_source.data_source_id, "name": "BoM", "kind": "authoritative"},
            "incidentId": "incident-001",
            "category": "weather",
            "occurredAt": "2026-03-09T00:00:00Z",
            "receivedAt": "2026-03-09T00:05:00Z",
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
            "payload": {"warning": "Major flood warning"},
            "confidenceScore": 0.95,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
            "provenance": {
                "sourceUri": "https://example.gov.au",
                "collectionMethod": "api",
            },
        },
    )
    assert ingest_response.status_code == 202

    listed = client.get("/api/signals?incidentId=incident-001")
    assert listed.status_code == 200
    listed_payload = listed.json()
    assert isinstance(listed_payload.get("items"), list)
    assert isinstance(listed_payload.get("total"), int)

    dashboard_response = client.get("/api/incidents/incident-001/dashboard", headers=_auth_headers())
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["incident"]["incidentId"] == "incident-001"

    approval_response = client.post(
        "/api/recommendations/rec-001/approvals",
        json={
            "approverPersonaId": "persona-incident-commander",
            "outcome": "approved",
            "rationale": "Community risk threshold met.",
        },
        headers=_auth_headers(),
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["outcome"] == "approved"

    alert_approval = client.post(
        "/api/alerts/alert-rec-001/approvals",
        json={
            "approverPersonaId": "persona-incident-commander",
            "rationale": "Alert content and safety review complete.",
        },
        headers=_auth_headers(),
    )
    assert alert_approval.status_code == 200, alert_approval.text

    publish_response = client.post(
        "/api/alerts/alert-rec-001/publish",
        json={"publishedByPersonaId": "persona-incident-commander"},
        headers=_auth_headers(),
    )
    assert publish_response.status_code == 200, publish_response.text
    assert publish_response.json()["status"] == "published"


def test_approval_requires_authenticated_persona_and_preserves_state_on_rejection() -> None:
    reset_state()
    RECOMMENDATIONS["rec-unauth"] = Recommendation(
        recommendation_id="rec-unauth",
        incident_id="incident-001",
        type="public_alert",
        summary="Issue alert",
        explanation="risk changed",
        supporting_signal_ids=[],
        required_approval_level="incident_commander",
    )

    client = TestClient(create_app())
    response = client.post(
        "/api/recommendations/rec-unauth/approvals",
        json={
            "approverPersonaId": "persona-incident-commander",
            "outcome": "approved",
            "rationale": "ok",
        },
    )
    assert response.status_code == 401
    assert RECOMMENDATIONS["rec-unauth"].status == "proposed"
