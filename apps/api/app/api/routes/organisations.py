from app.services.organisation_intelligence_service import OrganisationIntelligenceService
from fastapi import APIRouter

router = APIRouter(prefix="/organisations", tags=["organisations"])


@router.get("")
async def list_organisations(jurisdictionId: str | None = None) -> list[dict[str, object]]:
    organisations = OrganisationIntelligenceService().list_organisations(jurisdictionId)
    return [organisation.model_dump(mode="json") for organisation in organisations]
