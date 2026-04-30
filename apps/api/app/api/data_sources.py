from uuid import uuid4

from app.services.governance_registry import GovernanceRegistryService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.domain.src.domain.models.data_source import DataSource, DataSourceKind, TrustTier

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])

_service = GovernanceRegistryService()


class DataSourceRegistration(BaseModel):
    name: str
    kind: DataSourceKind
    sub_category: str = ""
    provider: str = ""
    collection_method: str = ""
    data_type: str = ""
    update_frequency: str = ""
    geographic_coverage: str = ""
    trust_tier: TrustTier = "tier_7_derived_computed"


class DataSourceUpdate(BaseModel):
    name: str | None = None
    sub_category: str | None = None
    provider: str | None = None
    collection_method: str | None = None
    data_type: str | None = None
    update_frequency: str | None = None
    geographic_coverage: str | None = None
    trust_tier: TrustTier | None = None
    status: str | None = None


@router.post("", status_code=201)
async def register_data_source(body: DataSourceRegistration) -> dict:
    source = DataSource(
        data_source_id=f"ds-{uuid4().hex[:12]}",
        **body.model_dump(),
    )
    saved = _service.register_source(source, actor_id="api-user")
    return saved.model_dump(mode="json")


@router.get("")
async def list_data_sources(
    kind: DataSourceKind | None = None,
    sub_category: str | None = None,
    trust_tier: TrustTier | None = None,
    compliance_status: str | None = None,
    governance_status: str | None = None,
    status: str | None = None,
    geographic_coverage: str | None = None,
) -> list[dict]:
    filters = {
        k: v
        for k, v in {
            "kind": kind,
            "sub_category": sub_category,
            "trust_tier": trust_tier,
            "compliance_status": compliance_status,
            "governance_status": governance_status,
            "status": status,
            "geographic_coverage": geographic_coverage,
        }.items()
        if v is not None
    }
    sources = _service.list_sources(**filters)
    return [s.model_dump(mode="json") for s in sources]


@router.get("/{data_source_id}")
async def get_data_source(data_source_id: str) -> dict:
    source = _service.get_source(data_source_id)
    return source.model_dump(mode="json")


@router.patch("/{data_source_id}")
async def update_data_source(data_source_id: str, body: DataSourceUpdate) -> dict:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    saved = _service.update_source(data_source_id, updates, actor_id="api-user")
    return saved.model_dump(mode="json")


@router.post("/{data_source_id}/deactivate")
async def deactivate_data_source(data_source_id: str) -> dict:
    saved = _service.deactivate_source(data_source_id, actor_id="api-user")
    return saved.model_dump(mode="json")
