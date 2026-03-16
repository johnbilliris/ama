"""Quickstart rehearsal flow — validates the end-to-end exercise sequence
described in quickstart.md: signal ingestion, dashboard, approval, alert
publish, preparedness replay, and cross-agency isolation."""

from app.main import create_app
from app.services.state_store import (
    ALERTS,
    PERSONAS,
    RECOMMENDATIONS,
    TASKS,
    reset_state,
)
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


def test_quickstart_full_rehearsal_flow() -> None:
    """Walk through the complete quickstart rehearsal:
    1. Ingest signal → auto-creates incident
    2. Load dashboard
    3. Approve recommendation → publish alert
    4. Run preparedness replay
    """
    reset_state()
    client = TestClient(create_app())

    # Step 1: Ingest an authoritative weather signal
    ingest = client.post(
        "/api/signals",
        json={
            "source": {"dataSourceId": "bom-001", "name": "BoM", "kind": "authoritative"},
            "incidentId": "incident-quickstart",
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
    assert ingest.status_code == 200

    # Step 2: Load the dashboard
    dashboard = client.get("/api/incidents/incident-quickstart/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["incident"]["incidentId"] == "incident-quickstart"

    # Step 3: Set up recommendation and alert, then approve and publish
    RECOMMENDATIONS["rec-qs"] = Recommendation(
        recommendation_id="rec-qs",
        incident_id="incident-quickstart",
        type="public_alert",
        summary="Issue community flood alert",
        explanation="Authoritative flood warning received.",
        supporting_signal_ids=[],
        required_approval_level="incident_commander",
    )
    ALERTS["alert-rec-qs"] = PublicAlert(
        alert_id="alert-rec-qs",
        incident_id="incident-quickstart",
        status="approved",
        audience_segments=["community"],
        languages=["en-AU"],
        channel_set=["sms", "push"],
        content_blocks={"headline": "Prepare to evacuate if directed."},
    )

    approval = client.post(
        "/api/recommendations/rec-qs/approvals",
        json={
            "approverPersonaId": "persona-commander",
            "outcome": "approved",
            "rationale": "Authoritative warning confirmed.",
        },
    )
    assert approval.status_code == 200

    publish = client.post(
        "/api/alerts/alert-rec-qs/publish",
        json={"publishedByPersonaId": "persona-commander"},
    )
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"

    # Step 4: Run a preparedness rehearsal
    replay = client.post(
        "/api/scenarios/replay",
        json={
            "scenarioName": "Quickstart Flood Rehearsal",
            "scenarioType": "flood",
            "jurisdictionIds": ["nsw"],
        },
    )
    assert replay.status_code == 200
    assert replay.json()["generated_findings"]


def test_quickstart_cross_agency_isolation() -> None:
    """Verify that cross-agency task updates are rejected per the quickstart
    acceptance check for role-specific workspace isolation."""
    reset_state()
    client = TestClient(create_app())

    PERSONAS["persona-ses"] = Persona(
        persona_id="persona-ses",
        display_name="SES Operations",
        organisation_id="ses-nsw",
        jurisdiction_id="nsw",
        role="operations_officer",
    )
    PERSONAS["persona-police"] = Persona(
        persona_id="persona-police",
        display_name="Police Liaison",
        organisation_id="nsw-police",
        jurisdiction_id="nsw",
        role="liaison_officer",
    )
    TASKS["task-qs-001"] = CoordinationTask(
        task_id="task-qs-001",
        incident_id="incident-quickstart",
        title="Deploy sandbags",
        assigned_persona_id="persona-ses",
        assigned_organisation_id="ses-nsw",
    )

    # SES persona can update their own task
    ok = client.post(
        "/api/tasks/task-qs-001/status",
        json={"personaId": "persona-ses", "status": "in_progress"},
    )
    assert ok.status_code == 200

    # Police persona cannot update SES task
    blocked = client.post(
        "/api/tasks/task-qs-001/status",
        json={"personaId": "persona-police", "status": "completed"},
    )
    assert blocked.status_code == 403
