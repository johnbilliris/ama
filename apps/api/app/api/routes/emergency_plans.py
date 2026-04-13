"""Emergency plan API routes for the Platform API.

Delegates to ``EmergencyPlanService`` for business logic and
``EmergencyPlanRepository`` for persistence.

FRs: FR-001–007 | Research: R-002
"""

from app.services.emergency_plan_service import EmergencyPlanService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/emergency-plans", tags=["emergency-plans"])
service = EmergencyPlanService()


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------


class CreatePlanInput(BaseModel):
    title: str
    region_id: str
    hazard_types: list[str]
    hierarchy_level: str = "local"
    parent_plan_id: str | None = None
    security_rating: str = "official"
    authority: str = ""
    created_by: str = ""


class UpdateSectionInput(BaseModel):
    title: str = ""
    content: str = ""


class TransitionInput(BaseModel):
    target_state: str
    user_role: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post("", status_code=201)
async def create_plan(payload: CreatePlanInput) -> dict:
    plan = await service.create_plan(
        title=payload.title,
        region_id=payload.region_id,
        hazard_types=payload.hazard_types,
        hierarchy_level=payload.hierarchy_level,
        parent_plan_id=payload.parent_plan_id,
        security_rating=payload.security_rating,
        authority=payload.authority,
        created_by=payload.created_by,
    )
    return plan


@router.get("")
async def list_plans(region_id: str | None = None, lifecycle_state: str | None = None) -> list[dict]:
    return await service.list_plans(region_id=region_id, lifecycle_state=lifecycle_state)


@router.get("/by-region/{region_id}/hierarchy")
async def get_hierarchy(region_id: str) -> dict:
    plans = await service.get_hierarchy(region_id)
    return {"region_id": region_id, "plans": plans}


@router.get("/{plan_id}")
async def get_plan(plan_id: str, region_id: str = "") -> dict:
    plan = await service.get_plan(plan_id, region_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found")
    return plan


@router.put("/{plan_id}/sections/{section_slug}")
async def update_section(plan_id: str, section_slug: str, payload: UpdateSectionInput, region_id: str = "") -> dict:
    try:
        return await service.update_section(plan_id, region_id, section_slug, payload.title, payload.content)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{plan_id}/transition")
async def transition_plan(plan_id: str, payload: TransitionInput, region_id: str = "") -> dict:
    try:
        return await service.transition_plan(plan_id, region_id, payload.target_state, payload.user_role)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{plan_id}/completeness")
async def get_completeness(plan_id: str, region_id: str = "") -> dict:
    try:
        return await service.get_completeness(plan_id, region_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
