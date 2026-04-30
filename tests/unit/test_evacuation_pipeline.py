"""Tests for evacuation.pipeline — end-to-end pipeline with mocks (T024)."""

from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.models import EvacuationPlan
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

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


def _make_pipeline(road_network=None):
    """Create pipeline with minimal mocks (no Cosmos, no LLM)."""
    if road_network is None:
        road_network = RoadNetworkLoader()
        road_network.load(SAMPLE_FILE)
    return EvacuationProcessingPipeline(
        config=EvacuationConfig(),
        road_network=road_network,
        cosmos_plans_container=None,
        cosmos_decisions_container=None,
        cosmos_assessments_container=None,
    )


# ---------------------------------------------------------------------------
# End-to-end pipeline with mocks
# ---------------------------------------------------------------------------


class TestEndToEndPipeline:
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
