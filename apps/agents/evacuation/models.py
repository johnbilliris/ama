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

import math
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


class PlanGenerationMethod(StrEnum):
    """Canonical summary generation outcomes for persisted plans."""

    ai_assisted = "ai_assisted"
    template_fallback = "template_fallback"
    safety_fallback = "safety_fallback"


class ReplanningTrigger(StrEnum):
    """Canonical trigger names stored in plan-update audit records."""

    new_road_closure = "new_road_closure"
    hazard_expansion = "hazard_expansion"
    progress_delay = "progress_delay"
    severity_escalation = "severity_escalation"
    manual_trigger = "manual_trigger"
    shelter_to_evacuation_recovery = "shelter_to_evacuation_recovery"


class ZoneDispositionType(StrEnum):
    """Operational disposition assigned to each evacuation zone."""

    evacuation = "evacuation"
    shelter_in_place = "shelter_in_place"
    partial_evacuation = "partial_evacuation"
    emergency_escalation = "emergency_escalation"


class OriginCoverageStatus(StrEnum):
    """Road-origin coverage for an exclusive zone population."""

    unassigned = "unassigned"
    covered = "covered"
    no_network_origin = "no_network_origin"
    not_required = "not_required"


class RoutingMode(StrEnum):
    """Completeness of deterministic hazard routing inputs."""

    hazard_aware = "hazard_aware"
    hazard_constrained_degraded = "hazard_constrained_degraded"


class HandoffClaimStatus(StrEnum):
    """Durable processing lifecycle for one scoped handoff."""

    processing = "processing"
    completed = "completed"
    rejected = "rejected"
    abandoned = "abandoned"


class VulnerabilityCategory(StrEnum):
    """Categories of vulnerable populations requiring special transport."""

    mobility_impaired = "mobility_impaired"
    medical_dependent = "medical_dependent"
    elderly_aged_care = "elderly_aged_care"
    children_schools_childcare = "children_schools_childcare"


class TransportPriority(StrEnum):
    """Operational priority for a vulnerable transport request."""

    critical = "critical"
    immediate = "immediate"
    high = "high"


class TransportCoordinationStatus(StrEnum):
    """Completeness of vulnerable transport coordination."""

    complete = "complete"
    partial = "partial"
    unavailable = "unavailable"


class TransportExclusionReason(StrEnum):
    """Why an identified facility did not create a mandatory request."""

    advisory_only = "advisory_only"
    outside_affected_area = "outside_affected_area"
    invalid_location = "invalid_location"
    unknown_category = "unknown_category"
    invalid_population = "invalid_population"
    no_destination = "no_destination"


class PhasePopulationType(StrEnum):
    """Population cohort represented by one evacuation phase."""

    vulnerable = "vulnerable"
    general = "general"
    advisory = "advisory"


class PhaseTransitionTrigger(StrEnum):
    """Modeled event that permits the next phase to begin."""

    population_threshold = "population_threshold"
    time_threshold = "time_threshold"
    phase_completion = "phase_completion"
    zero_population = "zero_population"
    blocked = "blocked"


class ClosureReason(StrEnum):
    """Reasons a road segment may be excluded from evacuation routes."""

    emergency_services_closure = "emergency_services_closure"
    flood_cut = "flood_cut"
    fire_proximity = "fire_proximity"
    structural_damage = "structural_damage"
    zone_1_closure = "zone_1_closure"
    capacity_exhausted = "capacity_exhausted"
    unspecified = "unspecified"


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
    population_estimate: int = Field(default=0, ge=0)
    vulnerability_categories: list[VulnerabilityCategory] = Field(default_factory=list)
    geometry_wkt: str | None = None
    # Fields used by ZoneComputer for Shapely-based zone computation
    zone_number: int = 0
    boundary: dict[str, object] = Field(default_factory=dict)
    membership_boundary: dict[str, object] = Field(default_factory=dict)
    vulnerable_population: int = Field(default=0, ge=0)
    evacuation_priority: str = ""
    status: str = ""
    origin_node_ids: list[str] = Field(default_factory=list)
    origin_coverage_status: OriginCoverageStatus = OriginCoverageStatus.unassigned
    unallocated_route_population: int = Field(default=0, ge=0)
    unallocated_vulnerable_population: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _validate_membership_counts(self) -> EvacuationZone:
        if self.vulnerable_population > self.population_estimate:
            raise ValueError("vulnerable population cannot exceed zone population")
        if len(self.origin_node_ids) != len(set(self.origin_node_ids)):
            raise ValueError("origin nodes must be unique within a zone")
        return self


class HazardRoutingContext(BaseModel):
    """Validated active-hazard inputs used by deterministic routing policy."""

    hazard_types: list[str] = Field(default_factory=list)
    source_assessment_ids: list[str] = Field(default_factory=list)
    incident_scope_key: str = ""
    bushfire_exclusion_areas: list[dict[str, object]] = Field(default_factory=list)
    wind_from_degrees: float | None = Field(default=None, ge=0, lt=360)
    policy_version: str = "hazard-routing-v1"


