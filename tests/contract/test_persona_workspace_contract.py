import base64
import json

import pytest
from app.main import create_app
from app.services.state_store import PERSONAS, TASKS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.persona import Persona


@pytest.fixture(autouse=True)
def _trusted_test_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")


def _auth_headers() -> dict[str, str]:
    claims = {
        "oid": "user-ops-001",
        "persona_id": "persona-ops-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": ["SimulationUser"],
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("ascii")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def test_persona_workspace_and_task_update_contract() -> None:
    reset_state()
    PERSONAS["persona-ops-001"] = Persona(
        persona_id="persona-ops-001",
        display_name="Operations Officer",
        organisation_id="ses-nsw",
        jurisdiction_id="nsw",
        role="operations_officer",
        active_incident_ids=["incident-001"],
    )
    TASKS["task-001"] = CoordinationTask(
        task_id="task-001",
        incident_id="incident-001",
        title="Open evacuation centre",
        assigned_persona_id="persona-ops-001",
        assigned_organisation_id="ses-nsw",
        priority="critical",
    )

    client = TestClient(create_app())

    workspace_response = client.get(
        "/api/personas/persona-ops-001/workspace?incidentId=incident-001",
        headers=_auth_headers(),
    )
    assert workspace_response.status_code == 200
    assert workspace_response.json()["persona"]["persona_id"] == "persona-ops-001"
    assert len(workspace_response.json()["tasks"]) == 1
    assert workspace_response.json()["incidentId"] == "incident-001"
    assert "pendingApprovals" in workspace_response.json()
    assert "inboundRequests" in workspace_response.json()

    status_response = client.patch(
        "/api/tasks/task-001",
        json={"personaId": "persona-ops-001", "status": "in_progress"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_progress"

    illegal_transition = client.patch(
        "/api/tasks/task-001",
        json={"personaId": "persona-ops-001", "status": "queued"},
    )
    assert illegal_transition.status_code == 409


def test_deprecated_task_status_alias_still_supported() -> None:
    reset_state()
    PERSONAS["persona-ops-001"] = Persona(
        persona_id="persona-ops-001",
        display_name="Operations Officer",
        organisation_id="ses-nsw",
        jurisdiction_id="nsw",
        role="operations_officer",
        active_incident_ids=["incident-001"],
    )
    TASKS["task-001"] = CoordinationTask(
        task_id="task-001",
        incident_id="incident-001",
        title="Open evacuation centre",
        assigned_persona_id="persona-ops-001",
        assigned_organisation_id="ses-nsw",
        priority="critical",
    )

    client = TestClient(create_app())
    status_response = client.post(
        "/api/tasks/task-001/status",
        json={"personaId": "persona-ops-001", "status": "in_progress"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_progress"


def test_workspace_requires_incident_id_query() -> None:
    reset_state()
    client = TestClient(create_app())
    response = client.get("/api/personas/persona-ops-001/workspace", headers=_auth_headers())
    assert response.status_code == 422
