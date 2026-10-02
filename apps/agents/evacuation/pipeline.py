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

import hashlib
import json
import logging
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

from common.async_bridge import run_async
from common.handoffs import AgentHandoffEvent
from evacuation import telemetry as tel
from evacuation.audit import AuditWriter, AuditWriteReceipt
from evacuation.config import EvacuationConfig
from evacuation.dedup import (
    HandoffClaimInProgressError,
    HandoffClaimStoreError,
    HandoffDeduplicator,
)
from evacuation.models import (
    AssemblyArea,
    ConfidenceAdjustment,
    CorridorLoad,
    DataSnapshot,
    DecisionType,
    DestinationAllocation,
    DestinationExclusion,
    EmergencyNotification,
    EvacuationDecisionRecord,
    EvacuationPlan,
    EvacuationZone,
    ExcludedRoad,
    HazardRoutingAttributes,
    HazardRoutingContext,
    HazardSourceSnapshot,
    HazardSummary,
    OriginCoverageStatus,
    PlanStatus,
    RoutingMode,
    Traceability,
    TransportCoordinationResult,
    TransportCoordinationStatus,
    TransportGroupExclusion,
    UnresolvedDestinationDemand,
    ZoneDisposition,
    ZoneDispositionType,
    confidence_to_level,
)
from evacuation.repository import EvacuationPlanRepository
from evacuation.road_network import RoadNetworkLoader
from evacuation.router import RouteComputer
from evacuation.templates import (
    generate_generic_evacuation_guidance,
    generate_plan_summary_template,
)
from evacuation.timeline import TimelineEstimator
from evacuation.transport import TransportCoordinator
from evacuation.versioning import VersionCounter, VersionReservationError
from evacuation.zones import HazardZoneInput, ZoneComputer
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from shapely.geometry import Point, shape

from packages.domain.src.domain.models.hazard_assessment import HazardAssessment
from packages.domain.src.domain.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


class EvacuationHandoffPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    recommendation_id: str = Field(alias="recommendationId", min_length=1)
    assessment_id: str = Field(alias="assessmentId", min_length=1)


class HandoffReferenceError(ValueError):
    """Permanent rejection caused by absent, malformed, or foreign provenance."""