class HazardRoutingAttributes(BaseModel):
    """Optional validated routing attributes from an assessment snapshot."""

    wind_from_degrees: float | None = Field(default=None, ge=0, lt=360)


class ExcludedRoad(BaseModel):
    """Road segment excluded from route planning."""

    road_id: str = ""
    edge_id: str = ""
    road_name: str
    closure_reason: ClosureReason
    exclusion_reason: str = ""
    source_hazard_type: str | None = None
    reported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def _synchronise_edge_id(self) -> ExcludedRoad:
        if self.road_id and self.edge_id and self.road_id != self.edge_id:
            raise ValueError("edge_id and road_id must match")
        identifier = self.edge_id or self.road_id
        if not identifier:
            raise ValueError("excluded road requires an edge identifier")
        self.edge_id = identifier
        self.road_id = identifier
        return self


class DestinationExclusion(BaseModel):
    """Assembly area rejected by deterministic hazard safety policy."""

    assembly_area_id: str
    assembly_area_name: str
    reason: str
    source_hazard_type: str


class HazardPreferenceEvidence(BaseModel):
    """Soft hazard preference applied to one edge in a selected path."""

    edge_id: str
    reason: str
    source_hazard_type: str
    multiplier: float = Field(gt=1)


class VehicleSuitability(BaseModel):
    """Machine-readable vehicle suitability across a route's edges."""

    standard: bool = True
    heavy: bool = True
    accessible: bool = False


class EvacuationRoute(BaseModel):
    """A single evacuation route from zone to assembly area."""

    route_id: str
    zone_id: str
    origin_zone: int = 0
    origin_node_id: str = ""
    assembly_area_id: str
    destination_assembly_area: str = ""
    route_name: str
    distance_km: float = 0.0
    total_distance_km: float = 0.0
    estimated_travel_minutes: int = 0
    estimated_travel_time_normal_min: float = Field(default=0.0, ge=0)
    estimated_travel_time_loaded_min: float = Field(default=0.0, ge=0)
    capacity_vehicles_per_hour: int = 0
    congestion_risk_pct: int = 0
    excluded_roads: list[ExcludedRoad] = Field(default_factory=list)
    waypoints: list[str] = Field(default_factory=list)
    path: list[str] = Field(default_factory=list)
    node_path: list[str] = Field(default_factory=list)
    allocated_population: int = Field(default=0, ge=0)
    evacuation_load_vehicles_per_hour: float = Field(default=0.0, ge=0)
    uncapped_utilisation_pct: float = Field(default=0.0, ge=0)
    estimated_utilisation_pct: float = Field(default=0.0, ge=0)
    congestion_risk: bool = False
    capacity_overloaded: bool = False
    bottleneck_edge_ids: list[str] = Field(default_factory=list)
    zone_shared_capacity_vehicles_per_hour: int = Field(default=0, ge=0)
    selection_rationale: str = ""
    routing_mode: RoutingMode = RoutingMode.hazard_constrained_degraded
    hazard_data_gaps: list[str] = Field(default_factory=list)
    hazard_risk_score: float = Field(default=0.0, ge=0)
    hazard_preference_evidence: list[HazardPreferenceEvidence] = Field(default_factory=list)
    vehicle_suitability: VehicleSuitability = Field(default_factory=VehicleSuitability)

    @model_validator(mode="after")
    def _synchronise_compatibility_fields(self) -> EvacuationRoute:
        if self.path and self.waypoints and self.path != self.waypoints:
            raise ValueError("path and waypoints must match")
        self.path = list(self.path or self.waypoints)
        self.waypoints = list(self.waypoints or self.path)

        parsed_zone = int(self.zone_id) if self.zone_id.isdigit() else 0
        if self.origin_zone and parsed_zone and self.origin_zone != parsed_zone:
            raise ValueError("origin_zone and zone_id must match")
        self.origin_zone = self.origin_zone or parsed_zone

        if self.destination_assembly_area and self.destination_assembly_area != self.assembly_area_id:
            raise ValueError("destination_assembly_area and assembly_area_id must match")
        self.destination_assembly_area = self.destination_assembly_area or self.assembly_area_id

        if (
            self.total_distance_km
            and self.distance_km
            and not math.isclose(
                self.total_distance_km,
                self.distance_km,
            )
        ):
            raise ValueError("total_distance_km and distance_km must match")
        self.total_distance_km = self.total_distance_km or self.distance_km
        self.distance_km = self.distance_km or self.total_distance_km

        if self.estimated_travel_time_loaded_min == 0 and self.estimated_travel_minutes:
            self.estimated_travel_time_loaded_min = float(self.estimated_travel_minutes)
        if self.estimated_utilisation_pct == 0 and self.uncapped_utilisation_pct:
            self.estimated_utilisation_pct = self.uncapped_utilisation_pct
        return self


