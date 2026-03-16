from fastapi import APIRouter

from app.services.preparedness_analysis_service import PreparednessAnalysisService

router = APIRouter(prefix="/frameworks", tags=["frameworks"])


@router.get("")
async def list_frameworks(jurisdictionId: str | None = None) -> list[dict[str, object]]:
    analysis = PreparednessAnalysisService().analyse("flood", [jurisdictionId] if jurisdictionId else ["nsw"])
    return analysis["frameworks"]
