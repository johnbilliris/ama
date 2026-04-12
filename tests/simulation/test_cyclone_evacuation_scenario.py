"""Simulation test — cyclone evacuation scenario (T056)."""

import pytest
from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.models import EvacuationPlan
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


def _make_cyclone_handoff():
    return AgentHandoffEvent(
        handoff_id="hf-cyclone-sim",
        incident_id="inc-cyclone-001",
        source_agent="risk_assessment",
        target_agent="evacuation",
        scope_key="live:inc-cyclone-001",
        confidence=0.80,
        payload={
            "assessmentId": "assess-cyclone",
            "recommendationId": "rec-cyclone",
            "hazard_type": "cyclone",
            "severity_level": "high",
            "affected_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.72, -16.96],
                        [145.82, -16.96],
                        [145.82, -16.88],
                        [145.72, -16.88],
                        [145.72, -16.96],
                    ]
                ],
            },
            "population_estimate": 15000,
            "time_horizon": "24h",
        },
    )


@pytest.fixture
def pipeline():
    road_network = RoadNetworkLoader()
    road_network.load(SAMPLE_FILE)
    return EvacuationProcessingPipeline(
        config=EvacuationConfig(),
        road_network=road_network,
    )


class TestCycloneEvacuationScenario:
    def test_cyclone_plan_produced(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert plan is not None
        assert isinstance(plan, EvacuationPlan)

    def test_cyclone_plan_id_format(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert plan.plan_id.startswith("ep-")

    def test_cyclone_zones_computed(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert len(plan.zones) > 0

    def test_cyclone_has_summary(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert len(plan.summary) > 0

    def test_cyclone_mobilisation_time(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        # Cyclone mobilisation: 120 minutes
        assert plan.mobilisation_time_minutes == 120

    def test_cyclone_phases_created(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert len(plan.phases) == 5

    def test_cyclone_traceability(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert plan.traceability is not None
        assert plan.traceability.source_handoff_id == "hf-cyclone-sim"

    def test_cyclone_confidence_score(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert 0.0 <= plan.confidence_score <= 1.0

    def test_cyclone_hazard_summary(self, pipeline):
        plan = pipeline.process_handoff(_make_cyclone_handoff())
        assert plan.hazard_summary is not None
        assert plan.hazard_summary.hazard_type == "cyclone"
