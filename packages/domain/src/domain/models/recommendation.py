from typing import Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
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
