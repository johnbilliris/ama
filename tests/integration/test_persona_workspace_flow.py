import pytest
from fastapi import HTTPException

from app.services.persona_workspace_service import PersonaWorkspaceService
from app.services.state_store import PERSONAS, TASKS, reset_state
from app.services.task_orchestration_service import TaskOrchestrationService
from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.persona import Persona


def seed_workspace_state() -> None:
    PERSONAS["persona-ops-001"] = Persona(
        persona_id="persona-ops-001",
        display_name="SES Operations",
        organisation_id="ses-nsw",
        jurisdiction_id="nsw",
        role="operations_officer",
        active_incident_ids=["incident-001"],
    )
    PERSONAS["persona-police-001"] = Persona(
        persona_id="persona-police-001",
        display_name="Police Liaison",
        organisation_id="nsw-police",
        jurisdiction_id="nsw",
        role="liaison_officer",
        active_incident_ids=["incident-001"],
    )
    TASKS["task-001"] = CoordinationTask(
        task_id="task-001",
        incident_id="incident-001",
        title="Coordinate sandbag deployment",
        assigned_persona_id="persona-ops-001",
        assigned_organisation_id="ses-nsw",
        priority="high",
    )
    TASKS["task-002"] = CoordinationTask(
        task_id="task-002",
        incident_id="incident-001",
        title="Close arterial road",
        assigned_persona_id="persona-police-001",
        assigned_organisation_id="nsw-police",
        dependency_task_ids=["task-001"],
        priority="critical",
    )


def test_workspace_filters_cross_agency_tasks() -> None:
    reset_state()
    seed_workspace_state()

    workspace = PersonaWorkspaceService().get_workspace("persona-ops-001")

    visible_task_ids = {task["task_id"] for task in workspace["tasks"]}
    assert visible_task_ids == {"task-001"}
    assert workspace["dependencies"] == []


def test_cross_agency_status_update_is_rejected() -> None:
    reset_state()
    seed_workspace_state()

    with pytest.raises(HTTPException) as exc_info:
        TaskOrchestrationService().update_task_status("task-001", "persona-police-001", "completed")

    assert exc_info.value.status_code == 403
