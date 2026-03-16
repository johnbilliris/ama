from packages.domain.src.domain.models.coordination_task import CoordinationTask


class ResourceAllocationAgent:
    def prioritize(self, tasks: list[CoordinationTask]) -> list[CoordinationTask]:
        priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(tasks, key=lambda task: priority_rank.get(task.priority, 99))