class TransientHandoffDependencyError(RuntimeError):
    """Retryable failure caused by an unavailable upstream store."""


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
        cosmos_recommendations_container: Any = None,
        population_data: list[dict] | None = None,
        facility_data: list[dict] | None = None,
        reference_data_metadata: dict[str, Any] | None = None,
        llm_generate_fn: Any = None,  # _generate_with_fallback callable
        emergency_notification_publisher: Any = None,
    ) -> None:
        self._config = config or EvacuationConfig()
        self._road_network = road_network or RoadNetworkLoader(
            staleness_hours=self._config.road_data_staleness_hours,
        )
        self._cosmos_plans = cosmos_plans_container
        self._cosmos_decisions = cosmos_decisions_container
        self._cosmos_assessments = cosmos_assessments_container
        self._cosmos_recommendations = cosmos_recommendations_container
        self._population_data_available = population_data is not None
        self._population_data = population_data or []
        self._facility_data_available = facility_data is not None
        self._facility_data = facility_data or []
        self._reference_data_metadata = reference_data_metadata or {}
        self._llm_generate_fn = llm_generate_fn
        self._emergency_notification_publisher = emergency_notification_publisher
        if self._emergency_notification_publisher is None and self._cosmos_decisions is not None:
            self._emergency_notification_publisher = self._persist_emergency_notification

        # Sub-components
        self._dedup = HandoffDeduplicator(
            window_minutes=self._config.handoff_dedup_window_minutes,
            cosmos_container=self._cosmos_plans,
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
        self._plan_repository = EvacuationPlanRepository(self._cosmos_plans)
        self._audit_observations: dict[
            str,
            list[EvacuationDecisionRecord],
        ] = {}
        self._audit_reconciliation_failures: dict[str, list[str]] = {}

        # Processing metrics
        self._active_plan_count: int = 0
        self._processing_queue_depth: int = 0
        self._handoff_outcome_lock = Lock()
        self._handoff_total_count = 0
        self._handoff_success_count = 0
        self._plan_telemetry_lock = Lock()
        self._committed_plan_ids: dict[str, set[str]] = {}
        self._overridden_plan_ids: dict[str, set[str]] = {}

    def _record_handoff_outcome(self, *, succeeded: bool = False) -> None:
        with self._handoff_outcome_lock:
            if succeeded:
                self._handoff_success_count += 1
            else:
                self._handoff_total_count += 1
            success_rate = self._handoff_success_count / self._handoff_total_count
        tel.handoff_success_rate.set(success_rate)

    def record_committed_plan(
        self,
        plan_id: str,
        tenant_id: str,
        *,
        commander_modified: bool = False,
    ) -> None:
        with self._plan_telemetry_lock:
            committed = self._committed_plan_ids.setdefault(tenant_id, set())
            overridden = self._overridden_plan_ids.setdefault(tenant_id, set())
            committed.add(plan_id)
            if commander_modified:
                overridden.add(plan_id)
            rate = len(overridden) / len(committed)
        tel.override_rate.set(rate, attributes={"tenant_id": tenant_id})

    @staticmethod
    def _semantic_collection_version(items: list[Any]) -> str:
        encoded_items = sorted(
            json.dumps(
                (item.model_dump(mode="json") if hasattr(item, "model_dump") else item),
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            for item in items
        )
        canonical = f"[{','.join(encoded_items)}]"
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _snapshot_record_ids(
        items: list[Any],
        candidate_fields: tuple[str, ...],
    ) -> list[str]:
        identifiers = []
        for item in items:
            value = item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            identifier = next(
                (
                    str(value[field])
                    for field in candidate_fields
                    if isinstance(value, dict) and value.get(field) not in (None, "")
                ),
                "",
            )
            if not identifier:
                canonical = json.dumps(
                    value,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                )
                identifier = f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
            identifiers.append(identifier)
        return sorted(identifiers)

    def _reference_data_state(
        self,
        available: bool,
    ) -> tuple[str, datetime | None, float | None]:
        if not available:
            return "unavailable", None, None
        raw_timestamp = self._reference_data_metadata.get("last_updated")
        if not raw_timestamp:
            return "freshness_unknown", None, None
        try:
            source_updated_at = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
        except ValueError:
            return "freshness_invalid", None, None
        if source_updated_at.tzinfo is None:
            return "freshness_invalid", None, None
        if source_updated_at > datetime.now(UTC):
            return "freshness_invalid", source_updated_at, None
        age_hours = max(
            0.0,
            (datetime.now(UTC) - source_updated_at).total_seconds() / 3600,
        )
        status = "stale" if age_hours > self._config.population_data_staleness_hours else "fresh"
        return status, source_updated_at, age_hours

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_handoff(self, handoff: AgentHandoffEvent) -> EvacuationPlan | None:
        """Execute full 10-stage pipeline.

        Returns the generated ``EvacuationPlan``, or ``None`` if the handoff
        was rejected (validation failure or duplicate).
        """
        tenant_id = handoff.tenant_id or "live"
        incident_id = handoff.incident_id
        with tel.start_span(
            "evacuation.process_handoff",
            attributes={
                "handoff_id": handoff.handoff_id,
                "incident_id": incident_id,
                "tenant_id": tenant_id,
                "source_agent": handoff.source_agent,
                "correlation_id": handoff.handoff_id,
            },
        ):
            pipeline_start = time.monotonic()
            incident_scope_key = f"{tenant_id}:{incident_id}"
            assumptions: list[str] = []
            self._audit_observations[handoff.handoff_id] = []
            self._audit_reconciliation_failures.pop(handoff.handoff_id, None)

            metric_dimensions = {
                "incident_id": incident_id,
                "tenant_id": tenant_id,
            }
            tel.handoff_intake_count.add(1, attributes=metric_dimensions)
            self._record_handoff_outcome()

            logger.info(
                "Pipeline started: handoff_id=%s incident=%s",
                handoff.handoff_id,
                incident_id,
            )

            # Stage 1 — Handoff intake and validation
            with tel.start_span("evacuation.validate_handoff") as _s1:
                accepted = self._stage_1_handoff_intake(handoff, incident_scope_key, tenant_id)
                if not accepted:
                    self._reconcile_terminal_audit(handoff.handoff_id)
                    return None

            tel.emit_handoff_received(handoff.handoff_id, incident_id, tenant_id)

            # Stage 2 — Assessment retrieval
            with tel.start_span("evacuation.retrieve_assessment"):
                try:
                    assessment_data = self._stage_2_retrieve_assessment(
                        handoff,
                        incident_scope_key,
                        tenant_id,
                        assumptions,
                    )
                except HandoffReferenceError as exc:
                    try:
                        self._dedup.reject(
                            tenant_id,
                            handoff.incident_id,
                            handoff.handoff_id,
                            incident_scope_key,
                            str(exc),
                        )
                    except (HandoffClaimInProgressError, HandoffClaimStoreError) as claim_exc:
                        raise TransientHandoffDependencyError(
                            "Failed to persist handoff rejection outcome"
                        ) from claim_exc
                    self._write_audit(
                        handoff_id=handoff.handoff_id,
                        incident_id=handoff.incident_id,
                        decision_type=DecisionType.handoff_rejected,
                        rationale=str(exc),
                        duration_ms=0.0,
                        incident_scope_key=incident_scope_key,
                        tenant_id=tenant_id,
                    )
                    self._reconcile_audit_steps(
                        handoff.handoff_id,
                        [
                            DecisionType.handoff_received.value,
                            DecisionType.handoff_rejected.value,
                        ],
                    )
                    tel.handoff_rejected_count.add(
                        1,
                        attributes=metric_dimensions,
                    )
                    return None
                except TransientHandoffDependencyError:
                    self._release_handoff_claim(
                        handoff,
                        incident_scope_key,
                        "Upstream dependency unavailable",
                    )
                    raise

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
                effective_network = self._stage_4_road_network_preparation(
                    handoff,
                    zones,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                assessment_data["effective_road_network_version"] = (
                    effective_network.get_version() or assessment_data.get("road_network_version", "unavailable")
                )
                road_status = str(assessment_data.get("road_data_status") or "")
                if road_status != "fresh":
                    tel.degradation_events.add(
                        1,
                        attributes={
                            **metric_dimensions,
                            "component": "road_network",
                        },
                    )
                    tel.emit_degradation_event(
                        "road_network",
                        2 if assessment_data.get("road_data_usable") else 3,
                    )

            # Stage 5 — Route computation
            with tel.start_span("evacuation.compute_routes") as s5:
                route_start = time.monotonic()
                routes = self._stage_5_compute_routes(
                    handoff,
                    zones,
                    assessment_data,
                    effective_network,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                route_ms = (time.monotonic() - route_start) * 1000
                tel.route_computation_time.record(
                    route_ms,
                    attributes=metric_dimensions,
                )
                if hasattr(s5, "set_attribute"):
                    s5.set_attribute("route.count", len(routes))

                # Check for congestion risk routes (>80% utilisation)
                for r in routes:
                    if r.get("congestion_risk", False):
                        tel.congestion_risk_routes.add(
                            1,
                            attributes={
                                "incident_id": incident_id,
                                "tenant_id": tenant_id,
                            },
                        )

            # Stage 6 — Transport coordination
            with tel.start_span("evacuation.coordinate_transport"):
                transport_result = self._stage_6_transport_coordination(
                    handoff,
                    zones,
                    routes,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                transport_reqs = [requirement.model_dump(mode="json") for requirement in transport_result.requirements]
                assessment_data["transport_coordination"] = transport_result.model_dump(mode="json")
                tel.transport_requests_generated.add(
                    len(transport_reqs),
                    attributes=metric_dimensions,
                )
                for tr in transport_reqs:
                    category = tr.get("category", "general")
                    tel.transport_by_category.add(
                        1,
                        attributes={
                            **metric_dimensions,
                            "category": category,
                        },
                    )
                total_vehicles = sum(tr.get("quantity_required", 0) for tr in transport_reqs)
                tel.transport_vehicles_estimated.set(
                    float(total_vehicles),
                    attributes=metric_dimensions,
                )

            # Stage 7 — Timeline estimation
            with tel.start_span("evacuation.estimate_timeline"):
                phases, zone_dispositions, timeline_assumptions = self._stage_7_timeline_estimation(
                    handoff,
                    zones,
                    routes,
                    transport_reqs,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                )
                assumptions.extend(timeline_assumptions)

                hazard_type = assessment_data.get("hazard_type", "bushfire")
                for disposition in zone_dispositions:
                    zone_number = str(disposition.zone_number)
                    if disposition.disposition == ZoneDispositionType.shelter_in_place:
                        tel.shelter_in_place_count.add(
                            1,
                            attributes=metric_dimensions,
                        )
                        tel.emit_shelter_in_place_recommended(
                            incident_id,
                            zone_number,
                            disposition.affected_population,
                            hazard_type,
                        )
                    elif disposition.disposition == ZoneDispositionType.emergency_escalation:
                        tel.emergency_escalation_count.add(
                            1,
                            attributes=metric_dimensions,
                        )
                        tel.emit_emergency_escalation(
                            incident_id,
                            zone_number,
                            disposition.affected_population,
                        )
                    if disposition.clearance_deficit_minutes > 0:
                        tel.time_deficit_flag_count.add(
                            1,
                            attributes=metric_dimensions,
                        )

            # Stage 8 — Plan summary generation
            with tel.start_span("evacuation.generate_summary"):
                summary, generation_method, confidence_score = self._stage_8_plan_summary(
                    handoff,
                    zones,
                    routes,
                    transport_reqs,
                    phases,
                    zone_dispositions,
                    assessment_data,
                    incident_scope_key,
                    tenant_id,
                    assumptions,
                )
                if generation_method in ("template_fallback", "safety_fallback"):
                    tel.fallback_mode_activations.add(
                        1,
                        attributes=metric_dimensions,
                    )
                    tel.degradation_events.add(
                        1,
                        attributes={**metric_dimensions, "component": "llm"},
                    )
                    tel.emit_degradation_event("llm", 2)

            # Stage 9 — Versioning and persistence
            plan = self._stage_9_versioning_persistence(
                handoff,
                zones,
                routes,
                transport_reqs,
                phases,
                zone_dispositions,
                summary,
                generation_method,
                confidence_score,
                assessment_data,
                incident_scope_key,
                tenant_id,
                assumptions,
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
            try:
                self._dedup.complete(
                    tenant_id,
                    handoff.incident_id,
                    handoff.handoff_id,
                    incident_scope_key,
                    plan.plan_id,
                )
            except (HandoffClaimInProgressError, HandoffClaimStoreError) as exc:
                raise TransientHandoffDependencyError(
                    "Plan persisted but handoff completion is pending recovery"
                ) from exc

            self.record_committed_plan(plan.plan_id, tenant_id)
            for zone in zones:
                tel.zone_population_covered.set(
                    float(zone.population_estimate),
                    attributes={
                        "incident_id": incident_id,
                        "tenant_id": tenant_id,
                        "zone": str(zone.zone_number),
                    },
                )
            tel.active_plans_gauge.set(
                float(self._active_plan_count),
                attributes={"tenant_id": tenant_id},
            )
            tel.routes_per_plan.record(
                len(routes),
                attributes={
                    "incident_id": incident_id,
                    "tenant_id": tenant_id,
                },
            )
            tel.version_count_per_incident.set(
                float(plan.version),
                attributes={
                    "incident_id": incident_id,
                    "tenant_id": tenant_id,
                },
            )
            tel.dynamic_update_rate.set(
                float(plan.version),
                attributes={
                    "incident_id": incident_id,
                    "tenant_id": tenant_id,
                },
            )
            tel.emit_plan_generated(
                plan_id=plan.plan_id,
                version=plan.version,
                confidence=confidence_score,
                routes_count=len(routes),
                generation_method=generation_method,
            )
            for route in routes:
                if route.get("congestion_risk", False):
                    tel.emit_route_conflict(
                        plan_id=plan.plan_id,
                        route_id=str(route.get("route_id") or ""),
                        utilisation_pct=float(route.get("congestion_risk_pct", 0.0)),
                    )
            for disposition in zone_dispositions:
                if disposition.clearance_deficit_minutes > 0:
                    tel.emit_time_deficit_detected(
                        plan.plan_id,
                        str(disposition.zone_number),
                        disposition.clearance_deficit_minutes,
                    )

            # Update audit gauges
            tel.audit_buffer_depth.set(
                float(self._audit_writer.buffer_depth),
                attributes=metric_dimensions,
            )
            audit_status = self._audit_writer.get_status()
            tier_val = {
                "healthy": 1,
                "buffering": 2,
                "degraded": 3,
            }[audit_status]
            tel.audit_tier.set(
                float(tier_val),
                attributes=metric_dimensions,
            )
            if self._road_network.is_loaded:
                tel.road_data_stale.set(
                    1.0 if self._road_network.is_stale() else 0.0,
                    attributes=metric_dimensions,
                )

            total_ms = (time.monotonic() - pipeline_start) * 1000
            tel.plan_generation_latency.record(
                total_ms,
                attributes={**metric_dimensions, "outcome": "succeeded"},
            )

            # SLA breach check (30-second SLA for initial plan)
            if total_ms > 30_000:
                tel.sla_breach_count.add(1)
                tel.emit_sla_breach(handoff.handoff_id, total_ms, "initial")

            self._record_handoff_outcome(succeeded=True)

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
            tel.handoff_rejected_count.add(
                1,
                attributes={
                    "incident_id": handoff.incident_id,
                    "tenant_id": tenant_id,
                },
            )
            return False

        if handoff.source_agent != "risk_assessment":
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.handoff_rejected,
                rationale=f"Untrusted handoff source: {handoff.source_agent}",
                duration_ms=(time.monotonic() - t0) * 1000,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
            )
            tel.handoff_rejected_count.add(
                1,
                attributes={
                    "incident_id": handoff.incident_id,
                    "tenant_id": tenant_id,
                },
            )
            return False

        if not handoff.incident_id.strip() or not handoff.tenant_id.strip() or not handoff.scope_key.strip():
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.handoff_rejected,
                rationale="Handoff incident, tenant, and scope values must be non-empty",
                duration_ms=(time.monotonic() - t0) * 1000,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id or "unknown",
            )
            tel.handoff_rejected_count.add(
                1,
                attributes={
                    "incident_id": handoff.incident_id,
                    "tenant_id": tenant_id or "unknown",
                },
            )
            return False

        try:
            EvacuationHandoffPayload.model_validate(handoff.payload)
        except ValidationError as exc:
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.handoff_rejected,
                rationale=f"Invalid evacuation handoff payload: {exc}",
                duration_ms=(time.monotonic() - t0) * 1000,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
            )
            tel.handoff_rejected_count.add(
                1,
                attributes={
                    "incident_id": handoff.incident_id,
                    "tenant_id": tenant_id,
                },
            )
            return False

        try:
            claim = self._dedup.try_claim(
                tenant_id,
                handoff.incident_id,
                handoff.handoff_id,
                incident_scope_key,
            )
        except (HandoffClaimInProgressError, HandoffClaimStoreError) as exc:
            raise TransientHandoffDependencyError(str(exc)) from exc
        if not claim.acquired:
            duration_ms = (time.monotonic() - t0) * 1000
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.duplicate_discarded,
                rationale=(
                    f"Completed duplicate handoff discarded: {handoff.handoff_id}; plan_id={claim.plan_id or 'none'}"
                ),
                duration_ms=duration_ms,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
            )
            logger.info("Duplicate handoff discarded: %s", handoff.handoff_id)
            tel.duplicate_discard_count.add(
                1,
                attributes={
                    "incident_id": handoff.incident_id,
                    "tenant_id": tenant_id,
                },
            )
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
        payload = EvacuationHandoffPayload.model_validate(handoff.payload)
        recommendation_doc = self._read_upstream(
            self._cosmos_recommendations,
            payload.recommendation_id,
            incident_scope_key,
            "recommendation",
        )
        assessment_doc = self._read_upstream(
            self._cosmos_assessments,
            payload.assessment_id,
            incident_scope_key,
            "assessment",
        )
        try:
            recommendation = Recommendation.model_validate(recommendation_doc)
            primary_assessment = HazardAssessment.model_validate(assessment_doc)
        except ValidationError as exc:
            raise HandoffReferenceError(f"Referenced evacuation provenance is malformed: {exc}") from exc

        self._validate_upstream_scope(handoff, recommendation, primary_assessment)
        if recommendation.type != "evacuation":
            raise HandoffReferenceError("Referenced recommendation is not an evacuation recommendation")
        if recommendation.assessment_id != primary_assessment.hazard_assessment_id:
            raise HandoffReferenceError("Recommendation references a different hazard assessment")
        active_assessments = self._load_active_assessments(
            handoff,
            primary_assessment,
            incident_scope_key,
        )
        primary_hazard_map = primary_assessment.hazard_map
        if primary_hazard_map is None:
            raise HandoffReferenceError("Hazard assessment does not contain a hazard map")
        hazard_sources = [self._hazard_source_snapshot(assessment) for assessment in active_assessments]

        assessment_data = {
            **primary_assessment.model_dump(mode="json"),
            "hazard_type": primary_hazard_map.hazard_type,
            "severity_level": primary_hazard_map.severity_level,
            "population_estimate": primary_hazard_map.population_estimate or 0,
            "affected_area": primary_hazard_map.affected_area,
            "time_horizon": primary_hazard_map.time_horizon,
            "hazard_confidence": primary_hazard_map.confidence_score,
            "hazard_sources": [source.model_dump(mode="json") for source in hazard_sources],
            "recommendation_id": recommendation.recommendation_id,
            "recommendation_summary": recommendation.summary,
            "recommendation_explanation": recommendation.explanation,
        }

        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.assessment_retrieved,
            rationale=(
                "Assessment source: persisted recommendation and hazard assessment. "
                f"Hazard type: {assessment_data.get('hazard_type', 'unknown')}"
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            hazard_type=assessment_data.get("hazard_type"),
            assessment_id=payload.assessment_id,
            recommendation_id=payload.recommendation_id,
            input_signal_ids=sorted(primary_assessment.input_signal_ids),
        )
        return assessment_data

    def _load_active_assessments(
        self,
        handoff: AgentHandoffEvent,
        primary_assessment: HazardAssessment,
        incident_scope_key: str,
    ) -> list[HazardAssessment]:
        now = datetime.now(UTC)
        documents = [primary_assessment.model_dump(mode="json")]
        if hasattr(self._cosmos_assessments, "query_items"):
            try:
                documents.extend(
                    self._cosmos_assessments.query_items(
                        query=("SELECT * FROM c WHERE c.incident_id = @incident_id AND c.status = @status"),
                        parameters=[
                            {"name": "@incident_id", "value": handoff.incident_id},
                            {"name": "@status", "value": "active"},
                        ],
                        partition_key=incident_scope_key,
                    )
                )
            except Exception as exc:
                raise TransientHandoffDependencyError("Active hazard assessment query failed") from exc

        active_by_id: dict[str, HazardAssessment] = {}
        for document in documents:
            try:
                assessment = HazardAssessment.model_validate(document)
            except ValidationError as exc:
                raise HandoffReferenceError(f"Active hazard assessment is malformed: {exc}") from exc
            self._validate_assessment_scope(handoff, assessment)
            if assessment.status != "active":
                continue
            if assessment.valid_until is not None and assessment.valid_until <= now:
                if assessment.hazard_assessment_id == primary_assessment.hazard_assessment_id:
                    raise HandoffReferenceError("Referenced hazard assessment has expired")
                continue
            self._validate_hazard_geometry(assessment)
            active_by_id[assessment.hazard_assessment_id] = assessment

        if primary_assessment.hazard_assessment_id not in active_by_id:
            raise HandoffReferenceError("Referenced hazard assessment is not active")
        return sorted(
            active_by_id.values(),
            key=lambda assessment: (
                assessment.generated_at,
                assessment.hazard_assessment_id,
            ),
        )

    def _hazard_source_snapshot(
        self,
        assessment: HazardAssessment,
    ) -> HazardSourceSnapshot:
        hazard_map = assessment.hazard_map
        if hazard_map is None:
            raise HandoffReferenceError("Active hazard assessment has no hazard map")
        geometry_json = json.dumps(
            hazard_map.affected_area,
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            return HazardSourceSnapshot(
                assessment_id=assessment.hazard_assessment_id,
                version=assessment.version,
                hazard_type=hazard_map.hazard_type,
                severity_level=hazard_map.severity_level,
                affected_area=hazard_map.affected_area,
                input_signal_ids=assessment.input_signal_ids,
                generated_at=assessment.generated_at,
                valid_until=assessment.valid_until,
                buffer_radius_metres=self._zone_computer.buffer_radius_metres(
                    hazard_map.hazard_type,
                    hazard_map.severity_level,
                ),
                geometry_sha256=hashlib.sha256(geometry_json.encode()).hexdigest(),
                routing_attributes=HazardRoutingAttributes.model_validate(
                    assessment.input_snapshot.get("hazard_routing", {})
                ),
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise HandoffReferenceError(f"Hazard routing attributes are invalid: {exc}") from exc

    def _build_hazard_routing_context(
        self,
        hazard_sources: list[HazardSourceSnapshot],
        incident_scope_key: str = "",
    ) -> HazardRoutingContext:
        wind_from_degrees = next(
            (
                float(source.routing_attributes.wind_from_degrees)
                for source in reversed(hazard_sources)
                if source.hazard_type == "bushfire" and source.routing_attributes.wind_from_degrees is not None
            ),
            None,
        )
        return HazardRoutingContext(
            hazard_types=sorted({source.hazard_type for source in hazard_sources}),
            source_assessment_ids=[source.assessment_id for source in hazard_sources],
            incident_scope_key=incident_scope_key,
            bushfire_exclusion_areas=[
                self._zone_computer.buffer_geometry_metres(
                    source.affected_area,
                    2_000,
                )
                for source in hazard_sources
                if source.hazard_type == "bushfire"
            ],
            wind_from_degrees=wind_from_degrees,
        )

    @staticmethod
    def _validate_hazard_geometry(assessment: HazardAssessment) -> None:
        if assessment.hazard_map is None:
            raise HandoffReferenceError("Active hazard assessment has no hazard map")
        try:
            hazard_geometry = shape(assessment.hazard_map.affected_area)
        except (TypeError, ValueError) as exc:
            raise HandoffReferenceError("Hazard assessment geometry is invalid") from exc
        if (
            hazard_geometry.geom_type not in {"Polygon", "MultiPolygon"}
            or hazard_geometry.is_empty
            or not hazard_geometry.is_valid
            or hazard_geometry.area <= 0
        ):
            raise HandoffReferenceError("Hazard assessment geometry must be a valid non-empty polygon")

    @staticmethod
    def _validate_assessment_scope(
        handoff: AgentHandoffEvent,
        assessment: HazardAssessment,
    ) -> None:
        if assessment.incident_id != handoff.incident_id:
            raise HandoffReferenceError("Active hazard assessment belongs to a different incident")
        if assessment.tenant_id != handoff.tenant_id:
            raise HandoffReferenceError("Active hazard assessment belongs to a different tenant")
        if assessment.incident_scope_key and assessment.incident_scope_key not in {
            handoff.scope_key,
            f"{handoff.tenant_id}:{handoff.incident_id}",
        }:
            raise HandoffReferenceError("Active hazard assessment belongs to a different incident scope")

    @staticmethod
    def _read_upstream(store: Any, record_id: str, partition_key: str, record_type: str) -> dict[str, Any]:
        if store is None:
            raise TransientHandoffDependencyError(f"{record_type} store is not configured")
        try:
            document = store.read_item(item=record_id, partition_key=partition_key)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
            if status_code == 404 or "NotFound" in type(exc).__name__:
                raise HandoffReferenceError(f"Referenced {record_type} {record_id} was not found") from exc
            raise TransientHandoffDependencyError(f"{record_type} store is unavailable") from exc
        if not isinstance(document, dict):
            raise HandoffReferenceError(f"Referenced {record_type} {record_id} is invalid")
        return document

    @staticmethod
    def _validate_upstream_scope(
        handoff: AgentHandoffEvent,
        recommendation: Recommendation,
        assessment: HazardAssessment,
    ) -> None:
        if recommendation.incident_id != handoff.incident_id or assessment.incident_id != handoff.incident_id:
            raise HandoffReferenceError("Referenced records belong to a different incident")
        if recommendation.tenant_id != handoff.tenant_id or assessment.tenant_id != handoff.tenant_id:
            raise HandoffReferenceError("Referenced records belong to a different tenant")
        for scope in (recommendation.incident_scope_key, assessment.incident_scope_key):
            if scope and scope not in {handoff.scope_key, f"{handoff.tenant_id}:{handoff.incident_id}"}:
                raise HandoffReferenceError("Referenced records belong to a different incident scope")

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
        population_status, population_updated_at, population_age_hours = self._reference_data_state(
            self._population_data_available
        )
        assessment_data["population_data_status"] = population_status
        assessment_data["population_source_updated_at"] = population_updated_at
        assessment_data["population_source_age_hours"] = population_age_hours
        if population_status != "fresh":
            age_text = f"{population_age_hours:.1f} hours old" if population_age_hours is not None else "age unknown"
            gap = f"population_data_{population_status}"
            assessment_data.setdefault("data_quality_gaps", []).append(gap)
            assessment_data["immediate_human_review_required"] = True
            assumptions.append(
                "POPULATION DATA DEGRADED: "
                f"status={population_status}; {age_text}. Population and "
                "vulnerability estimates require local verification."
            )

        hazard_geojson = assessment_data.get("affected_area") or assessment_data.get(
            "hazard_geojson",
        )

        if hazard_geojson:
            try:
                hazard_sources = [
                    HazardSourceSnapshot.model_validate(source) for source in assessment_data.get("hazard_sources", [])
                ]
                hazard_inputs = [
                    HazardZoneInput(
                        affected_area=source.affected_area,
                        hazard_type=source.hazard_type,
                        severity_level=source.severity_level,
                        assessment_id=source.assessment_id,
                    )
                    for source in hazard_sources
                ] or [
                    HazardZoneInput(
                        affected_area=hazard_geojson,
                        hazard_type=str(assessment_data.get("hazard_type", "bushfire")),
                        severity_level=str(assessment_data.get("severity_level", "high")),
                    )
                ]
                with tel.start_span(
                    "evacuation.shapely_intersection",
                    attributes={"hazard.count": len(hazard_inputs)},
                ):
                    zones = self._zone_computer.compute_zones_multi_hazard(
                        hazards=hazard_inputs,
                        population_data=self._population_data or None,
                    )
                assessment_data["affected_area"] = self._zone_computer.merge_affected_areas(hazard_inputs)
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
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> RoadNetworkLoader:
        """Load road network (if needed) and apply zone-based capacity reduction."""
        t0 = time.monotonic()

        # Ensure road network is loaded
        if not self._road_network.is_loaded:
            try:
                self._road_network.load(self._config.road_network_file_path)
            except Exception as exc:
                logger.warning("Road network load failed: %s", exc)
                assumptions.append(
                    f"Road network could not be loaded ({exc}); no route, "
                    "destination, passability, or capacity will be computed."
                )

        road_status = "unavailable"
        road_age_hours = self._road_network.source_age_hours()
        if self._road_network.is_loaded and self._road_network.node_count > 0 and self._road_network.edge_count > 0:
            if self._road_network.is_stale():
                road_status = "stale"
            elif self._road_network.last_refresh_failed:
                road_status = "fresh_cache_refresh_failed"
            else:
                road_status = "fresh"
        road_usable = road_status in {"fresh", "fresh_cache_refresh_failed"}
        assessment_data.update(
            {
                "road_data_status": road_status,
                "road_data_usable": road_usable,
                "road_source_updated_at": self._road_network.source_updated_at,
                "road_source_age_hours": road_age_hours,
                "road_refresh_failure_reason": (self._road_network.refresh_failure_reason),
                "road_network_version": (
                    self._road_network.get_version() if self._road_network.is_loaded else "unavailable"
                ),
            }
        )
        if road_status != "fresh":
            age_text = f"{road_age_hours:.1f} hours old" if road_age_hours is not None else "age unknown"
            gap = f"road_data_{road_status}"
            assessment_data.setdefault("data_quality_gaps", []).append(gap)
            assessment_data["immediate_human_review_required"] = True
            use_text = (
                "Fresh last-known-good roads retained for provisional computation"
                if road_usable
                else "Computed routing and destination selection disabled"
            )
            assumptions.append(
                "ROAD DATA DEGRADED: "
                f"status={road_status}; {age_text}. {use_text}; immediate "
                "incident-controller review is required."
            )
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.degradation_detected,
                rationale=(
                    f"Road data status={road_status}; age_hours={road_age_hours}; "
                    f"version={assessment_data['road_network_version']}; "
                    f"routing_enabled={road_usable}; "
                    f"refresh_failure={self._road_network.refresh_failure_reason or 'none'}"
                ),
                duration_ms=(time.monotonic() - t0) * 1000,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
                hazard_type=str(assessment_data.get("hazard_type") or ""),
                data_quality_gaps=[gap],
                immediate_human_review_required=True,
            )

        effective_network = self._road_network
        if not road_usable:
            effective_network = RoadNetworkLoader(
                staleness_hours=self._config.road_data_staleness_hours,
            )
        elif self._road_network.is_loaded and zones:
            try:
                zone_polygons = self._zone_computer.get_zone_polygons(zones)
                edges_as_dicts = []
                for edge in self._road_network.get_all_edges():
                    edge_dict = edge.model_dump()
                    geom = self._road_network.get_edge_geometry(edge.id)
                    if geom is not None:
                        edge_dict["_geometry"] = geom
                    edges_as_dicts.append(edge_dict)

                with tel.start_span(
                    "evacuation.apply_zone_capacity_reduction",
                    attributes={"zone.count": len(zone_polygons)},
                ):
                    adjusted_edges = self._zone_computer.apply_zone_capacity_reduction(
                        edges_as_dicts,
                        zone_polygons,
                    )
                effective_network = self._road_network.effective_copy(adjusted_edges)
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
        return effective_network

    # ------------------------------------------------------------------
    # Stage 5 — Route Computation
    # ------------------------------------------------------------------

    def _stage_5_compute_routes(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        assessment_data: dict[str, Any],
        road_network: RoadNetworkLoader,
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> list[dict[str, Any]]:
        """Compute evacuation routes using Dijkstra's algorithm."""
        t0 = time.monotonic()
        route_models = []
        hazard_type = assessment_data.get("hazard_type", "bushfire")

        if not road_network.is_loaded:
            assumptions.append("Road network not available; route computation skipped.")
            for zone in zones:
                zone.origin_node_ids = []
                zone.origin_coverage_status = (
                    OriginCoverageStatus.no_network_origin
                    if zone.population_estimate > 0
                    else OriginCoverageStatus.not_required
                )
            duration_ms = (time.monotonic() - t0) * 1000
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.routes_computed,
                rationale="No road network — route computation skipped",
                duration_ms=duration_ms,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
                routes_count=0,
            )
            return []

        route_computer = RouteComputer(
            road_network=road_network,
            config=self._config,
            hazard_context=self._build_hazard_routing_context(
                [HazardSourceSnapshot.model_validate(source) for source in assessment_data.get("hazard_sources", [])],
                incident_scope_key,
            ),
        )

        # Get closed edges to exclude
        closed_edge_ids = {edge.id for edge in road_network.get_closed_edges()}

        origin_nodes_by_zone = self._assign_zone_origin_nodes(zones, road_network)
        for zone in zones:
            origin_nodes = origin_nodes_by_zone[zone.zone_number]
            zone.origin_node_ids = origin_nodes
            zone.origin_coverage_status = (
                OriginCoverageStatus.covered
                if origin_nodes
                else (
                    OriginCoverageStatus.no_network_origin
                    if zone.population_estimate > 0
                    else OriginCoverageStatus.not_required
                )
            )
            if zone.origin_coverage_status == OriginCoverageStatus.no_network_origin:
                assumptions.append(
                    f"Zone {zone.zone_number} has population but no road-network "
                    "origin within its exclusive membership."
                )

            evacuation_routes = route_computer.compute_routes(
                origin_nodes=origin_nodes,
                zone_number=zone.zone_number,
                population=zone.population_estimate,
                hazard_type=hazard_type,
                excluded_edge_ids=closed_edge_ids,
                allocate_population=False,
            )
            route_models.extend(evacuation_routes)

        with tel.start_span("evacuation.multi_path_distribution"):
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
            zone.unallocated_vulnerable_population = route_computer.unallocated_vulnerable_population_by_zone.get(
                zone.zone_number,
                min(
                    zone.vulnerable_population,
                    zone.unallocated_route_population,
                ),
            )
        all_routes = [route.model_dump() for route in route_models]

        assessment_data["routing_mode"] = route_computer.routing_mode.value
        assessment_data["hazard_routing_data_gaps"] = route_computer.hazard_data_gaps
        assessment_data["excluded_destinations"] = [
            exclusion.model_dump(mode="json") for exclusion in route_computer.destination_exclusions
        ]
        assessment_data["corridor_loads"] = [load.model_dump(mode="json") for load in route_computer.corridor_loads]
        assessment_data["destination_allocations"] = [
            allocation.model_dump(mode="json") for allocation in route_computer.destination_allocations
        ]
        assessment_data["unresolved_destination_demands"] = [
            demand.model_dump(mode="json") for demand in route_computer.unresolved_destination_demands
        ]
        if route_computer.unresolved_destination_demands:
            assumptions.append(
                "ASSEMBLY CAPACITY GAP: "
                + "; ".join(
                    f"Zone {demand.zone_number} {demand.population} people: {demand.reason}"
                    for demand in route_computer.unresolved_destination_demands
                )
            )
        assessment_data["excluded_roads"] = [road.model_dump(mode="json") for road in route_computer.excluded_roads]
        assessment_data["zero_route_zones"] = [
            zone.zone_number
            for zone in zones
            if not any(
                int(route.zone_id) == zone.zone_number and route.allocated_population > 0 for route in route_models
            )
        ]
        unavailable_roads_by_reason: dict[str, int] = {}
        for road in route_computer.excluded_roads:
            reason = road.source_hazard_type or road.closure_reason.value
            unavailable_roads_by_reason[reason] = unavailable_roads_by_reason.get(reason, 0) + 1
        assessment_data["unavailable_roads_by_reason"] = unavailable_roads_by_reason
        if route_computer.hazard_data_gaps:
            assumptions.append("HAZARD ROUTING DEGRADED: " + ", ".join(route_computer.hazard_data_gaps))

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
            routes_count=len(route_ids),
            constraints_applied=sorted(
                f"road_exclusion:{road['edge_id']}" for road in assessment_data.get("excluded_roads", [])
            ),
        )
        return all_routes

    # ------------------------------------------------------------------
    # Stage 6 — Transport Coordination
    # ------------------------------------------------------------------

    def _stage_6_transport_coordination(
        self,
        handoff: AgentHandoffEvent,
        zones: list[EvacuationZone],
        routes: list[dict[str, Any]],
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> TransportCoordinationResult:
        """Compute transport requirements for vulnerable populations."""
        t0 = time.monotonic()

        zone_dicts = [z.model_dump() for z in zones]
        facility_status, facility_updated_at, facility_age_hours = self._reference_data_state(
            self._facility_data_available
        )
        assessment_data["facility_data_status"] = facility_status
        assessment_data["facility_source_updated_at"] = facility_updated_at
        assessment_data["facility_source_age_hours"] = facility_age_hours
        if facility_status != "fresh":
            age_text = f"{facility_age_hours:.1f} hours old" if facility_age_hours is not None else "age unknown"
            gap = f"facility_data_{facility_status}"
            assessment_data.setdefault("data_quality_gaps", []).append(gap)
            assessment_data["immediate_human_review_required"] = True
            assumptions.append(
                "FACILITY DATA DEGRADED: "
                f"status={facility_status}; {age_text}. Zero transport "
                "requests must not be interpreted as zero vulnerable people."
            )
        assembly_area_dicts = (
            [
                {
                    "assembly_area_id": aa.assembly_area_id,
                    "name": aa.name,
                    "coordinates": aa.coordinates,
                    "accessibility_features": aa.accessibility_features,
                    "shelter_types": aa.shelter_types,
                }
                for aa in self._road_network.get_assembly_areas()
            ]
            if self._road_network.is_loaded and assessment_data.get("road_data_usable", True)
            else []
        )

        with tel.start_span(
            "evacuation.query_facilities",
            attributes={"facility.count": len(self._facility_data)},
        ):
            transport_result = self._transport_coordinator.coordinate_transport(
                zones=zone_dicts,
                facilities=(self._facility_data if self._facility_data_available else None),
                assembly_areas=assembly_area_dicts,
                incident_scope_key=incident_scope_key,
                destination_allocations=assessment_data.get(
                    "destination_allocations",
                    [],
                ),
                routes=routes,
            )
        assumptions.extend(transport_result.assumptions)
        for exclusion in transport_result.exclusions:
            if exclusion.reason.value not in {
                "outside_affected_area",
                "advisory_only",
            }:
                assumptions.append(f"Transport group {exclusion.facility_id} excluded: {exclusion.details}")

        duration_ms = (time.monotonic() - t0) * 1000
        self._write_audit(
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            decision_type=DecisionType.transport_coordinated,
            rationale=(
                f"Identified {len(transport_result.requirements)} transport "
                f"requirement(s) from {len(self._facility_data)} facilities; "
                f"status={transport_result.status.value}."
            ),
            duration_ms=duration_ms,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            population_affected=sum(z.vulnerable_population for z in zones),
            transport_requests_count=len(transport_result.requirements),
        )
        return transport_result

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
    ) -> tuple[list[Any], list[ZoneDisposition], list[str]]:
        """Compute phases and persist one auditable disposition per zone."""
        t0 = time.monotonic()
        hazard_type = assessment_data.get("hazard_type", "bushfire")

        # Parse time horizon
        time_horizon_hours: float | None = None
        time_horizon_str = assessment_data.get("time_horizon")
        if time_horizon_str:
            time_horizon_hours = self._parse_time_horizon(time_horizon_str)

        zone_dicts = [z.model_dump() for z in zones]

        with tel.start_span(
            "evacuation.compute_phase",
            attributes={"phase.count": 5},
        ):
            phases, dispositions, assumptions = self._timeline_estimator.estimate_timeline(
                zones=zone_dicts,
                routes=routes,
                transport_requirements=transport_reqs,
                hazard_type=hazard_type,
                hazard_time_horizon_hours=time_horizon_hours,
                corridor_loads=assessment_data.get("corridor_loads", []),
                timeline_anchor=handoff.created_at,
            )

        duration_ms = (time.monotonic() - t0) * 1000
        for disposition in dispositions:
            if disposition.disposition == ZoneDispositionType.emergency_escalation:
                self._route_emergency_notification(
                    handoff,
                    disposition,
                    incident_scope_key,
                    tenant_id,
                )
            decision_type = (
                DecisionType.shelter_in_place_recommended
                if disposition.disposition == ZoneDispositionType.shelter_in_place
                else DecisionType.timeline_estimated
            )
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=decision_type,
                rationale=disposition.rationale,
                duration_ms=duration_ms / max(1, len(dispositions)),
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
                zone_ids=[str(disposition.zone_number)],
                population_affected=disposition.affected_population,
                zone_dispositions=[disposition],
            )
        return phases, dispositions, assumptions

    def _route_emergency_notification(
        self,
        handoff: AgentHandoffEvent,
        disposition: ZoneDisposition,
        incident_scope_key: str,
        tenant_id: str,
    ) -> None:
        notification = EmergencyNotification(
            notification_id=(f"emergency-{handoff.handoff_id}-zone-{disposition.zone_number}"),
            handoff_id=handoff.handoff_id,
            incident_id=handoff.incident_id,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            zone_id=disposition.zone_id,
            affected_population=disposition.affected_population,
            rationale=disposition.rationale,
        )
        disposition.emergency_notification_id = notification.notification_id
        if self._emergency_notification_publisher is None:
            disposition.prerequisites.append(
                "Emergency notification integration unavailable; contact services manually"
            )
            return
        try:
            receipt = self._emergency_notification_publisher(notification)
        except Exception:
            logger.exception(
                "Emergency notification failed for incident %s zone %s",
                handoff.incident_id,
                disposition.zone_number,
            )
            disposition.prerequisites.append("Emergency notification failed; contact services manually")
            return
        if receipt:
            disposition.emergency_notification_receipt = str(receipt)

    def _persist_emergency_notification(
        self,
        notification: EmergencyNotification,
    ) -> str:
        if self._cosmos_decisions is None:
            raise RuntimeError("Emergency notification store is unavailable")
        body = notification.model_dump(mode="json")
        body["id"] = notification.notification_id
        try:
            self._cosmos_decisions.create_item(body=body)
        except Exception as exc:
            if "409" not in str(exc) and "Conflict" not in str(exc):
                raise
        return notification.notification_id

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
        zone_dispositions: list[ZoneDisposition],
        assessment_data: dict[str, Any],
        incident_scope_key: str,
        tenant_id: str,
        assumptions: list[str],
    ) -> tuple[str, str, float]:
        """Generate plan summary via LLM or template fallback.

        Returns (summary_text, generation_method, confidence_score).
        """
        hazard_type = assessment_data.get("hazard_type", "bushfire")
        total_pop = sum(z.population_estimate for z in zones)

        phase_data = [phase.model_dump(mode="json") if hasattr(phase, "model_dump") else phase for phase in phases]
        disposition_data = [disposition.model_dump(mode="json") for disposition in zone_dispositions]
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
            "phases": phase_data,
            "zone_dispositions": disposition_data,
            "hazard_severity": assessment_data.get("severity_level", "high"),
            "time_horizon": assessment_data.get("time_horizon", "unknown"),
            "routing_mode": assessment_data.get(
                "routing_mode",
                RoutingMode.hazard_constrained_degraded.value,
            ),
            "hazard_routing_data_gaps": assessment_data.get(
                "hazard_routing_data_gaps",
                [],
            ),
            "excluded_roads": assessment_data.get("excluded_roads", []),
            "excluded_destinations": assessment_data.get(
                "excluded_destinations",
                [],
            ),
            "zero_route_zones": assessment_data.get("zero_route_zones", []),
            "unresolved_destination_demands": assessment_data.get(
                "unresolved_destination_demands",
                [],
            ),
            "road_data_status": assessment_data.get(
                "road_data_status",
                "fresh",
            ),
            "population_data_status": assessment_data.get(
                "population_data_status",
                "unavailable",
            ),
            "facility_data_status": assessment_data.get(
                "facility_data_status",
                "unavailable",
            ),
            "immediate_human_review_required": bool(assessment_data.get("immediate_human_review_required")),
            "urgent_assumptions": self._summary_assumption_warnings(assumptions),
        }
        provisional_data = {
            **plan_data,
            "confidence_score": handoff.confidence,
            "confidence_level": confidence_to_level(handoff.confidence).value,
            "generation_method": "template_fallback",
        }
        template_text = generate_plan_summary_template(
            plan_data=provisional_data,
            hazard_type=hazard_type,
            max_length=self._config.max_summary_length,
        )
        generation_method = "template_fallback"
        summary_grounding_result = "deterministic_fallback"
        model_commentary = ""
        content_safety_result = "not_checked"
        content_safety_validation_method = ""
        content_safety_reason = ""
        content_safety_reference = ""
        model_deployment_id = ""
        requires_human_review = self._llm_generate_fn is None
        confidence_score = handoff.confidence
        confidence_adjustments: list[ConfidenceAdjustment] = []

        def reduce_confidence(reason: str) -> None:
            nonlocal confidence_score
            if any(item.reason == reason for item in confidence_adjustments):
                return
            factor = self._config.fallback_confidence_reduction
            confidence_score = max(
                0.0,
                min(1.0, confidence_score * factor),
            )
            confidence_adjustments.append(ConfidenceAdjustment(reason=reason, factor=factor))

        if self._llm_generate_fn is not None:
            try:
                fact_manifest = json.dumps(
                    plan_data,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                )
                with tel.start_span("evacuation.llm_call"):
                    response = self._llm_generate_fn(
                        purpose="reasoning",
                        prompt=(
                            "Review the validated evacuation fact manifest without "
                            "changing routes, dispositions, deadlines, exclusions, "
                            "transport, or confidence. Return one short, non-directive "
                            "commander-review comment with no new numbers or safety "
                            f"claims. Incident: {handoff.incident_id}. FACTS: "
                            f"{fact_manifest}"
                        ),
                        template_text=template_text,
                        correlation_id=handoff.handoff_id,
                        max_output_tokens=400,
                        timeout_seconds=10.0,
                    )
                raw_text = str(response.get("text", "")).strip()
                raw_method = str(response.get("generation_method", "template_fallback"))
                content_safety_result = str(response.get("content_safety_result", "not_checked"))
                content_safety_validation_method = str(response.get("content_safety_validation_method", "") or "")
                content_safety_reason = str(response.get("content_safety_reason", "") or "")
                content_safety_reference = str(response.get("content_safety_reference", "") or "")
                model_deployment_id = str(response.get("model_deployment_id", "") or "")
                requires_human_review = bool(response.get("requires_human_review", False))
                with tel.start_span("evacuation.content_safety_check"):
                    if raw_method == "safety_fallback" or content_safety_result not in {"passed", "not_checked"}:
                        generation_method = "safety_fallback"
                        summary_grounding_result = "safety_fallback"
                        requires_human_review = True
                    elif raw_method == "llm" and self._model_commentary_is_grounded(raw_text):
                        generation_method = "ai_assisted"
                        summary_grounding_result = "grounded"
                        model_commentary = raw_text
                    else:
                        generation_method = "template_fallback"
                        summary_grounding_result = "empty_output" if not raw_text else "ungrounded_output"
                        requires_human_review = True

                if content_safety_result not in ("passed", "not_checked"):
                    tel.content_safety_failures.add(1)
                    self._write_audit(
                        handoff_id=handoff.handoff_id,
                        incident_id=handoff.incident_id,
                        decision_type=DecisionType.content_safety_failure,
                        rationale=(
                            "Content safety rejected model summary; deterministic "
                            f"fallback persisted. result={content_safety_result}; "
                            f"method={content_safety_validation_method or 'unknown'}; "
                            f"reason={content_safety_reason or 'unknown'}"
                        ),
                        duration_ms=0,
                        incident_scope_key=incident_scope_key,
                        tenant_id=tenant_id,
                        generation_method="safety_fallback",
                        immediate_human_review_required=True,
                        summary_grounding_result=summary_grounding_result,
                        content_safety_result=content_safety_result,
                        content_safety_validation_method=(content_safety_validation_method),
                        content_safety_reason=content_safety_reason,
                        content_safety_reference=content_safety_reference,
                    )
            except Exception as exc:
                logger.warning("LLM plan summary generation failed: %s", exc)
                generation_method = "template_fallback"
                summary_grounding_result = "generation_exception"
                requires_human_review = True

        # Apply confidence reduction for template fallback
        if generation_method in ("template_fallback", "safety_fallback"):
            reduce_confidence(f"generation_{generation_method}")
        if any(
            assumption.startswith("TIME DEFICIT:")
            or "DESTINATION DEFICIT" in assumption
            or "no viable evacuation routes" in assumption.lower()
            or "no road-network origin" in assumption.lower()
            for assumption in assumptions
        ):
            reduce_confidence("operational_deficit")
        if assessment_data.get("routing_mode") == RoutingMode.hazard_constrained_degraded.value:
            reduce_confidence("hazard_routing_data_degraded")
        if assessment_data.get("road_data_status") not in (None, "fresh"):
            reduce_confidence("road_data_degraded")
        if assessment_data.get("population_data_status") not in (None, "fresh"):
            reduce_confidence("population_data_degraded")
        if assessment_data.get("facility_data_status") not in (None, "fresh"):
            reduce_confidence("facility_data_degraded")
        if confidence_to_level(confidence_score).value == "low":
            requires_human_review = True
        if requires_human_review:
            assessment_data["immediate_human_review_required"] = True
        assessment_data["confidence_adjustments"] = [item.model_dump(mode="json") for item in confidence_adjustments]
        assessment_data.update(
            {
                "summary_grounding_result": summary_grounding_result,
                "content_safety_result": content_safety_result,
                "content_safety_validation_method": (content_safety_validation_method),
                "content_safety_reason": content_safety_reason,
                "content_safety_reference": content_safety_reference,
                "model_deployment_id": model_deployment_id,
            }
        )
        if assessment_data.get("road_data_status") in {"stale", "unavailable"}:
            assessment_data["generic_guidance"] = generate_generic_evacuation_guidance(hazard_type)
        if confidence_adjustments:
            self._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.degradation_detected,
                rationale=(
                    "Data/model degradation adjusted confidence: "
                    + ", ".join(item.reason for item in confidence_adjustments)
                ),
                duration_ms=0,
                incident_scope_key=incident_scope_key,
                tenant_id=tenant_id,
                confidence_raw=handoff.confidence,
                confidence_adjusted=confidence_score,
                generation_method=generation_method,
                data_quality_gaps=assessment_data.get("data_quality_gaps", []),
                confidence_adjustments=confidence_adjustments,
                immediate_human_review_required=bool(assessment_data.get("immediate_human_review_required")),
                summary_grounding_result=summary_grounding_result,
                content_safety_result=content_safety_result,
                content_safety_validation_method=(content_safety_validation_method),
                content_safety_reason=content_safety_reason,
                content_safety_reference=content_safety_reference,
            )
        final_plan_data = {
            **plan_data,
            "confidence_score": confidence_score,
            "confidence_level": confidence_to_level(confidence_score).value,
            "generation_method": generation_method,
            "immediate_human_review_required": bool(assessment_data.get("immediate_human_review_required")),
        }
        commentary_block = f"\n\nMODEL COMMENTARY: {model_commentary}" if model_commentary else ""
        template_limit = max(
            200,
            self._config.max_summary_length - len(commentary_block),
        )
        with tel.start_span("evacuation.template_render"):
            summary = generate_plan_summary_template(
                plan_data=final_plan_data,
                hazard_type=hazard_type,
                max_length=template_limit,
            )
        if commentary_block:
            confidence_marker = "\n\nCONFIDENCE:"
            marker_index = summary.rfind(confidence_marker)
            if marker_index >= 0:
                summary = summary[:marker_index] + commentary_block + summary[marker_index:]
            else:
                summary += commentary_block
        summary = summary[: self._config.max_summary_length]
        return summary, generation_method, confidence_score

    @staticmethod
    def _model_commentary_is_grounded(text: str) -> bool:
        normalized = " ".join(text.lower().split())
        return normalized in {
            "operational facts reviewed; retain commander approval controls.",
            "commander review should retain validated facts.",
            "commander approval should follow validated facts.",
        }

    @staticmethod
    def _summary_assumption_warnings(
        assumptions: list[str],
    ) -> list[str]:
        prefixes = (
            "URGENT",
            "EMERGENCY:",
            "ROAD DATA DEGRADED:",
            "POPULATION DATA DEGRADED:",
            "FACILITY DATA DEGRADED:",
            "DESTINATION DEFICIT:",
            "TIME DEFICIT:",
        )
        grouped: dict[str, list[str]] = {}
        for assumption in assumptions:
            prefix = next(
                (candidate for candidate in prefixes if assumption.startswith(candidate)),
                None,
            )
            if prefix is not None:
                grouped.setdefault(prefix, []).append(assumption)
        return [
            (
                f"{items[0][:120]} ({len(items)} urgent warning(s))"
                if prefix == "URGENT"
                else (f"{prefix} {len(items)} structured warning(s); first: {items[0][len(prefix) :].strip()[:90]}")
            )
            for prefix in prefixes
            if (items := grouped.get(prefix))
        ]

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
        zone_dispositions: list[ZoneDisposition],
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
        destination_allocations = [
            DestinationAllocation.model_validate(allocation)
            for allocation in assessment_data.get("destination_allocations", [])
        ]
        unresolved_destination_demands = [
            UnresolvedDestinationDemand.model_validate(demand)
            for demand in assessment_data.get(
                "unresolved_destination_demands",
                [],
            )
        ]
        if not destination_allocations and not unresolved_destination_demands:
            unresolved_destination_demands = [
                UnresolvedDestinationDemand(
                    zone_number=zone.zone_number,
                    population=zone.population_estimate,
                    vulnerable_population=zone.vulnerable_population,
                    reason="no_reachable_destination",
                    details="No route-backed destination allocation was produced",
                )
                for zone in zones
                if zone.population_estimate > 0
            ]

        # Assign version via OCC
        try:
            with tel.start_span("evacuation.assign_version"):
                version = run_async(
                    self._version_counter.assign_version(
                        incident_id=incident_id,
                        incident_scope_key=incident_scope_key,
                    )
                )
        except VersionReservationError as exc:
            self._release_handoff_claim(
                handoff,
                incident_scope_key,
                "Version reservation unavailable",
            )
            raise TransientHandoffDependencyError("Plan version reservation is temporarily unavailable") from exc
        plan_id = self._version_counter.format_plan_id(incident_id, version)
        try:
            self._dedup.assign_plan_id(
                tenant_id,
                incident_id,
                handoff.handoff_id,
                incident_scope_key,
                plan_id,
            )
        except (HandoffClaimInProgressError, HandoffClaimStoreError) as exc:
            raise TransientHandoffDependencyError("Failed to link reserved plan to handoff claim") from exc

        # Build assembly areas from road network
        assembly_areas: list[AssemblyArea] = []
        if self._road_network.is_loaded and assessment_data.get(
            "road_data_usable",
            True,
        ):
            for aa_config in self._road_network.get_assembly_areas():
                area_allocations = [
                    allocation
                    for allocation in destination_allocations
                    if allocation.assembly_area_id == aa_config.assembly_area_id
                ]
                assigned_population = sum(allocation.assigned_population for allocation in area_allocations)
                assembly_areas.append(
                    AssemblyArea(
                        assembly_area_id=aa_config.assembly_area_id,
                        name=aa_config.name,
                        capacity=aa_config.capacity_persons,
                        current_occupancy=aa_config.current_occupancy_persons,
                        residual_capacity=(
                            None
                            if aa_config.current_occupancy_persons is None
                            else aa_config.capacity_persons - aa_config.current_occupancy_persons - assigned_population
                        ),
                        assigned_population=assigned_population,
                        assigned_vulnerable_population=sum(
                            allocation.assigned_vulnerable_population for allocation in area_allocations
                        ),
                        assigned_zones=sorted({allocation.zone_number for allocation in area_allocations}),
                        latitude=aa_config.coordinates.get("lat", 0.0),
                        longitude=aa_config.coordinates.get("lng", 0.0),
                        accessible=("wheelchair_accessible" in aa_config.accessibility_features),
                        shelter_available=bool(aa_config.shelter_types),
                        accessibility_features=aa_config.accessibility_features,
                        shelter_types=aa_config.shelter_types,
                    )
                )

        # Build evacuation routes from dicts
        from evacuation.models import EvacuationRoute

        route_models = [EvacuationRoute.model_validate(r) for r in routes]
        route_zone_numbers = {int(route.zone_id) for route in route_models if route.zone_id.isdigit()}
        for zone in zones:
            if zone.zone_number not in route_zone_numbers and zone.unallocated_route_population == 0:
                zone.unallocated_route_population = zone.population_estimate

        # Build transport requirement models
        from evacuation.models import TransportRequirement

        transport_models = [TransportRequirement.model_validate(t) for t in transport_reqs]
        transport_coordination = TransportCoordinationResult.model_validate(
            assessment_data.get(
                "transport_coordination",
                {
                    "status": TransportCoordinationStatus.unavailable.value,
                    "requirements": transport_reqs,
                },
            )
        )

        # Build evacuation phases
        from evacuation.models import EvacuationPhase

        phase_models = [p if isinstance(p, EvacuationPhase) else EvacuationPhase.model_validate(p) for p in phases]

        # Mobilisation time
        mobilisation_min = self._config.mobilisation_time_for(hazard_type)

        estimated_completion = self._timeline_estimator.plan_completion_minutes(phase_models)
        shelter_zone_ids = [
            str(disposition.zone_number)
            for disposition in zone_dispositions
            if disposition.disposition == ZoneDispositionType.shelter_in_place
        ]

        # Build traceability
        assessment_id = assessment_data.get(
            "hazard_assessment_id",
            assessment_data.get("assessmentId", ""),
        )
        hazard_sources = [
            HazardSourceSnapshot.model_validate(source) for source in assessment_data.get("hazard_sources", [])
        ]
        assessment_ids = [source.assessment_id for source in hazard_sources]
        input_signal_ids = sorted({signal_id for source in hazard_sources for signal_id in source.input_signal_ids})
        assembly_area_configs = self._road_network.get_assembly_areas() if self._road_network.is_loaded else []
        population_record_ids = self._snapshot_record_ids(
            self._population_data,
            ("population_area_id", "area_id", "id"),
        )
        facility_record_ids = self._snapshot_record_ids(
            self._facility_data,
            ("facility_id", "id"),
        )
        assembly_area_record_ids = self._snapshot_record_ids(
            assembly_area_configs,
            ("assembly_area_id", "id"),
        )
        traceability = Traceability(
            source_handoff_id=handoff.handoff_id,
            risk_assessment_id=str(assessment_id) if assessment_id else None,
            risk_assessment_ids=assessment_ids,
            recommendation_id=str(assessment_data.get("recommendation_id") or ""),
            input_signal_ids=input_signal_ids,
            input_data_versions={
                "road_network": (self._road_network.get_version() if self._road_network.is_loaded else "n/a"),
                "population": self._semantic_collection_version(self._population_data),
                "facilities": self._semantic_collection_version(self._facility_data),
                "assembly_areas": self._semantic_collection_version(
                    self._road_network.get_assembly_areas() if self._road_network.is_loaded else []
                ),
                "config": self._config.compute_config_hash()[:16],
            },
            model_id=None,
            prompt_template_version="1.0",
            generation_method=generation_method,
        )

        # Build data snapshot
        data_snapshot = DataSnapshot(
            road_network_version=str(
                assessment_data.get("effective_road_network_version")
                or (self._road_network.get_version() if self._road_network.is_loaded else "")
            ),
            population_data_version=self._semantic_collection_version(self._population_data),
            facility_data_version=self._semantic_collection_version(self._facility_data),
            assembly_area_data_version=self._semantic_collection_version(assembly_area_configs),
            population_data_available=self._population_data_available,
            facility_data_available=self._facility_data_available,
            assembly_area_data_available=self._road_network.is_loaded,
            population_record_ids=population_record_ids,
            facility_record_ids=facility_record_ids,
            assembly_area_record_ids=assembly_area_record_ids,
            population_record_count=len(self._population_data),
            facility_record_count=len(self._facility_data),
            assembly_area_record_count=len(assembly_area_configs),
            road_data_status=str(assessment_data.get("road_data_status") or "fresh"),
            road_source_updated_at=assessment_data.get("road_source_updated_at"),
            road_source_age_hours=assessment_data.get("road_source_age_hours"),
            population_data_status=str(assessment_data.get("population_data_status") or "unavailable"),
            population_source_updated_at=assessment_data.get("population_source_updated_at"),
            population_source_age_hours=assessment_data.get("population_source_age_hours"),
            facility_data_status=str(assessment_data.get("facility_data_status") or "unavailable"),
            facility_source_updated_at=assessment_data.get("facility_source_updated_at"),
            facility_source_age_hours=assessment_data.get("facility_source_age_hours"),
            road_refresh_failure_reason=str(assessment_data.get("road_refresh_failure_reason") or ""),
            hazard_data_timestamp=max(
                (source.generated_at for source in hazard_sources),
                default=datetime.now(UTC),
            ),
            hazard_assessment_ids=assessment_ids,
            hazard_geometry_algorithm="per-hazard-aeqd-level-union-v1",
        )

        # Build hazard summary
        hazard_summary = HazardSummary(
            hazard_type=hazard_type,
            hazard_types=sorted({source.hazard_type for source in hazard_sources}),
            severity_level=max(
                (source.severity_level for source in hazard_sources),
                key={
                    "low": 0,
                    "moderate": 1,
                    "high": 2,
                    "critical": 3,
                }.get,
                default=assessment_data.get("severity_level", ""),
            ),
            time_horizon=str(assessment_data.get("time_horizon") or ""),
            affected_area_km2=assessment_data.get("affected_area_km2", 0.0),
            direction_of_travel=assessment_data.get("direction_of_travel", ""),
            estimated_arrival_minutes=assessment_data.get("estimated_arrival_minutes"),
            source_assessment_id=str(assessment_id) if assessment_id else None,
            affected_area=assessment_data.get("affected_area", {}),
            sources=hazard_sources,
            population_estimate=assessment_data.get("population_estimate"),
        )

        total_pop = sum(z.population_estimate for z in zones)
        vulnerable_pop = sum(z.vulnerable_population for z in zones)
        phase_population = sum(phase.population_moved + phase.population_remaining for phase in phase_models)
        origin_node_ids = [node_id for zone in zones for node_id in zone.origin_node_ids]
        allocated_population = sum(route.allocated_population for route in route_models)
        unallocated_population = sum(zone.unallocated_route_population for zone in zones)
        destination_population = sum(allocation.assigned_population for allocation in destination_allocations)
        unresolved_destination_population = sum(demand.population for demand in unresolved_destination_demands)
        allocation_by_zone_destination = {
            (allocation.zone_number, allocation.assembly_area_id): (allocation.assigned_population)
            for allocation in destination_allocations
        }
        route_population_by_zone_destination: dict[tuple[int, str], int] = {}
        for route in route_models:
            if route.allocated_population <= 0:
                continue
            key = (int(route.zone_id), route.assembly_area_id)
            route_population_by_zone_destination[key] = (
                route_population_by_zone_destination.get(key, 0) + route.allocated_population
            )
        resolved_transport_destinations = {
            (
                requirement.origin_zone,
                requirement.destination_assembly_area_id,
            )
            for requirement in transport_models
            if requirement.destination_resolved
        }
        resolved_transport_routes = {
            requirement.destination_route_id for requirement in transport_models if requirement.destination_resolved
        }
        routed_destinations = {
            (int(route.zone_id), route.assembly_area_id) for route in route_models if route.allocated_population > 0
        }
        disposition_population = sum(disposition.affected_population for disposition in zone_dispositions)
        disposition_zones = [disposition.zone_number for disposition in zone_dispositions]
        expected_zones = [zone.zone_number for zone in zones]
        if (
            disposition_population != total_pop
            or phase_population != total_pop
            or vulnerable_pop > total_pop
            or allocated_population + unallocated_population != total_pop
            or destination_population + unresolved_destination_population != total_pop
            or allocation_by_zone_destination != route_population_by_zone_destination
            or not resolved_transport_destinations.issubset(routed_destinations)
            or not resolved_transport_routes.issubset({route.route_id for route in route_models})
            or len(origin_node_ids) != len(set(origin_node_ids))
            or len(set(disposition_zones)) != len(disposition_zones)
            or sorted(disposition_zones) != sorted(expected_zones)
        ):
            raise RuntimeError("Zone population and origin reconciliation failed")

        source_expiries = [source.valid_until for source in hazard_sources if source.valid_until is not None]
        plan_valid_until = (
            min(source_expiries)
            if source_expiries
            else (datetime.now(UTC) + timedelta(hours=self._config.plan_expiry_hours))
        )
        previous_document: dict[str, Any] | None = None
        source_plan_id: str | None = None
        change_summary: str | None = None
        if version > 1:
            source_plan_id = self._version_counter.format_plan_id(
                incident_id,
                version - 1,
            )
            change_summary = (
                f"Regenerated from {source_plan_id} using handoff {handoff.handoff_id} and current input snapshots"
            )
            if self._cosmos_plans is not None:
                try:
                    previous_document = self._cosmos_plans.read_item(
                        item=source_plan_id,
                        partition_key=incident_scope_key,
                    )
                except Exception as exc:
                    if self._persistence_status(exc) != 404:
                        raise TransientHandoffDependencyError("Failed to resolve previous plan version") from exc
        plan = EvacuationPlan(
            plan_id=plan_id,
            incident_id=incident_id,
            version=version,
            status=PlanStatus.proposed,
            confidence_score=confidence_score,
            hazard_summary=hazard_summary,
            affected_area=assessment_data.get("affected_area", {}),
            routing_mode=assessment_data.get(
                "routing_mode",
                RoutingMode.hazard_constrained_degraded.value,
            ),
            hazard_routing_data_gaps=assessment_data.get(
                "hazard_routing_data_gaps",
                [],
            ),
            excluded_destinations=[
                DestinationExclusion.model_validate(exclusion)
                for exclusion in assessment_data.get(
                    "excluded_destinations",
                    [],
                )
            ],
            excluded_roads=[ExcludedRoad.model_validate(road) for road in assessment_data.get("excluded_roads", [])],
            unavailable_roads_by_reason=assessment_data.get(
                "unavailable_roads_by_reason",
                {},
            ),
            zero_route_zones=assessment_data.get("zero_route_zones", []),
            corridor_loads=[CorridorLoad.model_validate(load) for load in assessment_data.get("corridor_loads", [])],
            zones=zones,
            routes=route_models,
            assembly_areas=assembly_areas,
            destination_allocations=destination_allocations,
            unresolved_destination_demands=unresolved_destination_demands,
            phases=phase_models,
            transport_requirements=transport_models,
            transport_coordination_status=transport_coordination.status,
            transport_exclusions=[
                TransportGroupExclusion.model_validate(exclusion) for exclusion in transport_coordination.exclusions
            ],
            identified_transport_population_by_zone=(transport_coordination.identified_population_by_zone),
            uncovered_vulnerable_population_by_zone=(transport_coordination.uncovered_vulnerable_population_by_zone),
            population_estimate=total_pop,
            total_population=total_pop,
            estimated_completion_minutes=estimated_completion,
            mobilisation_time_minutes=mobilisation_min,
            shelter_in_place_zones=shelter_zone_ids,
            zone_dispositions=zone_dispositions,
            traceability=traceability,
            data_snapshot=data_snapshot,
            assumptions=list(assumptions),
            data_quality_gaps=sorted(set(assessment_data.get("data_quality_gaps", []))),
            confidence_adjustments=[
                ConfidenceAdjustment.model_validate(item) for item in assessment_data.get("confidence_adjustments", [])
            ],
            immediate_human_review_required=bool(assessment_data.get("immediate_human_review_required")),
            generic_guidance=str(assessment_data.get("generic_guidance") or ""),
            generation_method=generation_method,
            summary_grounding_result=str(assessment_data.get("summary_grounding_result") or "deterministic"),
            content_safety_result=str(assessment_data.get("content_safety_result") or "not_checked"),
            content_safety_validation_method=str(assessment_data.get("content_safety_validation_method") or ""),
            content_safety_reason=str(assessment_data.get("content_safety_reason") or ""),
            content_safety_reference=str(assessment_data.get("content_safety_reference") or ""),
            model_deployment_id=str(assessment_data.get("model_deployment_id") or ""),
            configuration_version=self._config.compute_config_hash()[:16],
            summary=summary,
            source_plan_id=source_plan_id,
            change_summary=change_summary,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
            simulation=tenant_id != "live",
            valid_until=plan_valid_until,
        )

        with tel.start_span("evacuation.persist_plan"):
            self._persist_plan_document(
                handoff=handoff,
                plan=plan,
                previous_document=previous_document,
                source_plan_id=source_plan_id,
                incident_scope_key=incident_scope_key,
            )

        if self._cosmos_plans is not None and hasattr(self._cosmos_plans, "query_items"):
            self._active_plan_count = self._plan_repository.total_active_count(tenant_id)
        else:
            self._active_plan_count += 1

        duration_ms = (time.monotonic() - t0) * 1000
        expected_audit_steps = self._expected_success_audit_steps(plan)
        expected_audit_counts = Counter(expected_audit_steps)
        observed_required_steps: list[str] = []
        observed_counts: Counter[str] = Counter()
        for observed_record in self._audit_observations.get(
            handoff.handoff_id,
            [],
        ):
            step = observed_record.decision_type.value
            if observed_counts[step] < expected_audit_counts[step]:
                observed_required_steps.append(step)
                observed_counts[step] += 1
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
            zone_dispositions=zone_dispositions,
            generation_method=generation_method,
            immediate_human_review_required=(plan.immediate_human_review_required),
            summary_grounding_result=plan.summary_grounding_result,
            content_safety_result=plan.content_safety_result,
            content_safety_validation_method=(plan.content_safety_validation_method),
            content_safety_reason=plan.content_safety_reason,
            content_safety_reference=plan.content_safety_reference,
            assessment_id=str(assessment_id) if assessment_id else None,
            recommendation_id=str(assessment_data.get("recommendation_id") or ""),
            input_signal_ids=input_signal_ids,
            routes_count=len(route_models),
            transport_requests_count=len(transport_models),
            constraints_applied=sorted(
                [
                    *(f"road_exclusion:{road.edge_id}" for road in plan.excluded_roads),
                    *(f"data_gap:{gap}" for gap in plan.data_quality_gaps),
                ]
            ),
            expected_steps=expected_audit_steps,
            observed_steps=[
                *observed_required_steps,
                DecisionType.plan_generated.value,
            ],
            stage_durations_ms=self._observed_stage_durations(
                handoff.handoff_id,
                {
                    DecisionType.plan_generated.value: duration_ms,
                },
            ),
        )
        return plan

    def _persist_plan_document(
        self,
        *,
        handoff: AgentHandoffEvent,
        plan: EvacuationPlan,
        previous_document: dict[str, Any] | None,
        source_plan_id: str | None,
        incident_scope_key: str,
    ) -> None:
        if self._cosmos_plans is None:
            return
        plan_id = plan.plan_id
        write_error: Exception | None = None
        try:
            document = plan.model_dump(mode="json")
            document["id"] = plan_id
            if previous_document is not None and previous_document.get("status") == PlanStatus.proposed.value:
                previous_etag = str(previous_document.get("_etag") or "")
                if not previous_etag:
                    raise RuntimeError("Previous proposal has no concurrency token")
                self._cosmos_plans.execute_item_batch(
                    batch_operations=[
                        (
                            "replace",
                            (
                                source_plan_id,
                                self._superseded_source_body(
                                    previous_document,
                                    plan_id,
                                    datetime.now(UTC),
                                ),
                            ),
                            {"if_match_etag": previous_etag},
                        ),
                        ("create", (document,)),
                    ],
                    partition_key=incident_scope_key,
                )
            else:
                self._cosmos_plans.create_item(body=document)
        except Exception as exc:
            write_error = exc
        try:
            persisted_document = self._cosmos_plans.read_item(
                item=plan_id,
                partition_key=incident_scope_key,
            )
            persisted_plan = EvacuationPlan.model_validate(persisted_document)
            if (
                persisted_plan.plan_id != plan_id
                or persisted_plan.version != plan.version
                or persisted_plan.incident_id != plan.incident_id
                or persisted_plan.incident_scope_key != incident_scope_key
                or persisted_plan.tenant_id != plan.tenant_id
                or persisted_plan.model_dump(mode="json") != plan.model_dump(mode="json")
            ):
                raise ValueError("Persisted plan identity does not match reservation")
        except Exception as read_error:
            uncertain = self._persistence_status(read_error) != 404
            reason = (
                f"write_error={write_error}; readback_error={read_error}"
                if write_error is not None
                else f"readback_error={read_error}"
            )
            try:
                self._version_counter.record_gap(
                    plan.incident_id,
                    incident_scope_key,
                    plan.version,
                    uncertain=uncertain,
                    reason=reason,
                )
            except VersionReservationError:
                logger.exception(
                    "Failed to record version %d persistence gap",
                    plan.version,
                )
            self._release_handoff_claim(
                handoff,
                incident_scope_key,
                f"Plan persistence unconfirmed for {plan_id}",
            )
            raise TransientHandoffDependencyError(f"Plan persistence unconfirmed for {plan_id}") from read_error
        logger.info(
            "Plan persistence verified: %s%s",
            plan_id,
            " after lost write response" if write_error is not None else "",
        )

    @staticmethod
    def _persistence_status(exc: Exception) -> int | None:
        status = getattr(exc, "status_code", None) or getattr(exc, "http_status", None)
        if isinstance(status, int):
            return status
        text = f"{type(exc).__name__} {exc}"
        for candidate in (404, 409, 412, 429, 500, 502, 503, 504):
            if str(candidate) in text:
                return candidate
        if "NotFound" in text:
            return 404
        return None

    @staticmethod
    def _superseded_source_body(
        source: dict[str, Any],
        new_plan_id: str,
        now: datetime,
    ) -> dict[str, Any]:
        body = {key: value for key, value in source.items() if not key.startswith("_")}
        body.update(
            {
                "status": PlanStatus.superseded.value,
                "superseded_by": new_plan_id,
                "superseded_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        )
        return body

    def _release_handoff_claim(
        self,
        handoff: AgentHandoffEvent,
        incident_scope_key: str,
        reason: str,
    ) -> None:
        try:
            self._dedup.release(
                handoff.handoff_id,
                tenant_id=handoff.tenant_id,
                incident_id=handoff.incident_id,
                incident_scope_key=incident_scope_key,
                reason=reason,
            )
        except HandoffClaimStoreError:
            logger.exception(
                "Failed to release durable handoff claim %s",
                handoff.handoff_id,
            )

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

        self._reconcile_audit_steps(
            handoff.handoff_id,
            self._expected_success_audit_steps(plan),
            plan=plan,
        )

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
            tel.degradation_events.add(
                1,
                attributes={
                    "incident_id": handoff.incident_id,
                    "tenant_id": tenant_id,
                    "component": "cosmos",
                },
            )
            tier_map = {"buffering": 2, "degraded": 3}
            tel.emit_degradation_event("cosmos", tier_map[audit_status])
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
                version=plan.version,
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
        zone_dispositions: list[ZoneDisposition] | None = None,
        data_quality_gaps: list[str] | None = None,
        confidence_adjustments: list[ConfidenceAdjustment] | None = None,
        immediate_human_review_required: bool = False,
        summary_grounding_result: str = "",
        content_safety_result: str = "",
        content_safety_validation_method: str = "",
        content_safety_reason: str = "",
        content_safety_reference: str = "",
        assessment_id: str | None = None,
        recommendation_id: str | None = None,
        input_signal_ids: list[str] | None = None,
        routes_count: int | None = None,
        transport_requests_count: int | None = None,
        constraints_applied: list[str] | None = None,
        replanning_triggers: list[str] | None = None,
        expected_steps: list[str] | None = None,
        observed_steps: list[str] | None = None,
        stage_durations_ms: dict[str, float] | None = None,
        completeness_warnings: list[str] | None = None,
        principal_id: str | None = None,
    ) -> AuditWriteReceipt | None:
        """Create and write an EvacuationDecisionRecord."""
        record = EvacuationDecisionRecord(
            handoff_id=handoff_id,
            operation_id=handoff_id,
            plan_id=plan_id,
            incident_id=incident_id,
            assessment_id=assessment_id,
            recommendation_id=recommendation_id,
            input_signal_ids=input_signal_ids or [],
            hazard_type=hazard_type,
            zone_ids=zone_ids or [],
            route_ids=route_ids or [],
            population_affected=population_affected,
            routes_count=routes_count,
            transport_requests_count=transport_requests_count,
            constraints_applied=constraints_applied or [],
            replanning_triggers=replanning_triggers or [],
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
            zone_dispositions=zone_dispositions or [],
            data_quality_gaps=data_quality_gaps or [],
            confidence_adjustments=confidence_adjustments or [],
            immediate_human_review_required=(immediate_human_review_required),
            summary_grounding_result=summary_grounding_result,
            content_safety_result=content_safety_result,
            content_safety_validation_method=content_safety_validation_method,
            content_safety_reason=content_safety_reason,
            content_safety_reference=content_safety_reference,
            expected_steps=expected_steps or [],
            observed_steps=observed_steps or [],
            stage_durations_ms=stage_durations_ms or {},
            completeness_warnings=completeness_warnings or [],
            principal_id=principal_id,
        )
        receipt = self._audit_writer.write(record)
        if receipt is not None and receipt.accepted:
            self._audit_observations.setdefault(handoff_id, []).append(record)
        return receipt

    def _reconcile_terminal_audit(self, handoff_id: str) -> None:
        terminal = [
            record.decision_type.value
            for record in self._audit_observations.get(handoff_id, [])
            if record.decision_type
            in {
                DecisionType.handoff_rejected,
                DecisionType.duplicate_discarded,
            }
        ]
        if len(terminal) != 1:
            raise RuntimeError(
                f"Audit completeness failure: expected one terminal intake decision; observed={terminal or 'none'}"
            )

    @staticmethod
    def _expected_success_audit_steps(plan: EvacuationPlan) -> list[str]:
        steps = [
            DecisionType.handoff_received.value,
            DecisionType.assessment_retrieved.value,
            DecisionType.zones_computed.value,
            DecisionType.road_network_loaded.value,
            DecisionType.routes_computed.value,
            DecisionType.transport_coordinated.value,
        ]
        steps.extend(
            (
                DecisionType.shelter_in_place_recommended.value
                if disposition.disposition == ZoneDispositionType.shelter_in_place
                else DecisionType.timeline_estimated.value
            )
            for disposition in plan.zone_dispositions
        )
        steps.append(DecisionType.plan_generated.value)
        return steps

    def _observed_stage_durations(
        self,
        handoff_id: str,
        additions: dict[str, float] | None = None,
    ) -> dict[str, float]:
        durations: dict[str, float] = {}
        for record in self._audit_observations.get(handoff_id, []):
            key = record.decision_type.value
            durations[key] = durations.get(key, 0.0) + record.processing_duration_ms
        for key, duration in (additions or {}).items():
            durations[key] = durations.get(key, 0.0) + duration
        return durations

    def _reconcile_audit_steps(
        self,
        handoff_id: str,
        expected_steps: list[str],
        *,
        plan: EvacuationPlan | None = None,
    ) -> None:
        observed_steps = [record.decision_type.value for record in self._audit_observations.get(handoff_id, [])]
        expected_counts = Counter(expected_steps)
        observed_counts = Counter(step for step in observed_steps if step in expected_counts)
        missing = list((expected_counts - observed_counts).elements())
        duplicates = list((observed_counts - expected_counts).elements())
        warnings = [
            *(f"missing:{step}" for step in missing),
            *(f"duplicate:{step}" for step in duplicates),
        ]
        if not warnings:
            return
        self._audit_reconciliation_failures[handoff_id] = warnings
        if plan is not None:
            self._write_audit(
                handoff_id=handoff_id,
                incident_id=plan.incident_id,
                decision_type=DecisionType.degradation_detected,
                rationale=("Audit completeness failure: " + ", ".join(warnings)),
                duration_ms=0,
                incident_scope_key=plan.incident_scope_key,
                tenant_id=plan.tenant_id,
                plan_id=plan.plan_id,
                version=plan.version,
                completeness_warnings=warnings,
                expected_steps=expected_steps,
                observed_steps=observed_steps,
            )
        raise RuntimeError("Audit completeness failure: " + ", ".join(warnings))

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

    def _assign_zone_origin_nodes(
        self,
        zones: list[EvacuationZone],
        road_network: RoadNetworkLoader | None = None,
    ) -> dict[int, list[str]]:
        """Assign every physical road node to at most one priority zone."""
        network = road_network or self._road_network
        assignments = {zone.zone_number: [] for zone in zones}
        if not network.is_loaded:
            return assignments

        zone_polygons = []
        for zone in sorted(zones, key=lambda candidate: candidate.zone_number):
            boundary = zone.membership_boundary or zone.boundary
            if not boundary:
                continue
            try:
                polygon = shape(boundary)
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                if not polygon.is_empty:
                    zone_polygons.append((zone.zone_number, polygon))
            except (TypeError, ValueError):
                continue

        for node in sorted(network.get_all_nodes(), key=lambda candidate: candidate.id):
            coordinates = node.coordinates
            if not coordinates:
                continue
            point = Point(coordinates.get("lng", 0), coordinates.get("lat", 0))
            for zone_number, polygon in zone_polygons:
                if polygon.covers(point):
                    assignments[zone_number].append(node.id)
                    break
        return assignments

    def _find_zone_origin_nodes(self, zone: EvacuationZone) -> list[str]:
        """Find road nodes owned by one zone using its membership geometry."""
        return self._assign_zone_origin_nodes([zone])[zone.zone_number]

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
