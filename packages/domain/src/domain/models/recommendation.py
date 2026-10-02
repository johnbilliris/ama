from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Recommendation(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    recommendation_id: str
    incident_id: str
    type: Literal["evacuation", "resource_allocation", "coordination", "public_alert", "infrastructure_action"]
    summary: str
    explanation: str
    supporting_signal_ids: list[str] = Field(default_factory=list)
    required_approval_level: str
    confidence_level: Literal["low", "medium", "high"] = "medium"
    status: Literal["proposed", "under_review", "approved", "rejected", "escalated", "executed", "expired"] = "proposed"
    proposed_by_agent: str = "risk_assessment"
    generation_method: Literal["llm", "template", "template_fallback", "safety_fallback"] = "template"
    model_deployment_id: str | None = None
    token_usage: dict[str, int] | None = None

    # --- Extended fields (012-risk-assessment-agent) ---
    assessment_id: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    severity_level: Literal["low", "moderate", "high", "critical"] = "moderate"
    override_by_user_id: str | None = None
    override_by_role: str | None = None
    override_justification: str | None = None
    override_timestamp: datetime | None = None
    incident_scope_key: str = ""
    tenant_id: str = "live"

    @field_validator("confidence_score")
    @classmethod
    def _validate_confidence_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v
