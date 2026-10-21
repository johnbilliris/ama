"""Contract tests for EvacuationPlan output schema (T023)."""

import re
from datetime import UTC, datetime

import pytest
from evacuation.models import (
    ConfidenceLevel,
    DataSnapshot,
    EvacuationPhase,
    EvacuationPlan,
    EvacuationRoute,
    EvacuationZone,
    HazardSourceSnapshot,
    HazardSummary,
    PlanStatus,
    Traceability,
    ZoneDisposition,
    ZoneDispositionType,
)


def _make_plan(**overrides):
    generated_at = datetime.now(UTC)
    hazard_area = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    hazard_source = HazardSourceSnapshot(
        assessment_id="assess-001",
        hazard_type="bushfire",
        severity_level="high",
        affected_area=hazard_area,
        input_signal_ids=["signal-001"],
        generated_at=generated_at,
        buffer_radius_metres=2_000,
        geometry_sha256="a" * 64,
    )
    defaults = dict(
        plan_id="ep-inc-001-v1",
        incident_id="inc-001",
        version=1,
        status=PlanStatus.proposed,
        confidence_score=0.85,
        affected_area=hazard_area,
        hazard_summary=HazardSummary(
            hazard_type="bushfire",
            hazard_types=["bushfire"],
            severity_level="high",
            time_horizon="4h",
            source_assessment_id="assess-001",
            affected_area=hazard_area,
            sources=[hazard_source],
        ),
        zones=[
            EvacuationZone(
                zone_id="1",
                zone_number=1,
                boundary=hazard_area,
            )
        ],
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
                rationale="No population movement required",
            )
        ],
        traceability=Traceability(
            source_handoff_id="hf-001",
            risk_assessment_id="assess-001",
            risk_assessment_ids=["assess-001"],
            recommendation_id="rec-001",
            input_signal_ids=["signal-001"],
            input_data_versions={"config": "cfg123"},
            generation_method="template_fallback",
        ),
        data_snapshot=DataSnapshot(
            road_network_version="abc123",
            population_data_version="pop123",
            facility_data_version="fac123",
            assembly_area_data_version="aa123",
            hazard_assessment_ids=["assess-001"],
            hazard_geometry_algorithm="per-hazard-aeqd-level-union-v1",
        ),
        generation_method="template_fallback",
        configuration_version="cfg123",
        summary="Test plan summary",
        incident_scope_key="live:inc-001",
        tenant_id="live",
        simulation=False,
        population_estimate=0,
        total_population=0,
    )
    defaults.update(overrides)
    return EvacuationPlan(**defaults)


# ---------------------------------------------------------------------------
# EvacuationPlan has all required sections
# ---------------------------------------------------------------------------


class TestPlanRequiredSections:
    def test_plan_has_plan_id(self):
        plan = _make_plan()
        assert plan.plan_id is not None

    def test_plan_has_incident_id(self):
        plan = _make_plan()
        assert plan.incident_id == "inc-001"

    def test_plan_has_version(self):
        plan = _make_plan()
        assert plan.version >= 1

    def test_plan_has_status(self):
        plan = _make_plan()
        assert plan.status == PlanStatus.proposed

    def test_plan_has_confidence_score(self):
        plan = _make_plan()
        assert 0.0 <= plan.confidence_score <= 1.0

    def test_plan_has_confidence_level(self):
        plan = _make_plan()
        assert plan.confidence_level in list(ConfidenceLevel)

    def test_plan_has_hazard_summary(self):
        plan = _make_plan()
        assert plan.hazard_summary is not None
        assert plan.hazard_summary.hazard_type == "bushfire"

    def test_plan_has_traceability(self):
        plan = _make_plan()
        assert plan.traceability is not None
        assert plan.traceability.source_handoff_id == "hf-001"

    def test_plan_has_data_snapshot(self):
        plan = _make_plan()
        assert plan.data_snapshot is not None

    def test_plan_has_summary(self):
        plan = _make_plan()
        assert len(plan.summary) > 0

    def test_plan_has_timestamps(self):
        plan = _make_plan()
        assert plan.created_at is not None
        assert plan.updated_at is not None

    def test_plan_lists_initialised(self):
        plan = _make_plan()
        assert isinstance(plan.zones, list)
        assert isinstance(plan.routes, list)
        assert isinstance(plan.assembly_areas, list)
        assert isinstance(plan.phases, list)
        assert isinstance(plan.transport_requirements, list)
        assert isinstance(plan.overrides, list)
        assert isinstance(plan.shelter_in_place_zones, list)


# ---------------------------------------------------------------------------
# plan_id format validation
# ---------------------------------------------------------------------------


class TestPlanIdFormat:
    def test_plan_id_matches_pattern(self):
        plan = _make_plan()
        assert re.match(r"^ep-.+-v\d+$", plan.plan_id)

    def test_various_valid_plan_ids(self):
        valid_ids = [
            "ep-inc-001-v1",
            "ep-qld-fire-2025-v42",
            "ep-abc-v1",
            "ep-x-v999",
        ]
        for pid in valid_ids:
            incident_id, version = pid[3:].rsplit("-v", 1)
            plan = _make_plan(
                plan_id=pid,
                incident_id=incident_id,
                version=int(version),
                incident_scope_key=f"live:{incident_id}",
                source_plan_id=(f"ep-{incident_id}-v{int(version) - 1}" if int(version) > 1 else None),
                change_summary=("Updated plan" if int(version) > 1 else None),
            )
            assert re.match(r"^ep-.+-v\d+$", plan.plan_id)

    def test_invalid_plan_id_rejected(self):
        invalid_ids = [
            "bad-format",
            "ep-v1",  # missing incident_id
            "plan-inc-001-v1",  # wrong prefix
        ]
        for pid in invalid_ids:
            with pytest.raises(Exception):
                _make_plan(plan_id=pid)

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"plan_id": "ep-other-v1"}, "incident"),
            ({"plan_id": "ep-inc-001-v2"}, "version"),
            ({"incident_scope_key": "other:inc-001"}, "tenant"),
            ({"incident_scope_key": "live:other"}, "incident"),
        ],
    )
    def test_inconsistent_plan_identity_rejected(self, overrides, message):
        with pytest.raises(Exception, match=message):
            _make_plan(**overrides)


