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
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DecisionType(str, Enum):
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


class FreshnessStatus(str, Enum):
    """Data source freshness health status."""

    healthy = "healthy"
    degraded = "degraded"
    offline = "offline"


class SourceType(str, Enum):
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
    inputs: dict = Field(default_factory=dict)
    output: dict = Field(default_factory=dict)
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
