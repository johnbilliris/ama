"""Tests for evacuation.models — enums, validators, and serialisation (T012)."""

from datetime import UTC, datetime

import pytest
from evacuation.models import (
    AuditBufferEntry,
    ClosureReason,
    ConfidenceLevel,
    DataSnapshot,
    DecisionType,
    EvacuationDecisionRecord,
    EvacuationPhase,
    EvacuationPlan,
    EvacuationRoute,
    EvacuationZone,
    HazardSourceSnapshot,
    HazardSummary,
    PhaseTransitionTrigger,
    PlanStatus,
    ShelterRequirements,
    Traceability,
    VulnerabilityCategory,
    ZoneDisposition,
    ZoneDispositionType,
    confidence_to_level,
)

# ---------------------------------------------------------------------------
# DecisionType enum
# ---------------------------------------------------------------------------


class TestDecisionType:
    def test_has_exactly_fifteen_values(self):
        assert len(DecisionType) == 15

    def test_all_expected_values_present(self):
        expected = {
            "handoff_received",
            "handoff_rejected",
            "duplicate_discarded",
            "assessment_retrieved",
            "road_network_loaded",
            "zones_computed",
            "routes_computed",
            "transport_coordinated",
            "timeline_estimated",
            "plan_generated",
            "plan_updated",
            "override_applied",
            "shelter_in_place_recommended",
            "degradation_detected",
            "content_safety_failure",
        }
        assert {e.value for e in DecisionType} == expected


# ---------------------------------------------------------------------------
# ConfidenceLevel enum
# ---------------------------------------------------------------------------


