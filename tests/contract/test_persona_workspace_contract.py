from fastapi.testclient import TestClient

from app.main import create_app
from app.services.state_store import PERSONAS, TASKS, reset_state
from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.persona import Persona


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

    workspace_response = client.get("/api/personas/persona-ops-001/workspace")
    assert workspace_response.status_code == 200
    assert workspace_response.json()["persona"]["persona_id"] == "persona-ops-001"
    assert len(workspace_response.json()["tasks"]) == 1

    status_response = client.post(
        "/api/tasks/task-001/status",
        json={"personaId": "persona-ops-001", "status": "in_progress"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_progress"
