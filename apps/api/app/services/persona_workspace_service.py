from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
)
from app.repositories.persona_registry_repository import (
    Persona as RegistryPersona,
)
from app.repositories.persona_registry_repository import (
    get_persona_registry_repository,
)
from app.services.operational_store import OperationalStore
from app.services.state_store import PERSONAS
from fastapi import HTTPException

from packages.domain.src.domain.models.simulation_tenant import SimulationParticipant


def _persona_view(
    persona_id: str,
    display_name: str,
    organisation_id: str,
    jurisdiction_id: str,
    role: str,
    decision_rights: list[str] | None = None,
    information_needs: list[str] | None = None,
    communication_pathways: list[str] | None = None,
) -> dict[str, object]:
    return {
        "persona_id": persona_id,
        "display_name": display_name,
        "organisation_id": organisation_id,
        "jurisdiction_id": jurisdiction_id,
        "role": role,
        "decision_rights": decision_rights or [],
        "information_needs": information_needs or [],
        "communication_pathways": communication_pathways or [],
    }


class PersonaWorkspaceService:
    def get_workspace(
        self,
        persona_id: str,
        incident_id: str,
        *,
        assignment: SimulationParticipant | None = None,
        tenant_id: str = "live",
    ) -> dict[str, object]:
        persona = PERSONAS.get(persona_id)
        if persona is not None:
            organisation_id = persona.organisation_id
            persona_view = _persona_view(
                persona_id=persona.persona_id,
                display_name=persona.display_name,
                organisation_id=persona.organisation_id,
                jurisdiction_id=persona.jurisdiction_id,
                role=persona.role,
                decision_rights=list(persona.decision_rights),
                information_needs=list(persona.information_needs),
                communication_pathways=list(persona.communication_pathways),
            )
        else:
            registry_persona = self._resolve_from_registry(persona_id)
            organisation_id = registry_persona.organisation_id or ""
            persona_view = _persona_view(
                persona_id=registry_persona.persona_id,
                display_name=registry_persona.display_name or registry_persona.persona_id,
                organisation_id=organisation_id,
                jurisdiction_id=registry_persona.jurisdiction_id or "",
                role=registry_persona.persona_id,
                decision_rights=list(registry_persona.decision_rights),
                information_needs=list(registry_persona.information_needs),
                communication_pathways=list(registry_persona.communication_pathways),
            )

        if assignment is not None:
            organisation_id = assignment.organisation_id or organisation_id
            persona_view["organisation_id"] = organisation_id
            persona_view["jurisdiction_id"] = assignment.jurisdiction_id or persona_view["jurisdiction_id"]
            persona_view["role"] = assignment.role

        repo = get_coordination_tasks_repository().bind(tenant_id)
        visible = [
            task
            for task in repo.list_for_persona_or_org(persona_id, organisation_id)
            if task.incident_id == incident_id
            and (
                assignment is None
                or not assignment.jurisdiction_id
                or not task.jurisdiction_id
                or task.jurisdiction_id.lower() == assignment.jurisdiction_id.lower()
            )
        ]
        visible_tasks = [task.model_dump(mode="json") for task in visible]

        dependency_ids = [dep_id for task in visible_tasks for dep_id in task.get("dependency_task_ids", [])]
        dependency_chain = []
        for task in repo.list_dependencies_for_incident(incident_id, dependency_ids):
            dependency_chain.append(
                {
                    "taskId": task.task_id,
                    "title": task.title,
                    "ownerOrganisationId": task.assigned_organisation_id,
                    "status": task.status,
                    "expectedCompletion": task.expected_completion.isoformat() if task.expected_completion else None,
                    "blockerReason": task.blocker_reason,
                }
            )

        tenant_store = OperationalStore(tenant_id)
        pending_approvals = [
            recommendation.model_dump(mode="json")
            for recommendation in tenant_store.recommendations.values()
            if recommendation.incident_id == incident_id
            and recommendation.status in {"proposed", "under_review", "escalated"}
        ]
        inbound_requests = [
            task.model_dump(mode="json")
            for task in visible
            if task.assigned_organisation_id == organisation_id and task.assigned_persona_id != persona_id
        ]

        return {
            "persona": persona_view,
            "incidentId": incident_id,
            "tasks": visible_tasks,
            "inboundRequests": inbound_requests,
            "pendingApprovals": pending_approvals,
            "dependencies": dependency_chain,
        }

    @staticmethod
    def _resolve_from_registry(persona_id: str) -> RegistryPersona:
        registry_persona = get_persona_registry_repository().find_by_id(persona_id)
        if registry_persona is None:
            raise HTTPException(status_code=404, detail="Persona not found")
        return registry_persona
