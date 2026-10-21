from datetime import datetime
from uuid import uuid4

from app.core.tenant_context import get_current_tenant
from app.repositories.coordination_tasks_repository import get_coordination_tasks_repository
from app.services.task_orchestration_service import TaskOrchestrationService
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from packages.domain.src.domain.models.coordination_task import CoordinationTaskStatus
from packages.domain.src.domain.tenant_mode import is_live_tenant

router = APIRouter(prefix="/tasks", tags=["tasks"])
_TASK_UPDATE_IDEMPOTENCY: dict[str, dict[str, object]] = {}


class TaskStatusUpdateInput(BaseModel):
    personaId: str
    status: CoordinationTaskStatus
    blockerReason: str | None = None
    expectedCompletion: datetime | None = None
    ifMatch: int | None = None


def _validate_replay_headers(request: Request, task_id: str, persona_id: str) -> None:
    replay_actor_id = request.headers.get("x-offline-actor-id")
    replay_tenant_id = request.headers.get("x-offline-tenant-id")
    replay_incident_id = request.headers.get("x-offline-incident-id")
    replay_mode = request.headers.get("x-offline-mode")

    if replay_actor_id and replay_actor_id != persona_id:
        raise HTTPException(status_code=403, detail="Offline replay actor does not match request persona")

    if replay_mode and replay_mode not in {"live", "rehearsal"}:
        raise HTTPException(status_code=422, detail="Invalid offline replay mode")

    if replay_tenant_id:
        try:
            tenant = get_current_tenant()
            if tenant.tenant_id != replay_tenant_id:
                raise HTTPException(status_code=403, detail="Offline replay tenant mismatch")
            current_mode = "live" if is_live_tenant(tenant.tenant_id) else "rehearsal"
            if replay_mode and replay_mode != current_mode:
                raise HTTPException(status_code=403, detail="Offline replay mode mismatch")
        except LookupError:
            if replay_tenant_id != "live":
                raise HTTPException(status_code=403, detail="Offline replay tenant cannot be validated")

    if replay_incident_id:
        task = get_coordination_tasks_repository().get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.incident_id != replay_incident_id:
            raise HTTPException(status_code=403, detail="Offline replay incident mismatch")


def _update_with_idempotency(request: Request, task_id: str, payload: TaskStatusUpdateInput) -> dict[str, object]:
    correlation_id = (
        request.headers.get("x-correlation-id") or request.headers.get("x-correlation-id".upper()) or str(uuid4())
    )
    _validate_replay_headers(request, task_id, payload.personaId)

    cache_key = "|".join(
        [
            correlation_id,
            task_id,
            payload.personaId,
            payload.status,
            str(payload.ifMatch),
        ]
    )
    existing = _TASK_UPDATE_IDEMPOTENCY.get(cache_key)
    if existing is not None:
        return existing

    task = TaskOrchestrationService().update_task_status(
        task_id,
        payload.personaId,
        payload.status,
        blocker_reason=payload.blockerReason,
        expected_completion=payload.expectedCompletion,
        if_match=payload.ifMatch,
    )
    response = task.model_dump(mode="json")
    _TASK_UPDATE_IDEMPOTENCY[cache_key] = response
    return response


@router.post("/{task_id}/status", deprecated=True)
async def update_task_status(task_id: str, payload: TaskStatusUpdateInput, request: Request) -> dict[str, object]:
    return _update_with_idempotency(request, task_id, payload)


@router.patch("/{task_id}")
async def patch_task(task_id: str, payload: TaskStatusUpdateInput, request: Request) -> dict[str, object]:
    return _update_with_idempotency(request, task_id, payload)
