from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Signal(BaseModel):
    signal_id: str
    incident_id: str | None = None
    data_source_id: str
    category: Literal[
        "weather",
        "hydrology",
        "fire",
        "geohazard",
        "infrastructure",
        "community_report",
        "social_report",
        "resource_status",
    ]
    occurred_at: datetime
    received_at: datetime
    jurisdiction_id: str | None = None
    location: dict[str, Any]
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float
    freshness_score: float
    validation_status: Literal["pending", "validated", "contradicted", "rejected", "escalated"]
    provenance: dict[str, Any] = Field(default_factory=dict)
