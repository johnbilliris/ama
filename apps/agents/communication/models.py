"""Communication Agent data models — Pydantic v2 models and enums per data-model.md.

Entities:
- 10 enums (AlertStatus, ChangeType, ChannelType, DeliveryStatus, GenerationMethod,
  ContentSafetyResult, ApprovalMode, UrgencyLevel, SegmentPriority, CommunicationDecisionType)
- 7 entity/embedded models (ContentBlock, ContentSafetyDetail, EscalationEvent,
  AudienceSegment, DeliveryRecord, PublicAlert, CommunicationDecisionRecord)
- 1 support type (AuditBufferEntry)
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AlertStatus(StrEnum):
    """Alert lifecycle states (10 values per data-model.md)."""

    drafting = "drafting"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    delivering = "delivering"
    delivered = "delivered"
    partially_delivered = "partially_delivered"
    superseded = "superseded"
    expired = "expired"
    cancelled = "cancelled"


# Valid state transitions per data-model.md state machine
VALID_STATUS_TRANSITIONS: dict[AlertStatus, set[AlertStatus]] = {
    AlertStatus.drafting: {AlertStatus.pending_review, AlertStatus.cancelled},
    AlertStatus.pending_review: {AlertStatus.approved, AlertStatus.rejected, AlertStatus.cancelled},
    AlertStatus.approved: {AlertStatus.delivering, AlertStatus.cancelled},
    AlertStatus.rejected: set(),
    AlertStatus.delivering: {AlertStatus.delivered, AlertStatus.partially_delivered},
    AlertStatus.delivered: {AlertStatus.superseded, AlertStatus.expired},
    AlertStatus.partially_delivered: {AlertStatus.superseded, AlertStatus.expired},
    AlertStatus.superseded: set(),
    AlertStatus.expired: set(),
    AlertStatus.cancelled: set(),
}


class ChangeType(StrEnum):
    """Alert version change types (4 values)."""

    initial = "initial"
    update = "update"
    correction = "correction"
    all_clear = "all_clear"


class ChannelType(StrEnum):
    """Delivery channel types (3 values)."""

    sms = "sms"
    push = "push"
    emergency_broadcast = "emergency_broadcast"


class DeliveryStatus(StrEnum):
    """Per-channel delivery status (5 values)."""

    pending = "pending"
    in_progress = "in_progress"
    delivered = "delivered"
    failed = "failed"
    retrying = "retrying"


class GenerationMethod(StrEnum):
    """How content was generated (4 values)."""

    llm = "llm"
    template = "template"
    template_fallback = "template_fallback"
    safety_fallback = "safety_fallback"


class ContentSafetyResult(StrEnum):
    """Overall content safety validation result (3 values)."""

    passed = "passed"
    failed_with_fallback = "failed_with_fallback"
    not_checked = "not_checked"


class ApprovalMode(StrEnum):
    """How the alert was approved (2 values)."""

    human_approved = "human_approved"
    escalated = "escalated"


class UrgencyLevel(StrEnum):
    """Zone-based urgency level (3 values)."""

    immediate = "immediate"
    watch = "watch"
    advisory = "advisory"


class SegmentPriority(StrEnum):
    """Audience segment priority (3 values)."""

    critical = "critical"
    high = "high"
    moderate = "moderate"


class CommunicationDecisionType(StrEnum):
    """All possible communication decision types (18 values per data-model.md)."""

    handoff_received = "handoff_received"
    handoff_rejected = "handoff_rejected"
    duplicate_discarded = "duplicate_discarded"
    alert_drafted = "alert_drafted"
    content_safety_evaluated = "content_safety_evaluated"
    back_translation_below_threshold = "back_translation_below_threshold"
    alert_versioned = "alert_versioned"
    approval_requested = "approval_requested"
    approval_action = "approval_action"
    escalation_triggered = "escalation_triggered"
    delivery_initiated = "delivery_initiated"
    delivery_succeeded = "delivery_succeeded"
    delivery_failed = "delivery_failed"
    audience_segmented = "audience_segmented"
    degradation_detected = "degradation_detected"
    content_safety_failure = "content_safety_failure"
    health_status_changed = "health_status_changed"
    template_fallback = "template_fallback"


# ---------------------------------------------------------------------------
# Embedded Models
# ---------------------------------------------------------------------------

ALLOWED_VULNERABILITY_CATEGORIES = {"aged_care", "hospital", "school", "disability_services"}


class ContentBlock(BaseModel):
    """Alert content for a single language."""

    language_code: str
    title: str = Field(max_length=200)
    body: str = Field(max_length=1200)
    action_items: str = Field(max_length=500)
    generation_method: GenerationMethod = GenerationMethod.llm
    content_safety_result: str = "passed"
    content_safety_failure_reason: str | None = None
    back_translation_score: float | None = None
    back_translation_flagged: bool = False
    translation_unavailable: bool = False


class ContentSafetyDetail(BaseModel):
    """Per-language content safety result."""

    language_code: str
    passed: bool
    failure_reason: str | None = None
    original_text_length: int = 0
    fallback_used: bool = False


class EscalationEvent(BaseModel):
    """Records a single escalation in the approval workflow."""

    level: int = Field(ge=1, le=3)
    from_commander_id: str
    to_commander_id: str | None = None
    elapsed_minutes: float = Field(ge=0.0)
    escalated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    held_for_next_available: bool = False


class AudienceSegment(BaseModel):
    """Audience targeting entity — defines a group of recipients."""

    segment_id: str = Field(default_factory=lambda: uuid4().hex)
    alert_id: str = ""
    zone_level: int = Field(ge=1, le=3)
    zone_boundary: dict = Field(default_factory=dict)
    population_estimate: int = Field(ge=0, default=0)
    estimated_segment_size: int = Field(ge=0, default=0)
    vulnerability_categories: list[str] = Field(default_factory=list)
    preferred_language: str = "en-AU"
    urgency_level: UrgencyLevel = UrgencyLevel.advisory
    priority: SegmentPriority = SegmentPriority.moderate
    delivery_channels: list[ChannelType] = Field(default_factory=list)
    missing_data_flags: list[str] = Field(default_factory=list)

    @field_validator("vulnerability_categories")
    @classmethod
    def _validate_vulnerability_categories(cls, v: list[str]) -> list[str]:
        for cat in v:
            if cat not in ALLOWED_VULNERABILITY_CATEGORIES:
                raise ValueError(
                    f"Invalid vulnerability category '{cat}'. "
                    f"Allowed: {ALLOWED_VULNERABILITY_CATEGORIES}"
                )
        return v

    @model_validator(mode="after")
    def _vulnerable_must_be_critical(self) -> AudienceSegment:
        if self.vulnerability_categories and self.priority != SegmentPriority.critical:
            raise ValueError(
                "Segments with vulnerability_categories must have priority=critical"
            )
        return self


class DeliveryRecord(BaseModel):
    """Delivery tracking entity — one record per alert × segment × channel."""

    delivery_id: str = Field(default_factory=lambda: uuid4().hex)
    alert_id: str
    alert_version: int = Field(ge=1)
    channel: ChannelType
    audience_segment_id: str
    language_used: str = "en-AU"
    delivery_status: DeliveryStatus = DeliveryStatus.pending
    attempt_count: int = Field(ge=0, default=0)
    max_retries: int = 3
    retry_backoff_intervals: list[float] = Field(default_factory=lambda: [1.0, 2.0, 4.0])
    failure_reason: str | None = None
    content_payload: str = ""
    segment_count: int | None = None
    is_deduplicated: bool = False
    deduplicated_by_segment_id: str | None = None
    initiated_at: datetime | None = None
    completed_at: datetime | None = None
    delivery_duration_ms: int | None = None
    tenant_id: str = "live"


# ---------------------------------------------------------------------------
# Primary Entity — PublicAlert
# ---------------------------------------------------------------------------

_ALERT_ID_PATTERN = re.compile(r"^ca-[a-zA-Z0-9_-]+-v\d+$")


class PublicAlert(BaseModel):
    """Primary output entity — a versioned, multilingual public alert."""

    alert_id: str
    incident_id: str
    version: int = Field(ge=1)
    status: AlertStatus = AlertStatus.drafting
    change_type: ChangeType = ChangeType.initial
    change_summary: str | None = None
    referenced_alert_id: str | None = None
    content_blocks: dict[str, ContentBlock] = Field(default_factory=dict)
    audience_segments: list[str] = Field(default_factory=list)
    languages: list[str] = Field(
        default_factory=lambda: ["en-AU", "zh-Hans", "ar", "vi", "el", "it"]
    )
    accessibility_attributes: list[str] = Field(default_factory=lambda: ["plain-language"])
    channel_set: list[ChannelType] = Field(default_factory=list)
    generation_method: GenerationMethod = GenerationMethod.llm
    model_deployment_id: str | None = None
    content_safety_result: ContentSafetyResult = ContentSafetyResult.passed
    content_safety_details: dict[str, ContentSafetyDetail] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    approval_mode: ApprovalMode | None = None
    approved_by_user_id: str | None = None
    approved_by_role: str | None = None
    approval_action: str | None = None
    approval_justification: str | None = None
    approved_at: datetime | None = None
    escalation_level: int = Field(ge=0, le=3, default=0)
    escalation_history: list[EscalationEvent] = Field(default_factory=list)
    recommendation_id: str = ""
    assessment_id: str = ""
    tenant_id: str = "live"
    published_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    _etag: str | None = None

    @field_validator("alert_id")
    @classmethod
    def _validate_alert_id(cls, v: str) -> str:
        if not _ALERT_ID_PATTERN.match(v):
            raise ValueError(
                f"alert_id must match pattern ^ca-[a-zA-Z0-9_-]+-v\\d+$, got '{v}'"
            )
        return v

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @model_validator(mode="after")
    def _validate_alert_rules(self) -> PublicAlert:
        # content_blocks must contain en-AU
        if self.content_blocks and "en-AU" not in self.content_blocks:
            raise ValueError("content_blocks must contain 'en-AU' key")

        # change_summary required for non-initial
        if self.change_type != ChangeType.initial and not self.change_summary:
            raise ValueError("change_summary is required for non-initial change_type")

        # referenced_alert_id required for correction and all_clear
        if self.change_type in (ChangeType.correction, ChangeType.all_clear):
            if not self.referenced_alert_id:
                raise ValueError(
                    f"referenced_alert_id is required for change_type={self.change_type.value}"
                )

        # approval_justification required when rejection
        if self.approval_action == "reject" and not self.approval_justification:
            raise ValueError("approval_justification is required when approval_action is 'reject'")

        return self


# ---------------------------------------------------------------------------
# Audit Entity — CommunicationDecisionRecord
# ---------------------------------------------------------------------------


class CommunicationDecisionRecord(BaseModel):
    """Append-only audit trail record persisted to Cosmos DB.

    Partition key: ``/tenant_id``
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    handoff_id: str | None = None
    alert_id: str | None = None
    delivery_id: str | None = None
    decision_type: CommunicationDecisionType
    content_safety_results: dict[str, str] | None = None
    generation_method: str | None = None
    confidence: float | None = None
    confidence_penalties_applied: list[str] | None = None
    processing_duration_ms: int | None = None
    agent_version: str = "0.1.0"
    config_version: str = ""
    input_snapshot: dict | None = None
    output_summary: str | None = None
    escalation_details: dict | None = None
    degradation_details: dict | None = None
    flush_source: str | None = None
    tenant_id: str = "live"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    buffered_at: datetime | None = None

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float | None) -> float | None:
        if v is not None:
            return max(0.0, min(1.0, v))
        return v


