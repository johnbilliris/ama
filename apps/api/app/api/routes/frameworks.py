from app.services.preparedness_analysis_service import PreparednessAnalysisService
from fastapi import APIRouter, Query, Request
import logging

router = APIRouter(prefix="/frameworks", tags=["frameworks"])
logger = logging.getLogger(__name__)


def _get_tenant_id(request: Request) -> str:
    ctx = getattr(request.state, "tenant_context", None)
    if ctx:
        return ctx.tenant_id
    return request.headers.get("X-Tenant-Id", "live")


@router.get("")
async def list_frameworks(request: Request, jurisdictionId: list[str] = Query(default=[])) -> list[dict[str, object]]:
    tenant_id = _get_tenant_id(request)
    logger.info("list_frameworks tenant_id=%s jurisdictions=%s", tenant_id, jurisdictionId)
    service = PreparednessAnalysisService()
    if not jurisdictionId:
        return []
    frameworks = service.list_frameworks_by_jurisdictions(jurisdictionId)
    return [fw.model_dump(mode="json") for fw in frameworks]