class TestCompleteEnvelope:
    @pytest.mark.parametrize(
        "overrides",
        [
            {"affected_area": {}},
            {"hazard_summary": None},
            {"zones": []},
            {"phases": []},
            {"zone_dispositions": []},
            {"traceability": None},
            {"data_snapshot": None},
            {"summary": ""},
            {"generation_method": ""},
            {"configuration_version": ""},
            {"incident_scope_key": ""},
        ],
    )
    def test_missing_safety_envelope_section_rejected(self, overrides):
        with pytest.raises(Exception):
            _make_plan(**overrides)

    def test_simulation_label_must_match_tenant(self):
        with pytest.raises(Exception, match="simulation"):
            _make_plan(simulation=True)

        plan = _make_plan(
            tenant_id="simulation",
            incident_scope_key="simulation:inc-001",
            simulation=True,
        )
        assert plan.simulation is True

    def test_legacy_llm_generation_label_is_rejected(self):
        with pytest.raises(Exception):
            _make_plan(generation_method="llm")

    def test_safety_fallback_requires_failed_evidence_and_review(self):
        with pytest.raises(Exception, match="safety fallback"):
            _make_plan(
                generation_method="safety_fallback",
                traceability=Traceability(
                    source_handoff_id="hf-001",
                    risk_assessment_id="assess-001",
                    risk_assessment_ids=["assess-001"],
                    recommendation_id="rec-001",
                    input_signal_ids=["signal-001"],
                    input_data_versions={"config": "cfg123"},
                    generation_method="safety_fallback",
                ),
            )


# ---------------------------------------------------------------------------
# Traceability references
# ---------------------------------------------------------------------------


class TestTraceabilityReferences:
    def test_source_handoff_id(self):
        plan = _make_plan()
        assert plan.traceability.source_handoff_id == "hf-001"

    def test_risk_assessment_id(self):
        plan = _make_plan()
        assert plan.traceability.risk_assessment_id == "assess-001"

    def test_prompt_template_version(self):
        plan = _make_plan()
        assert plan.traceability.prompt_template_version == "1.0"

    def test_generation_method(self):
        plan = _make_plan()
        assert plan.traceability.generation_method == plan.generation_method

    def test_input_data_versions(self):
        plan = _make_plan(
            traceability=Traceability(
                source_handoff_id="hf-1",
                risk_assessment_id="assess-001",
                risk_assessment_ids=["assess-001"],
                recommendation_id="rec-001",
                input_signal_ids=["signal-001"],
                input_data_versions={
                    "road_network": "v1.0",
                    "config": "cfg123",
                },
                generation_method="template_fallback",
            )
        )
        assert plan.traceability.input_data_versions["road_network"] == "v1.0"


# ---------------------------------------------------------------------------
# Serialisation round-trip
# ---------------------------------------------------------------------------


class TestPlanSerialisation:
    def test_model_dump_round_trip(self):
        plan = _make_plan()
        data = plan.model_dump(mode="json")
        restored = EvacuationPlan.model_validate(data)
        assert restored.plan_id == plan.plan_id
        assert restored.incident_id == plan.incident_id
        assert restored.confidence_score == plan.confidence_score

    def test_json_serialisation(self):
        plan = _make_plan()
        json_str = plan.model_dump_json()
        assert "ep-inc-001-v1" in json_str
        assert "bushfire" in json_str

    def test_nonempty_route_serializes_complete_compatible_contract(self):
        route = EvacuationRoute(
            route_id="route-1",
            zone_id="1",
            origin_node_id="node-1",
            assembly_area_id="aa-1",
            route_name="Complete route",
            distance_km=5,
            estimated_travel_minutes=10,
            estimated_travel_time_normal_min=5,
            estimated_travel_time_loaded_min=10,
            waypoints=["edge-1"],
            node_path=["node-1", "node-2"],
            uncapped_utilisation_pct=81.5,
            estimated_utilisation_pct=81.5,
            congestion_risk=True,
            selection_rationale="Computed from connected path and capacity evidence",
        )
        document = _make_plan(routes=[route]).model_dump(mode="json")
        serialized = document["routes"][0]

        required = {
            "path",
            "origin_zone",
            "destination_assembly_area",
            "total_distance_km",
            "estimated_travel_time_normal_min",
            "estimated_travel_time_loaded_min",
            "estimated_utilisation_pct",
            "vehicle_suitability",
            "selection_rationale",
            "waypoints",
            "zone_id",
            "assembly_area_id",
            "distance_km",
            "estimated_travel_minutes",
        }
        assert required.issubset(serialized)
        restored = EvacuationPlan.model_validate(document)
        assert restored.routes[0].path == ["edge-1"]