class CorridorLoad(BaseModel):
    """Plan-wide traffic ledger for one physical road edge."""

    edge_id: str
    capacity_vehicles_per_hour: int = Field(ge=0)
    current_traffic_load_vehicles_per_hour: float = Field(ge=0)
    evacuation_load_vehicles_per_hour: float = Field(ge=0)
    total_load_vehicles_per_hour: float = Field(ge=0)
    uncapped_utilisation_pct: float = Field(ge=0)
    capacity_overloaded: bool
    route_ids: list[str] = Field(default_factory=list)


class AssemblyArea(BaseModel):
    """Designated assembly/staging area for evacuees."""

    assembly_area_id: str
    name: str
    capacity: int = 0
    current_occupancy: int | None = Field(default=None, ge=0)
    residual_capacity: int | None = Field(default=None, ge=0)
    assigned_population: int = Field(default=0, ge=0)
    assigned_vulnerable_population: int = Field(default=0, ge=0)
    assigned_zones: list[int] = Field(default_factory=list)
    latitude: float = 0.0
    longitude: float = 0.0
    accessible: bool = False
    shelter_available: bool = False
    accessibility_features: list[str] = Field(default_factory=list)
    shelter_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _reconcile_capacity(self) -> AssemblyArea:
        if self.assigned_vulnerable_population > self.assigned_population:
            raise ValueError("assigned vulnerable population cannot exceed assigned population")
        if self.current_occupancy is not None:
            expected_residual = self.capacity - self.current_occupancy - self.assigned_population
            if expected_residual < 0:
                raise ValueError("assembly assignment exceeds verified capacity")
            if self.residual_capacity != expected_residual:
                raise ValueError("assembly residual capacity does not reconcile")
        elif self.residual_capacity is not None:
            raise ValueError("residual capacity requires known occupancy")
        return self


class DestinationAllocation(BaseModel):
    """Population assigned to one reachable assembly area from one zone."""

    assembly_area_id: str
    assembly_area_name: str
    zone_number: int = Field(ge=1)
    assigned_population: int = Field(ge=0)
    assigned_vulnerable_population: int = Field(ge=0)
    residual_capacity_before: int = Field(ge=0)
    residual_capacity_after: int = Field(ge=0)
    route_ids: list[str] = Field(default_factory=list)
    accessibility_features: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _reconcile_assignment(self) -> DestinationAllocation:
        if self.assigned_vulnerable_population > self.assigned_population:
            raise ValueError("destination vulnerable population cannot exceed assignment")
        if self.residual_capacity_before - self.assigned_population != self.residual_capacity_after:
            raise ValueError("destination residual capacity does not reconcile")
        return self


class UnresolvedDestinationDemand(BaseModel):
    """Population that cannot be assigned to a verified destination."""

    zone_number: int = Field(ge=1)
    population: int = Field(ge=0)
    vulnerable_population: int = Field(default=0, ge=0)
    reason: str
    details: str

    @model_validator(mode="after")
    def _validate_vulnerable_subset(self) -> UnresolvedDestinationDemand:
        if self.vulnerable_population > self.population:
            raise ValueError("unresolved vulnerable population cannot exceed total")
        return self


class TransportRequirement(BaseModel):
    """Transport resource needed for a specific vulnerability category."""

    requirement_id: str = ""
    facility_id: str = ""
    facility_name: str = ""
    category: VulnerabilityCategory
    vehicle_type: str
    estimated_individuals: int = Field(default=0, ge=0)
    quantity_required: int = Field(default=0, ge=0)
    estimated_trips: int = Field(default=1, ge=1)
    pickup_location: dict[str, float] = Field(default_factory=dict)
    destination_assembly_area_id: str = ""
    destination_assembly_area_name: str = ""
    destination_route_id: str = ""
    destination_resolved: bool = True
    unresolved_destination_reason: str | None = None
    priority_level: TransportPriority = TransportPriority.high
    origin_zone: int = Field(default=0, ge=0)
    phase_number: int | None = Field(default=None, ge=1)
    special_considerations: list[str] = Field(default_factory=list)
    count_basis: str = "facility_capacity"
    dispatch_authorized: bool = False
    notes: str = ""

    def to_resource_allocation_payload(self) -> dict[str, object]:
        """Return the strict Resource Allocation handoff shape."""
        return {
            "requirementId": self.requirement_id,
            "vehicleType": self.vehicle_type,
            "quantity": self.quantity_required,
            "pickupLocation": {
                "lat": self.pickup_location.get("lat"),
                "lon": self.pickup_location.get("lng"),
            },
            "priority": self.priority_level.value,
            "estimatedIndividuals": self.estimated_individuals,
            "facilityId": self.facility_id,
            "facilityName": self.facility_name,
            "destinationAssemblyAreaId": self.destination_assembly_area_id,
            "destinationAssemblyAreaName": self.destination_assembly_area_name,
            "destinationRouteId": self.destination_route_id,
            "destinationResolved": self.destination_resolved,
            "unresolvedDestinationReason": self.unresolved_destination_reason,
            "originZone": self.origin_zone,
            "phaseNumber": self.phase_number,
            "specialConsiderations": self.special_considerations,
            "countBasis": self.count_basis,
            "dispatchAuthorized": False,
        }