class TestConfidenceLevel:
    def test_has_three_values(self):
        assert len(ConfidenceLevel) == 3

    def test_expected_values(self):
        assert {e.value for e in ConfidenceLevel} == {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# PlanStatus enum
# ---------------------------------------------------------------------------


class TestPlanStatus:
    def test_has_seven_values(self):
        assert len(PlanStatus) == 7

    def test_expected_values(self):
        expected = {
            "proposed",
            "approved",
            "rejected",
            "superseded",
            "expired",
            "cancelled",
            "paused",
        }
        assert {e.value for e in PlanStatus} == expected


# ---------------------------------------------------------------------------
# VulnerabilityCategory enum
# ---------------------------------------------------------------------------


class TestVulnerabilityCategory:
    def test_has_four_values(self):
        assert len(VulnerabilityCategory) == 4

    def test_expected_values(self):
        expected = {
            "mobility_impaired",
            "medical_dependent",
            "elderly_aged_care",
            "children_schools_childcare",
        }
        assert {e.value for e in VulnerabilityCategory} == expected


# ---------------------------------------------------------------------------
# ClosureReason enum
# ---------------------------------------------------------------------------


class TestClosureReason:
    def test_has_seven_values(self):
        assert len(ClosureReason) == 7

    def test_expected_values(self):
        expected = {
            "emergency_services_closure",
            "flood_cut",
            "fire_proximity",
            "structural_damage",
            "zone_1_closure",
            "capacity_exhausted",
            "unspecified",
        }
        assert {e.value for e in ClosureReason} == expected


# ---------------------------------------------------------------------------
# confidence_to_level mapping
# ---------------------------------------------------------------------------


class TestConfidenceToLevel:
    @pytest.mark.parametrize(
        "score, expected",
        [
            (0.0, ConfidenceLevel.low),
            (0.39, ConfidenceLevel.low),
            (0.4, ConfidenceLevel.medium),
            (0.5, ConfidenceLevel.medium),
            (0.69, ConfidenceLevel.medium),
            (0.7, ConfidenceLevel.high),
            (0.85, ConfidenceLevel.high),
            (1.0, ConfidenceLevel.high),
        ],
    )
    def test_maps_correctly(self, score, expected):
        assert confidence_to_level(score) == expected

    def test_boundary_below_0_4(self):
        assert confidence_to_level(0.399) == ConfidenceLevel.low

    def test_boundary_at_0_4(self):
        assert confidence_to_level(0.4) == ConfidenceLevel.medium

    def test_boundary_below_0_7(self):
        assert confidence_to_level(0.699) == ConfidenceLevel.medium

    def test_boundary_at_0_7(self):
        assert confidence_to_level(0.7) == ConfidenceLevel.high


# ---------------------------------------------------------------------------
# EvacuationPlan validation
# ---------------------------------------------------------------------------


class TestEvacuationPlan:
    def _minimal(self, **overrides):
        area = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        }
        source = HazardSourceSnapshot(
            assessment_id="assess-001",
            hazard_type="bushfire",
            severity_level="high",
            affected_area=area,
            generated_at=datetime.now(UTC),
            buffer_radius_metres=2_000,
            geometry_sha256="a" * 64,
        )
        defaults = dict(
            plan_id="ep-inc-001-v1",
            incident_id="inc-001",
            affected_area=area,
            hazard_summary=HazardSummary(
                hazard_type="bushfire",
                hazard_types=["bushfire"],
                severity_level="high",
                time_horizon="4h",
                source_assessment_id="assess-001",
                affected_area=area,
                sources=[source],
            ),
            zones=[EvacuationZone(zone_id="1", zone_number=1, boundary=area)],
            phases=[EvacuationPhase(phase_number=1, zone_ids=["1"])],
            zone_dispositions=[
                ZoneDisposition(
                    zone_id="1",
                    zone_number=1,
                    disposition=ZoneDispositionType.shelter_in_place,
                    urgency="immediate",
                    affected_population=0,
                    evacuating_population=0,
                    remaining_population=0,
                    rationale="No movement required",
                )
            ],
            traceability=Traceability(
                source_handoff_id="hf-001",
                risk_assessment_id="assess-001",
                risk_assessment_ids=["assess-001"],
                recommendation_id="rec-001",
                input_data_versions={"config": "config"},
                generation_method="template_fallback",
            ),
            data_snapshot=DataSnapshot(
                road_network_version="road",
                population_data_version="population",
                facility_data_version="facility",
                assembly_area_data_version="assembly",
                hazard_assessment_ids=["assess-001"],
                hazard_geometry_algorithm="per-hazard-aeqd-level-union-v1",
            ),
            summary="Complete plan",
            generation_method="template_fallback",
            configuration_version="config",
            incident_scope_key="live:inc-001",
            simulation=False,
            assumptions=[],
            population_estimate=0,
            total_population=0,
        )
        defaults.update(overrides)
        return EvacuationPlan(**defaults)

    def test_valid_construction(self):
        plan = self._minimal()
        assert plan.plan_id == "ep-inc-001-v1"
        assert plan.incident_id == "inc-001"
        assert plan.version == 1
        assert plan.status == PlanStatus.proposed

    def test_confidence_score_clamped_above_one(self):
        plan = self._minimal(confidence_score=1.5)
        assert plan.confidence_score == 1.0

    def test_confidence_score_clamped_below_zero(self):
        plan = self._minimal(confidence_score=-0.5)
        assert plan.confidence_score == 0.0

    def test_confidence_score_normal_range(self):
        plan = self._minimal(confidence_score=0.75)
        assert plan.confidence_score == 0.75

    def test_version_must_be_gte_one(self):
        with pytest.raises(Exception):
            self._minimal(version=0)

    def test_version_negative_raises(self):
        with pytest.raises(Exception):
            self._minimal(version=-1)

    def test_plan_id_format_valid(self):
        plan = self._minimal(
            plan_id="ep-my-incident-v3",
            incident_id="my-incident",
            version=3,
            incident_scope_key="live:my-incident",
            source_plan_id="ep-my-incident-v2",
            change_summary="Updated test plan",
        )
        assert plan.plan_id == "ep-my-incident-v3"

    def test_plan_id_invalid_format_raises(self):
        with pytest.raises(Exception):
            self._minimal(plan_id="bad-format")

    def test_plan_id_missing_prefix_raises(self):
        with pytest.raises(Exception):
            self._minimal(plan_id="plan-inc-v1")

    def test_plan_id_missing_version_suffix_raises(self):
        with pytest.raises(Exception):
            self._minimal(plan_id="ep-inc-001")

    def test_confidence_level_auto_derived_low(self):
        plan = self._minimal(confidence_score=0.2)
        assert plan.confidence_level == ConfidenceLevel.low

    def test_confidence_level_auto_derived_medium(self):
        plan = self._minimal(confidence_score=0.5)
        assert plan.confidence_level == ConfidenceLevel.medium

    def test_confidence_level_auto_derived_high(self):
        plan = self._minimal(confidence_score=0.8)
        assert plan.confidence_level == ConfidenceLevel.high

    def test_optional_lists_default_empty(self):
        plan = self._minimal()
        assert plan.routes == []
        assert plan.assembly_areas == []
        assert plan.transport_requirements == []
        assert plan.overrides == []
        assert plan.shelter_in_place_zones == []

    def test_timestamps_populated(self):
        plan = self._minimal()
        assert plan.created_at is not None
        assert plan.updated_at is not None

    def test_valid_until_requires_timezone(self):
        from datetime import datetime

        with pytest.raises(ValueError, match="timezone-aware"):
            self._minimal(valid_until=datetime(2026, 1, 1))


