from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Incident(BaseModel):
    incident_id: str
    title: str
    incident_type: Literal["bushfire", "flood", "cyclone", "storm", "earthquake", "other"]
    status: Literal["monitoring", "active", "stabilising", "recovery", "closed", "rehearsal"]
    severity: Literal["advisory", "watch", "warning", "emergency"]
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str] = Field(default_factory=list)
    owning_framework_ids: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
