"""Governance health score and constitutional gate status models.

New domain models for the governance dashboard feature (021).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DimensionScore(BaseModel):
    """Score for one of the four health score dimensions."""

    dimension: Literal[
        "constitutional_compliance",
        "operational_readiness",
        "data_source_governance",
        "recovery_progress",
    ]
    score: float = Field(ge=0.0, le=100.0, description="Dimension score 0-100")
    weight: float = Field(ge=0.0, le=1.0, description="Weight factor (must sum to 1.0)")
    weighted_score: float = Field(ge=0.0, le=100.0, description="score × weight")
    input_count: int = Field(ge=0, description="Number of inputs used for this dimension")
    stale: bool = Field(default=False, description="True if underlying data is older than cache TTL")


class GovernanceHealthScore(BaseModel):
    """Composite governance health score (0-100) with traffic light status."""

    id: str = Field(description="Unique score ID, format: health-score-{tenant_id}-{timestamp}")
    tenant_id: str = Field(description="Tenant context: 'live' or 'sim-{scenarioRunId}'")
    score: float = Field(ge=0.0, le=100.0, description="Composite score")
    status: Literal["green", "amber", "red"]
    dimensions: list[DimensionScore] = Field(min_length=4, max_length=4)
    calculated_at: datetime
    cache_ttl_s: int = Field(default=300, description="Cache time-to-live in seconds")
    has_active_incident: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_dimensions(self) -> "GovernanceHealthScore":
        weights_sum = sum(d.weight for d in self.dimensions)
        if abs(weights_sum - 1.0) > 0.01:
            msg = f"Dimension weights must sum to 1.0, got {weights_sum}"
            raise ValueError(msg)
        computed_score = sum(d.weighted_score for d in self.dimensions)
        if abs(computed_score - self.score) > 0.01:
            msg = f"Score {self.score} does not match sum of weighted scores {computed_score}"
            raise ValueError(msg)
        return self

    @staticmethod
    def derive_status(score: float) -> Literal["green", "amber", "red"]:
        """Derive traffic light status from score."""
        if score >= 80:
            return "green"
        if score >= 50:
            return "amber"
        return "red"


class ConstitutionalGateStatus(BaseModel):
    """Compliance status for one of the 10 constitutional gates."""

    gate_number: int = Field(ge=1, le=10, description="Gate 1-10")
    gate_name: str = Field(description="Human-readable gate name")
    status: Literal["compliant", "non_compliant", "partially_compliant", "assessment_pending"]
    severity: Literal["info", "warning", "critical"] | None = Field(
        default=None,
        description="Severity indicator for non-compliant/partially-compliant gates",
    )
    last_assessment_date: datetime | None = Field(default=None)
    evidence_count: int = Field(ge=0, default=0, description="Number of evidence artefacts")
    detail_url: str = Field(description="Navigation URL to detailed compliance view")
