from typing import Literal

from app.core.auth import require_authenticated_persona
from app.services.operational_store import OperationalStore
from app.services.recommendation_service import RecommendationService
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class ApprovalDecisionInput(BaseModel):
    approverPersonaId: str | None = None
    outcome: Literal["approved", "rejected", "escalated", "timed_out"]
    rationale: str = Field(min_length=1)
    conditions: list[str] = Field(default_factory=list)


@router.post("/{recommendation_id}/approvals")
async def record_approval(
    recommendation_id: str,
    payload: ApprovalDecisionInput,
    request: Request,
) -> dict[str, object]:
    if not OperationalStore.current().recommendations.contains(recommendation_id):
        raise HTTPException(status_code=404, detail="Recommendation not found")

    actor_persona_id = require_authenticated_persona(request, payload.approverPersonaId)

    decision = RecommendationService().record_approval(
        recommendation_id=recommendation_id,
        approver_persona_id=actor_persona_id,
        outcome=payload.outcome,
        rationale=payload.rationale,
        conditions=payload.conditions,
        approver_roles=tuple(getattr(request.state, "claims", {}).get("roles", [])),
    )
    request.state.audit_outcome = decision.outcome
    return decision.model_dump(mode="json")
