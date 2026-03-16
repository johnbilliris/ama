from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HazardAssessment(BaseModel):
    hazard_assessment_id: str
    incident_id: str
    assessment_type: Literal[
        "spread_prediction",
        "impact_projection",
        "route_risk",
        "infrastructure_risk",
        "community_impact",
    ]
    input_signal_ids: list[str] = Field(default_factory=list)
    summary: str
    confidence_level: Literal["low", "medium", "high"]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
