"""Monitoring Agent data models — Pydantic v2 models and enums per data-model.md.

Entities:
- DecisionType (9-value enum)
- FreshnessStatus / SourceType enums
- MonitoringDecisionRecord (audit trail entity, Cosmos DB)
- DataFreshnessIndicator (in-memory per-source freshness)
- AuditBufferEntry (degradation support)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DecisionType(StrEnum):
    """All possible monitoring decision types (9 values per data-model.md)."""

    summarised = "summarised"
    escalated = "escalated"
    blocked = "blocked"
    handed_off = "handed_off"
    held_for_review = "held_for_review"
    associated = "associated"
    degradation_detected = "degradation_detected"
    discarded = "discarded"
    validation_failed = "validation_failed"


class FreshnessStatus(StrEnum):
    """Data source freshness health status."""

    healthy = "healthy"
    degraded = "degraded"
    offline = "offline"


class SourceType(StrEnum):
    """Data source classification."""

    authoritative = "authoritative"
    iot = "iot"
    social = "social"


# ---------------------------------------------------------------------------
# MonitoringDecisionRecord
# ---------------------------------------------------------------------------


class MonitoringDecisionRecord(BaseModel):
    """Append-only audit trail record persisted to Cosmos DB.

    Partition key: ``incident_scope_key`` = ``{tenant_id}:{incident_id}``
    or ``{tenant_id}:unassociated:{hash}``.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    signal_id: str
    decision: DecisionType
    confidence: float
    effective_confidence: float | None = None
    freshness_score: float | None = None
    inputs: dict[str, object] = Field(default_factory=dict)
    output: dict[str, object] = Field(default_factory=dict)
    agent_version: str = "0.1.0"
    reasoning_summary: str = ""
    llm_classification: str | None = None
    content_safety_result: str | None = None
    incident_scope_key: str = ""
    tenant_id: str = "live"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    buffered_at: datetime | None = None
    flush_source: str | None = None


# ---------------------------------------------------------------------------
# DataFreshnessIndicator
# ---------------------------------------------------------------------------


class DataFreshnessIndicator(BaseModel):
    """Per-source freshness tracker (in-memory, emitted as metrics)."""

    data_source_id: str
    source_type: SourceType
    last_signal_received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    current_freshness_score: float = 1.0
    staleness_threshold_minutes: int = 15
    status: FreshnessStatus = FreshnessStatus.healthy
    last_status_change_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class AuditBufferEntry(BaseModel):
    """Temporary wrapper for audit records during Cosmos DB unavailability."""

    record: MonitoringDecisionRecord
    buffered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry_at: datetime | None = None


# ---------------------------------------------------------------------------
# M&E Framework request/response models (FRs: FR-008–014)
# ---------------------------------------------------------------------------


class CreateMEFrameworkRequest(BaseModel):
    """Request to create a new M&E framework for an incident programme."""

    incident_id: str
    program_name: str
    affected_community_definition: str = ""
    created_by: str = ""


class SelectOutcomesRequest(BaseModel):
    """Request to select outcomes from the catalogue for a framework."""

    outcomes: list[dict[str, object]]  # [{catalogue_outcome_id, domain, objective_type, community_restatement?}]


class CreateProgramLogicRequest(BaseModel):
    """Request to create a program logic model for a framework."""

    model_type: str = "ex_ante"
    resources_inputs: list[dict[str, object]] = []
    activities: list[dict[str, object]] = []
    outputs: list[dict[str, object]] = []
    intermediate_outcomes: list[dict[str, object]] = []
    final_outcomes: list[dict[str, object]] = []
    outcome_chain_links: list[dict[str, object]] = []
    timeline_months: int | None = None


class SetStandardsRequest(BaseModel):
    """Request to set standards of success for selected indicators."""

    standards: list[
        dict[str, object]
    ]  # [{catalogue_outcome_id, indicator_id, threshold_value, threshold_operator, ...}]


class SetCollectionScheduleRequest(BaseModel):
    """Request to set an indicator data-collection schedule."""

    schedules: list[dict[str, object]]  # [{indicator_id, frequency, next_due_date}]


class MonitoringReportResponse(BaseModel):
    """Response for a monitoring report snapshot."""

    framework_id: str
    incident_id: str
    indicators_status: list[dict[str, object]]
    overdue_indicators: list[str]
    staleness_warnings: list[str]
    generated_at: str


class CreateEvaluationRequest(BaseModel):
    """Request to generate an evaluation report."""

    evaluation_period_start: str
    evaluation_period_end: str
    generated_by: str = "manual"
    created_by: str = ""


class EvaluationReportResponse(BaseModel):
    """Response for a generated evaluation report."""

    report_id: str
    framework_id: str
    domain_findings: dict[str, object]
    summary: str
    recommendations: list[dict[str, object]]
    generated_by: str
    created_at: str
