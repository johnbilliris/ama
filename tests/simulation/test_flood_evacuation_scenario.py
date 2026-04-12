"""Simulation test — flood evacuation scenario (T059)."""

import pytest
from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.models import EvacuationPlan
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


def _make_flood_handoff():
    return AgentHandoffEvent(
        handoff_id="hf-flood-sim",
        incident_id="inc-flood-001",
        source_agent="risk_assessment",
        target_agent="evacuation",
        scope_key="live:inc-flood-001",
        confidence=0.75,
        payload={
            "assessmentId": "assess-flood",
            "recommendationId": "rec-flood",
            "hazard_type": "flood",
            "severity_level": "high",
            "affected_area": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.73, -16.94],
                        [145.79, -16.94],
                        [145.79, -16.89],
                        [145.73, -16.89],
                        [145.73, -16.94],
                    ]
                ],
            },
            "population_estimate": 10000,
            "time_horizon": "48h",
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


class TestFloodEvacuationScenario:
    def test_flood_plan_produced(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan is not None
        assert isinstance(plan, EvacuationPlan)

    def test_flood_plan_id_format(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan.plan_id.startswith("ep-")

    def test_flood_zones_computed(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert len(plan.zones) > 0

    def test_flood_has_summary(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert len(plan.summary) > 0

    def test_flood_mobilisation_time(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        # Flood mobilisation: 120 minutes
        assert plan.mobilisation_time_minutes == 120

    def test_flood_phases_created(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert len(plan.phases) == 5

    def test_flood_traceability(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan.traceability is not None
        assert plan.traceability.source_handoff_id == "hf-flood-sim"

    def test_flood_hazard_summary(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan.hazard_summary is not None
        assert plan.hazard_summary.hazard_type == "flood"

    def test_flood_confidence(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert 0.0 <= plan.confidence_score <= 1.0

    def test_flood_incident_scope_key(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan.incident_scope_key == "live:inc-flood-001"
