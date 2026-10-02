import logging

from app.middleware.auth import authorize_management
from app.services.organisation_intelligence_service import OrganisationIntelligenceService
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/organisations", tags=["organisations"])
logger = logging.getLogger(__name__)

_ORG_CATALOGUE: dict[str, dict[str, object]] = {}
_PERSONA_CATALOGUE: dict[str, dict[str, object]] = {}
_JURISDICTION_CATALOGUE: dict[str, dict[str, object]] = {}


class ManagedOrganisationInput(BaseModel):
    organisation_id: str
    name: str
    category: str
    jurisdiction_ids: list[str] = Field(default_factory=list)
    operating_role: str
    authority_level: str
    version: int = Field(default=1, ge=1)


class ManagedPersonaInput(BaseModel):
    persona_id: str
    organisation_id: str
    jurisdiction_id: str
    display_name: str
    role: str
    version: int = Field(default=1, ge=1)


class ManagedJurisdictionInput(BaseModel):
    jurisdiction_id: str
    name: str
    level: str
    policy_set_id: str
    geometry_fidelity: str = "approximate"
    version: int = Field(default=1, ge=1)


def _get_tenant_id(request: Request) -> str:
    ctx = getattr(request.state, "tenant_context", None)
    if ctx:
        return ctx.tenant_id
    return request.headers.get("X-Tenant-Id", "live")


@router.get("")
async def list_organisations(
    request: Request, jurisdictionId: list[str] = Query(default=[])
) -> list[dict[str, object]]:
    tenant_id = _get_tenant_id(request)
    logger.info("list_organisations tenant_id=%s jurisdictions=%s", tenant_id, jurisdictionId)
    organisations = OrganisationIntelligenceService().list_organisations(jurisdictionId if jurisdictionId else None)
    base = [organisation.model_dump(mode="json") for organisation in organisations]
    if not jurisdictionId:
        return base + list(_ORG_CATALOGUE.values())

    scoped_managed = [
        organisation
        for organisation in _ORG_CATALOGUE.values()
        if any(jid in jurisdictionId for jid in organisation.get("jurisdiction_ids", []))
    ]
    return base + scoped_managed


@router.post("/management", dependencies=[Depends(authorize_management)])
async def create_organisation(payload: ManagedOrganisationInput) -> dict[str, object]:
    if payload.organisation_id in _ORG_CATALOGUE:
        raise HTTPException(status_code=409, detail="Organisation already exists")
    record = payload.model_dump(mode="json")
    _ORG_CATALOGUE[payload.organisation_id] = record
    return record


@router.put("/management/{organisation_id}", dependencies=[Depends(authorize_management)])
async def update_organisation(organisation_id: str, payload: ManagedOrganisationInput) -> dict[str, object]:
    existing = _ORG_CATALOGUE.get(organisation_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Organisation not found")
    if payload.version != int(existing.get("version", 1)):
        raise HTTPException(status_code=409, detail="Version conflict")
    updated = payload.model_dump(mode="json")
    updated["version"] = payload.version + 1
    _ORG_CATALOGUE[organisation_id] = updated
    return updated


@router.post("/management/personas", dependencies=[Depends(authorize_management)])
async def create_persona(payload: ManagedPersonaInput) -> dict[str, object]:
    if payload.persona_id in _PERSONA_CATALOGUE:
        raise HTTPException(status_code=409, detail="Persona already exists")
    record = payload.model_dump(mode="json")
    _PERSONA_CATALOGUE[payload.persona_id] = record
    return record


@router.put("/management/personas/{persona_id}", dependencies=[Depends(authorize_management)])
async def update_persona(persona_id: str, payload: ManagedPersonaInput) -> dict[str, object]:
    existing = _PERSONA_CATALOGUE.get(persona_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    if payload.version != int(existing.get("version", 1)):
        raise HTTPException(status_code=409, detail="Version conflict")
    updated = payload.model_dump(mode="json")
    updated["version"] = payload.version + 1
    _PERSONA_CATALOGUE[persona_id] = updated
    return updated


@router.post("/management/jurisdictions", dependencies=[Depends(authorize_management)])
async def create_jurisdiction(payload: ManagedJurisdictionInput) -> dict[str, object]:
    if payload.jurisdiction_id in _JURISDICTION_CATALOGUE:
        raise HTTPException(status_code=409, detail="Jurisdiction already exists")
    record = payload.model_dump(mode="json")
    _JURISDICTION_CATALOGUE[payload.jurisdiction_id] = record
    return record


@router.put("/management/jurisdictions/{jurisdiction_id}", dependencies=[Depends(authorize_management)])
async def update_jurisdiction(jurisdiction_id: str, payload: ManagedJurisdictionInput) -> dict[str, object]:
    existing = _JURISDICTION_CATALOGUE.get(jurisdiction_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    if payload.version != int(existing.get("version", 1)):
        raise HTTPException(status_code=409, detail="Version conflict")
    updated = payload.model_dump(mode="json")
    updated["version"] = payload.version + 1
    _JURISDICTION_CATALOGUE[jurisdiction_id] = updated
    return updated
