from app.services.state_store import PERSONAS, TASKS
from fastapi import HTTPException


class PersonaWorkspaceService:
    def get_workspace(self, persona_id: str) -> dict[str, object]:
        persona = PERSONAS.get(persona_id)
        if persona is None:
            raise HTTPException(status_code=404, detail="Persona not found")

        visible_tasks = [
            task.model_dump(mode="json")
            for task in TASKS.values()
            if task.assigned_persona_id == persona_id or task.assigned_organisation_id == persona.organisation_id
        ]

        dependency_ids = {dependency_id for task in visible_tasks for dependency_id in task.get("dependency_task_ids", [])}
        dependency_chain = [
            task.model_dump(mode="json")
            for task in TASKS.values()
            if task.task_id in dependency_ids and task.assigned_organisation_id == persona.organisation_id
        ]

        return {
            "persona": persona.model_dump(mode="json"),
            "tasks": visible_tasks,
            "dependencies": dependency_chain,
        }
