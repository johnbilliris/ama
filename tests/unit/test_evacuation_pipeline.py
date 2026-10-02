"""Tests for evacuation.pipeline — end-to-end pipeline with mocks (T024)."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from common.handoffs import AgentHandoffEvent
from evacuation import telemetry as tel
from evacuation.config import EvacuationConfig
from evacuation.models import (
    DecisionType,
    EmergencyNotification,
    EvacuationPlan,
    EvacuationZone,
    OriginCoverageStatus,
    RoutingMode,
    ZoneDispositionType,
)
from evacuation.pipeline import EvacuationProcessingPipeline, TransientHandoffDependencyError
from evacuation.road_network import RoadNetworkLoader
from evacuation.versioning import VersionReservationError
from shapely.geometry import shape

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


def _make_handoff(
    handoff_id="hf-001",
    incident_id="inc-001",
    source_agent="risk_assessment",
    target_agent="evacuation",
    confidence=0.85,
    hazard_type="bushfire",
    assessment_id="assess-001",
    recommendation_id="rec-001",
):
    return AgentHandoffEvent(
        handoff_id=handoff_id,
        incident_id=incident_id,
        source_agent=source_agent,
        target_agent=target_agent,
        scope_key=f"live:{incident_id}",
        confidence=confidence,
        payload={
            "assessmentId": assessment_id,
            "recommendationId": recommendation_id,
            "hazard_type": hazard_type,
            "severity_level": "high",
            "affected_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.75, -16.95],
                        [145.80, -16.95],
                        [145.80, -16.90],
                        [145.75, -16.90],
                        [145.75, -16.95],
                    ]
                ],
            },
            "population_estimate": 5000,
        },
    )


class _Store:
    def __init__(self, documents):
        self.documents = documents

    def read_item(self, item, partition_key):
        document = self.documents[item]
        assert partition_key == document["incident_scope_key"]
        return document

    def query_items(self, query, parameters, partition_key):
        assert "c.incident_id = @incident_id" in query
        values = {parameter["name"]: parameter["value"] for parameter in parameters}
        return [
            document
            for document in self.documents.values()
            if document.get("incident_scope_key") == partition_key
            and document.get("incident_id") == values["@incident_id"]
            and document.get("status") == values["@status"]
        ]


def _recommendation(**overrides):
    document = {
        "recommendation_id": "rec-001",
        "incident_id": "inc-001",
        "type": "evacuation",
        "summary": "Evacuate affected communities",
        "explanation": "The route-risk assessment exceeds the evacuation threshold",
        "required_approval_level": "incident_commander",
        "assessment_id": "assess-001",
        "confidence_score": 0.85,
        "severity_level": "high",
        "incident_scope_key": "live:inc-001",
        "tenant_id": "live",
    }
    document.update(overrides)
    return document


def _assessment(**overrides):
    generated_at = datetime.now(UTC)
    document = {
        "hazard_assessment_id": "assess-001",
        "incident_id": "inc-001",
        "assessment_type": "route_risk",
        "input_signal_ids": ["signal-001"],
        "summary": "Bushfire threatens evacuation corridors",
        "confidence_level": "high",
        "generated_at": generated_at.isoformat(),
        "valid_until": (generated_at + timedelta(hours=4)).isoformat(),
        "status": "active",
        "incident_scope_key": "live:inc-001",
        "tenant_id": "live",
        "hazard_map": {
            "affected_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.75, -16.95],
                        [145.80, -16.95],
                        [145.80, -16.90],
                        [145.75, -16.90],
                        [145.75, -16.95],
                    ]
                ],
            },
            "severity_level": "high",
            "hazard_type": "bushfire",
            "confidence_score": 0.85,
            "time_horizon": "4h",
            "population_estimate": 5000,
        },
    }
    document.update(overrides)
    return document


def _secondary_hazard_assessment():
    assessment = _assessment(
        hazard_assessment_id="assess-002",
        version=2,
        input_signal_ids=["signal-002"],
    )
    assessment["hazard_map"] = {
        "affected_area": {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.69, -16.89],
                    [145.76, -16.89],
                    [145.76, -16.82],
                    [145.69, -16.82],
                    [145.69, -16.89],
                ]
            ],
        },
        "severity_level": "critical",
        "hazard_type": "cyclone",
        "confidence_score": 0.9,
        "time_horizon": "12h",
        "population_estimate": 3000,
    }
    return assessment


def _make_pipeline(
    road_network=None,
    recommendation_store=None,
    assessment_store=None,
    emergency_notification_publisher=None,
    plans_store=None,
    population_data=None,
    facility_data=None,
    reference_data_metadata=None,
    llm_generate_fn=None,
):
    """Create pipeline with minimal mocks (no Cosmos, no LLM)."""
    if road_network is None:
        road_network = RoadNetworkLoader(
            now=lambda: datetime(2026, 4, 16, 1, tzinfo=UTC),
        )
        road_network.load(SAMPLE_FILE)
    return EvacuationProcessingPipeline(
        config=EvacuationConfig(),
        road_network=road_network,
        cosmos_plans_container=plans_store,
        cosmos_decisions_container=None,
        cosmos_assessments_container=assessment_store or _Store({"assess-001": _assessment()}),
        cosmos_recommendations_container=recommendation_store or _Store({"rec-001": _recommendation()}),
        population_data=population_data,
        facility_data=facility_data,
        reference_data_metadata=reference_data_metadata,
        llm_generate_fn=llm_generate_fn,
        emergency_notification_publisher=emergency_notification_publisher,
    )


# ---------------------------------------------------------------------------
# End-to-end pipeline with mocks
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
    def test_suppressed_required_audit_stage_fails_reconciliation(self):
        pipeline = _make_pipeline()
        original_write = pipeline.audit_writer.write

        def suppress_routes(record):
            if record.decision_type == DecisionType.routes_computed:
                return None
            return original_write(record)

        pipeline.audit_writer.write = suppress_routes

        with pytest.raises(RuntimeError, match="routes_computed"):
            pipeline.process_handoff(_make_handoff(handoff_id="hf-suppressed-audit"))
        assert pipeline._audit_reconciliation_failures["hf-suppressed-audit"] == ["missing:routes_computed"]
        warnings = [entry.record for entry in pipeline.audit_writer._buffer if entry.record.completeness_warnings]
        assert warnings[-1].completeness_warnings == ["missing:routes_computed"]

    def test_success_audit_reconciles_exact_steps_and_domain_content(self):
        pipeline = _make_pipeline(
            population_data=[],
            facility_data=[],
            reference_data_metadata={"last_updated": datetime.now(UTC).isoformat()},
        )
        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-canonical-audit"))

        assert plan is not None
        records = pipeline._audit_observations["hf-canonical-audit"]
        generated = next(record for record in records if record.decision_type == DecisionType.plan_generated)
        assert generated.expected_steps == generated.observed_steps
        assert generated.assessment_id == "assess-001"
        assert generated.recommendation_id == "rec-001"
        assert generated.input_signal_ids == ["signal-001"]
        assert generated.routes_count == len(plan.routes)
        assert generated.transport_requests_count == len(plan.transport_requirements)
        assert generated.route_ids == [route.route_id for route in plan.routes]
        assert set(generated.expected_steps).issubset(generated.stage_durations_ms)
        assert all(duration >= 0 for duration in generated.stage_durations_ms.values())
        assert generated.configuration_version == plan.configuration_version

    def test_rejected_and_duplicate_handoffs_have_exact_terminal_audits(self):
        pipeline = _make_pipeline()
        rejected = _make_handoff(
            handoff_id="hf-rejected-audit",
            target_agent="other",
        )
        assert pipeline.process_handoff(rejected) is None
        assert [record.decision_type for record in pipeline._audit_observations[rejected.handoff_id]] == [
            DecisionType.handoff_rejected
        ]

        handoff = _make_handoff(handoff_id="hf-duplicate-audit")
        assert pipeline.process_handoff(handoff) is not None
        assert pipeline.process_handoff(handoff) is None
        assert [record.decision_type for record in pipeline._audit_observations[handoff.handoff_id]] == [
            DecisionType.duplicate_discarded
        ]

    def test_actionable_transport_request_is_persisted_linked_and_not_dispatched(self):
        facility = {
            "facility_id": "facility-access-centre",
            "name": "Access Centre",
            "type": "disability_care",
            "coordinates": {"lat": -16.878, "lng": 145.7554},
            "capacity": 40,
            "vulnerability_category": "mobility_impaired",
            "special_considerations": ["assisted_transport"],
        }
        pipeline = _make_pipeline(facility_data=[facility])

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-actionable-transport"))

        assert plan is not None
        assert len(plan.transport_requirements) == 1
        request = plan.transport_requirements[0]
        assert request.facility_id == "facility-access-centre"
        assert request.estimated_individuals == 40
        assert request.quantity_required == 10
        assert request.origin_zone == 2
        assert request.phase_number == 3
        assert request.dispatch_authorized is False
        assert request.destination_route_id
        allocation = next(
            allocation
            for allocation in plan.destination_allocations
            if allocation.zone_number == request.origin_zone
            and allocation.assembly_area_id == request.destination_assembly_area_id
        )
        assert allocation.assigned_vulnerable_population >= 40
        assert any(
            route.allocated_population > 0
            and route.origin_zone == request.origin_zone
            and route.destination_assembly_area == request.destination_assembly_area_id
            for route in plan.routes
        )
        selected_route = next(route for route in plan.routes if route.route_id == request.destination_route_id)
        assert selected_route.destination_assembly_area == (request.destination_assembly_area_id)
        assert selected_route.vehicle_suitability.accessible is True
        assert [linked.requirement_id for linked in plan.phases[2].transport_requirements] == [request.requirement_id]
        assert plan.uncovered_vulnerable_population_by_zone[1] >= 0
        payload = plan.to_resource_allocation_payload()
        assert payload["dispatchAuthorized"] is False
        assert payload["transportRequirements"][0]["requirementId"] == (request.requirement_id)

    def test_assembly_claims_and_capacity_are_grounded(self):
        plan = _make_pipeline().process_handoff(_make_handoff(handoff_id="hf-assembly-grounding"))

        assert plan is not None
        assert all(area.current_occupancy == 0 for area in plan.assembly_areas)
        assert all(area.shelter_available is False for area in plan.assembly_areas)
        assert all(
            area.accessible == ("wheelchair_accessible" in area.accessibility_features) for area in plan.assembly_areas
        )
        assert all(area.current_occupancy + area.assigned_population <= area.capacity for area in plan.assembly_areas)
        assert sum(area.assigned_population for area in plan.assembly_areas) == sum(
            allocation.assigned_population for allocation in plan.destination_allocations
        )

    def test_all_full_destinations_retain_unresolved_transport_request(
        self,
        monkeypatch,
        tmp_path,
    ):
        from tests.unit.test_evacuation_router import (
            _assembly_area,
            _edge,
            _micro_network,
        )

        network = _micro_network(
            tmp_path,
            [_edge("only-road", "origin", "safe", 1)],
            [
                _assembly_area(
                    "safe-aa",
                    "safe",
                    capacity_persons=40,
                    current_occupancy_persons=40,
                )
            ],
        )
        facility = {
            "facility_id": "facility-full-test",
            "name": "Full Capacity Facility",
            "coordinates": {"lat": 0, "lng": 0},
            "capacity": 40,
            "vulnerability_category": "mobility_impaired",
        }
        pipeline = _make_pipeline(
            road_network=network,
            facility_data=[facility],
        )
        zone = EvacuationZone(
            zone_id="zone-1",
            zone_number=1,
            population_estimate=40,
            vulnerable_population=40,
            boundary={
                "type": "Polygon",
                "coordinates": [[[-1, -1], [2, -1], [2, 2], [-1, 2], [-1, -1]]],
            },
            membership_boundary={
                "type": "Polygon",
                "coordinates": [[[-1, -1], [2, -1], [2, 2], [-1, 2], [-1, -1]]],
            },
        )

        def mocked_zones(handoff, assessment_data, scope, tenant, assumptions):
            del assessment_data, assumptions
            pipeline._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.zones_computed,
                rationale="Mocked one complete zone",
                duration_ms=0,
                incident_scope_key=scope,
                tenant_id=tenant,
                zone_ids=["1"],
                population_affected=40,
            )
            return [zone]

        def mocked_network(handoff, zones, assessment_data, scope, tenant, assumptions):
            del zones, assumptions
            assessment_data["road_data_status"] = "fresh"
            assessment_data["road_data_usable"] = True
            pipeline._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.road_network_loaded,
                rationale="Mocked fresh road network",
                duration_ms=0,
                incident_scope_key=scope,
                tenant_id=tenant,
            )
            return network

        monkeypatch.setattr(pipeline, "_stage_3_compute_zones", mocked_zones)
        monkeypatch.setattr(
            pipeline,
            "_stage_4_road_network_preparation",
            mocked_network,
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-all-full"))

        assert plan is not None
        assert plan.destination_allocations == []
        assert plan.unresolved_destination_demands[0].reason == ("no_accessible_capacity")
        assert plan.zero_route_zones == [1]
        assert "Unresolved destination demand:" in plan.summary
        assert len(plan.transport_requirements) == 1
        assert plan.transport_requirements[0].destination_resolved is False
        assert plan.transport_requirements[0].estimated_individuals == 40
        assert plan.transport_coordination_status.value == "partial"

    def test_pipeline_produces_plan(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert isinstance(plan, EvacuationPlan)

    def test_plan_has_valid_id(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert plan.plan_id.startswith("ep-")
        assert plan.plan_id.endswith("-v1")

    def test_plan_has_incident_id(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert plan.incident_id == "inc-001"

    def test_plan_has_zones(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert len(plan.zones) > 0

    def test_plan_has_traceability(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert plan.traceability is not None
        assert plan.traceability.source_handoff_id == "hf-001"

    def test_all_active_hazards_expand_persisted_plan_geometry(self):
        primary = _assessment()
        second = _secondary_hazard_assessment()
        pipeline = _make_pipeline(assessment_store=_Store({"assess-001": primary, "assess-002": second}))

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-multi-hazard"))

        assert plan is not None
        assert plan.traceability.risk_assessment_ids == [
            "assess-001",
            "assess-002",
        ]
        assert plan.data_snapshot.hazard_assessment_ids == [
            "assess-001",
            "assess-002",
        ]
        assert len(plan.hazard_summary.sources) == 2
        assert plan.hazard_summary.hazard_types == ["bushfire", "cyclone"]
        assert plan.hazard_summary.severity_level == "critical"
        merged_area = shape(plan.affected_area)
        assert merged_area.covers(shape(second["hazard_map"]["affected_area"]))
        assert shape(plan.zones[0].boundary).equals(merged_area)
        assert all("edge-002" not in route.waypoints for route in plan.routes)

    def test_invalid_secondary_active_hazard_rejects_entire_plan(self):
        invalid = _assessment(
            hazard_assessment_id="assess-invalid",
            input_signal_ids=["signal-invalid"],
        )
        invalid["hazard_map"]["affected_area"] = {
            "type": "Polygon",
            "coordinates": [],
        }
        pipeline = _make_pipeline(assessment_store=_Store({"assess-001": _assessment(), "assess-invalid": invalid}))

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-invalid-active-hazard"))

        assert plan is None
        rejection = next(
            entry.record
            for entry in pipeline.audit_writer._buffer
            if entry.record.decision_type == DecisionType.handoff_rejected
        )
        assert "valid non-empty polygon" in rejection.decision_rationale

    def test_invalid_wind_direction_rejects_hazard_source(self):
        assessment = _assessment(input_snapshot={"hazard_routing": {"wind_from_degrees": 361}})
        pipeline = _make_pipeline(assessment_store=_Store({"assess-001": assessment}))

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-invalid-wind"))

        assert plan is None
        rejection = next(
            entry.record
            for entry in pipeline.audit_writer._buffer
            if entry.record.decision_type == DecisionType.handoff_rejected
        )
        assert "Hazard routing attributes are invalid" in rejection.decision_rationale

    def test_plan_has_data_snapshot(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert plan.data_snapshot is not None

    def test_plan_has_summary(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert len(plan.summary) > 0

    def test_missing_hazard_reference_data_is_persisted_as_degraded(self):
        pipeline = _make_pipeline()

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-routing-degraded"))

        assert plan is not None
        assert plan.routing_mode == RoutingMode.hazard_constrained_degraded
        assert "bushfire.wind_from_degrees" in plan.hazard_routing_data_gaps
        assert "commander review" in plan.summary
        assert "safe passage" not in plan.summary
        assert "ROUTING EVIDENCE:" in plan.summary
        assert "Unavailable roads:" in plan.summary
        assert "Zones without routes:" in plan.summary
        assert plan.unavailable_roads_by_reason
        assert plan.zero_route_zones == [1]
        assert sum(plan.unavailable_roads_by_reason.values()) == len(plan.excluded_roads)
        assert all(route.selection_rationale for route in plan.routes)
        assert all(route.vehicle_suitability for route in plan.routes)
        assert all(route.path == route.waypoints for route in plan.routes)


# ---------------------------------------------------------------------------
# Handoff rejection
# ---------------------------------------------------------------------------


class TestHandoffRejection:
    def test_wrong_target_agent_rejected(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(target_agent="monitoring")
        plan = pipeline.process_handoff(handoff)
        assert plan is None

    def test_correct_target_agent_accepted(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(target_agent="evacuation")
        plan = pipeline.process_handoff(handoff)
        assert plan is not None

    def test_wrong_source_agent_rejected(self):
        pipeline = _make_pipeline()

        assert pipeline.process_handoff(_make_handoff(source_agent="evacuation")) is None

    def test_missing_reference_ids_rejected(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        handoff.payload = {}

        assert pipeline.process_handoff(handoff) is None

    def test_foreign_tenant_assessment_rejected(self):
        assessment = _assessment(tenant_id="tenant-two")
        pipeline = _make_pipeline(assessment_store=_Store({"assess-001": assessment}))

        assert pipeline.process_handoff(_make_handoff()) is None

    def test_malformed_hazard_geometry_rejected(self):
        assessment = _assessment(
            hazard_map={
                "affected_area": {"type": "Polygon", "coordinates": []},
                "severity_level": "high",
                "hazard_type": "bushfire",
                "confidence_score": 0.85,
                "time_horizon": "4h",
                "population_estimate": 5000,
            }
        )
        pipeline = _make_pipeline(assessment_store=_Store({"assess-001": assessment}))

        assert pipeline.process_handoff(_make_handoff()) is None

    def test_transient_store_failure_releases_handoff_for_redelivery(self):
        class _Unavailable:
            def read_item(self, item, partition_key):
                raise TimeoutError("Cosmos unavailable")

        pipeline = _make_pipeline(recommendation_store=_Unavailable())
        handoff = _make_handoff()

        with pytest.raises(TransientHandoffDependencyError):
            pipeline.process_handoff(handoff)
        with pytest.raises(TransientHandoffDependencyError):
            pipeline.process_handoff(handoff)

    def test_plan_persistence_failure_releases_handoff_for_redelivery(self):
        class _UnavailablePlans:
            def read_item(self, item, partition_key):
                raise RuntimeError("404 NotFound")

            def create_item(self, body):
                if body["id"].endswith("_plan_counter"):
                    return body
                raise TimeoutError("Cosmos unavailable")

        pipeline = _make_pipeline()
        pipeline._cosmos_plans = _UnavailablePlans()
        pipeline._version_counter._container = pipeline._cosmos_plans
        handoff = _make_handoff(handoff_id="hf-plan-write-failure")

        with pytest.raises(TransientHandoffDependencyError, match="Plan persistence unconfirmed"):
            pipeline.process_handoff(handoff)
        with pytest.raises(TransientHandoffDependencyError, match="Plan persistence unconfirmed"):
            pipeline.process_handoff(handoff)

    def test_version_reservation_failure_is_retryable(self):
        class _FailingCounter:
            async def assign_version(self, incident_id, incident_scope_key):
                raise VersionReservationError("reservation exhausted")

        pipeline = _make_pipeline()
        pipeline._version_counter = _FailingCounter()
        handoff = _make_handoff(handoff_id="hf-version-failure")
        with pytest.raises(
            TransientHandoffDependencyError,
            match="version reservation is temporarily unavailable",
        ):
            pipeline.process_handoff(handoff)
        with pytest.raises(
            TransientHandoffDependencyError,
            match="version reservation is temporarily unavailable",
        ):
            pipeline.process_handoff(handoff)


class TestPlanPersistenceConfirmation:
    @staticmethod
    def _store(*, fail_before_write=False, lose_write_response=False, fail_readback=False):
        from tests.unit.test_evacuation_dedup import _DurableClaimStore

        class Store(_DurableClaimStore):
            def __init__(self):
                super().__init__()
                self.fail_before_write = fail_before_write
                self.lose_write_response = lose_write_response
                self.fail_readback = fail_readback

            def create_item(self, body):
                is_plan = body.get("id", "").startswith("ep-")
                if is_plan and self.fail_before_write:
                    self.fail_before_write = False
                    raise RuntimeError("503 ServiceUnavailable")
                document = super().create_item(body)
                if is_plan and self.lose_write_response:
                    self.lose_write_response = False
                    raise TimeoutError("write response lost")
                return document

            def read_item(self, item, partition_key):
                if item.startswith("ep-") and self.fail_readback:
                    self.fail_readback = False
                    raise TimeoutError("readback timeout")
                return super().read_item(item, partition_key)

        return Store()

    @staticmethod
    def _plan_documents(store):
        return [document for document in store.documents.values() if document.get("id", "").startswith("ep-")]

    def test_accepted_write_with_lost_response_is_confirmed_by_readback(self):
        store = self._store(lose_write_response=True)
        pipeline = _make_pipeline(plans_store=store)
        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-lost-write-response"))
        assert plan is not None
        assert pipeline.active_plan_count == 1
        assert [document["plan_id"] for document in self._plan_documents(store)] == [plan.plan_id]
        completed_claim = next(
            document for document in store.documents.values() if document.get("handoff_id") == "hf-lost-write-response"
        )
        assert completed_claim["status"] == "completed"
        counter = store.read_item("inc-001_plan_counter", "live:inc-001")
        assert counter["orphaned_versions"] == []
        assert counter["uncertain_versions"] == []

    def test_confirmed_absence_records_orphan_without_success_signals(
        self,
        monkeypatch,
    ):
        store = self._store(fail_before_write=True)
        pipeline = _make_pipeline(plans_store=store)
        active_plans = _GaugeCapture()
        generated_events = []
        monkeypatch.setattr(tel, "active_plans_gauge", active_plans)
        monkeypatch.setattr(
            tel,
            "emit_plan_generated",
            lambda **values: generated_events.append(values),
        )
        handoff = _make_handoff(handoff_id="hf-orphaned-version")
        with pytest.raises(TransientHandoffDependencyError, match="unconfirmed"):
            pipeline.process_handoff(handoff)
        assert pipeline.active_plan_count == 0
        assert self._plan_documents(store) == []
        assert active_plans.values == []
        assert generated_events == []
        assert not any(
            entry.record.decision_type == DecisionType.plan_generated and entry.record.plan_id is not None
            for entry in pipeline.audit_writer._buffer
        )
        counter = store.read_item("inc-001_plan_counter", "live:inc-001")
        assert counter["orphaned_versions"][0]["version"] == 1

        recovered = _make_pipeline(plans_store=store).process_handoff(handoff)
        assert recovered is not None
        assert recovered.version == 2
        assert len(self._plan_documents(store)) == 1

    def test_readback_timeout_recovers_existing_plan_without_v2(self):
        store = self._store(fail_readback=True)
        first = _make_pipeline(plans_store=store)
        handoff = _make_handoff(handoff_id="hf-readback-timeout")
        with pytest.raises(TransientHandoffDependencyError, match="unconfirmed"):
            first.process_handoff(handoff)
        assert first.active_plan_count == 0
        assert len(self._plan_documents(store)) == 1
        assert not any(
            entry.record.decision_type == DecisionType.plan_generated and entry.record.plan_id is not None
            for entry in first.audit_writer._buffer
        )
        counter = store.read_item("inc-001_plan_counter", "live:inc-001")
        assert counter["uncertain_versions"][0]["version"] == 1

        replay = _make_pipeline(plans_store=store).process_handoff(handoff)
        assert replay is None
        plans = self._plan_documents(store)
        assert len(plans) == 1
        assert plans[0]["version"] == 1
        assert store.read_item("inc-001_plan_counter", "live:inc-001")["current_version"] == 1


class TestPipelinePlanLifecycle:
    def test_new_handoff_supersedes_older_proposal(self):
        from tests.unit.test_evacuation_dedup import _DurableClaimStore

        store = _DurableClaimStore()
        pipeline = _make_pipeline(plans_store=store)
        first = pipeline.process_handoff(_make_handoff(handoff_id="hf-lifecycle-1"))
        second = pipeline.process_handoff(_make_handoff(handoff_id="hf-lifecycle-2"))
        assert first is not None and second is not None
        first_document = store.read_item(first.plan_id, "live:inc-001")
        second_document = store.read_item(second.plan_id, "live:inc-001")
        assert first_document["status"] == "superseded"
        assert first_document["superseded_by"] == second.plan_id
        assert second_document["status"] == "proposed"
        assert second_document["source_plan_id"] == first.plan_id

    def test_approved_source_remains_authoritative_when_new_handoff_creates_proposal(self):
        from tests.unit.test_evacuation_dedup import _DurableClaimStore

        store = _DurableClaimStore()
        pipeline = _make_pipeline(plans_store=store)
        first = pipeline.process_handoff(_make_handoff(handoff_id="hf-approved-1"))
        assert first is not None
        first_document = store.read_item(first.plan_id, "live:inc-001")
        first_document["status"] = "approved"
        first_document["approved_at"] = datetime.now(UTC).isoformat()
        first_document["valid_until"] = None
        store.replace_item(
            first.plan_id,
            {key: value for key, value in first_document.items() if not key.startswith("_")},
            etag=first_document["_etag"],
            match_condition=object(),
        )
        second = pipeline.process_handoff(_make_handoff(handoff_id="hf-approved-2"))
        assert second is not None
        approved = store.read_item(first.plan_id, "live:inc-001")
        proposal = store.read_item(second.plan_id, "live:inc-001")
        assert approved["status"] == "approved"
        assert proposal["status"] == "proposed"
        assert proposal["source_plan_id"] == first.plan_id

    def test_new_active_hazard_changes_next_plan_and_zone_one_roads(self):
        from tests.unit.test_evacuation_dedup import _DurableClaimStore

        plan_store = _DurableClaimStore()
        assessment_store = _Store({"assess-001": _assessment()})
        pipeline = _make_pipeline(
            assessment_store=assessment_store,
            plans_store=plan_store,
        )
        first = pipeline.process_handoff(_make_handoff(handoff_id="hf-before-second-hazard"))
        assert first is not None
        assessment_store.documents["assess-002"] = _secondary_hazard_assessment()

        second = pipeline.process_handoff(_make_handoff(handoff_id="hf-after-second-hazard"))

        assert second is not None
        assert second.version == 2
        assert len(second.hazard_summary.sources) == 2
        assert not shape(first.affected_area).equals(shape(second.affected_area))
        edge_geometry = pipeline._road_network.get_edge_geometry("edge-002")
        assert edge_geometry is not None
        first_zone = pipeline._zone_computer.classify_edge_zone(
            edge_geometry,
            pipeline._zone_computer.get_zone_polygons(first.zones),
        )
        second_zone = pipeline._zone_computer.classify_edge_zone(
            edge_geometry,
            pipeline._zone_computer.get_zone_polygons(second.zones),
        )
        assert first_zone != 1
        assert second_zone == 1
        assert all("edge-002" not in route.waypoints for route in second.routes)


# ---------------------------------------------------------------------------
# Duplicate discard
# ---------------------------------------------------------------------------


class TestDuplicateDiscard:
    def test_duplicate_handoff_discarded(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(handoff_id="hf-dup")
        plan1 = pipeline.process_handoff(handoff)
        plan2 = pipeline.process_handoff(handoff)  # same handoff_id
        assert plan1 is not None
        assert plan2 is None  # Discarded as duplicate

    def test_different_ids_not_duplicate(self):
        pipeline = _make_pipeline()
        plan1 = pipeline.process_handoff(_make_handoff(handoff_id="hf-a"))
        plan2 = pipeline.process_handoff(_make_handoff(handoff_id="hf-b"))
        assert plan1 is not None
        assert plan2 is not None


class TestEffectiveRoadNetwork:
    def test_stage4_applies_capacity_copy_without_mutating_base(self, monkeypatch):
        road_network = RoadNetworkLoader(
            now=lambda: datetime(2026, 4, 16, 1, tzinfo=UTC),
        )
        road_network.load(SAMPLE_FILE)
        pipeline = _make_pipeline(road_network)
        base_edge = road_network.get_all_edges()[0]
        base_capacity = base_edge.capacity_vehicles_per_hour
        handoff = _make_handoff()
        zone = EvacuationZone(
            zone_id="zone-2",
            zone_number=2,
            boundary={
                "type": "Polygon",
                "coordinates": [[[145.7, -17.0], [145.9, -17.0], [145.9, -16.8], [145.7, -16.8], [145.7, -17.0]]],
            },
        )

        monkeypatch.setattr(pipeline._zone_computer, "get_zone_polygons", lambda _zones: [(2, object())])

        def reduce(edges, _polygons):
            adjusted = [dict(edge) for edge in edges]
            adjusted[0]["capacity_vehicles_per_hour"] = base_capacity // 2
            return adjusted

        monkeypatch.setattr(pipeline._zone_computer, "apply_zone_capacity_reduction", reduce)

        first = pipeline._stage_4_road_network_preparation(
            handoff,
            [zone],
            {},
            "live:inc-001",
            "live",
            [],
        )
        second = pipeline._stage_4_road_network_preparation(
            handoff,
            [zone],
            {},
            "live:inc-001",
            "live",
            [],
        )

        assert first is not road_network
        assert first.get_edge(base_edge.id).capacity_vehicles_per_hour == base_capacity // 2
        assert second.get_edge(base_edge.id).capacity_vehicles_per_hour == base_capacity // 2
        assert road_network.get_edge(base_edge.id).capacity_vehicles_per_hour == base_capacity

    def test_stale_source_disables_computed_routes_but_persists_guidance(self):
        road_network = RoadNetworkLoader(
            now=lambda: datetime(2026, 4, 17, tzinfo=UTC),
        )
        road_network.load(SAMPLE_FILE)
        pipeline = _make_pipeline(road_network)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-stale-road"))

        assert plan is not None
        assert plan.routes == []
        assert plan.assembly_areas == []
        assert plan.immediate_human_review_required is True
        assert plan.data_snapshot.road_data_status == "stale"
        assert plan.data_snapshot.road_source_age_hours == pytest.approx(24)
        assert "No route, destination, road passability, or capacity" in plan.summary
        assert "fire threat" in plan.summary
        assert "road_data_degraded" in {item.reason for item in plan.confidence_adjustments}
        degradation_records = [
            entry.record
            for entry in pipeline.audit_writer._buffer
            if entry.record.decision_type == DecisionType.degradation_detected
        ]
        assert any(
            record.immediate_human_review_required and "road_data_stale" in record.data_quality_gaps
            for record in degradation_records
        )

    def test_failed_refresh_uses_only_fresh_last_known_good(self, tmp_path):
        road_network = RoadNetworkLoader(
            now=lambda: datetime(2026, 4, 16, 1, tzinfo=UTC),
        )
        road_network.load(SAMPLE_FILE)
        invalid = tmp_path / "invalid.json"
        invalid.write_text("{invalid", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            road_network.load(str(invalid))
        pipeline = _make_pipeline(road_network)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-fresh-cache"))

        assert plan is not None
        assert plan.routes
        assert plan.data_snapshot.road_data_status == ("fresh_cache_refresh_failed")
        assert plan.data_snapshot.road_refresh_failure_reason
        assert plan.immediate_human_review_required is True
        assert "last-known-good road snapshot" in plan.summary

    def test_failed_refresh_does_not_revive_expired_cache(self, tmp_path):
        road_network = RoadNetworkLoader(
            now=lambda: datetime(2026, 4, 17, tzinfo=UTC),
        )
        road_network.load(SAMPLE_FILE)
        invalid = tmp_path / "invalid.json"
        invalid.write_text("{invalid", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            road_network.load(str(invalid))
        pipeline = _make_pipeline(road_network)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-stale-cache"))

        assert plan is not None
        assert plan.routes == []
        assert plan.data_snapshot.road_data_status == "stale"
        assert plan.data_snapshot.road_refresh_failure_reason
        assert plan.immediate_human_review_required is True

    def test_no_road_cache_does_not_drop_handoff(self):
        pipeline = _make_pipeline(RoadNetworkLoader())
        pipeline._config = EvacuationConfig(road_network_file_path="data/road-networks/missing.json")

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-no-road-cache"))

        assert plan is not None
        assert plan.routes == []
        assert plan.data_snapshot.road_data_status == "unavailable"
        assert plan.data_snapshot.road_network_version == "unavailable"
        assert plan.immediate_human_review_required is True

    def test_stale_reference_data_is_used_with_age_and_confidence_degradation(self):
        fresh_timestamp = datetime.now(UTC).isoformat()
        stale_timestamp = (datetime.now(UTC) - timedelta(days=2)).isoformat()
        fresh = _make_pipeline(
            population_data=[],
            facility_data=[],
            reference_data_metadata={"last_updated": fresh_timestamp},
        ).process_handoff(_make_handoff(handoff_id="hf-fresh-reference"))
        stale = _make_pipeline(
            population_data=[],
            facility_data=[],
            reference_data_metadata={"last_updated": stale_timestamp},
        ).process_handoff(_make_handoff(handoff_id="hf-stale-reference"))

        assert fresh is not None and stale is not None
        assert fresh.routes and stale.routes
        assert stale.data_snapshot.population_data_status == "stale"
        assert stale.data_snapshot.facility_data_status == "stale"
        assert stale.data_snapshot.population_source_age_hours >= 48
        assert stale.data_snapshot.facility_source_age_hours >= 48
        assert any(assumption.startswith("POPULATION DATA DEGRADED") for assumption in stale.assumptions)
        assert any(assumption.startswith("FACILITY DATA DEGRADED") for assumption in stale.assumptions)
        assert stale.confidence_score < fresh.confidence_score
        reasons = {item.reason for item in stale.confidence_adjustments}
        assert "population_data_degraded" in reasons
        assert "facility_data_degraded" in reasons


class TestExclusiveOriginAssignment:
    @staticmethod
    def _population_area(name, min_x, max_x, population, vulnerable):
        return {
            "area_name": name,
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [min_x, -16.94],
                        [max_x, -16.94],
                        [max_x, -16.91],
                        [min_x, -16.91],
                        [min_x, -16.94],
                    ]
                ],
            },
            "population_estimate": population,
            "vulnerable_population_estimate": vulnerable,
        }

    def test_pipeline_reconciles_unique_authoritative_population(self):
        population_data = [
            self._population_area("inner", 145.76, 145.79, 100, 7),
            self._population_area("middle", 145.81, 145.83, 200, 40),
            self._population_area("outer", 145.86, 145.88, 300, 90),
        ]
        pipeline = _make_pipeline(population_data=population_data)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-exclusive-population"))

        assert plan is not None
        assert [zone.population_estimate for zone in plan.zones] == [100, 200, 300]
        assert [zone.vulnerable_population for zone in plan.zones] == [7, 40, 90]
        assert plan.total_population == 600
        assert (
            sum(phase.population_moved + phase.population_remaining for phase in plan.phases) == plan.total_population
        )
        assert sum(disposition.affected_population for disposition in plan.zone_dispositions) == plan.total_population
        origin_node_ids = [node_id for zone in plan.zones for node_id in zone.origin_node_ids]
        assert len(origin_node_ids) == len(set(origin_node_ids))

    def test_boundary_node_is_owned_once_by_highest_priority_zone(self):
        pipeline = _make_pipeline()
        node = pipeline._road_network.get_node("node-001")
        assert node is not None
        longitude = node.coordinates["lng"]
        latitude = node.coordinates["lat"]
        zones = [
            EvacuationZone(
                zone_number=1,
                membership_boundary={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [longitude - 0.01, latitude - 0.01],
                            [longitude, latitude - 0.01],
                            [longitude, latitude + 0.01],
                            [longitude - 0.01, latitude + 0.01],
                            [longitude - 0.01, latitude - 0.01],
                        ]
                    ],
                },
            ),
            EvacuationZone(
                zone_number=2,
                membership_boundary={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [longitude, latitude - 0.01],
                            [longitude + 0.01, latitude - 0.01],
                            [longitude + 0.01, latitude + 0.01],
                            [longitude, latitude + 0.01],
                            [longitude, latitude - 0.01],
                        ]
                    ],
                },
            ),
        ]

        assignments = pipeline._assign_zone_origin_nodes(zones)

        assert "node-001" in assignments[1]
        assert "node-001" not in assignments[2]
        assert len(assignments[1] + assignments[2]) == len(set(assignments[1] + assignments[2]))

    def test_zone_outside_network_has_no_fabricated_route(self):
        pipeline = _make_pipeline()
        zone = EvacuationZone(
            zone_id="zone-uncovered",
            zone_number=1,
            population_estimate=100,
            vulnerable_population=20,
            membership_boundary={
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
        )
        assumptions = []

        routes = pipeline._stage_5_compute_routes(
            _make_handoff(),
            [zone],
            {"hazard_type": "bushfire"},
            pipeline._road_network,
            "live:inc-001",
            "live",
            assumptions,
        )

        assert routes == []
        assert zone.origin_node_ids == []
        assert zone.origin_coverage_status == OriginCoverageStatus.no_network_origin
        assert any("no road-network origin" in assumption for assumption in assumptions)

        _, dispositions, _ = pipeline._stage_7_timeline_estimation(
            _make_handoff(),
            [zone],
            routes,
            [],
            {"hazard_type": "bushfire", "time_horizon": "12h"},
            "live:inc-001",
            "live",
        )
        assert dispositions[0].origin_coverage_status == OriginCoverageStatus.no_network_origin
        assert "no road-network origin" in dispositions[0].rationale


class _CounterCapture:
    def __init__(self):
        self.total = 0

    def add(self, amount, attributes=None):
        del attributes
        self.total += amount


class _CounterCallCapture:
    def __init__(self):
        self.calls = []

    def add(self, amount, attributes=None):
        self.calls.append((amount, attributes))


class _GaugeCapture:
    def __init__(self):
        self.values = []

    def set(self, value, attributes=None):
        self.values.append((value, attributes))


class _SpanCapture:
    def __init__(self, tracer, name, attributes):
        self._tracer = tracer
        self.name = name
        self.attributes = attributes or {}
        self.parent = tracer.stack[-1].name if tracer.stack else None

    def __enter__(self):
        self._tracer.stack.append(self)
        self._tracer.spans.append(self)
        return self

    def __exit__(self, *args):
        del args
        self._tracer.stack.pop()

    def set_attribute(self, key, value):
        self.attributes[key] = value

    def add_event(self, name, attributes=None):
        del name, attributes


class _TracerCapture:
    def __init__(self):
        self.stack = []
        self.spans = []

    def start_as_current_span(self, name, attributes=None):
        return _SpanCapture(self, name, attributes)


class TestPipelineTelemetry:
    def test_handoff_success_rate_includes_rejected_handoffs(
        self,
        monkeypatch,
    ):
        success_rate = _GaugeCapture()
        monkeypatch.setattr(tel, "handoff_success_rate", success_rate)
        pipeline = _make_pipeline()

        rejected = pipeline.process_handoff(
            _make_handoff(
                handoff_id="hf-telemetry-rejected",
                target_agent="other",
            )
        )
        accepted = pipeline.process_handoff(_make_handoff(handoff_id="hf-telemetry-accepted"))

        assert rejected is None
        assert accepted is not None
        assert success_rate.values[-1] == (0.5, None)

    @pytest.mark.parametrize(
        ("status", "expected_tier"),
        [("healthy", 1.0), ("buffering", 2.0), ("degraded", 3.0)],
    )
    def test_audit_tier_matches_storage_state(
        self,
        monkeypatch,
        status,
        expected_tier,
    ):
        audit_tier = _GaugeCapture()
        monkeypatch.setattr(tel, "audit_tier", audit_tier)
        pipeline = _make_pipeline()
        monkeypatch.setattr(pipeline.audit_writer, "get_status", lambda: status)

        plan = pipeline.process_handoff(_make_handoff(handoff_id=f"hf-audit-tier-{status}"))

        assert plan is not None
        assert audit_tier.values[-1] == (
            expected_tier,
            {"incident_id": "inc-001", "tenant_id": "live"},
        )

    def test_route_conflict_event_uses_persisted_plan_and_typed_percentage(
        self,
        monkeypatch,
    ):
        pipeline = _make_pipeline()
        original_compute = pipeline._stage_5_compute_routes
        events = []

        def congested_routes(*args, **kwargs):
            routes = original_compute(*args, **kwargs)
            assert routes
            routes[0].update(
                {
                    "congestion_risk": True,
                    "congestion_risk_pct": 85,
                    "uncapped_utilisation_pct": 185.0,
                    "estimated_utilisation_pct": 185.0,
                }
            )
            return routes

        monkeypatch.setattr(
            pipeline,
            "_stage_5_compute_routes",
            congested_routes,
        )
        monkeypatch.setattr(
            tel,
            "emit_route_conflict",
            lambda **values: events.append(values),
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-route-conflict-event"))

        assert plan is not None
        assert events == [
            {
                "plan_id": plan.plan_id,
                "route_id": plan.routes[0].route_id,
                "utilisation_pct": 85.0,
            }
        ]

    def test_nested_spans_have_real_stage_parents_and_correlation(
        self,
        monkeypatch,
    ):
        tracer = _TracerCapture()
        monkeypatch.setattr(tel, "tracer", tracer)
        pipeline = _make_pipeline(
            llm_generate_fn=lambda **kwargs: {
                "text": "commander review should retain validated facts.",
                "generation_method": "llm",
                "content_safety_result": "passed",
                "content_safety_validation_method": "azure_ai",
            }
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-span-hierarchy"))

        assert plan is not None
        by_name = {}
        for span in tracer.spans:
            by_name.setdefault(span.name, span)
        root = by_name["evacuation.process_handoff"]
        assert root.parent is None
        assert root.attributes["correlation_id"] == "hf-span-hierarchy"
        assert root.attributes["incident_id"] == "inc-001"
        assert root.attributes["tenant_id"] == "live"
        expected_parents = {
            "evacuation.shapely_intersection": "evacuation.compute_zones",
            "evacuation.apply_zone_capacity_reduction": ("evacuation.prepare_road_network"),
            "evacuation.dijkstra_run": "evacuation.compute_routes",
            "evacuation.multi_path_distribution": "evacuation.compute_routes",
            "evacuation.query_facilities": "evacuation.coordinate_transport",
            "evacuation.compute_phase": "evacuation.estimate_timeline",
            "evacuation.llm_call": "evacuation.generate_summary",
            "evacuation.content_safety_check": "evacuation.generate_summary",
            "evacuation.template_render": "evacuation.generate_summary",
            "evacuation.assign_version": "evacuation.process_handoff",
            "evacuation.persist_plan": "evacuation.process_handoff",
            "evacuation.write_audit": "evacuation.process_handoff",
        }
        assert {name: by_name[name].parent for name in expected_parents} == expected_parents

    def test_medical_transport_metrics_use_category_and_vehicle_quantity(
        self,
        monkeypatch,
    ):
        category_counter = _CounterCallCapture()
        vehicle_gauge = _GaugeCapture()
        monkeypatch.setattr(tel, "transport_by_category", category_counter)
        monkeypatch.setattr(
            tel,
            "transport_vehicles_estimated",
            vehicle_gauge,
        )
        pipeline = _make_pipeline(
            facility_data=[
                {
                    "facility_id": "medical-1",
                    "name": "Medical Support Centre",
                    "type": "hospital",
                    "coordinates": {"lat": -16.878, "lng": 145.7554},
                    "capacity": 20,
                    "vulnerability_category": "medical_dependent",
                }
            ]
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-medical-telemetry"))

        assert plan is not None
        requirement = plan.transport_requirements[0]
        assert requirement.category.value == "medical_dependent"
        assert category_counter.calls == [
            (
                1,
                {
                    "incident_id": "inc-001",
                    "tenant_id": "live",
                    "category": "medical_dependent",
                },
            )
        ]
        assert vehicle_gauge.values[-1] == (
            float(requirement.quantity_required),
            {"incident_id": "inc-001", "tenant_id": "live"},
        )


class TestZoneDispositionPipeline:
    def test_safe_shelter_never_emits_emergency(self, monkeypatch):
        emergency_notifications: list[EmergencyNotification] = []
        shelter_counter = _CounterCapture()
        emergency_counter = _CounterCapture()
        emergency_events = []
        monkeypatch.setattr(tel, "shelter_in_place_count", shelter_counter)
        monkeypatch.setattr(tel, "emergency_escalation_count", emergency_counter)
        monkeypatch.setattr(
            tel,
            "emit_emergency_escalation",
            lambda *args: emergency_events.append(args),
        )
        assessment = _assessment()
        assessment["hazard_map"]["time_horizon"] = "12h"
        pipeline = _make_pipeline(
            assessment_store=_Store({"assess-001": assessment}),
            emergency_notification_publisher=lambda notification: emergency_notifications.append(notification),
        )

        def shelter_zone(handoff, assessment_data, scope, tenant, assumptions):
            del assessment_data, assumptions
            zone = EvacuationZone(
                zone_id="zone-1",
                zone_number=1,
                population_estimate=100,
                vulnerable_population=10,
            )
            pipeline._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.zones_computed,
                rationale="Mocked shelter test zone",
                duration_ms=0,
                incident_scope_key=scope,
                tenant_id=tenant,
                zone_ids=["1"],
                population_affected=100,
            )
            return [zone]

        monkeypatch.setattr(pipeline, "_stage_3_compute_zones", shelter_zone)

        def mocked_routes(handoff, zones, assessment_data, network, scope, tenant, assumptions):
            del zones, assessment_data, network, assumptions
            pipeline._write_audit(
                handoff_id=handoff.handoff_id,
                incident_id=handoff.incident_id,
                decision_type=DecisionType.routes_computed,
                rationale="Mocked no viable routes",
                duration_ms=0,
                incident_scope_key=scope,
                tenant_id=tenant,
                routes_count=0,
            )
            return []

        monkeypatch.setattr(pipeline, "_stage_5_compute_routes", mocked_routes)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-safe-shelter"))
        assert plan is not None
        disposition = plan.zone_dispositions[0]
        assert disposition.disposition == ZoneDispositionType.shelter_in_place
        assert disposition.emergency_notification_id is None
        assert emergency_notifications == []
        populated_phases = [
            phase for phase in plan.phases if phase.zone_ids == ["1"] and phase.population_remaining > 0
        ]
        assert all(phase.duration_minutes is None for phase in populated_phases)
        assert shelter_counter.total == 1
        assert emergency_counter.total == 0
        assert emergency_events == []

    @pytest.mark.parametrize("time_horizon", ["1h", None])
    def test_blocked_imminent_or_unknown_horizon_routes_operator_notification(
        self,
        time_horizon,
    ):
        notifications: list[EmergencyNotification] = []

        def publish(notification):
            notifications.append(notification)
            return f"receipt:{notification.notification_id}"

        pipeline = _make_pipeline(emergency_notification_publisher=publish)
        _, dispositions, _ = pipeline._stage_7_timeline_estimation(
            _make_handoff(handoff_id="hf-emergency"),
            [EvacuationZone(zone_id="zone-1", zone_number=1, population_estimate=100)],
            [],
            [],
            {"hazard_type": "bushfire", "time_horizon": time_horizon},
            "live:inc-001",
            "live",
        )
        disposition = dispositions[0]
        assert disposition.disposition == ZoneDispositionType.emergency_escalation
        assert disposition.urgency == "maximum"
        assert disposition.emergency_notification_receipt.startswith("receipt:")
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.target == "emergency_services_operator"
        assert notification.public_order_authorized is False
        assert notification.affected_population == 100

        disposition_audits = [entry.record for entry in pipeline.audit_writer._buffer if entry.record.zone_dispositions]
        assert len(disposition_audits) == 1
        assert (
            disposition_audits[0].zone_dispositions[0].emergency_notification_receipt
            == disposition.emergency_notification_receipt
        )

    def test_partial_clearance_persists_remaining_population_and_reduced_confidence(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        zones = [
            EvacuationZone(
                zone_id="zone-1",
                zone_number=1,
                population_estimate=1000,
                vulnerable_population=100,
            )
        ]
        routes = [
            {
                "zone_id": "1",
                "distance_km": 20,
                "capacity_vehicles_per_hour": 100,
            }
        ]
        phases, dispositions, assumptions = pipeline._stage_7_timeline_estimation(
            handoff,
            zones,
            routes,
            [],
            {"hazard_type": "bushfire", "time_horizon": "2h"},
            "live:inc-001",
            "live",
        )
        disposition = dispositions[0]
        assert disposition.disposition == ZoneDispositionType.partial_evacuation
        assert disposition.clearance_deficit_minutes > 0
        assert disposition.evacuating_population + disposition.remaining_population == 1000
        assert any(assumption.startswith("TIME DEFICIT:") for assumption in assumptions)

        _, _, confidence = pipeline._stage_8_plan_summary(
            handoff,
            zones,
            routes,
            [],
            phases,
            dispositions,
            {"hazard_type": "bushfire", "time_horizon": "2h"},
            "live:inc-001",
            "live",
            assumptions,
        )
        assert confidence == pytest.approx(0.85 * 0.8 * 0.8)


class TestGroundedSummaryGeneration:
    @staticmethod
    def _fresh_pipeline(response):
        return _make_pipeline(
            population_data=[],
            facility_data=[],
            reference_data_metadata={"last_updated": datetime.now(UTC).isoformat()},
            llm_generate_fn=lambda **kwargs: response(kwargs) if callable(response) else response,
        )

    def test_safe_success_uses_canonical_label_and_final_confidence(self):
        pipeline = self._fresh_pipeline(
            {
                "text": "Operational facts reviewed; retain commander approval controls.",
                "generation_method": "llm",
                "content_safety_result": "passed",
                "content_safety_validation_method": "azure_ai",
                "requires_human_review": False,
                "model_deployment_id": "model-1",
            }
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-summary-success"))

        assert plan is not None
        assert plan.generation_method == "ai_assisted"
        assert plan.traceability.generation_method == "ai_assisted"
        assert "CONFIDENCE:" in plan.summary
        assert f"({plan.confidence_score:.0%})" in plan.summary
        assert "Operational facts reviewed" in plan.summary

    @pytest.mark.parametrize(
        "model_text",
        [
            "",
            "All roads are safe. No urgent action is required.",
        ],
    )
    def test_empty_or_contradictory_model_text_uses_template(self, model_text):
        pipeline = self._fresh_pipeline(
            {
                "text": model_text,
                "generation_method": "llm",
                "content_safety_result": "passed",
                "requires_human_review": False,
            }
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id=f"hf-summary-{len(model_text)}"))

        assert plan is not None
        assert plan.generation_method == "template_fallback"
        if model_text:
            assert model_text not in plan.summary
        assert sum(item.reason == "generation_template_fallback" for item in plan.confidence_adjustments) == 1

    def test_blocked_text_never_persists_and_safety_metadata_is_audited(self):
        unsafe = "Unsafe model output must never persist"
        pipeline = self._fresh_pipeline(
            {
                "text": "safe deterministic template replacement",
                "generation_method": "safety_fallback",
                "content_safety_result": "failed_with_fallback",
                "content_safety_validation_method": "keyword_fallback",
                "content_safety_reason": "blocked_keyword",
                "content_safety_reference": "evidence-1",
                "requires_human_review": True,
                "unsafe_text_for_test": unsafe,
            }
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-summary-blocked"))

        assert plan is not None
        assert plan.generation_method == "safety_fallback"
        assert unsafe not in plan.model_dump_json()
        assert plan.content_safety_result == "failed_with_fallback"
        assert plan.content_safety_validation_method == "keyword_fallback"
        assert plan.content_safety_reason == "blocked_keyword"
        assert plan.content_safety_reference == "evidence-1"
        assert plan.immediate_human_review_required is True
        audits = [
            entry.record
            for entry in pipeline.audit_writer._buffer
            if entry.record.decision_type == DecisionType.content_safety_failure
        ]
        assert len(audits) == 1
        assert audits[0].content_safety_reference == "evidence-1"
        generated = [
            entry.record
            for entry in pipeline.audit_writer._buffer
            if entry.record.decision_type == DecisionType.plan_generated
        ]
        assert len(generated) == 1
        assert generated[0].generation_method == "safety_fallback"
        assert generated[0].content_safety_result == "failed_with_fallback"
        assert generated[0].content_safety_validation_method == ("keyword_fallback")
        assert generated[0].content_safety_reference == "evidence-1"

    def test_generation_exception_uses_one_fallback_reduction(self):
        def fail_generation(**kwargs):
            del kwargs
            raise TimeoutError("model unavailable")

        pipeline = self._fresh_pipeline(fail_generation)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-summary-exception"))

        assert plan is not None
        assert plan.generation_method == "template_fallback"
        assert plan.summary_grounding_result == "generation_exception"
        assert sum(item.reason == "generation_template_fallback" for item in plan.confidence_adjustments) == 1

    def test_degraded_validator_review_flag_survives_success(self):
        pipeline = self._fresh_pipeline(
            {
                "text": "Commander review should retain validated facts.",
                "generation_method": "llm",
                "content_safety_result": "passed",
                "content_safety_validation_method": "keyword_fallback",
                "requires_human_review": True,
            }
        )

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-summary-validator"))

        assert plan is not None
        assert plan.generation_method == "ai_assisted"
        assert plan.content_safety_validation_method == "keyword_fallback"
        assert plan.immediate_human_review_required is True
        assert plan.summary.startswith("IMMEDIATE HUMAN REVIEW REQUIRED")

    def test_low_initial_confidence_is_visible_and_requires_review(self):
        pipeline = self._fresh_pipeline(
            {
                "text": "Commander approval should follow validated facts.",
                "generation_method": "llm",
                "content_safety_result": "passed",
                "content_safety_validation_method": "azure_ai",
                "requires_human_review": False,
            }
        )

        plan = pipeline.process_handoff(
            _make_handoff(
                handoff_id="hf-summary-low",
                confidence=0.2,
            )
        )

        assert plan is not None
        assert plan.immediate_human_review_required is True
        assert plan.summary.startswith("IMMEDIATE HUMAN REVIEW REQUIRED")
        assert f"({plan.confidence_score:.0%})" in plan.summary

    def test_long_assumptions_cannot_remove_urgent_warning(self):
        pipeline = self._fresh_pipeline(
            {
                "text": "Model commentary " * 200,
                "generation_method": "llm",
                "content_safety_result": "passed",
                "requires_human_review": False,
            }
        )
        pipeline._config = EvacuationConfig(max_summary_length=400)

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-summary-length"))

        assert plan is not None
        assert len(plan.summary) <= 400
        assert "CONFIDENCE:" in plan.summary
        assert plan.assumptions

    def test_structured_assumptions_are_not_appended_then_truncated(self):
        pipeline = self._fresh_pipeline(
            {
                "text": "Commander review should retain validated facts.",
                "generation_method": "llm",
                "content_safety_result": "passed",
                "content_safety_validation_method": "azure_ai",
            }
        )
        long_warning = "URGENT DATA WARNING " + ("detail " * 500)
        original_zones = pipeline._stage_3_compute_zones

        def empty_zones(*args):
            zones = original_zones(*args)
            zones[0].population_estimate = 0
            zones[0].vulnerable_population = 0
            return zones

        pipeline._stage_3_compute_zones = empty_zones
        original_summary = pipeline._stage_8_plan_summary

        def summary_with_warning(*args):
            args[-1].append(long_warning)
            return original_summary(*args)

        pipeline._stage_8_plan_summary = summary_with_warning

        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-summary-assumptions"))

        assert plan is not None
        assert long_warning in plan.assumptions
        assert "URGENT DATA WARNING" in plan.summary
        assert "CONFIDENCE:" in plan.summary

    def test_persisted_plan_and_final_audit_reconcile_every_zone(self):
        pipeline = _make_pipeline()
        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-dispositions"))
        assert plan is not None
        assert len(plan.zone_dispositions) == len(plan.zones)
        assert len({item.zone_number for item in plan.zone_dispositions}) == len(plan.zones)
        assert sum(item.affected_population for item in plan.zone_dispositions) == plan.total_population
        assert (
            sum(route.allocated_population for route in plan.routes)
            + sum(zone.unallocated_route_population for zone in plan.zones)
            == plan.total_population
        )
        route_ids = {route.route_id for route in plan.routes}
        assert all(set(load.route_ids).issubset(route_ids) for load in plan.corridor_loads)
        assert all(
            route.congestion_risk_pct == min(100, round(route.uncapped_utilisation_pct)) for route in plan.routes
        )
        assert all(
            item.evacuating_population + item.remaining_population == item.affected_population
            for item in plan.zone_dispositions
        )
        if any(phase.clearance_blocked for phase in plan.phases):
            assert plan.estimated_completion_minutes is None

        final_audit = next(
            entry.record
            for entry in reversed(pipeline.audit_writer._buffer)
            if entry.record.decision_type == DecisionType.plan_generated and entry.record.plan_id == plan.plan_id
        )
        assert final_audit.zone_dispositions == plan.zone_dispositions
        disposition_audits = [
            entry.record for entry in pipeline.audit_writer._buffer if len(entry.record.zone_dispositions) == 1
        ]
        assert len(disposition_audits) == len(plan.zones)
        assert {audit.zone_dispositions[0].zone_number for audit in disposition_audits} == {
            zone.zone_number for zone in plan.zones
        }
