"""Evacuation Agent — route optimisation, transport coordination, and evacuation planning.

Provides:
- EvacuationAgent class (subclasses LLMCallMixin)
- FastAPI app factory ``create_app()`` with:
  - GET /health  (6 health checks)
  - POST /override (plan status transitions)
  - POST /replan (manual replanning trigger)
- Service Bus consumer loop (``run_consumer()``)
- ``__main__`` entrypoint on port 8082
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import time
from collections.abc import Awaitable, Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import TYPE_CHECKING, Any

from azure.core import MatchConditions
from common.entra_principal import AuthenticatedPrincipal, EntraPrincipalResolver, normalize_role
from common.handoffs import AgentHandoffEvent

if TYPE_CHECKING:
    from apps.agents.common.llm_mixin import LLMCallMixin
else:
    from common.llm_mixin import LLMCallMixin
from evacuation import telemetry as tel
from evacuation.audit import AuditQueryPage
from evacuation.config import EvacuationConfig
from evacuation.models import (
    ConfidenceAdjustment,
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPhase,
    EvacuationPlan,
    EvacuationRoute,
    EvacuationZone,
    HazardSourceSnapshot,
    OriginCoverageStatus,
    OverrideMetadata,
    PlanStatus,
    ZoneDispositionType,
    confidence_to_level,
)
from evacuation.pipeline import EvacuationProcessingPipeline, TransientHandoffDependencyError
from evacuation.replanner import DynamicReplanner
from evacuation.repository import EvacuationPlanRepository
from evacuation.road_network import RoadNetworkLoader
from evacuation.router import RouteComputer
from evacuation.templates import generate_plan_summary_template
from fastapi import Request, Response

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _CachedDependencyHealth:
    status: str
    checked_at: datetime | None = None
    last_successful_at: datetime | None = None
    latency_ms: int | None = None


# ---------------------------------------------------------------------------
# Valid status transitions for plan overrides
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
    PlanStatus.proposed: {
        PlanStatus.approved,
        PlanStatus.rejected,
        PlanStatus.cancelled,
        PlanStatus.paused,
    },
    PlanStatus.approved: {
        PlanStatus.superseded,
        PlanStatus.cancelled,
        PlanStatus.paused,
    },
    PlanStatus.paused: {
        PlanStatus.approved,
        PlanStatus.cancelled,
        PlanStatus.superseded,
    },
}

# Override action → target status mapping
_ACTION_STATUS_MAP: dict[str, PlanStatus] = {
    "approve": PlanStatus.approved,
    "reject": PlanStatus.rejected,
    "cancel": PlanStatus.cancelled,
    "pause": PlanStatus.paused,
    "resume": PlanStatus.approved,
    "modify": PlanStatus.proposed,  # creates new version
}

_VALID_ACTIONS = set(_ACTION_STATUS_MAP.keys())
_MODIFICATION_FIELDS = {
    "route_override": "routes",
    "zone_boundary_change": "zones",
    "phase_reprioritization": "phases",
}
_AUTHORIZED_OVERRIDE_ROLES = {
    "incident_commander",
}


class InvalidPlanModificationError(ValueError):
    """Raised when a commander modification cannot produce a safe plan."""


def _cosmos_write_body(document: dict[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in document.items() if not key.startswith("_")}


def _source_guard_for_new_proposal(
    source: dict[str, Any],
    new_plan_id: str,
    now: datetime,
) -> dict[str, Any]:
    guard = _cosmos_write_body(source)
    if source.get("status") == PlanStatus.proposed.value:
        guard.update(
            {
                "status": PlanStatus.superseded.value,
                "superseded_by": new_plan_id,
                "superseded_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        )
    return guard


def _validate_modification_payload(
    modifications: dict[str, Any] | None,
) -> tuple[str, str, list[dict[str, Any]]]:
    if not modifications or set(modifications) != {"override_type", "details"}:
        raise InvalidPlanModificationError("modify requires only override_type and details")

    override_type = modifications.get("override_type")
    field_name = _MODIFICATION_FIELDS.get(str(override_type))
    if field_name is None:
        raise InvalidPlanModificationError(f"override_type must be one of {sorted(_MODIFICATION_FIELDS)}")

    details = modifications.get("details")
    if not isinstance(details, dict) or set(details) != {field_name}:
        raise InvalidPlanModificationError(f"{override_type} details must contain only {field_name}")
    values = details[field_name]
    if not isinstance(values, list) or not values:
        raise InvalidPlanModificationError(f"{field_name} must be a non-empty list")
    if not all(isinstance(value, dict) for value in values):
        raise InvalidPlanModificationError(f"Every {field_name} entry must be an object")
    return str(override_type), field_name, values


def _recompute_timeline(agent: EvacuationAgent, document: dict[str, Any]) -> None:
    hazard_summary = document.get("hazard_summary") or {}
    arrival_minutes = hazard_summary.get("estimated_arrival_minutes")
    horizon_hours = float(arrival_minutes) / 60 if arrival_minutes is not None else None
    anchor_value = document.get("created_at")
    timeline_anchor = datetime.fromisoformat(str(anchor_value).replace("Z", "+00:00")) if anchor_value else None
    phases, zone_dispositions, _ = agent._pipeline._timeline_estimator.estimate_timeline(
        zones=document.get("zones", []),
        routes=document.get("routes", []),
        transport_requirements=document.get("transport_requirements", []),
        hazard_type=hazard_summary.get("hazard_type", "bushfire"),
        hazard_time_horizon_hours=horizon_hours,
        corridor_loads=document.get("corridor_loads", []),
        timeline_anchor=timeline_anchor,
    )
    document["phases"] = [phase.model_dump(mode="json") for phase in phases]
    document["shelter_in_place_zones"] = [
        str(disposition.zone_number) for disposition in zone_dispositions if disposition.recommended
    ]
    document["zone_dispositions"] = [disposition.model_dump(mode="json") for disposition in zone_dispositions]
    document["estimated_completion_minutes"] = agent._pipeline._timeline_estimator.plan_completion_minutes(phases)


def _recompute_transport_coordination(
    agent: EvacuationAgent,
    document: dict[str, Any],
    zones: list[EvacuationZone],
) -> None:
    assembly_areas = (
        [
            {
                "assembly_area_id": area.assembly_area_id,
                "name": area.name,
                "coordinates": area.coordinates,
            }
            for area in agent._road_network.get_assembly_areas()
        ]
        if agent._road_network.is_loaded
        else []
    )
    result = agent._pipeline._transport_coordinator.coordinate_transport(
        zones=[zone.model_dump(mode="json") for zone in zones],
        facilities=(agent._pipeline._facility_data if agent._pipeline._facility_data_available else None),
        assembly_areas=assembly_areas,
        incident_scope_key=str(document.get("incident_scope_key", "")),
        destination_allocations=document.get("destination_allocations", []),
        routes=document.get("routes", []),
    )
    document["transport_requirements"] = [requirement.model_dump(mode="json") for requirement in result.requirements]
    document["transport_coordination_status"] = result.status.value
    document["transport_exclusions"] = [exclusion.model_dump(mode="json") for exclusion in result.exclusions]
    document["identified_transport_population_by_zone"] = result.identified_population_by_zone
    document["uncovered_vulnerable_population_by_zone"] = result.uncovered_vulnerable_population_by_zone


def _recompute_routes(agent: EvacuationAgent, document: dict[str, Any]) -> None:
    if not agent._road_network.is_loaded:
        raise InvalidPlanModificationError("Road network is unavailable for zone recomputation")

    hazard_summary = document.get("hazard_summary") or {}
    zones = [EvacuationZone.model_validate(zone) for zone in document.get("zones", [])]
    zone_polygons = agent._pipeline._zone_computer.get_zone_polygons(zones)
    edge_documents = []
    for edge in agent._road_network.get_all_edges():
        edge_document = edge.model_dump()
        geometry = agent._road_network.get_edge_geometry(edge.id)
        if geometry is not None:
            edge_document["_geometry"] = geometry
        edge_documents.append(edge_document)
    adjusted_edges = agent._pipeline._zone_computer.apply_zone_capacity_reduction(
        edge_documents,
        zone_polygons,
    )
    effective_network = agent._road_network.effective_copy(adjusted_edges)
    data_snapshot = dict(document.get("data_snapshot") or {})
    data_snapshot["road_network_version"] = effective_network.get_version()
    data_snapshot["snapshot_at"] = datetime.now(UTC).isoformat()
    document["data_snapshot"] = data_snapshot
    hazard_sources = [
        HazardSourceSnapshot.model_validate(source)
        for source in (document.get("hazard_summary") or {}).get("sources", [])
    ]
    route_computer = RouteComputer(
        road_network=effective_network,
        config=agent._config,
        hazard_context=agent._pipeline._build_hazard_routing_context(
            hazard_sources,
            str(document.get("incident_scope_key", "")),
        ),
    )
    excluded_edges = {edge.id for edge in effective_network.get_closed_edges()}
    route_models: list[EvacuationRoute] = []
    origins_by_zone = agent._pipeline._assign_zone_origin_nodes(
        zones,
        effective_network,
    )
    for zone in zones:
        origins = origins_by_zone[zone.zone_number]
        zone.origin_node_ids = origins
        zone.origin_coverage_status = (
            OriginCoverageStatus.covered
            if origins
            else (
                OriginCoverageStatus.no_network_origin
                if zone.population_estimate > 0
                else OriginCoverageStatus.not_required
            )
        )
        if not origins and zone.population_estimate > 0:
            raise InvalidPlanModificationError(
                f"Zone {zone.zone_id or zone.zone_number} does not intersect the road network"
            )
        computed = route_computer.compute_routes(
            origin_nodes=origins,
            zone_number=zone.zone_number,
            population=zone.population_estimate,
            hazard_type=hazard_summary.get("hazard_type", "bushfire"),
            excluded_edge_ids=excluded_edges,
            allocate_population=False,
        )
        route_models.extend(computed)
    route_computer.allocate_plan_routes(
        route_models,
        {zone.zone_number: zone.population_estimate for zone in zones},
        {zone.zone_number: zone.vulnerable_population for zone in zones},
    )
    for zone in zones:
        zone.unallocated_route_population = route_computer.unallocated_population_by_zone.get(
            zone.zone_number,
            zone.population_estimate,
        )
    document["zones"] = [zone.model_dump(mode="json") for zone in zones]
    document["routes"] = [route.model_dump(mode="json") for route in route_models]
    document["routing_mode"] = route_computer.routing_mode.value
    document["hazard_routing_data_gaps"] = route_computer.hazard_data_gaps
    document["excluded_destinations"] = [
        exclusion.model_dump(mode="json") for exclusion in route_computer.destination_exclusions
    ]
    document["corridor_loads"] = [load.model_dump(mode="json") for load in route_computer.corridor_loads]
    document["destination_allocations"] = [
        allocation.model_dump(mode="json") for allocation in route_computer.destination_allocations
    ]
    document["unresolved_destination_demands"] = [
        demand.model_dump(mode="json") for demand in route_computer.unresolved_destination_demands
    ]
    document["excluded_roads"] = [road.model_dump(mode="json") for road in route_computer.excluded_roads]
    _set_route_inventory(
        document,
        zones,
        document["routes"],
        document["excluded_roads"],
    )


def _set_route_inventory(
    document: dict[str, Any],
    zones: list[EvacuationZone],
    routes: list[dict[str, Any]],
    excluded_roads: list[dict[str, Any]],
) -> None:
    routed_zone_numbers = {
        int(route.get("zone_id", 0))
        for route in routes
        if str(route.get("zone_id", "")).isdigit() and int(route.get("allocated_population", 0)) > 0
    }
    document["zero_route_zones"] = [zone.zone_number for zone in zones if zone.zone_number not in routed_zone_numbers]
    by_reason: dict[str, int] = {}
    for road in excluded_roads:
        reason = str(road.get("source_hazard_type") or road.get("closure_reason") or "unspecified")
        by_reason[reason] = by_reason.get(reason, 0) + 1
    document["unavailable_roads_by_reason"] = by_reason


def _validate_commander_routes(
    agent: EvacuationAgent,
    source: dict[str, Any],
    values: list[dict[str, Any]],
) -> tuple[list[EvacuationRoute], RouteComputer, list[EvacuationZone]]:
    if not agent._road_network.is_loaded:
        raise InvalidPlanModificationError("Road network is unavailable for route validation")

    zones_by_id: dict[str, dict[str, Any]] = {}
    for zone in source.get("zones", []):
        for zone_id in (zone.get("zone_id"), zone.get("zone_number")):
            if zone_id not in (None, ""):
                zones_by_id[str(zone_id)] = zone
    routes = [EvacuationRoute.model_validate(value) for value in values]
    zones = [EvacuationZone.model_validate(zone) for zone in source.get("zones", [])]
    hazard_summary = source.get("hazard_summary") or {}
    hazard_sources = [HazardSourceSnapshot.model_validate(item) for item in hazard_summary.get("sources", [])]
    route_computer = RouteComputer(
        road_network=agent._road_network,
        config=agent._config,
        hazard_context=agent._pipeline._build_hazard_routing_context(
            hazard_sources,
            str(source.get("incident_scope_key", "")),
        ),
    )
    route_computer.compute_routes(
        [],
        0,
        0,
        hazard_summary.get("hazard_type", "bushfire"),
        excluded_edge_ids={edge.id for edge in agent._road_network.get_closed_edges()},
    )
    unavailable_edge_ids = {road.edge_id for road in route_computer.excluded_roads}
    rejected_destination_ids = {item.assembly_area_id for item in route_computer.destination_exclusions}
    for route in routes:
        if route.zone_id not in zones_by_id:
            raise InvalidPlanModificationError(f"Route {route.route_id} references an unknown zone")
        assembly_area = agent._road_network.get_assembly_area(route.assembly_area_id)
        if assembly_area is None:
            raise InvalidPlanModificationError(f"Route {route.route_id} references an unknown assembly area")
        if route.assembly_area_id in rejected_destination_ids:
            raise InvalidPlanModificationError(f"Route {route.route_id} uses a hazard-exposed assembly area")
        if not route.waypoints:
            raise InvalidPlanModificationError(f"Route {route.route_id} requires road edges")

        edges = []
        for edge_id in route.waypoints:
            edge = agent._road_network.get_edge(edge_id)
            if edge is None:
                raise InvalidPlanModificationError(f"Route {route.route_id} references unknown road edge {edge_id}")
            if edge.closure_status == "closed" or edge.capacity_vehicles_per_hour <= 0:
                raise InvalidPlanModificationError(f"Route {route.route_id} uses unavailable road edge {edge_id}")
            if edge_id in unavailable_edge_ids:
                raise InvalidPlanModificationError(f"Route {route.route_id} uses hazard-excluded road edge {edge_id}")
            edges.append(edge)

        for previous, current in zip(edges, edges[1:], strict=False):
            previous_nodes = {previous.from_node, previous.to_node}
            current_nodes = {current.from_node, current.to_node}
            if previous_nodes.isdisjoint(current_nodes):
                raise InvalidPlanModificationError(f"Route {route.route_id} road edges are not contiguous")
        if assembly_area.node_id not in {edges[-1].from_node, edges[-1].to_node}:
            raise InvalidPlanModificationError(f"Route {route.route_id} does not terminate at its assembly area")

        current_node = assembly_area.node_id
        reversed_nodes = [current_node]
        for edge in reversed(edges):
            if edge.from_node == current_node:
                current_node = edge.to_node
            elif edge.to_node == current_node:
                current_node = edge.from_node
            else:
                raise InvalidPlanModificationError(f"Route {route.route_id} road direction is disconnected")
            reversed_nodes.append(current_node)
        route.excluded_roads = route_computer.excluded_roads
        route_computer.populate_route_static_evidence(
            route,
            list(reversed(reversed_nodes)),
        )

    route_computer.allocate_plan_routes(
        routes,
        {zone.zone_number: zone.population_estimate for zone in zones},
        {zone.zone_number: zone.vulnerable_population for zone in zones},
    )
    for zone in zones:
        zone.unallocated_route_population = route_computer.unallocated_population_by_zone.get(
            zone.zone_number,
            zone.population_estimate,
        )
    return routes, route_computer, zones


def _apply_plan_modification(
    agent: EvacuationAgent,
    source: dict[str, Any],
    modifications: dict[str, Any] | None,
) -> tuple[dict[str, Any], str, dict[str, object], dict[str, object]]:
    override_type, field_name, values = _validate_modification_payload(modifications)
    modified = _cosmos_write_body(source)
    original_values: dict[str, object] = {field_name: deepcopy(source.get(field_name, []))}

    try:
        if override_type == "route_override":
            routes, route_computer, zones = _validate_commander_routes(
                agent,
                source,
                values,
            )
            normalized_routes = [route.model_dump(mode="json") for route in routes]
            original_routes = [
                EvacuationRoute.model_validate(route).model_dump(mode="json") for route in source.get("routes", [])
            ]
            if normalized_routes == original_routes:
                raise InvalidPlanModificationError("Modification does not change the plan")
            modified["routes"] = normalized_routes
            modified["zones"] = [zone.model_dump(mode="json") for zone in zones]
            modified["routing_mode"] = route_computer.routing_mode.value
            modified["hazard_routing_data_gaps"] = route_computer.hazard_data_gaps
            modified["excluded_destinations"] = [
                item.model_dump(mode="json") for item in route_computer.destination_exclusions
            ]
            modified["excluded_roads"] = [road.model_dump(mode="json") for road in route_computer.excluded_roads]
            modified["corridor_loads"] = [load.model_dump(mode="json") for load in route_computer.corridor_loads]
            modified["destination_allocations"] = [
                allocation.model_dump(mode="json") for allocation in route_computer.destination_allocations
            ]
            modified["unresolved_destination_demands"] = [
                demand.model_dump(mode="json") for demand in route_computer.unresolved_destination_demands
            ]
            data_snapshot = dict(modified.get("data_snapshot") or {})
            data_snapshot["road_network_version"] = agent._road_network.get_version()
            data_snapshot["snapshot_at"] = datetime.now(UTC).isoformat()
            modified["data_snapshot"] = data_snapshot
            _set_route_inventory(
                modified,
                zones,
                normalized_routes,
                modified["excluded_roads"],
            )
            _recompute_transport_coordination(agent, modified, zones)
            _recompute_timeline(agent, modified)
        elif override_type == "zone_boundary_change":
            zones = [EvacuationZone.model_validate(value) for value in values]
            for zone in zones:
                if not zone.boundary:
                    raise InvalidPlanModificationError("Every changed zone requires a boundary")
            normalized_zones = [zone.model_dump(mode="json") for zone in zones]
            original_zones = [
                EvacuationZone.model_validate(zone).model_dump(mode="json") for zone in source.get("zones", [])
            ]
            if normalized_zones == original_zones:
                raise InvalidPlanModificationError("Modification does not change the plan")
            modified["zones"] = normalized_zones
            modified["total_population"] = sum(zone.population_estimate for zone in zones)
            modified["population_estimate"] = modified["total_population"]
            _recompute_routes(agent, modified)
            _recompute_transport_coordination(agent, modified, zones)
            _recompute_timeline(agent, modified)
        else:
            phases = [EvacuationPhase.model_validate(value) for value in values]
            known_zone_ids = {
                str(zone_id)
                for zone in source.get("zones", [])
                for zone_id in (zone.get("zone_id"), zone.get("zone_number"))
                if zone_id not in (None, "")
            }
            if any(set(phase.zone_ids) - known_zone_ids for phase in phases):
                raise InvalidPlanModificationError("phase reprioritization references an unknown zone")
            source_population = sum(int(phase.get("population_moved", 0)) for phase in source.get("phases", []))
            if sum(phase.population_moved for phase in phases) != source_population:
                raise InvalidPlanModificationError("phase reprioritization must preserve the planned population")
            next_offset = float(source.get("mobilisation_time_minutes", 0))
            anchor_value = source.get("created_at")
            timeline_anchor = datetime.fromisoformat(str(anchor_value).replace("Z", "+00:00")) if anchor_value else None
            for phase_number, phase in enumerate(phases, start=1):
                if phase.duration_minutes is None:
                    raise InvalidPlanModificationError("blocked phases cannot be reprioritized with a finite timeline")
                old_start = phase.start_offset_minutes
                transition_delta = (
                    phase.selected_transition_offset_minutes - old_start
                    if phase.selected_transition_offset_minutes is not None
                    else phase.duration_minutes
                )
                population_delta = (
                    phase.population_transition_offset_minutes - old_start
                    if phase.population_transition_offset_minutes is not None
                    else None
                )
                time_delta = (
                    phase.time_transition_offset_minutes - old_start
                    if phase.time_transition_offset_minutes is not None
                    else None
                )
                phase.phase_number = phase_number
                phase.start_offset_minutes = next_offset
                phase.completion_offset_minutes = next_offset + phase.duration_minutes
                phase.selected_transition_offset_minutes = next_offset + min(
                    max(0.0, transition_delta),
                    phase.duration_minutes,
                )
                phase.population_transition_offset_minutes = (
                    None if population_delta is None else next_offset + max(0.0, population_delta)
                )
                phase.time_transition_offset_minutes = (
                    None if time_delta is None else next_offset + max(0.0, time_delta)
                )
                phase.starts_at = (
                    timeline_anchor + timedelta(minutes=next_offset) if timeline_anchor is not None else None
                )
                phase.completes_at = (
                    timeline_anchor + timedelta(minutes=phase.completion_offset_minutes)
                    if timeline_anchor is not None
                    else None
                )
                phase.transition_at = (
                    timeline_anchor + timedelta(minutes=phase.selected_transition_offset_minutes)
                    if timeline_anchor is not None
                    else None
                )
                next_offset = phase.selected_transition_offset_minutes
                EvacuationPhase.model_validate(phase.model_dump())
            normalized_phases = [phase.model_dump(mode="json") for phase in phases]
            original_phases = [
                EvacuationPhase.model_validate(phase).model_dump(mode="json") for phase in source.get("phases", [])
            ]
            if normalized_phases == original_phases:
                raise InvalidPlanModificationError("Modification does not change the plan")
            modified["phases"] = normalized_phases
            modified["estimated_completion_minutes"] = agent._pipeline._timeline_estimator.plan_completion_minutes(
                phases
            )
    except InvalidPlanModificationError:
        raise
    except (TypeError, ValueError) as exc:
        raise InvalidPlanModificationError(str(exc)) from exc

    _refresh_deterministic_summary(agent, modified)
    modified_values: dict[str, object] = {
        field_name: deepcopy(modified[field_name]),
    }
    if override_type in {"route_override", "zone_boundary_change"}:
        modified_values["phases"] = deepcopy(modified["phases"])
        modified_values["estimated_completion_minutes"] = modified["estimated_completion_minutes"]
    if override_type == "zone_boundary_change":
        modified_values["routes"] = deepcopy(modified["routes"])
        modified_values["total_population"] = modified["total_population"]
    return modified, override_type, original_values, modified_values


def _refresh_deterministic_summary(
    agent: EvacuationAgent,
    document: dict[str, Any],
) -> None:
    adjustments = [ConfidenceAdjustment.model_validate(item) for item in document.get("confidence_adjustments", [])]
    fallback_reason = "generation_template_fallback"
    generation_adjustment = next(
        (item for item in adjustments if item.reason.startswith("generation_")),
        None,
    )
    if generation_adjustment is None:
        factor = agent._config.fallback_confidence_reduction
        document["confidence_score"] = max(
            0.0,
            min(1.0, float(document.get("confidence_score", 0)) * factor),
        )
        adjustments.append(ConfidenceAdjustment(reason=fallback_reason, factor=factor))
    elif generation_adjustment.reason != fallback_reason:
        adjustments = [
            (
                ConfidenceAdjustment(
                    reason=fallback_reason,
                    factor=item.factor,
                )
                if item is generation_adjustment
                else item
            )
            for item in adjustments
        ]
    document["confidence_adjustments"] = [item.model_dump(mode="json") for item in adjustments]
    document["generation_method"] = "template_fallback"
    document["summary_grounding_result"] = "deterministic_update"
    document["content_safety_result"] = "not_checked"
    document["content_safety_validation_method"] = ""
    document["content_safety_reason"] = ""
    document["content_safety_reference"] = ""
    document["model_deployment_id"] = ""
    document["immediate_human_review_required"] = True
    traceability = dict(document.get("traceability") or {})
    traceability["generation_method"] = "template_fallback"
    document["traceability"] = traceability
    hazard_summary = document.get("hazard_summary") or {}
    document["summary"] = generate_plan_summary_template(
        {
            "population_estimate": document.get("population_estimate", 0),
            "zones": document.get("zones", []),
            "routes": document.get("routes", []),
            "assembly_areas": document.get("assembly_areas", []),
            "transport_requirements": document.get(
                "transport_requirements",
                [],
            ),
            "phases": document.get("phases", []),
            "zone_dispositions": document.get("zone_dispositions", []),
            "confidence_score": document.get("confidence_score", 0),
            "confidence_level": confidence_to_level(float(document.get("confidence_score", 0))).value,
            "hazard_severity": hazard_summary.get("severity_level", "high"),
            "time_horizon": hazard_summary.get("time_horizon", "unknown"),
            "routing_mode": document.get("routing_mode"),
            "hazard_routing_data_gaps": document.get(
                "hazard_routing_data_gaps",
                [],
            ),
            "excluded_roads": document.get("excluded_roads", []),
            "excluded_destinations": document.get(
                "excluded_destinations",
                [],
            ),
            "zero_route_zones": document.get("zero_route_zones", []),
            "unresolved_destination_demands": document.get(
                "unresolved_destination_demands",
                [],
            ),
            "road_data_status": (document.get("data_snapshot") or {}).get(
                "road_data_status",
                "fresh",
            ),
            "population_data_status": (document.get("data_snapshot") or {}).get(
                "population_data_status", "unavailable"
            ),
            "facility_data_status": (document.get("data_snapshot") or {}).get(
                "facility_data_status",
                "unavailable",
            ),
            "immediate_human_review_required": True,
            "urgent_assumptions": (agent._pipeline._summary_assumption_warnings(document.get("assumptions", []))),
            "generation_method": "template_fallback",
        },
        hazard_type=str(hazard_summary.get("hazard_type") or "unknown"),
        max_length=agent._config.max_summary_length,
    )


class EvacuationAgent(LLMCallMixin):
    """Evacuation planning agent with full pipeline and replanning support.

    Subclasses ``LLMCallMixin`` to get ``_generate_with_fallback()``.
    """

    def __init__(
        self,
        config: EvacuationConfig | None = None,
        road_network: RoadNetworkLoader | None = None,
        cosmos_plans_container: Any = None,
        cosmos_decisions_container: Any = None,
        cosmos_assessments_container: Any = None,
        cosmos_recommendations_container: Any = None,
        population_data: list[dict[str, object]] | None = None,
        facility_data: list[dict[str, object]] | None = None,
        reference_data_metadata: dict[str, Any] | None = None,
        emergency_notification_publisher: Any = None,
    ) -> None:
        super().__init__()  # initialises LLMCallMixin (_llm_client, _content_safety)
        self._config = config or EvacuationConfig()
        self._road_network = road_network or RoadNetworkLoader(
            staleness_hours=self._config.road_data_staleness_hours,
        )

        # Build processing pipeline
        self._pipeline = EvacuationProcessingPipeline(
            config=self._config,
            road_network=self._road_network,
            cosmos_plans_container=cosmos_plans_container,
            cosmos_decisions_container=cosmos_decisions_container,
            cosmos_assessments_container=cosmos_assessments_container,
            cosmos_recommendations_container=cosmos_recommendations_container,
            population_data=population_data,
            facility_data=facility_data,
            reference_data_metadata=reference_data_metadata,
            llm_generate_fn=self._generate_with_fallback,
            emergency_notification_publisher=emergency_notification_publisher,
        )

        # Build replanner
        self._replanner = DynamicReplanner(config=self._config)

        # Cosmos refs for override endpoint
        self._cosmos_plans = cosmos_plans_container
        self._plan_repository = EvacuationPlanRepository(cosmos_plans_container)

        # Runtime metrics
        self._last_llm_latency_ms: int | None = None
        self._last_cosmos_write_ok: bool | None = None
        self._processing_queue_depth: int = 0
        self._last_health_status: str | None = None
        self._health_lock = RLock()
        self._llm_health = _CachedDependencyHealth(status="unknown")
        self._cosmos_health = _CachedDependencyHealth(
            status=("unknown" if cosmos_plans_container is not None else "not_configured")
        )
        self._queue_health = _CachedDependencyHealth(
            status=(
                "offline"
                if self._config.azure_servicebus_connection or self._config.azure_servicebus_namespace
                else "not_configured"
            )
        )

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process_handoff(self, handoff: AgentHandoffEvent) -> EvacuationPlan | None:
        """Delegate to the 10-stage processing pipeline."""
        try:
            plan = self._pipeline.process_handoff(handoff)
        except TransientHandoffDependencyError:
            if self._cosmos_plans is not None:
                self.update_cosmos_health(False, datetime.now(UTC))
            raise
        if self._cosmos_plans is not None and plan is not None:
            self.update_cosmos_health(True, datetime.now(UTC))
        self.update_active_plan_count(
            self._pipeline.active_plan_count,
            tenant_id=handoff.tenant_id,
        )
        return plan

    def update_llm_health(
        self,
        *,
        status: str,
        checked_at: datetime,
        latency_ms: int | None,
    ) -> None:
        with self._health_lock:
            previous_success = self._llm_health.last_successful_at
            self._llm_health = _CachedDependencyHealth(
                status=status,
                checked_at=checked_at,
                last_successful_at=(checked_at if status in {"healthy", "degraded"} else previous_success),
                latency_ms=latency_ms,
            )
            self._last_llm_latency_ms = latency_ms

    def update_cosmos_health(self, succeeded: bool, checked_at: datetime) -> None:
        with self._health_lock:
            previous_success = self._cosmos_health.last_successful_at
            self._cosmos_health = _CachedDependencyHealth(
                status="healthy" if succeeded else "degraded",
                checked_at=checked_at,
                last_successful_at=checked_at if succeeded else previous_success,
            )
            self._last_cosmos_write_ok = succeeded

    def update_queue_health(
        self,
        *,
        status: str,
        depth: int | None = None,
        checked_at: datetime | None = None,
    ) -> None:
        if status not in {"connected", "reconnecting", "offline", "not_configured"}:
            raise ValueError("invalid queue health status")
        if depth is not None and depth < 0:
            raise ValueError("queue depth cannot be negative")
        observation_time = checked_at or datetime.now(UTC)
        with self._health_lock:
            if depth is not None:
                self._processing_queue_depth = depth
            previous_success = self._queue_health.last_successful_at
            self._queue_health = _CachedDependencyHealth(
                status=status,
                checked_at=observation_time,
                last_successful_at=(observation_time if status == "connected" else previous_success),
            )

    def change_queue_depth(self, delta: int) -> None:
        with self._health_lock:
            self._processing_queue_depth = max(
                0,
                self._processing_queue_depth + delta,
            )

    def update_active_plan_count(
        self,
        count: int,
        *,
        tenant_id: str | None = None,
    ) -> None:
        if count < 0:
            raise ValueError("active plan count cannot be negative")
        with self._health_lock:
            self._pipeline._active_plan_count = count
        tel.active_plans_gauge.set(
            float(count),
            attributes={"tenant_id": tenant_id} if tenant_id else None,
        )

    def change_active_plan_count(
        self,
        delta: int,
        *,
        tenant_id: str | None = None,
    ) -> None:
        with self._health_lock:
            self._pipeline._active_plan_count = max(
                0,
                self._pipeline._active_plan_count + delta,
            )
            count = self._pipeline._active_plan_count
        tel.active_plans_gauge.set(
            float(count),
            attributes={"tenant_id": tenant_id} if tenant_id else None,
        )

    @staticmethod
    def _health_time(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    def health_snapshot(self) -> dict[str, Any]:
        """Return the six-check readiness snapshot without dependency I/O."""
        now = datetime.now(UTC)
        with self._health_lock:
            llm = self._llm_health
            cosmos = self._cosmos_health
            queue = self._queue_health
            queue_depth = self._processing_queue_depth
            active_count = self._pipeline.active_plan_count

        road_loaded = (
            self._road_network.is_loaded and self._road_network.node_count > 0 and self._road_network.edge_count > 0
        )
        road_stale = road_loaded and self._road_network.is_stale()
        road_status = "offline" if not road_loaded else ("degraded" if road_stale else "healthy")
        queue_status = (
            "offline"
            if queue.status == "offline"
            else ("backpressure" if queue_depth >= 20 else ("healthy" if queue.status == "connected" else queue.status))
        )
        active_status = "healthy" if active_count < 40 else "warning"
        audit_status, audit_buffer_depth = self._pipeline.audit_writer.health_snapshot()
        critical_failure = road_status == "offline" or queue_status == "offline"
        nonhealthy = {
            road_status,
            llm.status,
            cosmos.status,
            active_status,
            queue_status,
            audit_status,
        } - {"healthy"}
        overall = "unhealthy" if critical_failure else ("degraded" if nonhealthy else "healthy")
        return {
            "status": overall,
            "agent_version": self._config.agent_version,
            "timestamp": self._health_time(now),
            "checks": {
                "road_network_loaded": {
                    "status": road_status,
                    "node_count": self._road_network.node_count,
                    "edge_count": self._road_network.edge_count,
                    "stale": bool(road_stale),
                    "last_loaded_at": self._health_time(self._road_network.loaded_at),
                    "source_updated_at": self._health_time(self._road_network.source_updated_at),
                },
                "llm_connectivity": {
                    "status": llm.status,
                    "last_checked_at": self._health_time(llm.checked_at),
                    "last_successful_at": self._health_time(llm.last_successful_at),
                    "latency_ms": llm.latency_ms,
                },
                "cosmos_connectivity": {
                    "status": cosmos.status,
                    "last_checked_at": self._health_time(cosmos.checked_at),
                    "last_successful_at": self._health_time(cosmos.last_successful_at),
                    "latency_ms": None,
                },
                "active_plan_count": {
                    "count": active_count,
                    "status": active_status,
                },
                "processing_queue_depth": {
                    "depth": queue_depth,
                    "status": queue_status,
                    "connected": queue.status == "connected",
                    "last_checked_at": self._health_time(queue.checked_at),
                    "last_successful_at": self._health_time(queue.last_successful_at),
                },
                "audit_store": {
                    "status": audit_status,
                    "buffer_depth": audit_buffer_depth,
                },
            },
        }

    def record_intake_rejection(
        self,
        *,
        handoff_id: str,
        reason: str,
        incident_id: str = "unknown",
        tenant_id: str = "unknown",
    ) -> None:
        """Persist a reasoned audit for raw broker work rejected before intake."""
        scope_key = f"{tenant_id}:{incident_id}"
        self._pipeline.audit_writer.write(
            EvacuationDecisionRecord(
                handoff_id=handoff_id,
                incident_id=incident_id,
                decision_type=DecisionType.handoff_rejected,
                decision_rationale=reason,
                generation_method="broker_intake",
                agent_version=self._config.agent_version,
                configuration_version=self._config.compute_config_hash()[:16],
                incident_scope_key=scope_key,
                tenant_id=tenant_id,
            )
        )

    def release_handoff_claim(self, handoff: AgentHandoffEvent, reason: str) -> None:
        """Release a scoped processing claim before broker redelivery."""
        self._pipeline._release_handoff_claim(
            handoff,
            f"{handoff.tenant_id}:{handoff.incident_id}",
            reason,
        )

    def list_plan_history(self, incident_id: str, tenant_id: str) -> list[dict[str, Any]]:
        return self._plan_repository.list_history(
            incident_id,
            f"{tenant_id}:{incident_id}",
        )

    def get_plan_version(
        self,
        incident_id: str,
        version: int,
        tenant_id: str,
    ) -> dict[str, Any] | None:
        if version < 1:
            return None
        return self._plan_repository.get(
            f"ep-{incident_id}-v{version}",
            f"{tenant_id}:{incident_id}",
        )

    def query_audits(
        self,
        *,
        incident_id: str,
        tenant_id: str,
        plan_id: str | None = None,
        decision_type: DecisionType | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> AuditQueryPage:
        return self._pipeline.audit_writer.query(
            incident_id=incident_id,
            tenant_id=tenant_id,
            plan_id=plan_id,
            decision_type=(decision_type.value if decision_type is not None else None),
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            cursor=cursor,
        )

    def active_plans(self, incident_id: str, tenant_id: str) -> list[EvacuationPlan]:
        self.expire_due_plans(incident_id, tenant_id)
        return self._plan_repository.active_plans(
            incident_id,
            f"{tenant_id}:{incident_id}",
        )

    def authoritative_plan(
        self,
        incident_id: str,
        tenant_id: str,
    ) -> EvacuationPlan | None:
        self.expire_due_plans(incident_id, tenant_id)
        return self._plan_repository.authoritative_plan(
            incident_id,
            f"{tenant_id}:{incident_id}",
        )

    def expire_due_plans(self, incident_id: str, tenant_id: str) -> list[EvacuationPlan]:
        try:
            expired = self._plan_repository.expire_due(
                incident_id,
                f"{tenant_id}:{incident_id}",
            )
        except Exception:
            self.update_cosmos_health(False, datetime.now(UTC))
            raise
        if self._cosmos_plans is not None:
            self.update_cosmos_health(True, datetime.now(UTC))
        self.change_active_plan_count(
            -len(expired),
            tenant_id=tenant_id,
        )
        for plan in expired:
            self._audit_plan_expiry(plan)
        return expired

    def expire_all_due_plans(self) -> list[EvacuationPlan]:
        try:
            expired = self._plan_repository.expire_all_due()
        except Exception:
            self.update_cosmos_health(False, datetime.now(UTC))
            raise
        if self._cosmos_plans is not None:
            self.update_cosmos_health(True, datetime.now(UTC))
        self.change_active_plan_count(-len(expired))
        for plan in expired:
            self._audit_plan_expiry(plan)
        return expired

    def record_health_transition(self, status: str, observed_at: datetime) -> None:
        previous = self._last_health_status
        self._last_health_status = status
        if previous is None or previous == status:
            return
        record = EvacuationDecisionRecord(
            handoff_id=f"health-{observed_at.isoformat()}",
            operation_id="health-transition",
            incident_id="system-health",
            decision_type=DecisionType.degradation_detected,
            decision_rationale=f"Health status changed from {previous} to {status}",
            generation_method="health_monitor",
            agent_version=self._config.agent_version,
            configuration_version=self._config.compute_config_hash()[:16],
            incident_scope_key="system:system-health",
            tenant_id="system",
            immediate_human_review_required=status != "healthy",
        )
        receipt = self._pipeline.audit_writer.write(record)
        if receipt is None or not receipt.accepted:
            raise RuntimeError("Health transition audit was not accepted")

    def _audit_plan_expiry(self, plan: EvacuationPlan) -> None:
        receipt = self._pipeline.audit_writer.write(
            EvacuationDecisionRecord(
                handoff_id=f"expiry-{plan.plan_id}",
                plan_id=plan.plan_id,
                incident_id=plan.incident_id,
                version=plan.version,
                decision_type=DecisionType.plan_updated,
                decision_rationale=(f"Plan expired at {plan.updated_at.isoformat()} after its review window elapsed"),
                generation_method="lifecycle_expiry",
                agent_version=self._config.agent_version,
                configuration_version=self._config.compute_config_hash()[:16],
                incident_scope_key=plan.incident_scope_key,
                tenant_id=plan.tenant_id,
                route_ids=[route.route_id for route in plan.routes],
                routes_count=len(plan.routes),
                transport_requests_count=len(plan.transport_requirements),
                zone_ids=[str(zone.zone_number) for zone in plan.zones],
                population_affected=plan.population_estimate,
                constraints_applied=["lifecycle:valid_until_elapsed"],
                assessment_id=plan.traceability.risk_assessment_id,
                recommendation_id=plan.traceability.recommendation_id,
                input_signal_ids=plan.traceability.input_signal_ids,
            )
        )
        if receipt is None or not receipt.accepted:
            raise RuntimeError("Plan expiry audit was not accepted")

    def process_replan(
        self,
        incident_id: str,
        current_plan: dict[str, Any] | None = None,
        new_road_closures: list[str] | None = None,
        hazard_area_change_pct: float | None = None,
        progress_delay_pct: float | None = None,
        new_severity: str | None = None,
        current_severity: str | None = None,
        manual_trigger: bool = False,
        shelter_zones_with_new_routes: list[int] | None = None,
        updated_zones: list[dict[str, Any]] | None = None,
        progress_completed_pct: float | None = None,
        expected_progress_pct: float | None = None,
        update_id: str | None = None,
        observed_at: datetime | None = None,
        requested_by: str | None = None,
        request_role: str | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate replan triggers and execute replan if warranted.

        Returns a dict with ``triggered``, ``triggers``, ``rate_limited``,
        ``material_change``, and optionally ``change_summary``.
        """
        import time as _time

        with tel.start_span(
            "evacuation.replan",
            attributes={
                "incident_id": incident_id,
                "tenant_id": str((current_plan or {}).get("tenant_id") or ""),
                "update_id": update_id or "",
                "correlation_id": update_id or f"replan-{incident_id}",
            },
        ):
            replan_start = _time.monotonic()
            if current_plan is None:
                raise RuntimeError("Replan requires a current persisted plan")
            if self._cosmos_plans is None:
                raise RuntimeError("Replan repository unavailable")
            if current_plan.get("incident_id") != incident_id:
                raise RuntimeError("Replan source belongs to another incident")
            incident_scope_key = str(current_plan.get("incident_scope_key") or "")
            tenant_id = str(current_plan.get("tenant_id") or "")
            etag = str(current_plan.get("_etag") or "")
            if not incident_scope_key or not tenant_id or not etag:
                raise RuntimeError("Replan source is missing scope or concurrency metadata")
            if observed_at is not None:
                if observed_at.tzinfo is None:
                    raise RuntimeError("Replan observation time must be timezone-aware")
                source_updated_at = datetime.fromisoformat(str(current_plan.get("updated_at")).replace("Z", "+00:00"))
                if source_updated_at.tzinfo is None:
                    source_updated_at = source_updated_at.replace(tzinfo=UTC)
                if observed_at < source_updated_at:
                    raise RuntimeError("Stale replan update predates the source plan")

            parsed_updated_zones: list[EvacuationZone] | None = None
            if updated_zones is not None:
                try:
                    parsed_updated_zones = [EvacuationZone.model_validate(zone) for zone in updated_zones]
                except (TypeError, ValueError) as exc:
                    raise RuntimeError(f"Updated zones are invalid: {exc}") from exc
                hazard_area_change_pct = self._derive_zone_area_change_pct(
                    current_plan.get("zones", []),
                    [zone.model_dump(mode="json") for zone in parsed_updated_zones],
                )
            elif hazard_area_change_pct is not None:
                raise RuntimeError("Hazard expansion requires an updated zone snapshot")

            if progress_completed_pct is not None or expected_progress_pct is not None:
                if progress_completed_pct is None or expected_progress_pct is None:
                    raise RuntimeError("Progress evidence requires completed and expected percentages")
                if not (0 <= progress_completed_pct <= 100 and 0 < expected_progress_pct <= 100):
                    raise RuntimeError("Progress percentages are outside 0..100")
                progress_delay_pct = max(
                    0.0,
                    (expected_progress_pct - progress_completed_pct) / expected_progress_pct * 100,
                )

            stored_severity = str((current_plan.get("hazard_summary") or {}).get("severity_level") or "")
            if current_severity is not None and current_severity != stored_severity:
                raise RuntimeError("Current severity assertion does not match the source plan")
            current_severity = stored_severity or current_severity

            with tel.start_span("evacuation.evaluate_replan_trigger"):
                triggers = self._replanner.evaluate_triggers(
                    incident_id=incident_id,
                    current_plan=current_plan,
                    new_road_closures=new_road_closures,
                    hazard_area_change_pct=hazard_area_change_pct,
                    progress_delay_pct=progress_delay_pct,
                    new_severity=new_severity,
                    current_severity=current_severity,
                    manual_trigger=manual_trigger,
                    shelter_zones_with_new_routes=shelter_zones_with_new_routes,
                )

            result: dict[str, Any] = {
                "status": "unchanged",
                "triggered": bool(triggers),
                "triggers": triggers,
                "rate_limited": False,
                "material_change": False,
                "change_summary": None,
                "previous_plan_id": current_plan.get("plan_id"),
                "new_plan_id": None,
                "audit_record_id": None,
                "update_id": update_id,
            }

            if not triggers:
                audit = self._write_replan_evaluation(
                    current_plan,
                    triggers,
                    "Replan evaluated; no material trigger was present",
                    update_id,
                    requested_by,
                    request_role,
                    justification,
                )
                result["audit_record_id"] = audit.id
                return result

            # Rate limiting
            if self._replanner.is_rate_limited(incident_scope_key):
                result["rate_limited"] = True
                result["status"] = "rate_limited"
                audit = self._write_replan_evaluation(
                    current_plan,
                    triggers,
                    "Replan rate limited; no plan version created",
                    update_id,
                    requested_by,
                    request_role,
                    justification,
                )
                result["audit_record_id"] = audit.id
                return result

            new_plan = _cosmos_write_body(current_plan)
            if parsed_updated_zones is not None:
                zones = parsed_updated_zones
                new_plan["zones"] = [zone.model_dump(mode="json") for zone in zones]
                new_plan["total_population"] = sum(zone.population_estimate for zone in zones)
                new_plan["population_estimate"] = new_plan["total_population"]
            else:
                zones = [EvacuationZone.model_validate(zone) for zone in new_plan.get("zones", [])]
            new_plan["total_population"] = sum(zone.population_estimate for zone in zones)
            new_plan["population_estimate"] = new_plan["total_population"]

            requested_closures = {
                edge_id for edge_id in (new_road_closures or []) if self._road_network.get_edge(edge_id) is not None
            }
            known_closures = {
                edge_id
                for edge_id in current_plan.get("last_road_closures", [])
                if self._road_network.get_edge(edge_id) is not None
            } | requested_closures
            with tel.start_span("evacuation.incremental_road_update"):
                effective_network = self._build_replan_network(zones, known_closures)
                new_plan["last_road_closures"] = sorted(known_closures)
                data_snapshot = dict(new_plan.get("data_snapshot") or {})
                data_snapshot["road_network_version"] = effective_network.get_version()
                data_snapshot["snapshot_at"] = datetime.now(UTC).isoformat()
                new_plan["data_snapshot"] = data_snapshot

            with tel.start_span("evacuation.recompute_affected_routes"):
                (
                    new_plan["routes"],
                    new_plan["routing_mode"],
                    new_plan["hazard_routing_data_gaps"],
                    new_plan["excluded_destinations"],
                    new_plan["corridor_loads"],
                    new_plan["excluded_roads"],
                    new_plan["destination_allocations"],
                    new_plan["unresolved_destination_demands"],
                ) = self._recompute_replan_routes(
                    current_plan=current_plan,
                    zones=zones,
                    road_network=effective_network,
                    closed_edge_ids=known_closures,
                    recompute_all=bool(updated_zones or new_severity),
                    recovery_zone_numbers=set(shelter_zones_with_new_routes or []),
                )
                new_plan["zones"] = [zone.model_dump(mode="json") for zone in zones]
                _set_route_inventory(
                    new_plan,
                    zones,
                    new_plan["routes"],
                    new_plan["excluded_roads"],
                )

            with tel.start_span("evacuation.update_transport"):
                if updated_zones is not None:
                    _recompute_transport_coordination(
                        self,
                        new_plan,
                        zones,
                    )

            with tel.start_span("evacuation.reestimate_timeline"):
                hazard_summary = dict(new_plan.get("hazard_summary") or {})
                if new_severity is not None:
                    hazard_summary["severity_level"] = new_severity
                new_plan["hazard_summary"] = hazard_summary
                arrival_minutes = hazard_summary.get("estimated_arrival_minutes")
                horizon_hours = float(arrival_minutes) / 60 if arrival_minutes is not None else None
                timeline_routes = deepcopy(new_plan["routes"])
                if progress_delay_pct is not None and progress_delay_pct > 0:
                    delay_factor = 1 + progress_delay_pct / 100
                    for route in timeline_routes:
                        capacity = int(route.get("capacity_vehicles_per_hour", 0))
                        route["capacity_vehicles_per_hour"] = (
                            max(
                                1,
                                int(capacity / delay_factor),
                            )
                            if capacity > 0
                            else 0
                        )
                phases, dispositions, timeline_assumptions = self._pipeline._timeline_estimator.estimate_timeline(
                    zones=new_plan["zones"],
                    routes=timeline_routes,
                    transport_requirements=new_plan.get("transport_requirements", []),
                    hazard_type=hazard_summary.get("hazard_type", "bushfire"),
                    hazard_time_horizon_hours=horizon_hours,
                    corridor_loads=new_plan.get("corridor_loads", []),
                    timeline_anchor=(
                        datetime.fromisoformat(
                            str(new_plan.get("created_at")).replace(
                                "Z",
                                "+00:00",
                            )
                        )
                        if new_plan.get("created_at")
                        else observed_at
                    ),
                )
                new_plan["assumptions"] = list(
                    dict.fromkeys(
                        [
                            *new_plan.get("assumptions", []),
                            *timeline_assumptions,
                        ]
                    )
                )
                new_plan["phases"] = [phase.model_dump(mode="json") for phase in phases]
                new_plan["zone_dispositions"] = [disposition.model_dump(mode="json") for disposition in dispositions]
                new_plan["shelter_in_place_zones"] = [
                    str(disposition.zone_number)
                    for disposition in dispositions
                    if disposition.disposition == ZoneDispositionType.shelter_in_place
                ]
                new_plan["estimated_completion_minutes"] = self._pipeline._timeline_estimator.plan_completion_minutes(
                    phases
                )
                if progress_delay_pct is not None:
                    new_plan["progress_delay_pct"] = progress_delay_pct
                if hazard_area_change_pct is not None:
                    new_plan["hazard_area_change_pct"] = hazard_area_change_pct

            result["material_change"] = self._replanner.detect_material_change(
                current_plan,
                new_plan,
            )
            if not result["material_change"]:
                self._replanner.record_replan(incident_scope_key)
                audit = self._write_replan_evaluation(
                    current_plan,
                    triggers,
                    "Replan evaluated; structured plan content is unchanged",
                    update_id,
                    requested_by,
                    request_role,
                    justification,
                )
                result["audit_record_id"] = audit.id
                return result

            now = datetime.now(UTC)
            with tel.start_span("evacuation.assign_version"):
                new_version, new_plan_id, counter_operation = self._reserve_replan_version(
                    incident_id,
                    incident_scope_key,
                    int(current_plan.get("version", 1)),
                )
            new_plan.update(
                {
                    "id": new_plan_id,
                    "plan_id": new_plan_id,
                    "version": new_version,
                    "status": PlanStatus.proposed.value,
                    "source_plan_id": current_plan.get("plan_id"),
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "replan_triggers": list(triggers),
                    "valid_until": current_plan.get("valid_until"),
                }
            )
            with tel.start_span("evacuation.generate_change_summary"):
                result["change_summary"] = self._build_replan_change_summary(
                    current_plan,
                    new_plan,
                    triggers,
                    known_closures,
                )
                new_plan["change_summary"] = result["change_summary"]
                _refresh_deterministic_summary(self, new_plan)
            try:
                validated = EvacuationPlan.model_validate(new_plan)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"Replanned document is invalid: {exc}") from exc

            with tel.start_span("evacuation.persist_plan"):
                try:
                    self._cosmos_plans.execute_item_batch(
                        batch_operations=[
                            counter_operation,
                            (
                                "replace",
                                (
                                    str(current_plan.get("plan_id")),
                                    _source_guard_for_new_proposal(
                                        current_plan,
                                        new_plan_id,
                                        now,
                                    ),
                                ),
                                {"if_match_etag": etag},
                            ),
                            ("create", (_cosmos_write_body(new_plan),)),
                        ],
                        partition_key=incident_scope_key,
                    )
                except Exception as exc:
                    if any(token in str(exc) for token in ("412", "PreconditionFailed", "409", "Conflict")):
                        raise RuntimeError("PreconditionFailed: stale plan") from exc
                    self.update_cosmos_health(False, datetime.now(UTC))
                    raise RuntimeError("Failed to persist replanned document") from exc
                self.update_cosmos_health(True, datetime.now(UTC))

            result.update(
                {
                    "previous_plan_id": current_plan.get("plan_id"),
                    "new_plan_id": new_plan_id,
                    "version": new_version,
                }
            )
            self._replanner.record_replan(incident_scope_key)

            with tel.start_span("evacuation.write_audit"):
                decision = EvacuationDecisionRecord(
                    handoff_id=update_id or f"replan-{incident_id}",
                    operation_id=update_id or f"replan-{incident_id}",
                    plan_id=new_plan_id,
                    incident_id=incident_id,
                    version=new_version,
                    decision_type=DecisionType.plan_updated,
                    decision_rationale=(result.get("change_summary") or "replan applied"),
                    generation_method="deterministic_replan",
                    agent_version=self._config.agent_version,
                    configuration_version=self._config.compute_config_hash()[:16],
                    incident_scope_key=incident_scope_key,
                    tenant_id=tenant_id,
                    route_ids=[route.route_id for route in validated.routes],
                    zone_ids=[str(zone.zone_number) for zone in validated.zones],
                    population_affected=validated.total_population,
                    confidence_raw=validated.confidence_score,
                    confidence_adjusted=validated.confidence_score,
                    zone_dispositions=validated.zone_dispositions,
                    assessment_id=validated.traceability.risk_assessment_id,
                    recommendation_id=validated.traceability.recommendation_id,
                    input_signal_ids=validated.traceability.input_signal_ids,
                    routes_count=len(validated.routes),
                    transport_requests_count=len(validated.transport_requirements),
                    constraints_applied=sorted(f"road_exclusion:{road.edge_id}" for road in validated.excluded_roads),
                    replanning_triggers=self._canonical_replanning_triggers(triggers),
                    principal_id=requested_by,
                )
                if requested_by:
                    decision.decision_rationale += (
                        f" Requested by {requested_by} ({request_role or 'unknown'}): "
                        f"{justification or 'no justification'}"
                    )
                receipt = self._pipeline.audit_writer.write(decision)
                if receipt is None or not receipt.accepted:
                    raise RuntimeError("Replan audit was not accepted")
                result["audit_record_id"] = decision.id
                result["status"] = "plan_version_created"

            self._pipeline.record_committed_plan(new_plan_id, tenant_id)
            if current_plan.get("status") != PlanStatus.proposed.value:
                self.change_active_plan_count(1, tenant_id=tenant_id)

            # Shelter-to-evacuation recovery metrics
            previous_shelter_zones = set(current_plan.get("shelter_in_place_zones", []))
            for zone_number in previous_shelter_zones:
                recovered_route = next(
                    (route for route in validated.routes if route.zone_id == str(zone_number) and route.route_id),
                    None,
                )
                if recovered_route is not None:
                    tel.shelter_to_evacuation_recovery_count.add(
                        1,
                        attributes={
                            "incident_id": incident_id,
                            "tenant_id": tenant_id,
                        },
                    )
                    tel.emit_shelter_to_evacuation_recovery(
                        plan_id=new_plan_id,
                        zone=str(zone_number),
                        new_route_id=recovered_route.route_id,
                    )

            # Emit PlanUpdated event
            tel.emit_plan_updated(
                plan_id=new_plan_id,
                version=new_version,
                triggers=triggers,
                change_summary=result.get("change_summary") or "",
            )
            tel.replan_count.add(
                1,
                attributes={
                    "incident_id": incident_id,
                    "tenant_id": tenant_id,
                },
            )

            # Replan latency & SLA
            replan_ms = (_time.monotonic() - replan_start) * 1000
            tel.replan_latency.record(
                replan_ms,
                attributes={
                    "incident_id": incident_id,
                    "tenant_id": tenant_id,
                    "outcome": "succeeded",
                },
            )
            if replan_ms > 15_000:
                tel.replan_sla_breach_count.add(1)
                tel.emit_sla_breach(
                    update_id or new_plan_id,
                    replan_ms,
                    "replan",
                )

            return result

    def _build_replan_network(
        self,
        zones: list[EvacuationZone],
        closed_edge_ids: set[str],
    ) -> RoadNetworkLoader:
        if not self._road_network.is_loaded:
            raise RuntimeError("Road network unavailable for replanning")
        edge_documents = []
        for edge in self._road_network.get_all_edges():
            document = edge.model_dump()
            if edge.id in closed_edge_ids:
                document["closure_status"] = "closed"
                document["closure_reason"] = "emergency_services_closure"
                document["capacity_vehicles_per_hour"] = 0
            geometry = self._road_network.get_edge_geometry(edge.id)
            if geometry is not None:
                document["_geometry"] = geometry
            edge_documents.append(document)
        zone_polygons = self._pipeline._zone_computer.get_zone_polygons(zones)
        adjusted_edges = self._pipeline._zone_computer.apply_zone_capacity_reduction(
            edge_documents,
            zone_polygons,
        )
        return self._road_network.effective_copy(adjusted_edges)

    def _write_replan_evaluation(
        self,
        current_plan: dict[str, Any],
        triggers: list[str],
        rationale: str,
        update_id: str | None,
        requested_by: str | None,
        request_role: str | None,
        justification: str | None,
    ) -> EvacuationDecisionRecord:
        incident_id = str(current_plan.get("incident_id", ""))
        record = EvacuationDecisionRecord(
            handoff_id=update_id or f"replan-evaluation-{incident_id}",
            operation_id=update_id or f"replan-evaluation-{incident_id}",
            plan_id=str(current_plan.get("plan_id", "")),
            incident_id=incident_id,
            version=int(current_plan.get("version", 0)),
            decision_type=DecisionType.plan_updated,
            decision_rationale=(
                f"{rationale}. Triggers: {triggers or 'none'}. "
                f"Requested by {requested_by or 'system'} "
                f"({request_role or 'system'}): {justification or 'not supplied'}"
            ),
            generation_method="deterministic_replan_evaluation",
            agent_version=self._config.agent_version,
            configuration_version=self._config.compute_config_hash()[:16],
            incident_scope_key=str(current_plan.get("incident_scope_key", "")),
            tenant_id=str(current_plan.get("tenant_id", "")),
            route_ids=[str(route.get("route_id", "")) for route in current_plan.get("routes", [])],
            routes_count=len(current_plan.get("routes", [])),
            transport_requests_count=len(current_plan.get("transport_requirements", [])),
            replanning_triggers=self._canonical_replanning_triggers(triggers),
            principal_id=requested_by,
            assessment_id=(current_plan.get("traceability") or {}).get("risk_assessment_id"),
            recommendation_id=(current_plan.get("traceability") or {}).get("recommendation_id"),
            input_signal_ids=list(
                (current_plan.get("traceability") or {}).get(
                    "input_signal_ids",
                    [],
                )
            ),
        )
        receipt = self._pipeline.audit_writer.write(record)
        if receipt is None or not receipt.accepted:
            raise RuntimeError("Replan evaluation audit was not accepted")
        return record

    @staticmethod
    def _canonical_replanning_triggers(triggers: list[str]) -> list[str]:
        mapping = {
            "road_closure": "new_road_closure",
            "hazard_expansion": "hazard_expansion",
            "progress_delay": "progress_delay",
            "severity_escalation": "severity_escalation",
            "manual_trigger": "manual_trigger",
            "shelter_recovery": "shelter_to_evacuation_recovery",
        }
        return [mapping[prefix] for trigger in triggers if (prefix := trigger.split(":", 1)[0]) in mapping]

    @staticmethod
    def _derive_zone_area_change_pct(
        current_zones: list[dict[str, Any]],
        updated_zones: list[dict[str, Any]],
    ) -> float:
        from shapely.geometry import shape
        from shapely.ops import unary_union

        def merged_area(zones: list[dict[str, Any]]) -> float:
            polygons = []
            for zone in zones:
                boundary = zone.get("boundary")
                if not boundary:
                    continue
                polygon = shape(boundary)
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                if not polygon.is_empty and polygon.area > 0:
                    polygons.append(polygon)
            return float(unary_union(polygons).area) if polygons else 0.0

        current_area = merged_area(current_zones)
        updated_area = merged_area(updated_zones)
        if current_area <= 0:
            return 100.0 if updated_area > 0 else 0.0
        return (updated_area - current_area) / current_area * 100

    def _recompute_replan_routes(
        self,
        *,
        current_plan: dict[str, Any],
        zones: list[EvacuationZone],
        road_network: RoadNetworkLoader,
        closed_edge_ids: set[str],
        recompute_all: bool,
        recovery_zone_numbers: set[int],
    ) -> tuple[
        list[dict[str, Any]],
        str,
        list[str],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        current_routes = deepcopy(current_plan.get("routes", []))
        zone_numbers_by_id = {
            str(identifier): zone.zone_number
            for zone in zones
            for identifier in (zone.zone_number, zone.zone_id)
            if identifier not in (None, "")
        }
        affected_zones = {
            zone_numbers_by_id[str(route.get("zone_id"))]
            for route in current_routes
            if closed_edge_ids.intersection(route.get("waypoints", []))
            and str(route.get("zone_id")) in zone_numbers_by_id
        }
        affected_zones.update(recovery_zone_numbers)
        if recompute_all:
            affected_zones.update(zone.zone_number for zone in zones)
        if not affected_zones:
            return (
                current_routes,
                str(
                    current_plan.get(
                        "routing_mode",
                        "hazard_constrained_degraded",
                    )
                ),
                list(current_plan.get("hazard_routing_data_gaps", [])),
                list(current_plan.get("excluded_destinations", [])),
                list(current_plan.get("corridor_loads", [])),
                list(current_plan.get("excluded_roads", [])),
                list(current_plan.get("destination_allocations", [])),
                list(current_plan.get("unresolved_destination_demands", [])),
            )

        retained = [
            route for route in current_routes if zone_numbers_by_id.get(str(route.get("zone_id"))) not in affected_zones
        ]
        hazard_sources = [
            HazardSourceSnapshot.model_validate(source)
            for source in (current_plan.get("hazard_summary") or {}).get(
                "sources",
                [],
            )
        ]
        route_computer = RouteComputer(
            road_network=road_network,
            config=self._config,
            hazard_context=self._pipeline._build_hazard_routing_context(
                hazard_sources,
                str(current_plan.get("incident_scope_key", "")),
            ),
        )
        excluded_edges = {edge.id for edge in road_network.get_closed_edges()}
        replacement_models: list[EvacuationRoute] = []
        origins_by_zone = self._pipeline._assign_zone_origin_nodes(
            zones,
            road_network,
        )
        for zone in zones:
            if zone.zone_number not in affected_zones:
                continue
            origins = origins_by_zone[zone.zone_number]
            zone.origin_node_ids = origins
            zone.origin_coverage_status = (
                OriginCoverageStatus.covered
                if origins
                else (
                    OriginCoverageStatus.no_network_origin
                    if zone.population_estimate > 0
                    else OriginCoverageStatus.not_required
                )
            )
            computed = route_computer.compute_routes(
                origin_nodes=origins,
                zone_number=zone.zone_number,
                population=zone.population_estimate,
                hazard_type=(current_plan.get("hazard_summary") or {}).get(
                    "hazard_type",
                    "bushfire",
                ),
                excluded_edge_ids=excluded_edges,
                allocate_population=False,
            )
            replacement_models.extend(computed)
        route_models = [EvacuationRoute.model_validate(route) for route in retained] + replacement_models
        route_computer.allocate_plan_routes(
            route_models,
            {zone.zone_number: zone.population_estimate for zone in zones},
            {zone.zone_number: zone.vulnerable_population for zone in zones},
        )
        for zone in zones:
            zone.unallocated_route_population = route_computer.unallocated_population_by_zone.get(
                zone.zone_number,
                zone.population_estimate,
            )
        retained_by_id = {str(route.get("route_id")): route for route in retained}
        allocation_fields = {
            "allocated_population",
            "evacuation_load_vehicles_per_hour",
            "uncapped_utilisation_pct",
            "congestion_risk_pct",
            "congestion_risk",
            "capacity_overloaded",
            "bottleneck_edge_ids",
            "zone_shared_capacity_vehicles_per_hour",
        }
        routes = []
        for route in route_models:
            route_document = route.model_dump(mode="json")
            retained_document = retained_by_id.get(route.route_id)
            if retained_document is None:
                routes.append(route_document)
                continue
            merged = deepcopy(retained_document)
            merged.update({field: route_document[field] for field in allocation_fields})
            routes.append(merged)
        if any(not route.get("route_id") for route in routes):
            raise RuntimeError("Replanning produced a route without an ID")
        return (
            routes,
            route_computer.routing_mode.value,
            route_computer.hazard_data_gaps,
            [exclusion.model_dump(mode="json") for exclusion in route_computer.destination_exclusions],
            [load.model_dump(mode="json") for load in route_computer.corridor_loads],
            [road.model_dump(mode="json") for road in route_computer.excluded_roads],
            [allocation.model_dump(mode="json") for allocation in route_computer.destination_allocations],
            [demand.model_dump(mode="json") for demand in route_computer.unresolved_destination_demands],
        )

    def _reserve_replan_version(
        self,
        incident_id: str,
        incident_scope_key: str,
        source_version: int,
    ) -> tuple[int, str, tuple[Any, ...]]:
        counter_id = f"{incident_id}_plan_counter"
        counter_document: dict[str, Any] | None = None
        try:
            counter_document = self._cosmos_plans.read_item(
                item=counter_id,
                partition_key=incident_scope_key,
            )
        except Exception as exc:
            if "404" not in str(exc) and "NotFound" not in str(exc):
                raise RuntimeError("Failed to reserve replan version") from exc
        current_version = int(counter_document.get("current_version", 0)) if counter_document is not None else 0
        version = max(source_version, current_version) + 1
        plan_id = f"ep-{incident_id}-v{version}"
        if counter_document is None:
            operation: tuple[Any, ...] = (
                "create",
                (
                    {
                        "id": counter_id,
                        "current_version": version,
                        "incident_scope_key": incident_scope_key,
                    },
                ),
            )
        else:
            counter_etag = str(counter_document.get("_etag") or "")
            if not counter_etag:
                raise RuntimeError("Version counter has no concurrency token")
            body = _cosmos_write_body(counter_document)
            body["current_version"] = version
            operation = (
                "replace",
                (counter_id, body),
                {"if_match_etag": counter_etag},
            )
        return version, plan_id, operation

    @staticmethod
    def _build_replan_change_summary(
        current_plan: dict[str, Any],
        new_plan: dict[str, Any],
        triggers: list[str],
        closed_edge_ids: set[str],
    ) -> str:
        changes = [f"Triggers: {', '.join(triggers)}"]
        old_routes = {
            str(route.get("route_id")): tuple(route.get("waypoints", [])) for route in current_plan.get("routes", [])
        }
        new_routes = {
            str(route.get("route_id")): tuple(route.get("waypoints", [])) for route in new_plan.get("routes", [])
        }
        if old_routes != new_routes:
            route_changes = []
            for route_id in sorted(set(old_routes) | set(new_routes)):
                old_path = old_routes.get(route_id)
                new_path = new_routes.get(route_id)
                if old_path == new_path:
                    continue
                route_changes.append(
                    f"{route_id}: {list(old_path) if old_path is not None else 'added'}"
                    f" -> {list(new_path) if new_path is not None else 'removed'}"
                )
            changes.append("Routes changed: " + "; ".join(route_changes))
        if closed_edge_ids:
            changes.append(f"Closed roads excluded: {sorted(closed_edge_ids)}")
        if current_plan.get("zones") != new_plan.get("zones"):
            changes.append("Zone boundaries or populations changed")
        if current_plan.get("assembly_areas") != new_plan.get("assembly_areas"):
            changes.append("Assembly areas changed")
        if current_plan.get("transport_requirements") != new_plan.get("transport_requirements"):
            changes.append("Transport coordination changed")
        if current_plan.get("phases") != new_plan.get("phases"):
            changes.append(
                "Timeline changed: "
                f"{current_plan.get('estimated_completion_minutes')} -> "
                f"{new_plan.get('estimated_completion_minutes')} minutes"
            )
        old_severity = (current_plan.get("hazard_summary") or {}).get("severity_level")
        new_severity = (new_plan.get("hazard_summary") or {}).get("severity_level")
        if old_severity != new_severity:
            changes.append(f"Severity changed: {old_severity} -> {new_severity}")
        return ". ".join(changes) + "."

    # ------------------------------------------------------------------
    # Backward-compatible API
    # ------------------------------------------------------------------

    def review(self, scenario_type: str, jurisdictions: list[str]) -> dict[str, object]:
        """Legacy review endpoint for backward compatibility."""
        route_pressure = "high" if scenario_type in {"flood", "bushfire"} else "moderate"
        return {
            "scenarioType": scenario_type,
            "jurisdictions": jurisdictions,
            "routePressure": route_pressure,
            "recommendation": ("Validate assembly areas and transport corridors before public release."),
        }


# ---------------------------------------------------------------------------
# FastAPI application — health, override, and replan endpoints
# ---------------------------------------------------------------------------

from pydantic import BaseModel as _PydanticBaseModel  # noqa: E402


class _RoadNetworkDetail(_PydanticBaseModel):
    status: str
    node_count: int = 0
    edge_count: int = 0
    stale: bool = False
    last_loaded_at: str | None = None
    source_updated_at: str | None = None


class _HealthCheckDetail(_PydanticBaseModel):
    status: str
    last_checked_at: str | None = None
    last_successful_at: str | None = None
    latency_ms: int | None = None


class _ActivePlanDetail(_PydanticBaseModel):
    count: int
    status: str


class _ProcessingQueueDetail(_PydanticBaseModel):
    depth: int
    status: str
    connected: bool = False
    last_checked_at: str | None = None
    last_successful_at: str | None = None


class _AuditStoreDetail(_PydanticBaseModel):
    status: str
    buffer_depth: int = 0


class _HealthChecks(_PydanticBaseModel):
    road_network_loaded: _RoadNetworkDetail
    llm_connectivity: _HealthCheckDetail
    cosmos_connectivity: _HealthCheckDetail
    active_plan_count: _ActivePlanDetail
    processing_queue_depth: _ProcessingQueueDetail
    audit_store: _AuditStoreDetail


class _HealthResponse(_PydanticBaseModel):
    status: str
    agent_version: str
    timestamp: str
    checks: _HealthChecks


class _OverrideRequest(_PydanticBaseModel):
    plan_id: str
    incident_id: str
    action: str  # approve | reject | cancel | pause | resume | modify
    user_id: str | None = None
    role: str | None = None
    justification: str
    modifications: dict[str, object] | None = None


class _OverrideResponse(_PydanticBaseModel):
    plan_id: str
    previous_status: str
    new_status: str
    override_timestamp: str
    audit_record_id: str
    new_version_plan_id: str | None = None


class _ReplanRequest(_PydanticBaseModel):
    plan_id: str
    incident_id: str
    update_id: str
    base_plan_version: int
    observed_at: datetime
    user_id: str | None = None
    role: str | None = None
    justification: str
    new_road_closures: list[str] | None = None
    updated_zones: list[dict[str, Any]] | None = None
    progress_completed_pct: float | None = None
    expected_progress_pct: float | None = None
    new_severity: str | None = None
    manual_trigger: bool = True
    shelter_zones_with_new_routes: list[int] | None = None


class _ReplanResponse(_PydanticBaseModel):
    status: str
    incident_id: str
    previous_plan_id: str
    new_plan_id: str | None = None
    audit_record_id: str
    triggered: bool
    triggers: list[str]
    material_change: bool
    change_summary: str | None = None


def create_app(
    agent: EvacuationAgent | None = None,
    config: EvacuationConfig | None = None,
    principal_resolver: Callable[[Any], AuthenticatedPrincipal | Awaitable[AuthenticatedPrincipal]] | None = None,
    lifespan: Any = None,
) -> Any:
    """Create the FastAPI application with health, override, and replan endpoints.

    Follows the same factory pattern as ``risk_assessment.agent.create_app()``.
    """
    from fastapi import Depends, FastAPI, HTTPException
    from fastapi.responses import JSONResponse

    _config = config or EvacuationConfig()
    app = FastAPI(
        title="Evacuation Agent",
        version=_config.agent_version,
        lifespan=lifespan,
    )

    # Store dependencies on app state
    app.state.agent = agent
    app.state.config = _config
    resolve_principal = principal_resolver or EntraPrincipalResolver()

    async def authorized_commander(request: Request) -> AuthenticatedPrincipal:
        resolved = resolve_principal(request)
        principal = await resolved if inspect.isawaitable(resolved) else resolved
        allowed_roles = {normalize_role(role) for role in _AUTHORIZED_OVERRIDE_ROLES}
        if not any(normalize_role(role) in allowed_roles for role in principal.roles):
            raise HTTPException(status_code=403, detail="Evacuation commander role is required")
        return principal

    def authorize_scope(
        principal: AuthenticatedPrincipal,
        *,
        incident_id: str,
        user_id: str | None,
        role: str | None,
        justification: str,
    ) -> str:
        if incident_id not in principal.incident_ids:
            raise HTTPException(status_code=403, detail="Commander is not assigned to this incident")
        if user_id is not None and user_id != principal.subject:
            raise HTTPException(status_code=403, detail="Body user_id must match authenticated identity")
        if role is not None and not principal.has_asserted_role(role):
            raise HTTPException(status_code=403, detail="Body role must match an authenticated role")
        if not justification.strip():
            raise HTTPException(status_code=422, detail="Justification must not be blank")
        return f"{principal.tenant_id}:{incident_id}"

    def cached_health() -> _HealthResponse:
        current_agent: EvacuationAgent | None = app.state.agent
        if current_agent is None:
            now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            return _HealthResponse(
                status="unhealthy",
                agent_version=_config.agent_version,
                timestamp=now,
                checks=_HealthChecks(
                    road_network_loaded=_RoadNetworkDetail(status="offline"),
                    llm_connectivity=_HealthCheckDetail(status="offline"),
                    cosmos_connectivity=_HealthCheckDetail(status="offline"),
                    active_plan_count=_ActivePlanDetail(
                        count=0,
                        status="healthy",
                    ),
                    processing_queue_depth=_ProcessingQueueDetail(
                        depth=0,
                        status="offline",
                    ),
                    audit_store=_AuditStoreDetail(status="degraded"),
                ),
            )
        return _HealthResponse.model_validate(current_agent.health_snapshot())

    # ------- GET /health, /live, /ready -------

    @app.get("/health", response_model=_HealthResponse)
    async def health() -> _HealthResponse:
        """Return the cached six-check capability snapshot without I/O."""
        return cached_health()

    @app.get("/live")
    async def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/ready")
    async def ready() -> Any:
        snapshot = cached_health()
        return JSONResponse(
            status_code=503 if snapshot.status == "unhealthy" else 200,
            content=snapshot.model_dump(mode="json"),
        )

    # ------- POST /override -------

    @app.get("/plans/{incident_id}/history")
    async def plan_history(
        incident_id: str,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> list[dict[str, Any]]:
        _agent: EvacuationAgent | None = app.state.agent
        if _agent is None or _agent._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")
        authorize_scope(
            principal,
            incident_id=incident_id,
            user_id=None,
            role=None,
            justification="history retrieval",
        )
        _agent.expire_due_plans(incident_id, principal.tenant_id)
        return [_cosmos_write_body(document) for document in _agent.list_plan_history(incident_id, principal.tenant_id)]

    @app.get("/audits/{incident_id}")
    async def audit_history(
        incident_id: str,
        plan_id: str | None = None,
        decision_type: DecisionType | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 50,
        cursor: str | None = None,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> dict[str, Any]:
        _agent: EvacuationAgent | None = app.state.agent
        if _agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialised")
        authorize_scope(
            principal,
            incident_id=incident_id,
            user_id=None,
            role=None,
            justification="audit history retrieval",
        )
        if plan_id is not None and not plan_id.startswith(f"ep-{incident_id}-v"):
            raise HTTPException(
                status_code=422,
                detail="plan_id does not belong to the requested incident",
            )
        try:
            page = _agent.query_audits(
                incident_id=incident_id,
                tenant_id=principal.tenant_id,
                plan_id=plan_id,
                decision_type=decision_type,
                from_timestamp=from_timestamp,
                to_timestamp=to_timestamp,
                limit=limit,
                cursor=cursor,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "records": [record.model_dump(mode="json") for record in page.records],
            "next_cursor": page.next_cursor,
        }

    @app.get("/plans/{incident_id}/active")
    async def active_plans(
        incident_id: str,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> list[dict[str, Any]]:
        _agent: EvacuationAgent | None = app.state.agent
        if _agent is None or _agent._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")
        authorize_scope(
            principal,
            incident_id=incident_id,
            user_id=None,
            role=None,
            justification="active plan retrieval",
        )
        return [plan.model_dump(mode="json") for plan in _agent.active_plans(incident_id, principal.tenant_id)]

    @app.get("/plans/{incident_id}/versions/{version}")
    async def plan_version(
        incident_id: str,
        version: int,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> dict[str, Any]:
        _agent: EvacuationAgent | None = app.state.agent
        if _agent is None or _agent._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")
        authorize_scope(
            principal,
            incident_id=incident_id,
            user_id=None,
            role=None,
            justification="historical plan retrieval",
        )
        document = _agent.get_plan_version(
            incident_id,
            version,
            principal.tenant_id,
        )
        if document is None:
            raise HTTPException(status_code=404, detail="Plan version not found")
        return _cosmos_write_body(document)

    @app.get("/plans/{incident_id}/authoritative")
    async def authoritative_plan(
        incident_id: str,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> dict[str, Any]:
        _agent: EvacuationAgent | None = app.state.agent
        if _agent is None or _agent._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")
        authorize_scope(
            principal,
            incident_id=incident_id,
            user_id=None,
            role=None,
            justification="authoritative plan retrieval",
        )
        plan = _agent.authoritative_plan(incident_id, principal.tenant_id)
        if plan is None:
            raise HTTPException(status_code=404, detail="No active plan found")
        return plan.model_dump(mode="json")

    @app.post("/override", response_model=_OverrideResponse)
    async def override(
        override_request: _OverrideRequest,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> _OverrideResponse:
        """Incident commander override of plan status.

        Valid actions: approve, reject, cancel, pause, resume, modify.

        Valid transitions:
        - proposed → approved, rejected, cancelled, paused
        - approved → superseded, cancelled, paused
        - paused → approved, cancelled, superseded
        """
        request = override_request
        now = datetime.now(UTC)
        _agent: EvacuationAgent | None = app.state.agent

        # Validate action
        if request.action not in _VALID_ACTIONS:
            raise HTTPException(
                status_code=422,
                detail=(f"Invalid action '{request.action}'. Must be one of: {sorted(_VALID_ACTIONS)}"),
            )

        target_status = _ACTION_STATUS_MAP[request.action]
        incident_scope_key = authorize_scope(
            principal,
            incident_id=request.incident_id,
            user_id=request.user_id,
            role=request.role,
            justification=request.justification,
        )
        if _agent is None or _agent._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")

        # Retrieve plan from Cosmos
        try:
            doc = _agent._cosmos_plans.read_item(
                item=request.plan_id,
                partition_key=incident_scope_key,
            )
        except Exception as exc:
            exc_str = str(exc)
            if "NotFound" in exc_str or "404" in exc_str:
                raise HTTPException(
                    status_code=404,
                    detail=f"Plan {request.plan_id} not found",
                )
            raise HTTPException(status_code=503, detail="Failed to load plan")

        previous_status = doc.get("status", "proposed")
        if (
            doc.get("tenant_id") != principal.tenant_id
            or doc.get("incident_id") != request.incident_id
            or doc.get("incident_scope_key") != incident_scope_key
        ):
            raise HTTPException(status_code=404, detail=f"Plan {request.plan_id} not found")
        current_ps = PlanStatus(previous_status)
        etag = str(doc.get("_etag") or "")
        if not etag:
            raise HTTPException(status_code=409, detail="Plan has no concurrency token")

        authorized_role = next(
            role
            for role in principal.roles
            if normalize_role(role) in {normalize_role(candidate) for candidate in _AUTHORIZED_OVERRIDE_ROLES}
        )
        new_version_plan_id: str | None = None
        audit_plan = doc
        active_plan_delta = 0

        if request.action == "modify":
            if current_ps not in {PlanStatus.proposed, PlanStatus.approved, PlanStatus.paused}:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot modify terminal plan in {previous_status} status",
                )
            try:
                modified_doc, override_type, original_values, modified_values = _apply_plan_modification(
                    _agent, doc, request.modifications
                )
            except InvalidPlanModificationError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

            counter_id = f"{request.incident_id}_plan_counter"
            counter_doc: dict[str, Any] | None = None
            try:
                counter_doc = _agent._cosmos_plans.read_item(
                    item=counter_id,
                    partition_key=incident_scope_key,
                )
            except Exception as exc:
                if "NotFound" not in str(exc) and "404" not in str(exc):
                    raise HTTPException(status_code=503, detail="Failed to reserve plan version") from exc

            source_version = int(doc.get("version", 1))
            current_version = int(counter_doc.get("current_version", 0)) if counter_doc else 0
            new_version = max(source_version, current_version) + 1
            new_version_plan_id = f"ep-{request.incident_id}-v{new_version}"
            modified_doc.update(
                {
                    "id": new_version_plan_id,
                    "plan_id": new_version_plan_id,
                    "version": new_version,
                    "status": PlanStatus.proposed.value,
                    "source_plan_id": request.plan_id,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "valid_until": doc.get("valid_until"),
                }
            )
            modified_doc["change_summary"] = (
                f"Commander {override_type} created {new_version_plan_id} from {request.plan_id}."
            )
            override_meta = OverrideMetadata(
                override_by_user_id=principal.subject,
                override_by_role=authorized_role,
                override_justification=request.justification,
                override_action_type=override_type,
                override_timestamp=now,
                source_plan_id=request.plan_id,
                original_values=original_values,
                modified_values=modified_values,
            )
            modified_doc["overrides"] = [
                *deepcopy(doc.get("overrides", [])),
                override_meta.model_dump(mode="json"),
            ]
            try:
                EvacuationPlan.model_validate(modified_doc)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail=f"Modified plan is invalid: {exc}") from exc

            counter_operation: (
                tuple[str, tuple[dict[str, object]]] | tuple[str, tuple[str, dict[str, object]], dict[str, str]]
            )
            if counter_doc is None:
                counter_operation = (
                    "create",
                    (
                        {
                            "id": counter_id,
                            "current_version": new_version,
                            "incident_scope_key": incident_scope_key,
                        },
                    ),
                )
            else:
                counter_etag = str(counter_doc.get("_etag") or "")
                if not counter_etag:
                    raise HTTPException(status_code=409, detail="Version counter has no concurrency token")
                counter_body = _cosmos_write_body(counter_doc)
                counter_body["current_version"] = new_version
                counter_operation = (
                    "replace",
                    (counter_id, counter_body),
                    {"if_match_etag": counter_etag},
                )

            try:
                _agent._cosmos_plans.execute_item_batch(
                    batch_operations=[
                        counter_operation,
                        (
                            "replace",
                            (
                                request.plan_id,
                                _source_guard_for_new_proposal(
                                    doc,
                                    new_version_plan_id,
                                    now,
                                ),
                            ),
                            {"if_match_etag": etag},
                        ),
                        ("create", (modified_doc,)),
                    ],
                    partition_key=incident_scope_key,
                )
            except Exception as exc:
                if any(token in str(exc) for token in ("PreconditionFailed", "412", "Conflict", "409")):
                    tel.version_conflict_retries.add(1)
                    tel.emit_version_conflict(incident_id=request.incident_id, retry_count=1)
                    raise HTTPException(
                        status_code=409,
                        detail="Concurrent override conflict — retry",
                    ) from exc
                raise HTTPException(status_code=503, detail="Failed to persist modified plan") from exc
            audit_plan = modified_doc
            target_status = PlanStatus.proposed
            if current_ps != PlanStatus.proposed:
                active_plan_delta = 1
        else:
            if request.modifications is not None:
                raise HTTPException(
                    status_code=422,
                    detail="modifications are only valid for the modify action",
                )
            allowed = _VALID_TRANSITIONS.get(current_ps, set())
            if target_status == current_ps or target_status not in allowed:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Invalid transition: {previous_status} -> {target_status.value}. "
                        f"Allowed from {previous_status}: "
                        f"{sorted(status.value for status in allowed)}"
                    ),
                )
            override_meta = OverrideMetadata(
                override_by_user_id=principal.subject,
                override_by_role=authorized_role,
                override_justification=request.justification,
                override_action_type=request.action,
                override_timestamp=now,
                source_plan_id=request.plan_id,
                original_values={"status": previous_status},
                modified_values={"status": target_status.value},
            )
            updated_doc = _cosmos_write_body(doc)
            updated_doc["status"] = target_status.value
            updated_doc["updated_at"] = now.isoformat()
            if request.action in {"approve", "resume"}:
                updated_doc["valid_until"] = None
                updated_doc["approved_at"] = now.isoformat()
                updated_doc["paused_at"] = None
            elif request.action == "pause":
                updated_doc["paused_at"] = now.isoformat()
                updated_doc["valid_until"] = (now + timedelta(hours=_config.plan_expiry_hours)).isoformat()
            updated_doc["overrides"] = [
                *deepcopy(doc.get("overrides", [])),
                override_meta.model_dump(mode="json"),
            ]
            try:
                source_plan_id = str(doc.get("source_plan_id") or "") if request.action == "approve" else ""
                if source_plan_id:
                    source_doc = _agent._cosmos_plans.read_item(
                        item=source_plan_id,
                        partition_key=incident_scope_key,
                    )
                    source_status = PlanStatus(source_doc.get("status"))
                    if source_status in {PlanStatus.approved, PlanStatus.paused}:
                        source_etag = str(source_doc.get("_etag") or "")
                        if not source_etag:
                            raise HTTPException(
                                status_code=409,
                                detail="Source plan has no concurrency token",
                            )
                        superseded_doc = _cosmos_write_body(source_doc)
                        superseded_doc.update(
                            {
                                "status": PlanStatus.superseded.value,
                                "superseded_by": request.plan_id,
                                "superseded_at": now.isoformat(),
                                "updated_at": now.isoformat(),
                            }
                        )
                        _agent._cosmos_plans.execute_item_batch(
                            batch_operations=[
                                (
                                    "replace",
                                    (source_plan_id, superseded_doc),
                                    {"if_match_etag": source_etag},
                                ),
                                (
                                    "replace",
                                    (request.plan_id, updated_doc),
                                    {"if_match_etag": etag},
                                ),
                            ],
                            partition_key=incident_scope_key,
                        )
                        active_plan_delta -= 1
                    else:
                        _agent._cosmos_plans.replace_item(
                            item=request.plan_id,
                            body=updated_doc,
                            etag=etag,
                            match_condition=MatchConditions.IfNotModified,
                        )
                else:
                    _agent._cosmos_plans.replace_item(
                        item=request.plan_id,
                        body=updated_doc,
                        etag=etag,
                        match_condition=MatchConditions.IfNotModified,
                    )
            except Exception as exc:
                if isinstance(exc, HTTPException):
                    raise
                _agent.update_cosmos_health(False, now)
                if "PreconditionFailed" in str(exc) or "412" in str(exc):
                    tel.version_conflict_retries.add(1)
                    tel.emit_version_conflict(incident_id=request.incident_id, retry_count=1)
                    raise HTTPException(
                        status_code=409,
                        detail="Concurrent override conflict — retry",
                    ) from exc
                raise HTTPException(status_code=503, detail="Failed to persist override") from exc
            _agent.update_cosmos_health(True, now)
            if request.action in {"reject", "cancel"}:
                active_plan_delta -= 1
            audit_plan = updated_doc

        if active_plan_delta:
            _agent.change_active_plan_count(
                active_plan_delta,
                tenant_id=principal.tenant_id,
            )

        # Write audit record
        audit_record = EvacuationDecisionRecord(
            handoff_id=f"override-{request.plan_id}",
            operation_id=f"override-{request.plan_id}-{now.isoformat()}",
            plan_id=str(audit_plan.get("plan_id", request.plan_id)),
            incident_id=request.incident_id,
            decision_type=DecisionType.override_applied,
            decision_rationale=(
                f"Override by {principal.subject} ({authorized_role}): {request.action} — {request.justification}"
            ),
            generation_method="human_override",
            agent_version=_config.agent_version,
            configuration_version=_config.compute_config_hash()[:16],
            version=int(audit_plan.get("version", 1)),
            route_ids=[str(route.get("route_id", "")) for route in audit_plan.get("routes", [])],
            zone_ids=[str(zone.get("zone_id") or zone.get("zone_number", "")) for zone in audit_plan.get("zones", [])],
            population_affected=int(audit_plan.get("total_population", 0)),
            confidence_raw=float(audit_plan.get("confidence_score", 0.0)),
            confidence_adjusted=float(audit_plan.get("confidence_score", 0.0)),
            incident_scope_key=incident_scope_key,
            tenant_id=principal.tenant_id,
            override_metadata=override_meta,
            routes_count=len(audit_plan.get("routes", [])),
            transport_requests_count=len(audit_plan.get("transport_requirements", [])),
            constraints_applied=[f"override:{request.action}"],
            principal_id=principal.subject,
            assessment_id=(audit_plan.get("traceability") or {}).get("risk_assessment_id"),
            recommendation_id=(audit_plan.get("traceability") or {}).get("recommendation_id"),
            input_signal_ids=list(
                (audit_plan.get("traceability") or {}).get(
                    "input_signal_ids",
                    [],
                )
            ),
        )

        if _agent:
            receipt = _agent._pipeline.audit_writer.write(audit_record)
            if receipt is None or not receipt.accepted:
                raise HTTPException(
                    status_code=503,
                    detail="Override persisted but audit was not accepted",
                )

        committed_plan_id = str(audit_plan.get("plan_id", request.plan_id))
        _agent._pipeline.record_committed_plan(
            committed_plan_id,
            principal.tenant_id,
            commander_modified=True,
        )
        override_metric_type = {
            "route_override": "route",
            "zone_boundary_change": "zone",
            "phase_reprioritization": "phase",
        }.get(override_meta.override_action_type, request.action)
        tel.override_by_type.add(
            1,
            attributes={
                "action": override_metric_type,
                "incident_id": request.incident_id,
                "tenant_id": principal.tenant_id,
            },
        )
        tel.emit_override_applied(
            plan_id=committed_plan_id,
            action=request.action,
            user_id=principal.subject,
            role=authorized_role,
            incident_id=request.incident_id,
            tenant_id=principal.tenant_id,
        )

        return _OverrideResponse(
            plan_id=request.plan_id,
            previous_status=previous_status,
            new_status=target_status.value,
            override_timestamp=now.isoformat(),
            audit_record_id=audit_record.id,
            new_version_plan_id=new_version_plan_id,
        )

    # ------- POST /replan -------

    @app.post("/replan", response_model=_ReplanResponse, status_code=202)
    async def replan(
        replan_request: _ReplanRequest,
        response: Response,
        principal: AuthenticatedPrincipal = Depends(authorized_commander),
    ) -> _ReplanResponse:
        """Trigger manual replanning evaluation for an incident."""
        request = replan_request
        _agent: EvacuationAgent | None = app.state.agent

        if _agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialised")
        if _agent._cosmos_plans is None:
            raise HTTPException(status_code=503, detail="Plan repository unavailable")
        incident_scope_key = authorize_scope(
            principal,
            incident_id=request.incident_id,
            user_id=request.user_id,
            role=request.role,
            justification=request.justification,
        )

        try:
            current_plan = _agent._cosmos_plans.read_item(
                item=request.plan_id,
                partition_key=incident_scope_key,
            )
        except Exception as exc:
            exc_str = str(exc)
            if "NotFound" in exc_str or "404" in exc_str:
                raise HTTPException(status_code=404, detail=f"Plan {request.plan_id} not found")
            raise HTTPException(status_code=503, detail="Failed to load current plan")
        if (
            current_plan.get("tenant_id") != principal.tenant_id
            or current_plan.get("incident_id") != request.incident_id
            or current_plan.get("incident_scope_key") != incident_scope_key
        ):
            raise HTTPException(status_code=404, detail=f"Plan {request.plan_id} not found")
        if current_plan.get("status") in {
            PlanStatus.rejected.value,
            PlanStatus.superseded.value,
            PlanStatus.expired.value,
            PlanStatus.cancelled.value,
        }:
            raise HTTPException(status_code=404, detail="No active source plan found")
        if int(current_plan.get("version", 0)) != request.base_plan_version:
            raise HTTPException(status_code=422, detail="Base plan version is stale")
        if request.observed_at.tzinfo is None:
            raise HTTPException(status_code=422, detail="observed_at must be timezone-aware")
        if not request.update_id.strip():
            raise HTTPException(status_code=422, detail="update_id must not be blank")
        if request.new_severity is not None and request.new_severity not in {
            "low",
            "moderate",
            "high",
            "critical",
        }:
            raise HTTPException(status_code=422, detail="new_severity is invalid")

        try:
            result = _agent.process_replan(
                incident_id=request.incident_id,
                current_plan=current_plan,
                new_road_closures=request.new_road_closures,
                updated_zones=request.updated_zones,
                progress_completed_pct=request.progress_completed_pct,
                expected_progress_pct=request.expected_progress_pct,
                new_severity=request.new_severity,
                manual_trigger=request.manual_trigger,
                shelter_zones_with_new_routes=request.shelter_zones_with_new_routes,
                update_id=request.update_id,
                observed_at=request.observed_at,
                requested_by=principal.subject,
                request_role=principal.commander_role,
                justification=request.justification,
            )
        except RuntimeError as exc:
            if "PreconditionFailed" in str(exc):
                raise HTTPException(status_code=409, detail="Concurrent replan conflict — retry")
            if any(
                token in str(exc)
                for token in (
                    "Stale",
                    "stale",
                    "invalid",
                    "outside",
                    "requires",
                    "does not match",
                    "predates",
                )
            ):
                raise HTTPException(status_code=422, detail=str(exc))
            raise HTTPException(status_code=503, detail="Replan processing failed")

        if result["rate_limited"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "rate_limited",
                    "audit_record_id": result["audit_record_id"],
                },
                headers={"Retry-After": str(_config.replan_rate_limit_seconds)},
            )
        if not result["material_change"]:
            response.status_code = 200

        return _ReplanResponse(
            status=result["status"],
            incident_id=request.incident_id,
            previous_plan_id=str(result["previous_plan_id"]),
            new_plan_id=result.get("new_plan_id"),
            audit_record_id=str(result["audit_record_id"]),
            triggered=result["triggered"],
            triggers=result["triggers"],
            material_change=result["material_change"],
            change_summary=result.get("change_summary"),
        )

    return app


# ---------------------------------------------------------------------------
# Service Bus consumer loop
# ---------------------------------------------------------------------------

_TRANSIENT_STATUS_CODES = {408, 409, 412, 429, 500, 502, 503, 504}


def _delivery_count(message: Any) -> int:
    try:
        return max(1, int(getattr(message, "delivery_count", 1) or 1))
    except (TypeError, ValueError):
        return 1


def _is_transient_consumer_failure(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, TransientHandoffDependencyError)):
        return True
    status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
    if status_code in _TRANSIENT_STATUS_CODES:
        return True
    name = type(exc).__name__.casefold()
    return any(token in name for token in ("timeout", "serverbusy", "servicebusconnection"))


def _update_consumer_health(
    agent: Any,
    status: str,
    *,
    depth_delta: int = 0,
) -> None:
    update = getattr(agent, "update_queue_health", None)
    if callable(update):
        update(status=status, checked_at=datetime.now(UTC))
    if depth_delta:
        change_depth = getattr(agent, "change_queue_depth", None)
        if callable(change_depth):
            change_depth(depth_delta)


def _record_poison_rejection(agent: EvacuationAgent, message: Any, reason: str) -> None:
    message_id = str(getattr(message, "message_id", "") or "unknown-message")
    try:
        agent.record_intake_rejection(
            handoff_id=message_id,
            reason=reason,
        )
    except Exception:
        logger.exception("Failed to audit poison Service Bus message %s", message_id)


def _process_service_bus_message(
    agent: EvacuationAgent,
    receiver: Any,
    message: Any,
    *,
    lock_renewer: Any = None,
) -> None:
    received_at = time.perf_counter()
    try:
        data = json.loads(str(message))
        handoff = AgentHandoffEvent.model_validate(data)
    except (json.JSONDecodeError, UnicodeError, ValueError, TypeError) as exc:
        reason = f"Poison handoff payload: {exc}"
        _record_poison_rejection(agent, message, reason)
        try:
            receiver.dead_letter_message(message, reason="InvalidHandoffPayload")
        except Exception:
            logger.exception("Failed to dead-letter poison Service Bus message")
        return

    acknowledgement_ms = (time.perf_counter() - received_at) * 1000
    tel.handoff_acknowledgement_latency.record(
        acknowledgement_ms,
        attributes={"tenant_id": handoff.tenant_id},
    )
    if acknowledgement_ms > 5000:
        tel.emit_sla_breach(
            handoff.handoff_id,
            acknowledgement_ms,
            "handoff_acknowledgement",
        )
    if lock_renewer is not None:
        try:
            lock_renewer.register(
                receiver,
                message,
                max_lock_renewal_duration=300,
            )
        except Exception as exc:
            if _is_transient_consumer_failure(exc):
                try:
                    receiver.abandon_message(message)
                except Exception:
                    logger.exception("Failed to abandon handoff after lock-renewal failure")
                return
            raise

    try:
        agent.process_handoff(handoff)
    except Exception as exc:
        if _is_transient_consumer_failure(exc):
            release_claim = getattr(agent, "release_handoff_claim", None)
            if callable(release_claim):
                release_claim(handoff, str(exc))
            try:
                if _delivery_count(message) >= handoff.max_attempts:
                    receiver.dead_letter_message(
                        message,
                        reason="TransientRetriesExhausted",
                    )
                else:
                    receiver.abandon_message(message)
            except Exception:
                logger.exception("Failed to settle transient evacuation handoff")
            return
        reason = f"Permanent handoff failure: {exc}"
        try:
            agent.record_intake_rejection(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                tenant_id=handoff.tenant_id,
                reason=reason,
            )
            receiver.dead_letter_message(message, reason="PermanentProcessingFailure")
        except Exception:
            logger.exception("Failed to settle permanent evacuation handoff")
        return

    try:
        receiver.complete_message(message)
    except Exception:
        logger.exception("Failed to complete evacuation handoff; broker redelivery remains authoritative")


def run_consumer(
    agent: EvacuationAgent,
    connection_string: str | None = None,
    fully_qualified_namespace: str | None = None,
    queue_name: str = "evacuation-handoffs",
    stop_event: Any = None,
    service_bus_client: Any = None,
    lock_renewer: Any = None,
    max_reconnect_attempts: int = 3,
    reconnect_delay_seconds: float = 0.5,
) -> None:
    """Service Bus consumer loop for processing handoff events.

    Reads messages from the ``evacuation-handoffs`` queue, deserialises them
    as ``AgentHandoffEvent``, and delegates to ``agent.process_handoff()``.

    This is a blocking call intended to run in a background thread or as the
    main loop of the agent process.
    """
    if service_bus_client is None and not connection_string and not fully_qualified_namespace:
        logger.warning("No Service Bus configuration — consumer not started")
        _update_consumer_health(agent, "not_configured")
        return

    logger.info("Starting Service Bus consumer on queue '%s'", queue_name)
    _update_consumer_health(agent, "reconnecting")

    owns_lock_renewer = False
    try:
        if service_bus_client is not None:

            def client_factory() -> Any:
                return service_bus_client
        else:
            try:
                from azure.servicebus import AutoLockRenewer, ServiceBusClient
            except ImportError:
                logger.error("azure-servicebus package not installed — consumer unavailable")
                return
            if lock_renewer is None:
                lock_renewer = AutoLockRenewer(max_lock_renewal_duration=300)
                owns_lock_renewer = True
            if connection_string:

                def client_factory() -> Any:
                    return ServiceBusClient.from_connection_string(connection_string)
            else:
                if not fully_qualified_namespace:
                    raise ValueError("fully_qualified_namespace is required for managed-identity Service Bus clients")
                from azure.identity import DefaultAzureCredential

                client_id = os.environ.get("AZURE_CLIENT_ID")
                credential = (
                    DefaultAzureCredential(managed_identity_client_id=client_id)
                    if client_id
                    else DefaultAzureCredential()
                )

                def client_factory() -> Any:
                    return ServiceBusClient(
                        fully_qualified_namespace=fully_qualified_namespace,
                        credential=credential,
                    )

        reconnect_attempt = 0
        while stop_event is None or not stop_event.is_set():
            try:
                client = client_factory()
                with client:
                    receiver = client.get_queue_receiver(queue_name=queue_name)
                    with receiver:
                        _update_consumer_health(agent, "connected")
                        while stop_event is None or not stop_event.is_set():
                            messages = receiver.receive_messages(
                                max_message_count=1,
                                max_wait_time=1,
                            )
                            reconnect_attempt = 0
                            for msg in messages:
                                _update_consumer_health(
                                    agent,
                                    "connected",
                                    depth_delta=1,
                                )
                                try:
                                    _process_service_bus_message(
                                        agent,
                                        receiver,
                                        msg,
                                        lock_renewer=lock_renewer,
                                    )
                                finally:
                                    _update_consumer_health(
                                        agent,
                                        "connected",
                                        depth_delta=-1,
                                    )
            except Exception:
                reconnect_attempt += 1
                _update_consumer_health(agent, "reconnecting")
                logger.exception(
                    "Service Bus receive failure; reconnect attempt %d/%d",
                    reconnect_attempt,
                    max_reconnect_attempts,
                )
                if reconnect_attempt >= max_reconnect_attempts:
                    logger.error("Service Bus reconnect budget exhausted")
                    _update_consumer_health(agent, "offline")
                    return
                if stop_event is not None:
                    if stop_event.wait(reconnect_delay_seconds):
                        return
                else:
                    time.sleep(reconnect_delay_seconds)
    finally:
        if owns_lock_renewer:
            close = getattr(lock_renewer, "close", None)
            if callable(close):
                close()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from evacuation.runtime import main

    main()
