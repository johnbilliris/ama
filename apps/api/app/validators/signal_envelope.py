from typing import Any

from pydantic import BaseModel, Field, field_validator


class SignalSourceEnvelope(BaseModel):
    dataSourceId: str
    name: str
    kind: str

    @field_validator("dataSourceId")
    @classmethod
    def data_source_id_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("dataSourceId must be non-empty")
        return v

    @field_validator("kind")
    @classmethod
    def kind_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("kind must be non-empty")
        return v


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

    @field_validator("category")
    @classmethod
    def category_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("category must be non-empty")
        return v

    @field_validator("confidenceScore")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidenceScore must be in range [0.0, 1.0]")
        return v

    @field_validator("freshnessScore")
    @classmethod
    def freshness_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("freshnessScore must be in range [0.0, 1.0]")
        return v