class TransportGroupExclusion(BaseModel):
    """Identified vulnerable facility excluded from mandatory transport."""

    facility_id: str
    facility_name: str
    estimated_individuals: int = Field(default=0, ge=0)
    reason: TransportExclusionReason
    zone_number: int | None = Field(default=None, ge=1)
    details: str


class TransportCoordinationResult(BaseModel):
    """Requests plus coverage and gap evidence for one plan."""

    status: TransportCoordinationStatus
    requirements: list[TransportRequirement] = Field(default_factory=list)
    exclusions: list[TransportGroupExclusion] = Field(default_factory=list)
    identified_population_by_zone: dict[int, int] = Field(default_factory=dict)
    uncovered_vulnerable_population_by_zone: dict[int, int] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)


class EvacuationPhase(BaseModel):
    """Phased evacuation timeline entry."""

    phase_number: int
    zone_ids: list[str] = Field(default_factory=list)
    zone_number: int = 0
    population_type: PhasePopulationType = PhasePopulationType.general
    estimated_population: int = Field(default=0, ge=0)
    routable_population: int = Field(default=0, ge=0)
    start_offset_minutes: float = Field(default=0.0, ge=0)
    duration_minutes: float | None = Field(default=0.0, ge=0)
    completion_offset_minutes: float | None = Field(default=None, ge=0)
    mobilisation_minutes: float = Field(default=0.0, ge=0)
    travel_minutes: float = Field(default=0.0, ge=0)
    clearance_minutes: float | None = Field(default=0.0, ge=0)
    effective_capacity_vehicles_per_hour: int = Field(default=0, ge=0)
    estimated_departure_rate_people_per_minute: float = Field(default=0.0, ge=0)
    population_transition_threshold: int = Field(default=0, ge=0)
    population_transition_offset_minutes: float | None = Field(default=None, ge=0)
    time_transition_offset_minutes: float | None = Field(default=None, ge=0)
    selected_transition_offset_minutes: float | None = Field(default=None, ge=0)
    selected_transition_trigger: PhaseTransitionTrigger = PhaseTransitionTrigger.phase_completion
    transition_delay_minutes: float = Field(default=0.0, ge=0)
    is_empty: bool = False
    buffer_multiplier: float = Field(default=1.0, ge=1.0)
    buffered_transport_population: int = Field(default=0, ge=0)
    route_edge_ids: list[str] = Field(default_factory=list)
    route_allocation_snapshot: dict[str, int] = Field(default_factory=dict)
    zone_shared_capacity_vehicles_per_hour: int = Field(default=0, ge=0)
    starts_at: datetime | None = None
    completes_at: datetime | None = None
    transition_at: datetime | None = None
    population_moved: int = 0
    population_remaining: int = 0
    clearance_blocked: bool = False
    transport_requirements: list[TransportRequirement] = Field(default_factory=list)
    description: str = ""

    @model_validator(mode="after")
    def _validate_timeline(self) -> EvacuationPhase:
        reconciled_population = self.population_moved + self.population_remaining
        if self.estimated_population == 0 and reconciled_population:
            self.estimated_population = reconciled_population
        if reconciled_population != self.estimated_population:
            raise ValueError("phase moved and remaining populations must reconcile")
        if self.routable_population > self.estimated_population:
            raise ValueError("routable population cannot exceed phase population")
        if self.buffered_transport_population > self.routable_population:
            raise ValueError("buffered transport population exceeds routable population")
        self.is_empty = self.estimated_population == 0
        if self.duration_minutes is None:
            if self.completion_offset_minutes is not None:
                raise ValueError("blocked phase cannot have a completion offset")
        else:
            expected_completion = self.start_offset_minutes + self.duration_minutes
            if self.completion_offset_minutes is None:
                self.completion_offset_minutes = expected_completion
            elif not math.isclose(
                self.completion_offset_minutes,
                expected_completion,
            ):
                raise ValueError("phase completion does not match start plus duration")
        if (
            self.selected_transition_offset_minutes is not None
            and self.selected_transition_offset_minutes < self.start_offset_minutes
        ):
            raise ValueError("phase transition cannot precede phase start")
        for timestamp in (self.starts_at, self.completes_at, self.transition_at):
            if timestamp is not None and timestamp.tzinfo is None:
                raise ValueError("phase timestamps must be timezone-aware")
        return self


class HazardSourceSnapshot(BaseModel):
    """Immutable active-hazard input used for one plan derivation."""

    assessment_id: str
    version: int = Field(default=1, ge=1)
    hazard_type: str
    severity_level: str
    affected_area: dict[str, object]
    input_signal_ids: list[str] = Field(default_factory=list)
    generated_at: datetime
    valid_until: datetime | None = None
    buffer_radius_metres: float = Field(gt=0)
    geometry_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    routing_attributes: HazardRoutingAttributes = Field(default_factory=HazardRoutingAttributes)


