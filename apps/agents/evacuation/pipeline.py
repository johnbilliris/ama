"""Evacuation processing pipeline — 10-stage orchestrator.

Stages:
1. Handoff intake and validation
2. Assessment retrieval from Cosmos DB
3. Evacuation zone computation (Shapely)
4. Road network preparation (zone-based capacity reduction)
5. Route computation (Dijkstra's)
6. Transport coordination (vulnerable populations)
7. Timeline estimation (5-phase + shelter-in-place)
8. Plan summary generation (LLM + template fallback)
9. Versioning and persistence (OCC + Cosmos DB)
10. Audit finalisation
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from common.async_bridge import run_async
from common.handoffs import AgentHandoffEvent
from evacuation import telemetry as tel
from evacuation.audit import AuditWriter
from evacuation.config import EvacuationConfig
from evacuation.dedup import HandoffDeduplicator
from evacuation.models import (
    AssemblyArea,
    DataSnapshot,
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPlan,
    EvacuationZone,
    HazardSummary,
    PlanStatus,
    Traceability,
    confidence_to_level,
)
from evacuation.road_network import RoadNetworkLoader
from evacuation.router import RouteComputer
from evacuation.templates import (
    generate_plan_summary_template,
)
from evacuation.timeline import TimelineEstimator
from evacuation.transport import TransportCoordinator
from evacuation.versioning import VersionCounter
from evacuation.zones import ZoneComputer

logger = logging.getLogger(__name__)


class EvacuationProcessingPipeline:
    """Ten-stage evacuation processing pipeline.

    Takes an ``AgentHandoffEvent`` as input and produces an ``EvacuationPlan``
    (or ``None`` on validation/dedup rejection).

    Each stage:
    - Is a separate private method (``_stage_N_…``)
    - Measures ``processing_duration_ms``
    - Writes an ``EvacuationDecisionRecord`` via ``AuditWriter``
    """

    def __init__(
        self,
        config: EvacuationConfig | None = None,
        road_network: RoadNetworkLoader | None = None,
        cosmos_plans_container: Any = None,
        cosmos_decisions_container: Any = None,
        cosmos_assessments_container: Any = None,
        population_data: list[dict] | None = None,
        facility_data: list[dict] | None = None,
        llm_generate_fn: Any = None,  # _generate_with_fallback callable
    ) -> None:
        self._config = config or EvacuationConfig()
        self._road_network = road_network or RoadNetworkLoader(
            staleness_hours=self._config.road_data_staleness_hours,
        )
        self._cosmos_plans = cosmos_plans_container
        self._cosmos_decisions = cosmos_decisions_container
        self._cosmos_assessments = cosmos_assessments_container
        self._population_data = population_data or []
        self._facility_data = facility_data or []
        self._llm_generate_fn = llm_generate_fn

        # Sub-components
        self._dedup = HandoffDeduplicator(
            window_minutes=self._config.handoff_dedup_window_minutes,
        )
        self._zone_computer = ZoneComputer()
        self._transport_coordinator = TransportCoordinator(config=self._config)
        self._timeline_estimator = TimelineEstimator(config=self._config)
        self._version_counter = VersionCounter(
            cosmos_container=self._cosmos_plans,
        )
        self._audit_writer = AuditWriter(
            config=self._config,
            cosmos_client=self._cosmos_decisions,
        )

        # Processing metrics
        self._active_plan_count: int = 0
        self._processing_queue_depth: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_handoff(self, handoff: AgentHandoffEvent) -> EvacuationPlan | None:
        """Execute full 10-stage pipeline.

        Returns the generated ``EvacuationPlan``, or ``None`` if the handoff
        was rejected (validation failure or duplicate).
        """
        with tel.start_span(
            "evacuation.process_handoff",
            attributes={
                "handoff_id": handoff.handoff_id,
                "incident_id": handoff.incident_id,
            },
        ):
            pipeline_start = time.monotonic()
            tenant_id = handoff.tenant_id or "live"
            incident_id = handoff.incident_id
            incident_scope_key = f"{tenant_id}:{incident_id}"
            assumptions: list[str] = []

            tel.handoff_intake_count.add(1)

            logger.info(
                "Pipeline started: handoff_id=%s incident=%s",
                handoff.handoff_id,
                incident_id,
            )

            # Stage 1 — Handoff intake and validation
            with tel.start_span("evacuation.validate_handoff") as _s1:
                accepted = self._stage_1_handoff_intake(handoff, incident_scope_key, tenant_id)
                if not accepted:
                    return None

            tel.emit_handoff_received(handoff.handoff_id, incident_id, tenant_id)

            # Stage 2 — Assessment retrieval
            with tel.start_span("evacuation.retrieve_assessment"):
                assessment_data = self._stage_2_retrieve_assessment(
                    handoff,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )

            # Stage 3 — Zone computation
            with tel.start_span("evacuation.compute_zones") as s3:
                zones = self._stage_3_compute_zones(
                    handoff,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                if hasattr(s3, "set_attribute"):
                    s3.set_attribute("zone.count", len(zones))
                    total_pop = sum(z.population_estimate for z in zones)
                    s3.set_attribute("zone.total_population", total_pop)

            # Stage 4 — Road network preparation
            with tel.start_span("evacuation.prepare_road_network"):
                self._stage_4_road_network_preparation(
                    handoff,
                    zones,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )

            # Stage 5 — Route computation
            with tel.start_span("evacuation.compute_routes") as s5:
                route_start = time.monotonic()
                routes = self._stage_5_compute_routes(
                    handoff,
                    zones,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                route_ms = (time.monotonic() - route_start) * 1000
                tel.route_computation_time.record(route_ms)
                if hasattr(s5, "set_attribute"):
                    s5.set_attribute("route.count", len(routes))

                # Check for congestion risk routes (>80% utilisation)
                for r in routes:
                    utilisation = r.get("capacity_utilisation_pct", 0.0)
                    if utilisation > 80:
                        tel.congestion_risk_routes.add(1)
                        tel.emit_route_conflict(
                            plan_id="",
                            route_id=r.get("route_id", ""),
                            utilisation_pct=utilisation,
                        )

            # Stage 6 — Transport coordination
            with tel.start_span("evacuation.coordinate_transport"):
                transport_reqs = self._stage_6_transport_coordination(
                    handoff,
                    zones,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                tel.transport_requests_generated.add(len(transport_reqs))
                for tr in transport_reqs:
                    category = tr.get("vulnerability_category", "general")
                    tel.transport_by_category.add(1, attributes={"category": category})
                total_vehicles = sum(tr.get("estimated_vehicles", 0) for tr in transport_reqs)
                tel.transport_vehicles_estimated.set(float(total_vehicles))

            # Stage 7 — Timeline estimation
            with tel.start_span("evacuation.estimate_timeline"):
                phases, shelter_zones, timeline_assumptions = self._stage_7_timeline_estimation(
                    handoff,
                    zones,
                    routes,
                    transport_reqs,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                )
                assumptions.extend(timeline_assumptions)

                # Shelter-in-place metrics & events
                hazard_type = assessment_data.get("hazard_type", "bushfire")
                for sz in shelter_zones:
                    tel.shelter_in_place_count.add(1)
                    zone_obj = next((z for z in zones if str(z.zone_number) == sz), None)
                    pop = zone_obj.population_estimate if zone_obj else 0
                    tel.emit_shelter_in_place_recommended(incident_id, sz, pop, hazard_type)

                # Emergency escalation: shelter-in-place with no routes for that zone
                for sz in shelter_zones:
                    zone_routes = [r for r in routes if str(r.get("zone_number", "")) == sz]
                    if not zone_routes:
                        zone_obj = next((z for z in zones if str(z.zone_number) == sz), None)
                        pop = zone_obj.population_estimate if zone_obj else 0
                        tel.emergency_escalation_count.add(1)
                        tel.emit_emergency_escalation(incident_id, sz, pop)

                # Time deficit detection
                time_horizon_str = assessment_data.get("time_horizon")
                if time_horizon_str:
                    time_horizon_hours = self._parse_time_horizon(time_horizon_str)
                    if time_horizon_hours is not None:
                        clearance_min = sum(p.duration_minutes for p in phases)
                        hazard_min = time_horizon_hours * 60
                        if clearance_min > hazard_min:
                            deficit = clearance_min - hazard_min
                            tel.time_deficit_flag_count.add(1)
                            tel.emit_time_deficit_detected("", "all", deficit)

            # Stage 8 — Plan summary generation
            with tel.start_span("evacuation.generate_summary"):
                summary, generation_method, confidence_score = self._stage_8_plan_summary(
                    handoff,
                    zones,
                    routes,
                    transport_reqs,
                    phases,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                if generation_method in ("template_fallback", "safety_fallback"):
                    tel.fallback_mode_activations.add(1)
                    tel.degradation_events.add(1)
                    tel.emit_degradation_event("llm", 2)

            # Stage 9 — Versioning and persistence
            with tel.start_span("evacuation.assign_version"):
                pass  # version assignment happens inside _stage_9
            with tel.start_span("evacuation.persist_plan"):
                plan = self._stage_9_versioning_persistence(
                    handoff,
                    zones,
                    routes,
                    transport_reqs,
                    phases,
                    shelter_zones,
                    summary,
                    generation_method,
                    confidence_score,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )

            # Record zone population gauges
            for z in zones:
                tel.zone_population_covered.set(
                    float(z.population_estimate),
                    attributes={"zone": str(z.zone_number)},
                )

            tel.active_plans_gauge.add(1.0)
            tel.routes_per_plan.record(len(routes))
            tel.version_count_per_incident.set(
                float(plan.version),
                attributes={"incident_id": incident_id},
            )
            tel.dynamic_update_rate.set(
                float(plan.version),
                attributes={"incident_id": incident_id},
            )

            # Emit PlanGenerated event
            tel.emit_plan_generated(
                plan_id=plan.plan_id,
                version=plan.version,
                confidence=confidence_score,
                routes_count=len(routes),
                generation_method=generation_method,
            )

            # Stage 10 — Audit finalisation
            with tel.start_span("evacuation.write_audit"):
                self._stage_10_audit_finalisation(
                    handoff,
                    plan,
                    incident_scope_key,
                    tenant_id,
                    pipeline_start,
                )

            # Update audit gauges
            tel.audit_buffer_depth.set(float(self._audit_writer.buffer_depth))
            audit_status = self._audit_writer.get_status()
            tier_val = 1 if audit_status == "healthy" else (2 if audit_status == "degraded" else 3)
            tel.audit_tier.set(float(tier_val))
            if self._road_network.is_loaded:
                tel.road_data_stale.set(1.0 if self._road_network.is_stale() else 0.0)

            total_ms = (time.monotonic() - pipeline_start) * 1000
            tel.plan_generation_latency.record(total_ms)

            # SLA breach check (30-second SLA for initial plan)
            if total_ms > 30_000:
                tel.sla_breach_count.add(1)
                tel.emit_sla_breach(handoff.handoff_id, total_ms, "initial")

            # Handoff success rate (simple: this succeeded)
            tel.handoff_success_rate.set(1.0)

            logger.info(
                "Pipeline completed: plan_id=%s duration=%.0fms",
                plan.plan_id,
                total_ms,
            )

            return plan

    @property
    def audit_writer(self) -> AuditWriter:
        """Expose audit writer for health checks and external access."""
        return self._audit_writer

    @property
    def active_plan_count(self) -> int:
        return self._active_plan_count

    @property
    def processing_queue_depth(self) -> int:
        return self._processing_queue_depth

    # ------------------------------------------------------------------
    # Stage 1 — Handoff Intake and Validation
    # ------------------------------------------------------------------

    def _stage_1_handoff_intake(
        self,
        handoff: AgentHandoffEvent,
        incident_scope_key: str,
        tenant_id: str,
    ) -> bool:
        """Validate handoff event and check for duplicates.

        Returns True if handoff is accepted, False if rejected/duplicate.
        """
        t0 = time.monotonic()

        # Validate target agent
        if handoff.target_agent != "evacuation":
            duration_ms = (time.monotonic() - t0) * 1000
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.handoff_rejected,
                rationale=f"Handoff targeted at '{handoff.target_agent}', not 'evacuation'",
                duration_ms=duration_ms,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
            )
            logger.warning(
                "Handoff rejected: target_agent=%s (expected 'evacuation')",
                handoff.target_agent,
            )
            tel.handoff_rejected_count.add(1)
            return False

        # Dedup check
        if self._dedup.is_duplicate(handoff.handoff_id):
            duration_ms = (time.monotonic() - t0) * 1000
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.duplicate_discarded,
                rationale=f"Duplicate handoff discarded: {handoff.handoff_id}",
                duration_ms=duration_ms,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
            )
            logger.info("Duplicate handoff discarded: %s", handoff.handoff_id)
            tel.duplicate_discard_count.add(1)
            return False

        # Accepted — write handoff_received audit
        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.handoff_received,
            rationale=(f"Handoff accepted from {handoff.source_agent}. Confidence={handoff.confidence:.2f}"),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            confidence_raw=handoff.confidence,
        )
        return True

    # ------------------------------------------------------------------
    # Stage 2 — Assessment Retrieval
    # ------------------------------------------------------------------

    def _stage_2_retrieve_assessment(
        self,
        handoff: AgentHandoffEvent,
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> dict[str, Any]:
        """Retrieve HazardAssessment from Cosmos DB using assessmentId from payload."""
        t0 = time.monotonic()
        assessment_data: dict[str, Any] = {}
        assessment_id = handoff.payload.get("assessmentId", "")

        if assessment_id and self._cosmos_assessments is not None:
            try:
                doc = self._cosmos_assessments.read_item(
                    item=str(assessment_id),
                    partition_key=incident_scope_key,
                )
                assessment_data = dict(doc)
                logger.info("Assessment retrieved: %s", assessment_id)
            except Exception as exc:
                logger.warning(
                    "Failed to retrieve assessment %s: %s",
                    assessment_id,
                    exc,
                )
                assumptions.append(
                    f"Assessment {assessment_id} could not be retrieved; using handoff payload data only."
                )
        elif not assessment_id:
            assumptions.append("No assessmentId in handoff payload; plan generated from handoff metadata only.")

        # Fallback: extract what we can from the handoff payload
        if not assessment_data:
            assessment_data = self._build_assessment_from_payload(handoff, assumptions)

        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.assessment_retrieved,
            rationale=(
                f"Assessment source: {'cosmos' if assessment_id else 'payload'}. "
                f"Hazard type: {assessment_data.get('hazard_type', 'unknown')}"
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            hazard_type=assessment_data.get("hazard_type"),
        )
        return assessment_data

    # ------------------------------------------------------------------
    # Stage 3 — Zone Computation
    # ------------------------------------------------------------------

    def _stage_3_compute_zones(
        self,
        handoff: AgentHandoffEvent,
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> list[EvacuationZone]:
        """Compute 3 concentric evacuation zones from hazard GeoJSON."""
        t0 = time.monotonic()
        zones: list[EvacuationZone] = []

        hazard_geojson = assessment_data.get("affected_area") or assessment_data.get(
            "hazard_geojson",
        )

        if hazard_geojson:
            try:
                zones = self._zone_computer.compute_zones(
                    hazard_geojson=hazard_geojson,
                    population_data=self._population_data or None,
                )
            except Exception as exc:
                logger.warning("Zone computation failed: %s", exc)
                assumptions.append(f"Zone computation from GeoJSON failed ({exc}); using default single zone.")
        else:
            assumptions.append("No hazard GeoJSON available; zones estimated from metadata.")

        # Fallback: create a single zone if computation produced nothing
        if not zones:
            pop_est = assessment_data.get("population_estimate", 1000)
            zones = [
                EvacuationZone(
                    zone_number=1,
                    population_estimate=pop_est,
                    vulnerable_population=int(pop_est * 0.15),
                    evacuation_priority="mandatory",
                    status="pending",
                ),
            ]

        duration_ms = (time.monotonic() - t0) * 1000
        total_pop = sum(z.population_estimate for z in zones)
        zone_ids = [str(z.zone_number) for z in zones]

        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.zones_computed,
            rationale=(f"Computed {len(zones)} zone(s) with total population {total_pop}. Zone IDs: {zone_ids}"),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            zone_ids=zone_ids,
            population_affected=total_pop,
        )
        return zones

    # ------------------------------------------------------------------
    # Stage 4 — Road Network Preparation
    # ------------------------------------------------------------------

    def _stage_4_road_network_preparation(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> None:
        """Load road network (if needed) and apply zone-based capacity reduction."""
        t0 = time.monotonic()

        # Ensure road network is loaded
        if not self._road_network.is_loaded:
            try:
                self._road_network.load(self._config.road_network_file_path)
            except Exception as exc:
                logger.warning("Road network load failed: %s", exc)
                assumptions.append(f"Road network could not be loaded ({exc}); routing will use fallback estimates.")

        # Apply zone-based capacity reduction
        if self._road_network.is_loaded and zones:
            try:
                zone_polygons = self._zone_computer.get_zone_polygons(zones)
                edges_as_dicts = []
                for edge in self._road_network.get_all_edges():
                    edge_dict = edge.model_dump()
                    geom = self._road_network.get_edge_geometry(edge.id)
                    if geom is not None:
                        edge_dict["_geometry"] = geom
                    edges_as_dicts.append(edge_dict)

                self._zone_computer.apply_zone_capacity_reduction(
                    edges_as_dicts,
                    zone_polygons,
                )

                # Apply closures back to the road network
                for edge_dict in edges_as_dicts:
                    if edge_dict.get("closure_status") == "closed":
                        self._road_network.apply_closure(
                            edge_dict["id"],
                            edge_dict.get("closure_reason", "zone_1_closure"),
                        )
            except Exception as exc:
                logger.warning("Zone capacity reduction failed: %s", exc)
                assumptions.append(f"Zone-based capacity reduction failed ({exc}); using original road capacities.")

        node_count = self._road_network.node_count if self._road_network.is_loaded else 0
        edge_count = self._road_network.edge_count if self._road_network.is_loaded else 0
        duration_ms = (time.monotonic() - t0) * 1000

        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.road_network_loaded,
            rationale=(
                f"Road network: {node_count} nodes, {edge_count} edges. "
                f"Version: {self._road_network.get_version() if self._road_network.is_loaded else 'n/a'}. "
                f"Stale: {self._road_network.is_stale() if self._road_network.is_loaded else 'n/a'}"
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
        )

    # ------------------------------------------------------------------
    # Stage 5 — Route Computation
    # ------------------------------------------------------------------

    def _stage_5_compute_routes(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> list[dict[str, Any]]:
        """Compute evacuation routes using Dijkstra's algorithm."""
        t0 = time.monotonic()
        all_routes: list[dict[str, Any]] = []
        hazard_type = assessment_data.get("hazard_type", "bushfire")

        if not self._road_network.is_loaded:
            assumptions.append("Road network not available; route computation skipped.")
            duration_ms = (time.monotonic() - t0) * 1000
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.routes_computed,
                rationale="No road network — route computation skipped",
                duration_ms=duration_ms,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
            )
            return all_routes

        route_computer = RouteComputer(
            road_network=self._road_network,
            config=self._config,
        )

        # Get closed edges to exclude
        closed_edge_ids = {e.id for e in self._road_network.get_closed_edges()}

        for zone in zones:
            # Find nodes within this zone's area
            origin_nodes = self._find_zone_origin_nodes(zone)
            if not origin_nodes:
                # Fallback: use first available node
                all_nodes = self._road_network.get_all_nodes()
                if all_nodes:
                    origin_nodes = [all_nodes[0].id]
                    assumptions.append(f"No nodes mapped to Zone {zone.zone_number}; using fallback origin node.")

            evacuation_routes = route_computer.compute_routes(
                origin_nodes=origin_nodes,
                zone_number=zone.zone_number,
                population=zone.population_estimate,
                hazard_type=hazard_type,
                excluded_edge_ids=closed_edge_ids,
            )

            for route in evacuation_routes:
                all_routes.append(route.model_dump())

        duration_ms = (time.monotonic() - t0) * 1000
        route_ids = [r.get("route_id", "") for r in all_routes]

        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.routes_computed,
            rationale=(f"Computed {len(all_routes)} route(s) across {len(zones)} zone(s). Hazard type: {hazard_type}"),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            route_ids=route_ids,
        )
        return all_routes

    # ------------------------------------------------------------------
    # Stage 6 — Transport Coordination
    # ------------------------------------------------------------------

    def _stage_6_transport_coordination(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> list[dict[str, Any]]:
        """Compute transport requirements for vulnerable populations."""
        t0 = time.monotonic()

        zone_dicts = [z.model_dump() for z in zones]
        assembly_area_dicts = (
            [
                {
                    "assembly_area_id": aa.assembly_area_id,
                    "name": aa.name,
                    "coordinates": aa.coordinates,
                }
                for aa in self._road_network.get_assembly_areas()
            ]
            if self._road_network.is_loaded
            else []
        )

        transport_reqs_models = self._transport_coordinator.compute_transport_requirements(
            zones=zone_dicts,
            facilities=self._facility_data,
            assembly_areas=assembly_area_dicts,
        )

        transport_reqs = [t.model_dump() for t in transport_reqs_models]

        if not transport_reqs and self._facility_data:
            assumptions.append("No transport requirements matched facility/zone intersection.")

        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.transport_coordinated,
            rationale=(
                f"Identified {len(transport_reqs)} transport requirement(s) from {len(self._facility_data)} facilities."
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            population_affected=sum(z.vulnerable_population for z in zones),
        )
        return transport_reqs

    # ------------------------------------------------------------------
    # Stage 7 — Timeline Estimation
    # ------------------------------------------------------------------

    def _stage_7_timeline_estimation(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        routes: list[dict[str, Any]],
        transport_reqs: list[dict[str, Any]],
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
    ) -> tuple[list[Any], list[str], list[str]]:
        """Compute 5-phase timeline with shelter-in-place detection.

        Returns (phases, shelter_in_place_zone_ids, assumptions).
        """
        t0 = time.monotonic()
        hazard_type = assessment_data.get("hazard_type", "bushfire")

        # Parse time horizon
        time_horizon_hours: float | None = None
        time_horizon_str = assessment_data.get("time_horizon")
        if time_horizon_str:
            time_horizon_hours = self._parse_time_horizon(time_horizon_str)

        zone_dicts = [z.model_dump() for z in zones]

        phases, shelter_recs, assumptions = self._timeline_estimator.estimate_timeline(
            zones=zone_dicts,
            routes=routes,
            transport_requirements=transport_reqs,
            hazard_type=hazard_type,
            hazard_time_horizon_hours=time_horizon_hours,
        )

        shelter_zone_ids = [str(s.zone_number) for s in shelter_recs if s.recommended]

        # Write shelter-in-place records
        for sip in shelter_recs:
            if sip.recommended:
                self._write_audit(
                    handoff_id=handoff.handoff_id,
                    incident_id=handoff.incident_id,
                    decision_type=DecisionType.shelter_in_place_recommended,
                    rationale=sip.reason,
                    duration_ms=0,
                    incident_scope_key=incident_scope_key,
                    tenant_id=tenant_id,
                    zone_ids=[str(sip.zone_number)],
                )

        duration_ms = (time.monotonic() - t0) * 1000
        total_duration_min = sum(p.duration_minutes for p in phases)
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.timeline_estimated,
            rationale=(
                f"Estimated {len(phases)} phase(s), "
                f"total duration {total_duration_min} min. "
                f"Shelter-in-place zones: {shelter_zone_ids or 'none'}"
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            zone_ids=shelter_zone_ids,
        )
        return phases, shelter_zone_ids, assumptions

    # ------------------------------------------------------------------
    # Stage 8 — Plan Summary Generation
    # ------------------------------------------------------------------

    def _stage_8_plan_summary(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        routes: list[dict[str, Any]],
        transport_reqs: list[dict[str, Any]],
        phases: list[Any],
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> tuple[str, str, float]:
        """Generate plan summary via LLM or template fallback.

        Returns (summary_text, generation_method, confidence_score).
        """
        t0 = time.monotonic()
        hazard_type = assessment_data.get("hazard_type", "bushfire")
        total_pop = sum(z.population_estimate for z in zones)

        # Build plan data dict for template
        plan_data = {
            "population_estimate": total_pop,
            "zones": [z.model_dump() for z in zones],
            "routes": routes,
            "assembly_areas": (
                [aa.model_dump() for aa in self._road_network.get_assembly_areas()]
                if self._road_network.is_loaded
                else []
            ),
            "transport_requirements": transport_reqs,
            "confidence_score": handoff.confidence,
            "confidence_level": confidence_to_level(handoff.confidence).value,
            "hazard_severity": assessment_data.get("severity_level", "high"),
            "time_horizon": assessment_data.get("time_horizon", "unknown"),
        }

        # Generate template text (always needed as fallback)
        template_text = generate_plan_summary_template(
            plan_data=plan_data,
            hazard_type=hazard_type,
            max_length=self._config.max_summary_length,
        )

        summary = template_text
        generation_method = "template_fallback"
        confidence_score = handoff.confidence

        # Try LLM generation
        if self._llm_generate_fn is not None:
            try:
                zone_desc = ", ".join(f"Zone {z.zone_number} (pop {z.population_estimate})" for z in zones)
                response = self._llm_generate_fn(
                    purpose="reasoning",
                    prompt=(
                        f"Generate a concise AIIMS-format evacuation plan summary. "
                        f"Incident: {handoff.incident_id}. "
                        f"Hazard: {hazard_type}. "
                        f"Zones: {zone_desc}. "
                        f"Routes: {len(routes)}. "
                        f"Total population: {total_pop}."
                    ),
                    template_text=template_text,
                    max_output_tokens=400,
                    timeout_seconds=10.0,
                )

                summary = str(response.get("text", template_text))
                generation_method = str(response.get("generation_method", "template_fallback"))

                # Content safety failure audit
                content_safety_result = response.get("content_safety_result", "passed")
                if content_safety_result not in ("passed", "not_checked"):
                    tel.content_safety_failures.add(1)
                    self._write_audit(
                        handoff_id=handoff.handoff_id,
                        incident_id=handoff.incident_id,
                        decision_type=DecisionType.content_safety_failure,
                        rationale=(f"Content safety check result: {content_safety_result}. Fell back to template."),
                        duration_ms=0,
                        incident_scope_key=incident_scope_key,
                        tenant_id=tenant_id,
                    )
            except Exception as exc:
                logger.warning("LLM plan summary generation failed: %s", exc)
                generation_method = "template_fallback"

        # Apply confidence reduction for template fallback
        if generation_method in ("template_fallback", "safety_fallback"):
            confidence_score = confidence_score * self._config.fallback_confidence_reduction
            confidence_score = max(0.0, min(1.0, confidence_score))

        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.plan_generated,
            rationale=(f"Summary generated via {generation_method}. Confidence: {confidence_score:.2f}"),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            confidence_raw=handoff.confidence,
            confidence_adjusted=confidence_score,
            generation_method=generation_method,
        )
        return summary, generation_method, confidence_score

    # ------------------------------------------------------------------
    # Stage 9 — Versioning and Persistence
    # ------------------------------------------------------------------

    def _stage_9_versioning_persistence(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        routes: list[dict[str, Any]],
        transport_reqs: list[dict[str, Any]],
        phases: list[Any],
        shelter_zone_ids: list[str],
        summary: str,
        generation_method: str,
        confidence_score: float,
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> EvacuationPlan:
        """Assign version, build EvacuationPlan, and persist to Cosmos DB."""
        t0 = time.monotonic()
        incident_id = handoff.incident_id
        hazard_type = assessment_data.get("hazard_type", "bushfire")

        # Assign version via OCC
        version = run_async(
            self._version_counter.assign_version(
                incident_id=incident_id,
                incident_scope_key=incident_scope_key,
            )
        )
        plan_id = self._version_counter.format_plan_id(incident_id, version)

        # Build assembly areas from road network
        assembly_areas: list[AssemblyArea] = []
        if self._road_network.is_loaded:
            for aa_config in self._road_network.get_assembly_areas():
                assembly_areas.append(
                    AssemblyArea(
                        assembly_area_id=aa_config.assembly_area_id,
                        name=aa_config.name,
                        capacity=aa_config.capacity_persons,
                        latitude=aa_config.coordinates.get("lat", 0.0),
                        longitude=aa_config.coordinates.get("lng", 0.0),
                        accessible=bool(aa_config.accessibility_features),
                        shelter_available=True,
                    )
                )

        # Build evacuation routes from dicts
        from evacuation.models import EvacuationRoute

        route_models = [EvacuationRoute.model_validate(r) for r in routes]

        # Build transport requirement models
        from evacuation.models import TransportRequirement

        transport_models = [TransportRequirement.model_validate(t) for t in transport_reqs]

        # Build evacuation phases
        from evacuation.models import EvacuationPhase

        phase_models = [p if isinstance(p, EvacuationPhase) else EvacuationPhase.model_validate(p) for p in phases]

        # Mobilisation time
        mobilisation_min = self._config.mobilisation_time_for(hazard_type)

        # Total estimated completion
        estimated_completion = sum(p.duration_minutes for p in phase_models) + mobilisation_min

        # Build traceability
        assessment_id = assessment_data.get(
            "hazard_assessment_id",
            assessment_data.get("assessmentId", ""),
        )
        traceability = Traceability(
            source_handoff_id=handoff.handoff_id,
            risk_assessment_id=str(assessment_id) if assessment_id else None,
            input_data_versions={
                "road_network": (self._road_network.get_version() if self._road_network.is_loaded else "n/a"),
                "config": self._config.compute_config_hash()[:16],
            },
            model_id=None,
            prompt_template_version="1.0",
            generation_method=generation_method,
        )

        # Build data snapshot
        data_snapshot = DataSnapshot(
            road_network_version=(self._road_network.get_version() if self._road_network.is_loaded else ""),
            population_data_version=f"{len(self._population_data)} records",
            hazard_data_timestamp=datetime.now(UTC),
        )

        # Build hazard summary
        hazard_summary = HazardSummary(
            hazard_type=hazard_type,
            severity_level=assessment_data.get("severity_level", ""),
            affected_area_km2=assessment_data.get("affected_area_km2", 0.0),
            direction_of_travel=assessment_data.get("direction_of_travel", ""),
            estimated_arrival_minutes=assessment_data.get("estimated_arrival_minutes"),
            source_assessment_id=str(assessment_id) if assessment_id else None,
        )

        # Append assumptions to summary
        if assumptions:
            assumption_text = " ASSUMPTIONS: " + "; ".join(assumptions)
            summary = (summary + assumption_text)[: self._config.max_summary_length]

        total_pop = sum(z.population_estimate for z in zones)

        plan = EvacuationPlan(
            plan_id=plan_id,
            incident_id=incident_id,
            version=version,
            status=PlanStatus.proposed,
            confidence_score=confidence_score,
            hazard_summary=hazard_summary,
            zones=zones,
            routes=route_models,
            assembly_areas=assembly_areas,
            phases=phase_models,
            transport_requirements=transport_models,
            total_population=total_pop,
            estimated_completion_minutes=estimated_completion,
            mobilisation_time_minutes=mobilisation_min,
            shelter_in_place_zones=shelter_zone_ids,
            traceability=traceability,
            data_snapshot=data_snapshot,
            summary=summary,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
        )

        # Persist to Cosmos DB
        if self._cosmos_plans is not None:
            try:
                doc = plan.model_dump(mode="json")
                doc["id"] = plan_id
                self._cosmos_plans.create_item(body=doc)
                logger.info("Plan persisted to Cosmos DB: %s", plan_id)
            except Exception as exc:
                logger.error("Failed to persist plan %s: %s", plan_id, exc)
                assumptions.append(f"Plan persistence failed: {exc}")

        self._active_plan_count += 1

        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.plan_generated,
            rationale=(
                f"Plan {plan_id} v{version} created. "
                f"Population: {total_pop}. "
                f"Routes: {len(route_models)}. "
                f"Shelter-in-place zones: {shelter_zone_ids or 'none'}"
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            plan_id=plan_id,
            version=version,
            confidence_raw=handoff.confidence,
            confidence_adjusted=confidence_score,
            zone_ids=[str(z.zone_number) for z in zones],
            route_ids=[r.get("route_id", "") for r in routes],
            population_affected=total_pop,
        )
        return plan

    # ------------------------------------------------------------------
    # Stage 10 — Audit Finalisation
    # ------------------------------------------------------------------

    def _stage_10_audit_finalisation(
        self,
        handoff: AgentHandoffEvent,
        plan: EvacuationPlan,
        incident_scope_key: str,
        tenant_id: str,
        pipeline_start: float,
    ) -> None:
        """Reconcile audit records and verify completeness."""
        time.monotonic()

        # Attempt to flush any buffered audit records
        flushed = self._audit_writer.flush()
        if flushed > 0:
            logger.info("Flushed %d buffered audit records during finalisation", flushed)

        # Check audit store health
        audit_status = self._audit_writer.get_status()
        if audit_status != "healthy":
            logger.warning(
                "Audit store status at finalisation: %s (buffer depth: %d)",
                audit_status,
                self._audit_writer.buffer_depth,
            )
            tel.degradation_events.add(1)
            tier_map = {"degraded": 2, "file_spill": 3}
            tel.emit_degradation_event("cosmos", tier_map.get(audit_status, 3))
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.degradation_detected,
                rationale=(
                    f"Audit store degraded at pipeline completion: {audit_status}. "
                    f"Buffer depth: {self._audit_writer.buffer_depth}"
                ),
                duration_ms=0,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
                plan_id=plan.plan_id,
            )

        total_ms = (time.monotonic() - pipeline_start) * 1000
        logger.info(
            "Audit finalisation complete for plan %s (total pipeline: %.0fms, audit: %s)",
            plan.plan_id,
            total_ms,
            audit_status,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_audit(
        self,
        *,
        handoff_id: str,
        incident_id: str,
        decision_type: DecisionType,
        rationale: str,
        duration_ms: float,
        incident_scope_key: str,
        tenant_id: str,
        plan_id: str | None = None,
        version: int | None = None,
        hazard_type: str | None = None,
        confidence_raw: float = 0.0,
        confidence_adjusted: float = 0.0,
        generation_method: str = "pipeline",
        zone_ids: list[str] | None = None,
        route_ids: list[str] | None = None,
        population_affected: int = 0,
    ) -> None:
        """Create and write an EvacuationDecisionRecord."""
        record = EvacuationDecisionRecord(
            handoff_id=handoff_id,
            plan_id=plan_id,
            incident_id=incident_id,
            hazard_type=hazard_type,
            zone_ids=zone_ids or [],
            route_ids=route_ids or [],
            population_affected=population_affected,
            confidence_raw=confidence_raw,
            confidence_adjusted=confidence_adjusted,
            version=version,
            decision_type=decision_type,
            processing_duration_ms=duration_ms,
            decision_rationale=rationale,
            generation_method=generation_method,
            agent_version=self._config.agent_version,
            configuration_version=self._config.compute_config_hash()[:16],
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
        )
        self._audit_writer.write(record)

    def _build_assessment_from_payload(
        self,
        handoff: AgentHandoffEvent,
        assumptions: list[str],
    ) -> dict[str, Any]:
        """Extract assessment-like data from handoff payload when Cosmos is unavailable."""
        payload = handoff.payload or {}
        assessment: dict[str, Any] = {
            "hazard_type": payload.get("hazard_type", "bushfire"),
            "severity_level": payload.get("severity_level", "high"),
            "population_estimate": payload.get("population_estimate", 1000),
            "affected_area_km2": payload.get("affected_area_km2", 0.0),
            "direction_of_travel": payload.get("direction_of_travel", ""),
            "time_horizon": payload.get("time_horizon"),
        }

        # Try to extract GeoJSON from payload
        affected_area = payload.get("affected_area") or payload.get("hazard_geojson")
        if affected_area:
            assessment["affected_area"] = affected_area

        if not any(v for v in [affected_area]):
            assumptions.append("No hazard GeoJSON in payload; zone computation will use defaults.")

        return assessment

    def _find_zone_origin_nodes(self, zone: EvacuationZone) -> list[str]:
        """Find road network nodes within a zone's boundary."""
        if not self._road_network.is_loaded or not zone.boundary:
            return []

        try:
            from shapely.geometry import Point, shape

            zone_poly = shape(zone.boundary)
            if not zone_poly.is_valid:
                zone_poly = zone_poly.buffer(0)

            origin_nodes: list[str] = []
            for node in self._road_network.get_all_nodes():
                coords = node.coordinates
                if coords:
                    pt = Point(coords.get("lng", 0), coords.get("lat", 0))
                    if zone_poly.contains(pt) or zone_poly.intersects(pt.buffer(0.001)):
                        origin_nodes.append(node.id)

            return origin_nodes
        except Exception:
            return []

    @staticmethod
    def _parse_time_horizon(time_horizon: str) -> float | None:
        """Parse time horizon string (e.g. '4h', '12h') to hours."""
        if not time_horizon:
            return None
        try:
            cleaned = str(time_horizon).strip().lower()
            if cleaned.endswith("h"):
                return float(cleaned[:-1])
            if cleaned.endswith("hr") or cleaned.endswith("hrs"):
                return float(cleaned.rstrip("hrs"))
            return float(cleaned)
        except (ValueError, TypeError):
            return None
