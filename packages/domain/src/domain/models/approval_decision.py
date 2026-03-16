from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ApprovalDecision(BaseModel):
    approval_decision_id: str
    recommendation_id: str | None = None
    public_alert_id: str | None = None
    approver_persona_id: str
    outcome: Literal["approved", "rejected", "escalated", "timed_out"]
    rationale: str
    conditions: list[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
