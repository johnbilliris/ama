from typing import Any

from app.services.public_alert_service import DELIVERY_TEMPLATES, PublicAlertService
from app.services.state_store import ALERTS
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/alerts", tags=["alerts"])
service = PublicAlertService()


class PublishAlertInput(BaseModel):
    publishedByPersonaId: str


class ApplyTemplateInput(BaseModel):
    templateKey: str


class SupersedeAlertInput(BaseModel):
    newAlertId: str


@router.get("/templates")
async def list_templates() -> dict[str, dict[str, str]]:
    return DELIVERY_TEMPLATES


@router.post("/{alert_id}/template")
async def apply_template(alert_id: str, payload: ApplyTemplateInput) -> dict[str, object]:
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = service.apply_template(alert_id, payload.templateKey)
    return alert.model_dump(mode="json")


@router.post("/{alert_id}/publish")
async def publish_alert(alert_id: str, payload: PublishAlertInput) -> dict[str, object]:
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = service.publish(alert_id, payload.publishedByPersonaId)
    return alert.model_dump(mode="json")


@router.post("/{alert_id}/deliver")
async def deliver_alert(alert_id: str) -> list[dict[str, Any]]:
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    return service.deliver(alert_id)


@router.post("/{alert_id}/supersede")
async def supersede_alert(alert_id: str, payload: SupersedeAlertInput) -> dict[str, object]:
    if alert_id not in ALERTS:
        raise HTTPException(status_code=404, detail="Alert not found")
    old = service.supersede(alert_id, payload.newAlertId)
    return old.model_dump(mode="json")
