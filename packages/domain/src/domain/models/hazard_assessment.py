from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HazardMap(BaseModel):
    """Embedded hazard map within a HazardAssessment."""

    affected_area: dict[str, Any] = Field(
        ..., description="GeoJSON Polygon of affected area"
    )
    severity_level: Literal["low", "moderate", "high", "critical"]
    hazard_type: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    time_horizon: str = Field(..., description="e.g. '4h', '12h', '24h'")
    population_estimate: int | None = None


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

    # --- Extended fields (012-risk-assessment-agent) ---
    version: int = Field(default=1, ge=1)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_adjusted: float = Field(default=0.0, ge=0.0, le=1.0)
    severity_level: Literal["low", "moderate", "high", "critical"] = "moderate"
    valid_until: datetime | None = None
    status: Literal["active", "superseded", "expired"] = "active"
    generation_method: Literal["llm", "template_fallback", "safety_fallback"] = "llm"
    model_deployment_id: str | None = None
    prompt_template_version: str = "1.0"
    configuration_version: str = ""
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    contradiction_detected: bool = False
    contradiction_details: list[dict[str, Any]] | None = None
    stale_signal_ids: list[str] | None = None
    related_incident_ids: list[str] | None = None
    hazard_map: HazardMap | None = None
    incident_scope_key: str = ""
    tenant_id: str = "live"

    @model_validator(mode="after")
    def _validate_valid_until(self) -> "HazardAssessment":
        if self.valid_until is not None and self.valid_until <= self.generated_at:
            raise ValueError("valid_until must be after generated_at")
        return self
