from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Signal(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

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
    owning_agency_id: str | None = None
    source_name: str | None = None
    source_kind: str | None = None
    trust_tier: str | None = None
    source_timestamp: datetime | None = None
    raw_payload_uri: str | None = None
    classification: Literal["public", "official", "official_sensitive"]
    pii_fields: list[str] = Field(default_factory=list)
    retention_until: datetime
    confidence_score: float
    freshness_score: float
    validation_status: Literal["pending", "validated", "contradicted", "rejected", "escalated"]
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_invariants(self) -> "Signal":
        if self.received_at < self.occurred_at:
            raise ValueError("received_at must be greater than or equal to occurred_at")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        if not 0.0 <= self.freshness_score <= 1.0:
            raise ValueError("freshness_score must be between 0.0 and 1.0")
        if self.retention_until < self.received_at:
            raise ValueError("retention_until must be greater than or equal to received_at")
        return self
