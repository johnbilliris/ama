import logging

from app.services.organisation_intelligence_service import OrganisationIntelligenceService
from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/organisations", tags=["organisations"])
logger = logging.getLogger(__name__)


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
    return [organisation.model_dump(mode="json") for organisation in organisations]
