"""Platform API routes for AI-assisted recovery analysis.

Provides endpoints for cross-domain correlation analysis, activity
recommendations, and community summary generation.

FRs: FR-025–028
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.ai_analysis_service import AIAnalysisService

router = APIRouter(prefix="/analysis", tags=["ai-analysis"])
_service = AIAnalysisService()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CrossDomainAnalysisInput(BaseModel):
    indicator_data: list[dict]


class RecommendationsInput(BaseModel):
    lagging_indicator_ids: list[str]


class CommunitySummaryInput(BaseModel):
    indicator_data: list[dict]
    domain_filter: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/cross-domain")
async def cross_domain_analysis(payload: CrossDomainAnalysisInput) -> dict:
    """Analyse cross-domain correlations in recovery indicator data."""
    return await _service.cross_domain_analysis(payload.indicator_data)


@router.post("/recommendations")
async def recommend_activities(payload: RecommendationsInput) -> list[dict]:
    """Recommend AIDR catalogue activities for lagging indicators."""
    return await _service.recommend_activities(payload.lagging_indicator_ids)


@router.post("/community-summary")
async def community_summary(payload: CommunitySummaryInput) -> dict:
    """Generate a plain-language recovery summary for community communication."""
    return await _service.community_summary(
        payload.indicator_data,
        domain_filter=payload.domain_filter,
    )
