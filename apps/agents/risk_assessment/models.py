"""Risk Assessment Agent data models — Pydantic v2 models and enums per data-model.md.

Entities:
- DecisionType (12-value enum)
- AssessmentType, ConfidenceLevel, SeverityLevel enums
- RiskAssessmentDecisionRecord (audit trail entity, Cosmos DB)
- AuditBufferEntry (degradation support)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DecisionType(StrEnum):
    """All possible risk assessment decision types (12 values per data-model.md)."""

    handoff_received = "handoff_received"
    handoff_rejected = "handoff_rejected"
    duplicate_discarded = "duplicate_discarded"
    signals_retrieved = "signals_retrieved"
    assessment_generated = "assessment_generated"
    recommendation_generated = "recommendation_generated"
    handoff_created = "handoff_created"
    handoff_delivered = "handoff_delivered"
    handoff_dead_lettered = "handoff_dead_lettered"
    contradiction_detected = "contradiction_detected"
    degradation_detected = "degradation_detected"
    content_safety_failure = "content_safety_failure"


class AssessmentType(StrEnum):
    """Hazard assessment type derived from signal category."""

    spread_prediction = "spread_prediction"
    impact_projection = "impact_projection"
    route_risk = "route_risk"
    infrastructure_risk = "infrastructure_risk"
    community_impact = "community_impact"


class ConfidenceLevel(StrEnum):
    """Discrete confidence level derived from numeric confidence score."""

    low = "low"
    medium = "medium"
    high = "high"


class SeverityLevel(StrEnum):
    """AIDR-aligned 4-level severity."""

    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


# ---------------------------------------------------------------------------
# Helper: confidence → level
# ---------------------------------------------------------------------------


def confidence_to_level(score: float) -> ConfidenceLevel:
    """Map numeric confidence to discrete level.

    low: <0.4, medium: [0.4, 0.7), high: ≥0.7
    """
    if score < 0.4:
        return ConfidenceLevel.low
    if score < 0.7:
        return ConfidenceLevel.medium
    return ConfidenceLevel.high


# ---------------------------------------------------------------------------
# RiskAssessmentDecisionRecord
# ---------------------------------------------------------------------------


class RiskAssessmentDecisionRecord(BaseModel):
    """Append-only audit trail record persisted to Cosmos DB.

    Partition key: ``incident_scope_key`` = ``{tenant_id}:{incident_id}``
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    handoff_id: str
    input_signal_ids: list[str] = Field(default_factory=list)
    assessment_id: str | None = None
    recommendation_id: str | None = None
    hazard_type: str | None = None
    severity_level: str | None = None
    confidence_raw: float = 0.0
    confidence_adjusted: float = 0.0
    version: int | None = None
    decision_type: DecisionType
    model_id: str | None = None
    prompt_template_version: str = "1.0"
    processing_duration_ms: float = 0.0
    decision_rationale: str = ""
    generation_method: str = "llm"
    escalation_targets: list[str] = Field(default_factory=list)
    agent_version: str = "0.1.0"
    configuration_version: str = ""
    incident_scope_key: str = ""
    tenant_id: str = "live"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    buffered_at: datetime | None = None
    flush_source: str | None = None

    @field_validator("confidence_raw", "confidence_adjusted")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class AuditBufferEntry(BaseModel):
    """Temporary wrapper for audit records during Cosmos DB unavailability."""

    record: RiskAssessmentDecisionRecord
    buffered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry_at: datetime | None = None