class TestZoneDisposition:
    def test_partial_evacuation_reconciles_population(self):
        disposition = ZoneDisposition(
            zone_id="1",
            zone_number=1,
            disposition=ZoneDispositionType.partial_evacuation,
            urgency="critical",
            affected_population=100,
            evacuating_population=60,
            remaining_population=40,
            prerequisites=["Keep the route open"],
            shelter_requirements=ShelterRequirements(
                building=["Use a structurally sound building"],
                supplies=["Maintain water and medication"],
                communication=["Monitor emergency services updates"],
            ),
            rationale="Only 60 residents can clear before impact",
        )
        assert disposition.evacuating_population + disposition.remaining_population == 100

    def test_population_mismatch_is_rejected(self):
        with pytest.raises(ValueError, match="must reconcile"):
            ZoneDisposition(
                zone_id="1",
                zone_number=1,
                disposition=ZoneDispositionType.partial_evacuation,
                urgency="critical",
                affected_population=100,
                evacuating_population=60,
                remaining_population=30,
                rationale="Invalid population split",
            )

    def test_blocked_phase_has_no_finite_clearance_duration(self):
        phase = EvacuationPhase(
            phase_number=1,
            zone_ids=["1"],
            duration_minutes=None,
            population_moved=0,
            population_remaining=100,
            clearance_blocked=True,
        )
        assert phase.duration_minutes is None
        assert phase.population_remaining == 100

    def test_phase_derives_completion_and_reconciles_population(self):
        phase = EvacuationPhase(
            phase_number=1,
            start_offset_minutes=10,
            duration_minutes=20,
            population_moved=60,
            population_remaining=40,
            selected_transition_offset_minutes=20,
            selected_transition_trigger=PhaseTransitionTrigger.population_threshold,
        )

        assert phase.estimated_population == 100
        assert phase.completion_offset_minutes == 30

    def test_phase_rejects_transition_before_start(self):
        with pytest.raises(ValueError, match="cannot precede"):
            EvacuationPhase(
                phase_number=1,
                start_offset_minutes=10,
                duration_minutes=20,
                selected_transition_offset_minutes=9,
            )


class TestEvacuationZone:
    def test_vulnerable_population_cannot_exceed_population(self):
        with pytest.raises(ValueError, match="cannot exceed"):
            EvacuationZone(
                zone_number=1,
                population_estimate=10,
                vulnerable_population=11,
            )


class TestEvacuationRoute:
    def test_legacy_fields_populate_canonical_route_contract(self):
        route = EvacuationRoute(
            route_id="route-1",
            zone_id="2",
            assembly_area_id="aa-1",
            route_name="Legacy route",
            distance_km=12.5,
            estimated_travel_minutes=25,
            waypoints=["edge-1", "edge-2"],
        )

        document = route.model_dump(mode="json")
        assert document["origin_zone"] == 2
        assert document["destination_assembly_area"] == "aa-1"
        assert document["total_distance_km"] == 12.5
        assert document["estimated_travel_time_loaded_min"] == 25.0
        assert document["path"] == ["edge-1", "edge-2"]
        assert document["vehicle_suitability"] == {
            "standard": True,
            "heavy": True,
            "accessible": False,
        }

    def test_conflicting_aliases_are_rejected(self):
        with pytest.raises(ValueError, match="path and waypoints"):
            EvacuationRoute(
                route_id="route-1",
                zone_id="1",
                assembly_area_id="aa-1",
                route_name="Conflicting route",
                waypoints=["edge-1"],
                path=["edge-2"],
            )

    def test_origin_nodes_must_be_unique(self):
        with pytest.raises(ValueError, match="must be unique"):
            EvacuationZone(
                zone_number=1,
                origin_node_ids=["node-1", "node-1"],
            )


# ---------------------------------------------------------------------------
# EvacuationDecisionRecord serialisation/deserialisation
# ---------------------------------------------------------------------------


