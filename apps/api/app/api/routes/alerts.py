from typing import Any

from app.core.auth import require_authenticated_persona
from app.services.operational_store import OperationalStore
from app.services.public_alert_service import DELIVERY_TEMPLATES, PublicAlertService
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/alerts", tags=["alerts"])
service = PublicAlertService()


class PublishAlertInput(BaseModel):
    publishedByPersonaId: str | None = None


class ApproveAlertDraftInput(BaseModel):
    approverPersonaId: str | None = None
    rationale: str
    conditions: list[str] = Field(default_factory=list)


class ApplyTemplateInput(BaseModel):
    templateKey: str


class SupersedeAlertInput(BaseModel):
    newAlertId: str


class UpdateAlertDraftInput(BaseModel):
    contentBlocks: dict[str, str] | None = None
    audienceSegments: list[str] | None = None
    languages: list[str] | None = None
    channelSet: list[str] | None = None


@router.get("/templates")
async def list_templates() -> dict[str, dict[str, str]]:
    return DELIVERY_TEMPLATES


@router.post("/{alert_id}/template")
async def apply_template(alert_id: str, payload: ApplyTemplateInput, request: Request) -> dict[str, object]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    require_authenticated_persona(request)
    alert = service.apply_template(alert_id, payload.templateKey)
    request.state.audit_outcome = "draft_updated"
    return alert.model_dump(mode="json")


@router.get("/{alert_id}")
async def get_alert(alert_id: str, request: Request) -> dict[str, object]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    require_authenticated_persona(request)
    return service.get_alert(alert_id).model_dump(mode="json")


@router.put("/{alert_id}/draft")
async def update_alert_draft(alert_id: str, payload: UpdateAlertDraftInput, request: Request) -> dict[str, object]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    require_authenticated_persona(request)
    alert = service.update_draft(
        alert_id,
        content_blocks=payload.contentBlocks,
        audience_segments=payload.audienceSegments,
        languages=payload.languages,
        channel_set=payload.channelSet,
    )
    request.state.audit_outcome = "draft_updated"
    return alert.model_dump(mode="json")


@router.post("/{alert_id}/publish")
async def publish_alert(alert_id: str, payload: PublishAlertInput, request: Request) -> dict[str, object]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    actor_persona_id = require_authenticated_persona(request, payload.publishedByPersonaId)
    alert = service.publish(alert_id, actor_persona_id)
    request.state.audit_outcome = "published"
    return alert.model_dump(mode="json")


@router.post("/{alert_id}/approvals")
async def approve_alert_draft(alert_id: str, payload: ApproveAlertDraftInput, request: Request) -> dict[str, object]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    actor_persona_id = require_authenticated_persona(request, payload.approverPersonaId)
    decision = service.approve_draft(
        alert_id=alert_id,
        approver_persona_id=actor_persona_id,
        approver_roles=tuple(getattr(request.state, "claims", {}).get("roles", [])),
        rationale=payload.rationale,
        conditions=payload.conditions,
    )
    request.state.audit_outcome = "approved"
    return decision.model_dump(mode="json")


@router.post("/{alert_id}/deliver")
async def deliver_alert(alert_id: str, request: Request) -> list[dict[str, Any]]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    require_authenticated_persona(request)
    receipts = service.deliver(alert_id)
    request.state.audit_outcome = "delivery_attempted"
    return receipts


@router.post("/{alert_id}/supersede")
async def supersede_alert(alert_id: str, payload: SupersedeAlertInput, request: Request) -> dict[str, object]:
    if not OperationalStore.current().alerts.contains(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    require_authenticated_persona(request)
    old = service.supersede(alert_id, payload.newAlertId)
    request.state.audit_outcome = "superseded"
    return old.model_dump(mode="json")
