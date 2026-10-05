import pytest
from app.services.persona_workspace_service import PersonaWorkspaceService
from app.services.state_store import PERSONAS, TASKS, reset_state
from app.services.task_orchestration_service import TaskOrchestrationService
from fastapi import HTTPException

from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.simulation_tenant import SimulationParticipant


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
        organisation_id="nswpf",
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
        dependency_task_ids=["task-002"],
        priority="high",
    )
    TASKS["task-002"] = CoordinationTask(
        task_id="task-002",
        incident_id="incident-001",
        title="Close arterial road",
        assigned_persona_id="persona-police-001",
        assigned_organisation_id="nswpf",
        dependency_task_ids=["task-001"],
        priority="critical",
    )


def test_workspace_filters_cross_agency_tasks() -> None:
    reset_state()
    seed_workspace_state()

    workspace = PersonaWorkspaceService().get_workspace("persona-ops-001", "incident-001")

    visible_task_ids = {task["task_id"] for task in workspace["tasks"]}
    assert visible_task_ids == {"task-001"}
    assert workspace["dependencies"] == [
        {
            "taskId": "task-002",
            "title": "Close arterial road",
            "ownerOrganisationId": "nswpf",
            "status": "queued",
            "expectedCompletion": None,
            "blockerReason": None,
        }
    ]


def test_cross_agency_status_update_is_rejected() -> None:
    reset_state()
    seed_workspace_state()

    with pytest.raises(HTTPException) as exc_info:
        TaskOrchestrationService().update_task_status("task-001", "persona-police-001", "completed")

    assert exc_info.value.status_code == 403


def test_illegal_transition_and_blocker_reason_rules() -> None:
    reset_state()
    seed_workspace_state()

    with pytest.raises(HTTPException) as illegal:
        TaskOrchestrationService().update_task_status("task-001", "persona-ops-001", "completed")
    assert illegal.value.status_code == 409

    TaskOrchestrationService().update_task_status("task-001", "persona-ops-001", "in_progress")
    with pytest.raises(HTTPException) as missing_reason:
        TaskOrchestrationService().update_task_status("task-001", "persona-ops-001", "blocked")
    assert missing_reason.value.status_code == 422


def test_if_match_conflict_rejected() -> None:
    reset_state()
    seed_workspace_state()
    service = TaskOrchestrationService()
    service.update_task_status("task-001", "persona-ops-001", "in_progress", if_match=1)

    with pytest.raises(HTTPException) as conflict:
        service.update_task_status("task-001", "persona-ops-001", "blocked", blocker_reason="waiting", if_match=1)
    assert conflict.value.status_code == 409


def test_simulation_assignment_filters_jurisdiction_and_populates_workflow() -> None:
    reset_state()
    PERSONAS["persona-ops-001"] = Persona(
        persona_id="persona-ops-001",
        display_name="SES Operations",
        organisation_id="ses-shared",
        jurisdiction_id="nsw",
        role="operations_officer",
    )
    TASKS.bucket_for("sim-drill")["task-nsw"] = CoordinationTask(
        task_id="task-nsw",
        incident_id="incident-001",
        title="NSW task",
        assigned_persona_id="persona-other",
        assigned_organisation_id="ses-shared",
        jurisdiction_id="nsw",
    )
    TASKS.bucket_for("sim-drill")["task-vic"] = CoordinationTask(
        task_id="task-vic",
        incident_id="incident-001",
        title="VIC task",
        assigned_persona_id="persona-other",
        assigned_organisation_id="ses-shared",
        jurisdiction_id="vic",
    )
    from app.services.operational_store import OperationalStore

    OperationalStore("sim-drill").recommendations.put(
        "rec-pending",
        Recommendation(
            recommendation_id="rec-pending",
            incident_id="incident-001",
            type="coordination",
            summary="Review resource staging",
            explanation="Exercise",
            required_approval_level="operations_officer",
            status="under_review",
        ),
    )
    assignment = SimulationParticipant(
        oid="user-ops",
        persona_id="persona-ops-001",
        organisation_id="ses-shared",
        jurisdiction_id="nsw",
        role="participant",
    )

    workspace = PersonaWorkspaceService().get_workspace(
        "persona-ops-001",
        "incident-001",
        assignment=assignment,
        tenant_id="sim-drill",
    )

    assert {task["task_id"] for task in workspace["tasks"]} == {"task-nsw"}
    assert {task["task_id"] for task in workspace["inboundRequests"]} == {"task-nsw"}
    assert {item["recommendation_id"] for item in workspace["pendingApprovals"]} == {"rec-pending"}
    assert workspace["persona"]["jurisdiction_id"] == "nsw"
