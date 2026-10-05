"""Quickstart rehearsal flow — validates the end-to-end exercise sequence
described in quickstart.md: signal ingestion, dashboard, approval, alert
publish, preparedness replay, and cross-agency isolation."""

import base64
import json

import pytest
from app.api.dependencies.governance_composition import get_governance_composition
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
from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


@pytest.fixture(autouse=True)
def _trusted_forwarded_principal_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")


def _auth_headers(
    persona_id: str = "planning-officer",
    role: str = "planning-officer",
) -> dict[str, str]:
    claims = {
        "sub": "user-quickstart-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": [role],
        "persona_id": persona_id,
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {
        "X-MS-CLIENT-PRINCIPAL": encoded,
    }


def test_quickstart_full_rehearsal_flow() -> None:
    """Walk through the complete quickstart rehearsal:
    1. Ingest signal → auto-creates incident
    2. Load dashboard
    3. Approve recommendation → publish alert
    4. Run preparedness replay
    """
    reset_state()
    client = TestClient(create_app())
    client.headers.update(_auth_headers())
    get_governance_composition(client.app).registry.register_source(
        DataSource(
            data_source_id="bom-warnings",
            name="BoM Warnings",
            kind="authoritative",
            trust_tier="tier_1_authoritative_government",
        ),
        actor_id="quickstart-suite",
    )

    # Step 1: Ingest an authoritative weather signal
    ingest = client.post(
        "/api/signals",
        json={
            "source": {"dataSourceId": "bom-warnings", "name": "BoM", "kind": "authoritative"},
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
    assert ingest.status_code == 202

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
        languages=["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
        channel_set=["sms", "push"],
        content_blocks={
            "headline": "Prepare to evacuate if directed.",
            "body": "Follow emergency service instructions.",
            "en-AU": "Prepare to evacuate if directed.",
            "zh-Hans": "如有指示，请准备疏散。",
            "ar": "استعد للإخلاء إذا طُلب منك ذلك.",
            "vi": "Chuẩn bị sơ tán nếu được yêu cầu.",
            "el": "Προετοιμαστείτε για εκκένωση εάν σας ζητηθεί.",
            "it": "Prepararsi all'evacuazione se richiesto.",
        },
        content_safety_result="passed",
    )

    approval = client.post(
        "/api/recommendations/rec-qs/approvals",
        json={
            "approverPersonaId": "planning-officer",
            "outcome": "approved",
            "rationale": "Authoritative warning confirmed.",
        },
        headers=_auth_headers("planning-officer", role="incident-commander"),
    )
    assert approval.status_code == 200

    alert_approval = client.post(
        "/api/alerts/alert-rec-qs/approvals",
        json={
            "approverPersonaId": "persona-incident-commander",
            "rationale": "Alert content and safety review complete.",
        },
        headers=_auth_headers("persona-incident-commander", role="incident-commander"),
    )
    assert alert_approval.status_code == 200, alert_approval.text

    publish = client.post(
        "/api/alerts/alert-rec-qs/publish",
        json={"publishedByPersonaId": "planning-officer"},
        headers=_auth_headers("planning-officer", role="incident-commander"),
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
        organisation_id="nswpf",
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
