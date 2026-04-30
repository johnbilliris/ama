import logging
from pathlib import Path

from app.services.seed_service import SeedService
from fastapi import APIRouter, Request

from packages.domain.src.domain.models.jurisdiction import Jurisdiction

router = APIRouter(prefix="/jurisdictions", tags=["jurisdictions"])
logger = logging.getLogger(__name__)

LEVEL_ORDER = {"commonwealth": 0, "state": 1, "territory": 2, "regional": 3, "local": 4}


def _get_tenant_id(request: Request) -> str:
    ctx = getattr(request.state, "tenant_context", None)
    if ctx:
        return ctx.tenant_id
    return request.headers.get("X-Tenant-Id", "live")


@router.get("")
async def list_jurisdictions(request: Request) -> list[dict[str, object]]:
    tenant_id = _get_tenant_id(request)
    logger.info("list_jurisdictions tenant_id=%s", tenant_id)
    from packages.domain.src.domain.seed import bootstrap as _seed_mod

    seed_root = Path(_seed_mod.__file__).resolve().parent
    seeds = SeedService().load(seed_root)
    jurisdictions = [Jurisdiction(**item) for item in seeds["jurisdictions"]]
    active = [j for j in jurisdictions if j.status == "active"]
    active.sort(key=lambda j: (LEVEL_ORDER.get(j.level, 99), j.name))
    return [
        {
            "jurisdiction_id": j.jurisdiction_id,
            "name": j.name,
            "level": j.level,
        }
        for j in active
    ]