class TestEvacuationDecisionRecord:
    @staticmethod
    def _record(**overrides):
        values = {
            "handoff_id": "hf-1",
            "operation_id": "hf-1",
            "incident_id": "inc-1",
            "decision_type": DecisionType.handoff_received,
            "decision_rationale": "Canonical decision",
            "agent_version": "0.1.0",
            "configuration_version": "config",
            "incident_scope_key": "tenant-a:inc-1",
            "tenant_id": "tenant-a",
        }
        values.update(overrides)
        return EvacuationDecisionRecord(**values)

    def test_required_fields(self):
        record = self._record()
        assert record.handoff_id == "hf-1"
        assert record.decision_type == DecisionType.handoff_received

    def test_confidence_clamped_above_one(self):
        record = self._record(
            handoff_id="hf-2",
            operation_id="hf-2",
            decision_type=DecisionType.plan_generated,
            plan_id="ep-inc-1-v1",
            version=1,
            routes_count=0,
            transport_requests_count=0,
            confidence_raw=1.5,
            confidence_adjusted=2.0,
        )
        assert record.confidence_raw == 1.0
        assert record.confidence_adjusted == 1.0

    def test_confidence_clamped_below_zero(self):
        record = self._record(
            handoff_id="hf-3",
            operation_id="hf-3",
            decision_type=DecisionType.plan_generated,
            plan_id="ep-inc-1-v1",
            version=1,
            routes_count=0,
            transport_requests_count=0,
            confidence_raw=-0.5,
            confidence_adjusted=-1.0,
        )
        assert record.confidence_raw == 0.0
        assert record.confidence_adjusted == 0.0

    def test_default_values(self):
        record = self._record(handoff_id="hf-4", operation_id="hf-4")
        assert record.zone_ids == []
        assert record.route_ids == []
        assert record.escalation_targets == []
        assert record.confidence_raw == 0.0
        assert record.confidence_adjusted == 0.0
        assert record.agent_version == "0.1.0"
        assert record.prompt_template_version == "1.0"
        assert record.generation_method == "llm"
        assert record.tenant_id == "tenant-a"

    def test_serialisation_round_trip(self):
        record = self._record(
            handoff_id="hf-rt",
            operation_id="hf-rt",
            decision_type=DecisionType.routes_computed,
            plan_id="ep-inc-1-v1",
            version=1,
            incident_id="inc-1",
            hazard_type="cyclone",
            zone_ids=["1", "2"],
            route_ids=["r-1"],
            population_affected=5000,
            confidence_raw=0.85,
            decision_rationale="Routes computed successfully",
            routes_count=1,
        )
        data = record.model_dump(mode="json")
        restored = EvacuationDecisionRecord.model_validate(data)
        assert restored.handoff_id == "hf-rt"
        assert restored.decision_type == DecisionType.routes_computed
        assert restored.zone_ids == ["1", "2"]
        assert restored.confidence_raw == 0.85

    def test_missing_handoff_id_raises(self):
        with pytest.raises(Exception):
            EvacuationDecisionRecord(
                decision_type=DecisionType.handoff_received,
            )

    def test_missing_decision_type_raises(self):
        with pytest.raises(Exception):
            EvacuationDecisionRecord(handoff_id="hf-5")

    def test_id_auto_generated(self):
        r1 = self._record(handoff_id="hf-a", operation_id="hf-a")
        r2 = self._record(handoff_id="hf-b", operation_id="hf-b")
        assert r1.id != r2.id  # UUIDs should be unique


# ---------------------------------------------------------------------------
# AuditBufferEntry
# ---------------------------------------------------------------------------


class TestAuditBufferEntry:
    def test_wraps_record(self):
        record = TestEvacuationDecisionRecord._record(
            handoff_id="hf-6",
            operation_id="hf-6",
        )
        entry = AuditBufferEntry(record=record)
        assert entry.record.handoff_id == "hf-6"
        assert entry.retry_count == 0
        assert entry.last_retry_at is None
        assert entry.buffered_at is not None

    def test_serialisation(self):
        record = TestEvacuationDecisionRecord._record(
            handoff_id="hf-7",
            operation_id="hf-7",
            decision_type=DecisionType.degradation_detected,
        )
        entry = AuditBufferEntry(record=record)
        data = entry.model_dump(mode="json")
        restored = AuditBufferEntry.model_validate(data)
        assert restored.record.handoff_id == "hf-7"
        assert restored.retry_count == 0
