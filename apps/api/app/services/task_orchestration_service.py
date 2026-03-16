from fastapi import HTTPException

from app.services.state_store import PERSONAS, TASKS
from packages.domain.src.domain.models.coordination_task import CoordinationTask


class TaskOrchestrationService:
    def upsert_task(self, task: CoordinationTask) -> CoordinationTask:
        TASKS[task.task_id] = task
        return task

    def update_task_status(self, task_id: str, persona_id: str, status: str) -> CoordinationTask:
        task = TASKS.get(task_id)
        persona = PERSONAS.get(persona_id)

        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if persona is None:
            raise HTTPException(status_code=404, detail="Persona not found")
        if task.assigned_persona_id != persona_id and task.assigned_organisation_id != persona.organisation_id:
            raise HTTPException(status_code=403, detail="Cross-agency task access denied")

        task.status = status
        TASKS[task_id] = task
        return task
