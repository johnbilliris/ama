from fastapi import APIRouter
from pydantic import BaseModel

from app.services.task_orchestration_service import TaskOrchestrationService

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatusUpdateInput(BaseModel):
    personaId: str
    status: str


@router.post("/{task_id}/status")
async def update_task_status(task_id: str, payload: TaskStatusUpdateInput) -> dict[str, object]:
    task = TaskOrchestrationService().update_task_status(task_id, payload.personaId, payload.status)
    return task.model_dump(mode="json")