# ---------------------------------------------------------------------------
# Audit Buffer Entry
# ---------------------------------------------------------------------------


class AuditBufferEntry(BaseModel):
    """Temporary wrapper for audit records during Cosmos DB unavailability."""

    record: CommunicationDecisionRecord
    buffered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry_at: datetime | None = None


# ---------------------------------------------------------------------------
# AWS Warning Request / Response (Phase 3 — US1)
# ---------------------------------------------------------------------------


class AwsWarningRequest(BaseModel):
    """Request payload to build an AWS three-tier warning alert."""

    incident_id: str
    warning_tier: str = Field(
        ..., pattern=r"^(advice|watch_and_act|emergency_warning)$"
    )
    hazard_type: str
    affected_areas: list[str] = Field(default_factory=list)
    action_statement_override: str | None = None
    supersedes_alert_id: str | None = None
    is_all_clear: bool = False
    tier_skip_justification: str | None = None
    approval_user_id: str | None = None


class AwsWarningResponse(BaseModel):
    """Response payload after creating an AWS warning alert."""

    alert_id: str
    warning_tier: str | None = None
    colour_code: str | None = None
    hazard_icon: str | None = None
    action_statement: str | None = None
    principles_checklist: dict[str, bool] = Field(default_factory=dict)
    chain_position: int = 1
    generation_method: str = "template"
