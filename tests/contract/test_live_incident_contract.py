from app.main import create_app
from app.services.state_store import ALERTS, INCIDENTS, RECOMMENDATIONS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


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
        languages=["en-AU"],
        channel_set=["sms"],
        content_blocks={"headline": "Prepare to evacuate."},
    )

    client = TestClient(create_app())

    ingest_response = client.post(
        "/api/signals",
        json={
            "source": {"dataSourceId": "bom-001", "name": "BoM", "kind": "authoritative"},
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
                "sourceKind": "authoritative",
            },
        },
    )
    assert ingest_response.status_code == 200

    dashboard_response = client.get("/api/incidents/incident-001/dashboard")
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["incident"]["incidentId"] == "incident-001"

    approval_response = client.post(
        "/api/recommendations/rec-001/approvals",
        json={
            "approverPersonaId": "persona-incident-commander",
            "outcome": "approved",
            "rationale": "Community risk threshold met.",
        },
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["outcome"] == "approved"

    publish_response = client.post(
        "/api/alerts/alert-rec-001/publish",
        json={"publishedByPersonaId": "persona-incident-commander"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"