class HazardSummary(BaseModel):
    """Summary of the hazard driving the evacuation."""

    hazard_type: str
    hazard_types: list[str] = Field(default_factory=list)
    severity_level: str = ""
    time_horizon: str = ""
    affected_area_km2: float = 0.0
    direction_of_travel: str = ""
    estimated_arrival_minutes: int | None = None
    source_assessment_id: str | None = None
    affected_area: dict[str, object] = Field(default_factory=dict)
    sources: list[HazardSourceSnapshot] = Field(default_factory=list)
    population_estimate: int | None = Field(default=None, ge=0)


class Traceability(BaseModel):
    """Provenance and lineage information for audit compliance."""

    source_handoff_id: str
    risk_assessment_id: str | None = None
    risk_assessment_ids: list[str] = Field(default_factory=list)
    recommendation_id: str | None = None
    input_signal_ids: list[str] = Field(default_factory=list)
    input_data_versions: dict[str, str] = Field(default_factory=dict)
    model_id: str | None = None
    prompt_template_version: str = "1.0"
    generation_method: PlanGenerationMethod = PlanGenerationMethod.template_fallback


class OverrideMetadata(BaseModel):
    """Metadata captured when an authorised user overrides a plan."""

    override_by_user_id: str
    override_by_role: str
    override_justification: str
    override_action_type: str
    override_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_plan_id: str | None = None
    original_values: dict[str, object] = Field(default_factory=dict)
    modified_values: dict[str, object] = Field(default_factory=dict)


class ShelterRequirements(BaseModel):
    """Minimum safety requirements for populations that cannot evacuate."""

    building: list[str] = Field(default_factory=list)
    supplies: list[str] = Field(default_factory=list)
    communication: list[str] = Field(default_factory=list)


class ZoneDisposition(BaseModel):
    """Structured movement or shelter outcome for one zone population."""

    zone_id: str
    zone_number: int
    disposition: ZoneDispositionType
    urgency: str
    affected_population: int = Field(ge=0)
    evacuating_population: int = Field(ge=0)
    remaining_population: int = Field(ge=0)
    origin_coverage_status: OriginCoverageStatus = OriginCoverageStatus.unassigned
    clearance_deficit_minutes: int = Field(default=0, ge=0)
    prerequisites: list[str] = Field(default_factory=list)
    shelter_requirements: ShelterRequirements = Field(default_factory=ShelterRequirements)
    rationale: str
    emergency_notification_id: str | None = None
    emergency_notification_receipt: str | None = None

    @model_validator(mode="after")
    def _reconcile_population(self) -> ZoneDisposition:
        if self.evacuating_population + self.remaining_population != self.affected_population:
            raise ValueError("evacuating and remaining populations must reconcile")
        if self.disposition == ZoneDispositionType.evacuation and self.remaining_population:
            raise ValueError("evacuation disposition cannot retain a population")
        if (
            self.disposition
            in {
                ZoneDispositionType.shelter_in_place,
                ZoneDispositionType.emergency_escalation,
            }
            and self.evacuating_population
        ):
            raise ValueError("blocked-zone disposition cannot move a population")
        return self

    @property
    def recommended(self) -> bool:
        return self.disposition == ZoneDispositionType.shelter_in_place

    @property
    def is_emergency_escalation(self) -> bool:
        return self.disposition == ZoneDispositionType.emergency_escalation


class EmergencyNotification(BaseModel):
    """Internal maximum-urgency request for authorized operator action."""

    notification_id: str
    handoff_id: str
    incident_id: str
    incident_scope_key: str
    tenant_id: str
    zone_id: str
    affected_population: int = Field(ge=0)
    urgency: str = "maximum"
    target: str = "emergency_services_operator"
    public_order_authorized: bool = False
    rationale: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HandoffProcessingClaim(BaseModel):
    """Replica-safe claim stored beside plans in the incident partition."""

    id: str
    handoff_id: str
    incident_id: str
    tenant_id: str
    incident_scope_key: str
    owner_id: str
    status: HandoffClaimStatus = HandoffClaimStatus.processing
    claimed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    lease_expires_at: datetime
    completed_at: datetime | None = None
    plan_id: str | None = None
    failure_reason: str | None = None
    ttl: int = Field(gt=0)


