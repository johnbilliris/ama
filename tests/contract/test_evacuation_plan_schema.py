"""Contract tests for EvacuationPlan output schema (T023)."""

import re

import pytest

from evacuation.models import (
    ConfidenceLevel,
    EvacuationPlan,
    HazardSummary,
    PlanStatus,
    Traceability,
    DataSnapshot,
)


def _make_plan(**overrides):
    defaults = dict(
        plan_id="ep-inc-001-v1",
        incident_id="inc-001",
        version=1,
        status=PlanStatus.proposed,
        confidence_score=0.85,
        hazard_summary=HazardSummary(hazard_type="bushfire", severity_level="high"),
        traceability=Traceability(
            source_handoff_id="hf-001",
            risk_assessment_id="assess-001",
        ),
        data_snapshot=DataSnapshot(road_network_version="abc123"),
        summary="Test plan summary",
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
            plan = _make_plan(plan_id=pid)
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
        assert plan.traceability.generation_method == "llm"

    def test_input_data_versions(self):
        plan = _make_plan(
            traceability=Traceability(
                source_handoff_id="hf-1",
                input_data_versions={"road_network": "v1.0"},
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
