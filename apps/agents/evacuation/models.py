"""Evacuation Agent data models — Pydantic v2 models and enums per data-model.md.

Entities:
- DecisionType (15-value enum)
- ConfidenceLevel, PlanStatus, VulnerabilityCategory, ClosureReason enums
- Embedded models: EvacuationZone, EvacuationRoute, ExcludedRoad,
  TransportRequirement, EvacuationPhase, HazardSummary, Traceability,
  OverrideMetadata, DataSnapshot, AssemblyArea
- EvacuationPlan (primary planning entity)
- EvacuationDecisionRecord (audit trail entity, Cosmos DB)
- AuditBufferEntry (degradation support)
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


class DecisionType(StrEnum):
    """All possible evacuation decision types (15 values per data-model.md)."""

    handoff_received = "handoff_received"
    handoff_rejected = "handoff_rejected"
    duplicate_discarded = "duplicate_discarded"
    assessment_retrieved = "assessment_retrieved"
    road_network_loaded = "road_network_loaded"
    zones_computed = "zones_computed"
    routes_computed = "routes_computed"
    transport_coordinated = "transport_coordinated"
    timeline_estimated = "timeline_estimated"
    plan_generated = "plan_generated"
    plan_updated = "plan_updated"
    override_applied = "override_applied"
    shelter_in_place_recommended = "shelter_in_place_recommended"
    degradation_detected = "degradation_detected"
    content_safety_failure = "content_safety_failure"


class ConfidenceLevel(StrEnum):
    """Discrete confidence level derived from numeric confidence score."""

    low = "low"
    medium = "medium"
    high = "high"


class PlanStatus(StrEnum):
    """Lifecycle status of an evacuation plan (7 states)."""

    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    superseded = "superseded"
    expired = "expired"
    cancelled = "cancelled"
    paused = "paused"


class VulnerabilityCategory(StrEnum):
    """Categories of vulnerable populations requiring special transport."""

    mobility_impaired = "mobility_impaired"
    medical_dependent = "medical_dependent"
    elderly_aged_care = "elderly_aged_care"
    children_schools_childcare = "children_schools_childcare"


class ClosureReason(StrEnum):
    """Reasons a road segment may be excluded from evacuation routes."""

    emergency_services_closure = "emergency_services_closure"
    flood_cut = "flood_cut"
    fire_proximity = "fire_proximity"
    structural_damage = "structural_damage"
    zone_1_closure = "zone_1_closure"
    capacity_exhausted = "capacity_exhausted"


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
# Embedded models
# ---------------------------------------------------------------------------


class EvacuationZone(BaseModel):
    """Geographic zone within the evacuation area."""

    zone_id: str = ""
    zone_name: str = ""
    priority: int = 1
    population_estimate: int = 0
    vulnerability_categories: list[VulnerabilityCategory] = Field(default_factory=list)
    geometry_wkt: str | None = None
    # Fields used by ZoneComputer for Shapely-based zone computation
    zone_number: int = 0
    boundary: dict[str, object] = Field(default_factory=dict)
    vulnerable_population: int = 0
    evacuation_priority: str = ""
    status: str = ""


class ExcludedRoad(BaseModel):
    """Road segment excluded from route planning."""

    road_id: str
    road_name: str
    closure_reason: ClosureReason
    reported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvacuationRoute(BaseModel):
    """A single evacuation route from zone to assembly area."""

    route_id: str
    zone_id: str
    assembly_area_id: str
    route_name: str
    distance_km: float = 0.0
    estimated_travel_minutes: int = 0
    capacity_vehicles_per_hour: int = 0
    congestion_risk_pct: int = 0
    excluded_roads: list[ExcludedRoad] = Field(default_factory=list)
    waypoints: list[str] = Field(default_factory=list)


class AssemblyArea(BaseModel):
    """Designated assembly/staging area for evacuees."""

    assembly_area_id: str
    name: str
    capacity: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    accessible: bool = True
    shelter_available: bool = False


class TransportRequirement(BaseModel):
    """Transport resource needed for a specific vulnerability category."""

    category: VulnerabilityCategory
    vehicle_type: str
    quantity_required: int = 0
    estimated_trips: int = 1
    notes: str = ""


class EvacuationPhase(BaseModel):
    """Phased evacuation timeline entry."""

    phase_number: int
    zone_ids: list[str] = Field(default_factory=list)
    start_offset_minutes: int = 0
    duration_minutes: int = 0
    population_moved: int = 0
    transport_requirements: list[TransportRequirement] = Field(default_factory=list)
    description: str = ""


class HazardSummary(BaseModel):
    """Summary of the hazard driving the evacuation."""

    hazard_type: str
    severity_level: str = ""
    affected_area_km2: float = 0.0
    direction_of_travel: str = ""
    estimated_arrival_minutes: int | None = None
    source_assessment_id: str | None = None


class Traceability(BaseModel):
    """Provenance and lineage information for audit compliance."""

    source_handoff_id: str
    risk_assessment_id: str | None = None
    input_data_versions: dict[str, str] = Field(default_factory=dict)
    model_id: str | None = None
    prompt_template_version: str = "1.0"
    generation_method: str = "llm"


class OverrideMetadata(BaseModel):
    """Metadata captured when an authorised user overrides a plan."""

    override_by: str
    override_reason: str
    override_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    previous_values: dict[str, object] = Field(default_factory=dict)


class DataSnapshot(BaseModel):
    """Point-in-time snapshot of data sources used to generate the plan."""

    road_network_version: str = ""
    population_data_version: str = ""
    weather_data_timestamp: datetime | None = None
    hazard_data_timestamp: datetime | None = None
    snapshot_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# EvacuationPlan (primary entity)
# ---------------------------------------------------------------------------


class EvacuationPlan(BaseModel):
    """Primary evacuation plan entity — persisted to Cosmos DB.

    Partition key: ``incident_scope_key`` = ``{tenant_id}:{incident_id}``
    """

    plan_id: str
    incident_id: str
    version: int = 1
    status: PlanStatus = PlanStatus.proposed
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.low
    hazard_summary: HazardSummary | None = None
    zones: list[EvacuationZone] = Field(default_factory=list)
    routes: list[EvacuationRoute] = Field(default_factory=list)
    assembly_areas: list[AssemblyArea] = Field(default_factory=list)
    phases: list[EvacuationPhase] = Field(default_factory=list)
    transport_requirements: list[TransportRequirement] = Field(default_factory=list)
    total_population: int = 0
    estimated_completion_minutes: int = 0
    mobilisation_time_minutes: int = 0
    shelter_in_place_zones: list[str] = Field(default_factory=list)
    traceability: Traceability | None = None
    data_snapshot: DataSnapshot | None = None
    overrides: list[OverrideMetadata] = Field(default_factory=list)
    summary: str = ""
    incident_scope_key: str = ""
    tenant_id: str = "live"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("confidence_score")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @field_validator("version")
    @classmethod
    def _version_gte_one(cls, v: int) -> int:
        if v < 1:
            raise ValueError("version must be >= 1")
        return v

    @field_validator("plan_id")
    @classmethod
    def _validate_plan_id(cls, v: str) -> str:
        if not re.match(r"^ep-.+-v\d+$", v):
            raise ValueError("plan_id must match format ep-{incident_id}-v{N}")
        return v

    @model_validator(mode="after")
    def _derive_confidence_level(self) -> EvacuationPlan:
        self.confidence_level = confidence_to_level(self.confidence_score)
        return self


# ---------------------------------------------------------------------------
# EvacuationDecisionRecord
# ---------------------------------------------------------------------------


class EvacuationDecisionRecord(BaseModel):
    """Append-only audit trail record persisted to Cosmos DB.

    Partition key: ``incident_scope_key`` = ``{tenant_id}:{incident_id}``
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    handoff_id: str
    plan_id: str | None = None
    incident_id: str | None = None
    hazard_type: str | None = None
    zone_ids: list[str] = Field(default_factory=list)
    route_ids: list[str] = Field(default_factory=list)
    population_affected: int = 0
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

    record: EvacuationDecisionRecord
    buffered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry_at: datetime | None = None
