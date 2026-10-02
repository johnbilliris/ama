from datetime import UTC, datetime

from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
)
from app.repositories.persona_registry_repository import (
    get_persona_registry_repository,
)
from app.services.audit_service import AuditService
from app.services.operational_store import OperationalStore
from app.services.state_store import PERSONAS
from fastapi import HTTPException

from packages.domain.src.domain.models.coordination_task import (
    CoordinationTask,
    CoordinationTaskStatus,
)


class TaskOrchestrationService:
    _ALLOWED_TRANSITIONS: dict[CoordinationTaskStatus, set[CoordinationTaskStatus]] = {
        "queued": {"in_progress", "blocked"},
        "in_progress": {"blocked", "completed"},
        "blocked": {"in_progress", "completed"},
        "completed": set(),
    }

    def upsert_task(self, task: CoordinationTask) -> CoordinationTask:
        return get_coordination_tasks_repository().upsert(task)

    def update_task_status(
        self,
        task_id: str,
        persona_id: str,
        status: CoordinationTaskStatus,
        *,
        blocker_reason: str | None = None,
        expected_completion: datetime | None = None,
        if_match: int | None = None,
    ) -> CoordinationTask:
        repo = get_coordination_tasks_repository()

        persona = PERSONAS.get(persona_id)
        organisation_id: str | None
        if persona is not None:
            organisation_id = persona.organisation_id
        else:
            registry_persona = get_persona_registry_repository().find_by_id(persona_id)
            if registry_persona is None:
                raise HTTPException(status_code=404, detail="Persona not found")
            organisation_id = registry_persona.organisation_id

        task = repo.get(task_id, organisation_id or None)
        if task is None and organisation_id:
            task = repo.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.assigned_persona_id != persona_id and task.assigned_organisation_id != (organisation_id or ""):
            raise HTTPException(status_code=403, detail="Cross-agency task access denied")

        if if_match is not None and if_match != task.version:
            raise HTTPException(status_code=409, detail="Task update conflict: stale version")

        allowed = self._ALLOWED_TRANSITIONS.get(task.status, set())
        if status != task.status and status not in allowed:
            raise HTTPException(
                status_code=409, detail=f"Illegal task status transition from {task.status} to {status}"
            )

        if status == "blocked" and not (blocker_reason and blocker_reason.strip()):
            raise HTTPException(status_code=422, detail="blockerReason is required when status is blocked")

        if status == "completed" and task.dependency_task_ids:
            for dep_id in task.dependency_task_ids:
                dependency = repo.get(dep_id)
                if dependency is None or dependency.status != "completed":
                    raise HTTPException(
                        status_code=409, detail="Cannot complete task while dependencies are incomplete"
                    )

        store = OperationalStore.current()
        AuditService().record_event(
            incident_id=task.incident_id,
            event_type="task_status",
            summary=f"Task {task.task_id} status changed to {status}",
            actor=persona_id,
            tenant_id=store.tenant_id,
            mode="live" if store.tenant_id == "live" else "rehearsal",
            correlation_id=f"task-{task.task_id}-{status}",
            outcome=str(status),
            route="/api/tasks/{task_id}",
            rationale="Task owner updated status",
            payload={
                "taskId": task.task_id,
                "status": str(status),
                "organisationId": task.assigned_organisation_id,
            },
        )

        task.status = status
        task.blocker_reason = blocker_reason if status == "blocked" else None
        task.expected_completion = expected_completion
        task.updated_at = datetime.now(UTC)
        task.version = task.version + 1
        repo.upsert(task)
        return task
