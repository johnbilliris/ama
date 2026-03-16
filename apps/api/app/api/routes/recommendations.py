from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.recommendation_service import RecommendationService
from app.services.state_store import RECOMMENDATIONS

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class ApprovalDecisionInput(BaseModel):
    approverPersonaId: str
    outcome: str
    rationale: str
    conditions: list[str] = Field(default_factory=list)


@router.post("/{recommendation_id}/approvals")
async def record_approval(recommendation_id: str, payload: ApprovalDecisionInput) -> dict[str, object]:
    if recommendation_id not in RECOMMENDATIONS:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    decision = RecommendationService().record_approval(
        recommendation_id=recommendation_id,
        approver_persona_id=payload.approverPersonaId,
        outcome=payload.outcome,
        rationale=payload.rationale,
        conditions=payload.conditions,
    )
    return decision.model_dump(mode="json")
