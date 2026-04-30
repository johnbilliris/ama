"""Platform API routes for recovery catalogue browsing.

Provides endpoints for listing outcomes, outcome detail, domain summaries,
activity suggestions, and evaluation question retrieval.

FRs: FR-015–024
"""

from app.services.recovery_catalogue_service import RecoveryCatalogueService
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/recovery-catalogue", tags=["recovery-catalogue"])
_service = RecoveryCatalogueService()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class SuggestActivitiesInput(BaseModel):
    lagging_indicator_ids: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/outcomes")
async def list_outcomes(
    domain: str | None = Query(None, description="Filter by domain"),
    objective_type: str | None = Query(None, description="Filter by objective type"),
) -> list[dict]:
    """List all recovery outcomes with optional domain/objective-type filter."""
    return await _service.list_outcomes(domain=domain, objective_type=objective_type)


@router.get("/outcomes/{outcome_id}")
async def get_outcome(outcome_id: str, domain: str = Query(..., description="Domain partition key")) -> dict:
    """Retrieve a single recovery outcome by ID."""
    result = await _service.get_outcome(outcome_id, domain)
    if not result:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
    return result


@router.get("/outcomes/{outcome_id}/activities")
async def get_activities_for_outcome(
    outcome_id: str,
    domain: str = Query(..., description="Domain partition key"),
) -> list[dict]:
    """List activities linked to a specific outcome."""
    return await _service.get_activities_for_outcome(outcome_id, domain)


@router.get("/outcomes/{outcome_id}/indicators")
async def get_indicators_for_outcome(
    outcome_id: str,
    domain: str = Query(..., description="Domain partition key"),
) -> list[dict]:
    """List indicators linked to a specific outcome."""
    return await _service.get_indicators_for_outcome(outcome_id, domain)


@router.get("/domains/{domain}/summary")
async def get_domain_summary(domain: str) -> dict:
    """Return aggregate counts for a recovery domain."""
    return await _service.get_domain_summary(domain)


@router.post("/suggest-activities")
async def suggest_activities(payload: SuggestActivitiesInput) -> list[dict]:
    """Suggest catalogue activities that address lagging indicators."""
    return await _service.suggest_activities(payload.lagging_indicator_ids)
