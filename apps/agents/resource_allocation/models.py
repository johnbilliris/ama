"""Resource Allocation Agent data models — Pydantic v2 models and enums per data-model.md.

Entities:
- DecisionType (16-value enum)
- ConfidenceLevel, PlanStatus, ResourceStatus, ResourceType enums
- DemandFulfilmentStatus, PriorityTier, UrgencyLevel enums
- ScoringRationale, DeploymentTimeline, ShortfallDetail, TradeOffAnalysis
- Traceability, OverrideMetadata, InputSnapshot (embedded support types)
- ResourceDemand, ResourceAssignment, ResourceInventoryItem
- ResourceDeploymentPlan (primary output)
- AllocationDecisionRecord (audit trail)
- AuditBufferEntry (degradation support)
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DecisionType(StrEnum):
    """All possible resource allocation decision types (16 values per data-model.md)."""

    handoff_received = "handoff_received"
    handoff_rejected = "handoff_rejected"
    duplicate_discarded = "duplicate_discarded"
    demand_identified = "demand_identified"
    resource_matched = "resource_matched"
    resource_excluded = "resource_excluded"
    partial_allocation = "partial_allocation"
    plan_generated = "plan_generated"
    plan_superseded = "plan_superseded"
    plan_expired = "plan_expired"
    override_applied = "override_applied"
    reallocation_recommended = "reallocation_recommended"
    transport_dispatched = "transport_dispatched"
    resource_status_updated = "resource_status_updated"
    degradation_detected = "degradation_detected"
    content_safety_failure = "content_safety_failure"


class ConfidenceLevel(StrEnum):
    """Discrete confidence level derived from numeric confidence score."""

    low = "low"
    medium = "medium"
    high = "high"


class PlanStatus(StrEnum):
    """Resource deployment plan lifecycle status."""

    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    superseded = "superseded"
    cancelled = "cancelled"
    expired = "expired"


class ResourceStatus(StrEnum):
    """Resource availability state machine (7 states)."""

    available = "available"
    reserved = "reserved"
    assigned = "assigned"
    en_route = "en_route"
    deployed = "deployed"
    returning = "returning"
    unavailable = "unavailable"


class ResourceType(StrEnum):
    """Resource category."""

    vehicle = "vehicle"
    personnel = "personnel"
    supply = "supply"
    facility = "facility"


class DemandFulfilmentStatus(StrEnum):
    """Demand fulfilment tracking status."""

    pending = "pending"
    partially_met = "partially_met"
    fully_met = "fully_met"
    unmet = "unmet"
    closed = "closed"


class PriorityTier(StrEnum):
    """Three-tier priority hierarchy."""

    tier_1_life_safety = "tier_1_life_safety"
    tier_2_property = "tier_2_property"
    tier_3_environment = "tier_3_environment"


class UrgencyLevel(StrEnum):
    """AIDR-aligned 4-level urgency."""

    critical = "critical"
    high = "high"
    moderate = "moderate"
    low = "low"


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
# Embedded Models
# ---------------------------------------------------------------------------


class ScoringRationale(BaseModel):
    """Per-assignment scoring explanation (9 fields)."""

    capability_match: float = 0.0
    distance_km: float = 0.0
    distance_factor: float = 0.0
    availability_factor: float = 0.0
    priority_weight: float = 0.0
    final_score: float = 0.0
    selection_reason: str = ""
    alternatives_considered: int = 0
    tie_break_applied: str | None = None


class DeploymentTimeline(BaseModel):
    """Estimated timeline per resource assignment (7 fields)."""

    assignment_id: str
    resource_id: str
    mobilisation_minutes: float = 0.0
    travel_minutes: float = 0.0
    total_deployment_minutes: float = 0.0
    estimated_departure: datetime = Field(default_factory=lambda: datetime.now(UTC))
    estimated_arrival: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ShortfallDetail(BaseModel):
    """Unmet/partially-met demand detail (8 fields)."""

    demand_id: str
    resource_type: ResourceType
    resource_sub_type: str = ""
    quantity_requested: int = 0
    quantity_assigned: int = 0
    quantity_unmet: int = 0
    reason: str = ""
    recommendation: str = ""


class TradeOffAnalysis(BaseModel):
    """Cross-incident trade-off details (6 fields)."""

    competing_incidents: list[str] = Field(default_factory=list)
    contested_resources: list[str] = Field(default_factory=list)
    allocations: list[dict[str, object]] = Field(default_factory=list)
    reallocation_recommendations: list[dict[str, object]] = Field(default_factory=list)
    impact_summary: str = ""
    requires_commander_approval: bool = True


class Traceability(BaseModel):
    """Provenance links (5 fields)."""

    handoff_id: str
    recommendation_id: str | None = None
    assessment_id: str | None = None
    evacuation_plan_id: str | None = None
    transport_requirement_ids: list[str] = Field(default_factory=list)


class OverrideMetadata(BaseModel):
    """Commander override details (6 fields)."""

    override_by_user_id: str
    override_by_role: str
    override_justification: str
    override_action_type: str
    override_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    original_plan_id: str = ""


class InputSnapshot(BaseModel):
    """Complete input data for reproducibility (5 fields)."""

    demands_snapshot: list[dict[str, object]] = Field(default_factory=list)
    inventory_snapshot_hash: str = ""
    inventory_staleness_minutes: float = 0.0
    config_version: str = ""
    scoring_parameters: dict[str, object] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Demand and Assignment
# ---------------------------------------------------------------------------


class ResourceDemand(BaseModel):
    """Identified resource demand extracted from handoff data."""

    demand_id: str
    incident_id: str
    source_id: str
    source_type: str  # coordination_task | transport_requirement
    resource_type: ResourceType
    resource_sub_type: str
    required_capabilities: list[str] = Field(default_factory=list)
    quantity: int = 1
    location: dict[str, object] = Field(default_factory=dict)
    estimated_individuals: int = Field(default=0, ge=0)
    destination_assembly_area_id: str = ""
    destination_assembly_area_name: str = ""
    destination_route_id: str = ""
    destination_resolved: bool = True
    unresolved_destination_reason: str | None = None
    origin_zone: int | None = Field(default=None, ge=1)
    phase_number: int | None = Field(default=None, ge=1)
    special_considerations: list[str] = Field(default_factory=list)
    count_basis: str = ""
    evacuation_plan_id: str = ""
    priority_tier: PriorityTier = PriorityTier.tier_2_property
    urgency: UrgencyLevel = UrgencyLevel.moderate
    urgency_raw: str | None = None
    fulfilment_status: DemandFulfilmentStatus = DemandFulfilmentStatus.pending
    handoff_id: str = ""
    incident_scope_key: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResourceAssignment(BaseModel):
    """Resource-to-demand assignment with scoring rationale."""

    assignment_id: str
    demand_id: str
    resource_id: str
    assignment_status: str = "proposed"
    score: float = 0.0
    scoring_rationale: ScoringRationale = Field(default_factory=ScoringRationale)
    estimated_travel_minutes: float = 0.0
    estimated_arrival_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mobilisation_minutes: float = 0.0
    distance_km: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Resource Inventory Item
# ---------------------------------------------------------------------------


class ResourceInventoryItem(BaseModel):
    """Resource in the inventory with state tracking."""

    resource_id: str
    resource_type: ResourceType
    resource_sub_type: str
    capabilities: list[str] = Field(default_factory=list)
    location: dict[str, object] = Field(default_factory=dict)
    status: ResourceStatus = ResourceStatus.available
    assigned_incident_id: str | None = None
    capacity: int | None = None
    initial_capacity: int | None = None
    last_status_update: datetime = Field(default_factory=lambda: datetime.now(UTC))
    managing_org_id: str | None = None
    flags: list[str] = Field(default_factory=list)
    continuous_deployment_hours: float = 0.0


# ---------------------------------------------------------------------------
# Primary Output: ResourceDeploymentPlan
# ---------------------------------------------------------------------------


class ResourceDeploymentPlan(BaseModel):
    """Versioned resource deployment plan (23 fields with validators)."""

    plan_id: str
    incident_id: str
    version: int = 1
    demands: list[ResourceDemand] = Field(default_factory=list)
    assignments: list[ResourceAssignment] = Field(default_factory=list)
    unmet_demands: list[ShortfallDetail] = Field(default_factory=list)
    deployment_timelines: list[DeploymentTimeline] = Field(default_factory=list)
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.medium
    status: PlanStatus = PlanStatus.proposed
    generation_method: str = "ai_assisted"
    configuration_version: str = ""
    input_snapshot: InputSnapshot = Field(default_factory=InputSnapshot)
    traceability: Traceability = Field(default_factory=lambda: Traceability(handoff_id=""))
    summary: str = ""
    trade_off_analysis: TradeOffAnalysis | None = None
    override_metadata: OverrideMetadata | None = None
    related_incident_ids: list[str] = Field(default_factory=list)
    expires_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    incident_scope_key: str = ""
    tenant_id: str = "live"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("plan_id")
    @classmethod
    def _validate_plan_id(cls, v: str) -> str:
        if not re.match(r"^rdp-.+-v\d+$", v):
            raise ValueError(f"plan_id must match rdp-{{incident_id}}-v{{N}}, got: {v}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"version must be >= 1, got: {v}")
        return v

    @field_validator("confidence_score")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @field_validator("confidence_level", mode="before")
    @classmethod
    def _derive_confidence_level(cls, v: object, info: object) -> object:
        """If confidence_level not explicitly set, derive from confidence_score."""
        return v


# ---------------------------------------------------------------------------
# Audit Record
# ---------------------------------------------------------------------------


class AllocationDecisionRecord(BaseModel):
    """Append-only audit trail record persisted to Cosmos DB.

    Partition key: ``incident_scope_key`` = ``{tenant_id}:{incident_id}``
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    handoff_id: str
    plan_id: str | None = None
    plan_version: int | None = None
    demand_id: str | None = None
    resource_id: str | None = None
    decision_type: DecisionType
    confidence_score: float = 0.0
    priority_tier: str | None = None
    urgency: str | None = None
    scoring_rationale: str | None = None
    resources_considered: int | None = None
    resources_excluded_reason: str | None = None
    processing_duration_ms: float = 0.0
    decision_rationale: str = ""
    generation_method: str = "algorithmic"
    override_by_user_id: str | None = None
    override_by_role: str | None = None
    override_justification: str | None = None
    agent_version: str = "0.1.0"
    configuration_version: str = ""
    incident_scope_key: str = ""
    tenant_id: str = "live"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    buffered_at: datetime | None = None
    flush_source: str | None = None

    @field_validator("confidence_score")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class AuditBufferEntry(BaseModel):
    """Temporary wrapper for audit records during Cosmos DB unavailability."""

    record: AllocationDecisionRecord
    buffered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry_at: datetime | None = None
