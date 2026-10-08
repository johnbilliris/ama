from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    approval_decision_id: str
    recommendation_id: str | None = None
    public_alert_id: str | None = None
    approver_persona_id: str
    outcome: Literal["approved", "rejected", "escalated", "timed_out"]
    rationale: str
    conditions: list[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def _validate_targets(self) -> "ApprovalDecision":
        has_recommendation = bool(self.recommendation_id)
        has_alert = bool(self.public_alert_id)
        if has_recommendation == has_alert:
            raise ValueError("Exactly one of recommendation_id or public_alert_id must be provided")
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        return self