class DataSnapshot(BaseModel):
    """Point-in-time snapshot of data sources used to generate the plan."""

    road_network_version: str = ""
    population_data_version: str = ""
    facility_data_version: str = ""
    assembly_area_data_version: str = ""
    population_data_available: bool = False
    facility_data_available: bool = False
    assembly_area_data_available: bool = False
    population_record_ids: list[str] = Field(default_factory=list)
    facility_record_ids: list[str] = Field(default_factory=list)
    assembly_area_record_ids: list[str] = Field(default_factory=list)
    population_record_count: int = Field(default=0, ge=0)
    facility_record_count: int = Field(default=0, ge=0)
    assembly_area_record_count: int = Field(default=0, ge=0)
    road_data_status: str = "freshness_unknown"
    road_source_updated_at: datetime | None = None
    road_source_age_hours: float | None = Field(default=None, ge=0)
    population_data_status: str = "unavailable"
    population_source_updated_at: datetime | None = None
    population_source_age_hours: float | None = Field(default=None, ge=0)
    facility_data_status: str = "unavailable"
    facility_source_updated_at: datetime | None = None
    facility_source_age_hours: float | None = Field(default=None, ge=0)
    road_refresh_failure_reason: str = ""
    weather_data_timestamp: datetime | None = None
    hazard_data_timestamp: datetime | None = None
    hazard_assessment_ids: list[str] = Field(default_factory=list)
    hazard_geometry_algorithm: str = ""
    snapshot_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConfidenceAdjustment(BaseModel):
    """One multiplicative confidence reduction with an auditable reason."""

    reason: str
    factor: float = Field(gt=0, le=1)


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
    affected_area: dict[str, object] = Field(default_factory=dict)
    routing_mode: RoutingMode = RoutingMode.hazard_constrained_degraded
    hazard_routing_data_gaps: list[str] = Field(default_factory=list)
    excluded_destinations: list[DestinationExclusion] = Field(default_factory=list)
    excluded_roads: list[ExcludedRoad] = Field(default_factory=list)
    unavailable_roads_by_reason: dict[str, int] = Field(default_factory=dict)
    zero_route_zones: list[int] = Field(default_factory=list)
    corridor_loads: list[CorridorLoad] = Field(default_factory=list)
    zones: list[EvacuationZone] = Field(default_factory=list)
    routes: list[EvacuationRoute] = Field(default_factory=list)
    assembly_areas: list[AssemblyArea] = Field(default_factory=list)
    destination_allocations: list[DestinationAllocation] = Field(default_factory=list)
    unresolved_destination_demands: list[UnresolvedDestinationDemand] = Field(default_factory=list)
    phases: list[EvacuationPhase] = Field(default_factory=list)
    transport_requirements: list[TransportRequirement] = Field(default_factory=list)
    transport_coordination_status: TransportCoordinationStatus = TransportCoordinationStatus.unavailable
    transport_exclusions: list[TransportGroupExclusion] = Field(default_factory=list)
    identified_transport_population_by_zone: dict[int, int] = Field(default_factory=dict)
    uncovered_vulnerable_population_by_zone: dict[int, int] = Field(default_factory=dict)
    population_estimate: int = Field(ge=0)
    total_population: int = 0
    estimated_completion_minutes: int | None = 0
    mobilisation_time_minutes: int = 0
    shelter_in_place_zones: list[str] = Field(default_factory=list)
    zone_dispositions: list[ZoneDisposition] = Field(default_factory=list)
    traceability: Traceability | None = None
    data_snapshot: DataSnapshot | None = None
    assumptions: list[str] = Field(default_factory=list)
    data_quality_gaps: list[str] = Field(default_factory=list)
    confidence_adjustments: list[ConfidenceAdjustment] = Field(default_factory=list)
    immediate_human_review_required: bool = False
    generic_guidance: str = ""
    generation_method: PlanGenerationMethod
    summary_grounding_result: str = "deterministic"
    content_safety_result: str = "not_checked"
    content_safety_validation_method: str = ""
    content_safety_reason: str = ""
    content_safety_reference: str = ""
    model_deployment_id: str = ""
    configuration_version: str = ""
    simulation: bool = False
    overrides: list[OverrideMetadata] = Field(default_factory=list)
    summary: str = ""
    source_plan_id: str | None = None
    change_summary: str | None = None
    valid_until: datetime | None = None
    approved_at: datetime | None = None
    paused_at: datetime | None = None
    superseded_at: datetime | None = None
    superseded_by: str | None = None
    incident_scope_key: str = ""
    tenant_id: str = "live"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_resource_allocation_payload(self) -> dict[str, object]:
        """Build a typed downstream payload without publishing or dispatching."""
        return {
            "evacuationPlanId": self.plan_id,
            "transportRequirements": [
                requirement.to_resource_allocation_payload() for requirement in self.transport_requirements
            ],
            "dispatchAuthorized": False,
        }

    def deterministic_replay_projection(self) -> dict[str, object]:
        """Return the exact operational plan surface used for replay checks."""
        volatile_fields = {
            "approved_at",
            "completes_at",
            "created_at",
            "emergency_notification_id",
            "emergency_notification_receipt",
            "generated_at",
            "hazard_data_timestamp",
            "override_timestamp",
            "paused_at",
            "reported_at",
            "snapshot_at",
            "source_handoff_id",
            "starts_at",
            "superseded_at",
            "transition_at",
            "updated_at",
            "valid_until",
            "weather_data_timestamp",
        }
        narrative_fields = {
            "change_summary",
            "description",
            "details",
            "notes",
            "rationale",
            "selection_rationale",
            "summary",
        }

        def strip_volatile(value: object) -> object:
            if isinstance(value, dict):
                return {
                    key: strip_volatile(item)
                    for key, item in value.items()
                    if key not in volatile_fields and key not in narrative_fields
                }
            if isinstance(value, list):
                return [strip_volatile(item) for item in value]
            return value

        projection = strip_volatile(self.model_dump(mode="json"))
        if not isinstance(projection, dict):
            raise TypeError("evacuation plan projection must be an object")
        return projection

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
        if self.valid_until is not None and self.valid_until.tzinfo is None:
            raise ValueError("valid_until must be timezone-aware")
        expected_plan_id = f"ep-{self.incident_id}-v{self.version}"
        if self.plan_id != expected_plan_id:
            if not self.plan_id.startswith(f"ep-{self.incident_id}-v"):
                raise ValueError("plan_id incident must match incident_id")
            raise ValueError("plan_id version must match version")
        expected_scope = f"{self.tenant_id}:{self.incident_id}"
        if self.incident_scope_key != expected_scope:
            if not self.incident_scope_key.startswith(f"{self.tenant_id}:"):
                raise ValueError("incident scope tenant must match tenant_id")
            raise ValueError("incident scope incident must match incident_id")
        if self.simulation != (self.tenant_id != "live"):
            raise ValueError("simulation label must match tenant_id")
        if not self.affected_area:
            raise ValueError("affected_area is required")
        if self.hazard_summary is None:
            raise ValueError("hazard_summary is required")
        if (
            not self.hazard_summary.hazard_type
            or not self.hazard_summary.severity_level
            or not self.hazard_summary.time_horizon
            or not self.hazard_summary.affected_area
            or not self.hazard_summary.sources
        ):
            raise ValueError("hazard_summary safety fields are required")
        if not self.zones:
            raise ValueError("at least one evacuation zone is required")
        if self.population_estimate != sum(zone.population_estimate for zone in self.zones):
            raise ValueError("population_estimate must equal zone populations")
        if self.total_population != self.population_estimate:
            raise ValueError("total_population must equal population_estimate")
        if not self.phases:
            raise ValueError("at least one evacuation phase is required")
        zone_numbers = {zone.zone_number for zone in self.zones}
        disposition_zones = {disposition.zone_number for disposition in self.zone_dispositions}
        if disposition_zones != zone_numbers or len(self.zone_dispositions) != len(zone_numbers):
            raise ValueError("zone dispositions must cover every zone exactly once")
        if self.traceability is None:
            raise ValueError("traceability is required")
        if (
            not self.traceability.source_handoff_id
            or not self.traceability.risk_assessment_id
            or not self.traceability.risk_assessment_ids
            or not self.traceability.recommendation_id
        ):
            raise ValueError("complete upstream traceability is required")
        if self.data_snapshot is None:
            raise ValueError("data_snapshot is required")
        if (
            not self.data_snapshot.road_network_version
            or not self.data_snapshot.population_data_version
            or not self.data_snapshot.facility_data_version
            or not self.data_snapshot.assembly_area_data_version
            or not self.data_snapshot.hazard_assessment_ids
            or not self.data_snapshot.hazard_geometry_algorithm
        ):
            raise ValueError("complete data snapshot versions are required")
        if not self.summary.strip():
            raise ValueError("summary is required")
        if not self.generation_method.strip():
            raise ValueError("generation_method is required")
        if not self.configuration_version.strip():
            raise ValueError("configuration_version is required")
        source_assessment_ids = [source.assessment_id for source in self.hazard_summary.sources]
        if self.traceability.risk_assessment_ids != source_assessment_ids:
            raise ValueError("traceability assessment IDs must match hazard sources")
        if self.traceability.risk_assessment_id not in source_assessment_ids:
            raise ValueError("primary assessment must be present in hazard sources")
        if self.hazard_summary.source_assessment_id != self.traceability.risk_assessment_id:
            raise ValueError("hazard and traceability primary assessments must match")
        if self.data_snapshot.hazard_assessment_ids != source_assessment_ids:
            raise ValueError("snapshot assessment IDs must match hazard sources")
        source_signal_ids = sorted(
            {signal_id for source in self.hazard_summary.sources for signal_id in source.input_signal_ids}
        )
        if self.traceability.input_signal_ids != source_signal_ids:
            raise ValueError("traceability signal IDs must match hazard sources")
        if self.hazard_summary.affected_area != self.affected_area:
            raise ValueError("hazard affected area must match plan affected area")
        if self.traceability.generation_method != self.generation_method:
            raise ValueError("generation_method must match traceability")
        if self.generation_method == PlanGenerationMethod.safety_fallback and (
            self.content_safety_result in {"", "passed", "not_checked"} or not self.immediate_human_review_required
        ):
            raise ValueError("safety fallback requires failed safety evidence and review")
        if self.generation_method == PlanGenerationMethod.ai_assisted and (
            self.content_safety_result != "passed" or not self.content_safety_validation_method
        ):
            raise ValueError("ai_assisted summary requires a passed content-safety validator")
        if self.traceability.input_data_versions.get("config") != self.configuration_version:
            raise ValueError("configuration_version must match traceability")
        snapshot_counts = (
            (
                self.data_snapshot.population_record_count,
                self.data_snapshot.population_record_ids,
                self.data_snapshot.population_data_available,
            ),
            (
                self.data_snapshot.facility_record_count,
                self.data_snapshot.facility_record_ids,
                self.data_snapshot.facility_data_available,
            ),
            (
                self.data_snapshot.assembly_area_record_count,
                self.data_snapshot.assembly_area_record_ids,
                self.data_snapshot.assembly_area_data_available,
            ),
        )
        if any(count != len(record_ids) for count, record_ids, _ in snapshot_counts):
            raise ValueError("snapshot record counts must match record IDs")
        if any(not available and count > 0 for count, _, available in snapshot_counts):
            raise ValueError("unavailable snapshot data cannot contain records")
        if self.data_snapshot.road_data_status in {"stale", "unavailable"}:
            if self.routes or self.assembly_areas or self.destination_allocations:
                raise ValueError("stale or unavailable roads cannot support computed routing")
            if not self.immediate_human_review_required:
                raise ValueError("degraded road data requires immediate review")
            if not self.generic_guidance.strip():
                raise ValueError("degraded road data requires generic guidance")
        if (
            self.data_snapshot.road_data_status == "fresh_cache_refresh_failed"
            and not self.immediate_human_review_required
        ):
            raise ValueError("failed road refresh requires immediate review")
        if self.version > 1 and (not self.source_plan_id or not (self.change_summary or "").strip()):
            raise ValueError("versioned plans require source_plan_id and change_summary")
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
    operation_id: str = ""
    plan_id: str | None = None
    incident_id: str
    assessment_id: str | None = None
    recommendation_id: str | None = None
    input_signal_ids: list[str] = Field(default_factory=list)
    hazard_type: str | None = None
    zone_ids: list[str] = Field(default_factory=list)
    route_ids: list[str] = Field(default_factory=list)
    population_affected: int = 0
    routes_count: int | None = Field(default=None, ge=0)
    transport_requests_count: int | None = Field(default=None, ge=0)
    constraints_applied: list[str] = Field(default_factory=list)
    replanning_triggers: list[ReplanningTrigger] = Field(default_factory=list)
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
    principal_id: str | None = None
    simulation: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    buffered_at: datetime | None = None
    flush_source: str | None = None
    override_metadata: OverrideMetadata | None = None
    zone_dispositions: list[ZoneDisposition] = Field(default_factory=list)
    data_quality_gaps: list[str] = Field(default_factory=list)
    confidence_adjustments: list[ConfidenceAdjustment] = Field(default_factory=list)
    immediate_human_review_required: bool = False
    summary_grounding_result: str = ""
    content_safety_result: str = ""
    content_safety_validation_method: str = ""
    content_safety_reason: str = ""
    content_safety_reference: str = ""
    expected_steps: list[str] = Field(default_factory=list)
    observed_steps: list[str] = Field(default_factory=list)
    stage_durations_ms: dict[str, float] = Field(default_factory=dict)
    completeness_warnings: list[str] = Field(default_factory=list)

    @field_validator("confidence_raw", "confidence_adjusted")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @model_validator(mode="after")
    def _derive_simulation_label(self) -> EvacuationDecisionRecord:
        self.simulation = self.tenant_id != "live"
        if self.timestamp.tzinfo is None:
            raise ValueError("audit timestamp must be timezone-aware")
        self.timestamp = self.timestamp.astimezone(UTC)
        if self.buffered_at is not None:
            if self.buffered_at.tzinfo is None:
                raise ValueError("audit buffered_at must be timezone-aware")
            self.buffered_at = self.buffered_at.astimezone(UTC)
        if not self.handoff_id.strip():
            raise ValueError("handoff_id is required")
        self.operation_id = self.operation_id or self.handoff_id
        if not self.operation_id.strip():
            raise ValueError("operation_id is required")
        if not self.incident_id.strip():
            raise ValueError("incident_id is required")
        if self.incident_scope_key != f"{self.tenant_id}:{self.incident_id}":
            raise ValueError("audit incident_scope_key must match tenant_id and incident_id")
        if not self.decision_rationale.strip():
            raise ValueError("decision_rationale is required")
        if not self.agent_version.strip() or not self.configuration_version.strip():
            raise ValueError("audit agent and configuration versions are required")
        if self.processing_duration_ms < 0:
            raise ValueError("processing_duration_ms cannot be negative")
        if self.plan_id is not None:
            if self.version is None:
                raise ValueError("plan-linked audit requires version")
            if self.plan_id != f"ep-{self.incident_id}-v{self.version}":
                raise ValueError("audit plan_id must match incident_id and version")
        if self.routes_count is not None and self.routes_count != len(self.route_ids):
            raise ValueError("routes_count must match route_ids")
        if self.decision_type in {
            DecisionType.plan_generated,
            DecisionType.plan_updated,
        } and (
            self.plan_id is None
            or self.version is None
            or self.routes_count is None
            or self.transport_requests_count is None
        ):
            raise ValueError("plan audit identity, version, and counts are required")
        if self.expected_steps and any(duration < 0 for duration in self.stage_durations_ms.values()):
            raise ValueError("stage durations cannot be negative")
        return self


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class AuditBufferEntry(BaseModel):
    """Temporary wrapper for audit records during Cosmos DB unavailability."""

    record: EvacuationDecisionRecord
    buffered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retry_count: int = 0
    last_retry_at: datetime | None = None
