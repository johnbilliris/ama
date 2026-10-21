from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
)


class TaskStatusSyncService:
    def summary_for_persona(self, persona_id: str) -> dict[str, int]:
        relevant_tasks = get_coordination_tasks_repository().list_for_persona_assignment(persona_id)
        return {
            "queued": sum(1 for task in relevant_tasks if task.status == "queued"),
            "inProgress": sum(1 for task in relevant_tasks if task.status == "in_progress"),
            "blocked": sum(1 for task in relevant_tasks if task.status == "blocked"),
            "completed": sum(1 for task in relevant_tasks if task.status == "completed"),
        }
