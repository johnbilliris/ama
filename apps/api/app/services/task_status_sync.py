from app.services.state_store import TASKS


class TaskStatusSyncService:
    def summary_for_persona(self, persona_id: str) -> dict[str, int]:
        relevant_tasks = [task for task in TASKS.values() if task.assigned_persona_id == persona_id]
        return {
            "queued": sum(1 for task in relevant_tasks if task.status == "queued"),
            "inProgress": sum(1 for task in relevant_tasks if task.status == "in_progress"),
            "completed": sum(1 for task in relevant_tasks if task.status == "completed"),
        }
