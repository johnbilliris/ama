import logging
from datetime import datetime

from app.middleware.auth import authorize_management
from app.services.preparedness_analysis_service import PreparednessAnalysisService
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/frameworks", tags=["frameworks"])
logger = logging.getLogger(__name__)

_FRAMEWORK_CATALOGUE: dict[str, dict[str, object]] = {}
_ASSIGNMENT_CATALOGUE: dict[str, dict[str, object]] = {}


class ManagedFrameworkInput(BaseModel):
    framework_id: str
    name: str
    framework_type: str
    status: str = "active"
    version: int = Field(default=1, ge=1)


class ManagedAssignmentInput(BaseModel):
    assignment_id: str
    framework_id: str
    jurisdiction_id: str | None = None
    organisation_id: str | None = None
    effective_from: datetime
    effective_to: datetime | None = None
    overrides: dict[str, object] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)


def _get_tenant_id(request: Request) -> str:
    ctx = getattr(request.state, "tenant_context", None)
    if ctx:
        return ctx.tenant_id
    return request.headers.get("X-Tenant-Id", "live")


def _stored_version(record: dict[str, object]) -> int:
    version = record.get("version", 1)
    if not isinstance(version, int):
        raise HTTPException(status_code=409, detail="Stored record version is invalid")
    return version


@router.get("")
async def list_frameworks(request: Request, jurisdictionId: list[str] = Query(default=[])) -> list[dict[str, object]]:
    tenant_id = _get_tenant_id(request)
    logger.info("list_frameworks tenant_id=%s jurisdictions=%s", tenant_id, jurisdictionId)
    service = PreparednessAnalysisService()
    if not jurisdictionId:
        return list(_FRAMEWORK_CATALOGUE.values())
    frameworks = service.list_frameworks_by_jurisdictions(jurisdictionId)
    return [fw.model_dump(mode="json") for fw in frameworks] + list(_FRAMEWORK_CATALOGUE.values())


@router.post("/management", dependencies=[Depends(authorize_management)])
async def create_framework(payload: ManagedFrameworkInput) -> dict[str, object]:
    if payload.framework_id in _FRAMEWORK_CATALOGUE:
        raise HTTPException(status_code=409, detail="Framework already exists")
    record = payload.model_dump(mode="json")
    _FRAMEWORK_CATALOGUE[payload.framework_id] = record
    return record


@router.put("/management/{framework_id}", dependencies=[Depends(authorize_management)])
async def update_framework(framework_id: str, payload: ManagedFrameworkInput) -> dict[str, object]:
    existing = _FRAMEWORK_CATALOGUE.get(framework_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Framework not found")
    if payload.version != _stored_version(existing):
        raise HTTPException(status_code=409, detail="Version conflict")
    updated = payload.model_dump(mode="json")
    updated["version"] = payload.version + 1
    _FRAMEWORK_CATALOGUE[framework_id] = updated
    return updated


@router.post("/management/assignments", dependencies=[Depends(authorize_management)])
async def create_assignment(payload: ManagedAssignmentInput) -> dict[str, object]:
    if payload.assignment_id in _ASSIGNMENT_CATALOGUE:
        raise HTTPException(status_code=409, detail="Assignment already exists")
    if payload.jurisdiction_id is None and payload.organisation_id is None:
        raise HTTPException(status_code=422, detail="Assignment scope requires jurisdiction_id or organisation_id")
    record = payload.model_dump(mode="json")
    _ASSIGNMENT_CATALOGUE[payload.assignment_id] = record
    return record


@router.put("/management/assignments/{assignment_id}", dependencies=[Depends(authorize_management)])
async def update_assignment(assignment_id: str, payload: ManagedAssignmentInput) -> dict[str, object]:
    existing = _ASSIGNMENT_CATALOGUE.get(assignment_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if payload.version != _stored_version(existing):
        raise HTTPException(status_code=409, detail="Version conflict")
    if payload.jurisdiction_id is None and payload.organisation_id is None:
        raise HTTPException(status_code=422, detail="Assignment scope requires jurisdiction_id or organisation_id")
    updated = payload.model_dump(mode="json")
    updated["version"] = payload.version + 1
    _ASSIGNMENT_CATALOGUE[assignment_id] = updated
    return updated
