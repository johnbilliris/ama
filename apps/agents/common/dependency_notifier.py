from packages.domain.src.domain.models.coordination_task import CoordinationTask


class DependencyNotifier:
    def summarize(self, task: CoordinationTask) -> dict[str, object]:
        return {
            "taskId": task.task_id,
            "dependencyTaskIds": task.dependency_task_ids,
            "status": task.status,
        }
