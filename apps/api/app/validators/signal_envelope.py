from typing import Any

from pydantic import BaseModel, Field


class SignalSourceEnvelope(BaseModel):
    dataSourceId: str
    name: str
    kind: str


class SignalEnvelope(BaseModel):
    source: SignalSourceEnvelope
    incidentId: str | None = None
    category: str
    occurredAt: str
    receivedAt: str
    jurisdictionId: str | None = None
    location: dict[str, Any]
    payload: dict[str, Any] = Field(default_factory=dict)
    confidenceScore: float
    freshnessScore: float
    validationStatus: str
    provenance: dict[str, Any] = Field(default_factory=dict)
