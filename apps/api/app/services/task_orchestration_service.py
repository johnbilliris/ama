from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
)
from app.repositories.persona_registry_repository import (
    get_persona_registry_repository,
)
from app.services.state_store import PERSONAS
from fastapi import HTTPException

from packages.domain.src.domain.models.coordination_task import CoordinationTask


class TaskOrchestrationService:
    def upsert_task(self, task: CoordinationTask) -> CoordinationTask:
        return get_coordination_tasks_repository().upsert(task)

    def update_task_status(self, task_id: str, persona_id: str, status: str) -> CoordinationTask:
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

        if (
            task.assigned_persona_id != persona_id
            and task.assigned_organisation_id != (organisation_id or "")
        ):
            raise HTTPException(status_code=403, detail="Cross-agency task access denied")

        task.status = status
        repo.upsert(task)
        return task
