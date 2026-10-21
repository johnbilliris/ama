"""Simulation test — flood evacuation scenario (T059)."""

from datetime import UTC, datetime, timedelta

import pytest
from common.handoffs import AgentHandoffEvent
from evacuation.agent import EvacuationAgent
from evacuation.config import EvacuationConfig
from evacuation.models import EvacuationPlan, ZoneDispositionType
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"
FLOOD_AREA = {
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
}


class _Store:
    def __init__(self, documents):
        self.documents = documents

    def read_item(self, item, partition_key):
        document = self.documents[item]
        assert partition_key == document["incident_scope_key"]
        return document


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
            "affected_area": FLOOD_AREA,
            "population_estimate": 10000,
            "time_horizon": "48h",
        },
    )


@pytest.fixture
def pipeline():
    road_network = RoadNetworkLoader(
        now=lambda: datetime(2026, 4, 16, 1, tzinfo=UTC),
    )
    road_network.load(SAMPLE_FILE)
    generated_at = datetime.now(UTC)
    scope_key = "live:inc-flood-001"
    recommendation = {
        "recommendation_id": "rec-flood",
        "incident_id": "inc-flood-001",
        "type": "evacuation",
        "summary": "Evacuate flood-affected communities",
        "explanation": "Flood depth and route-risk thresholds are exceeded",
        "required_approval_level": "incident_commander",
        "assessment_id": "assess-flood",
        "confidence_score": 0.75,
        "severity_level": "high",
        "incident_scope_key": scope_key,
        "tenant_id": "live",
    }
    assessment = {
        "hazard_assessment_id": "assess-flood",
        "incident_id": "inc-flood-001",
        "assessment_type": "route_risk",
        "input_signal_ids": ["flood-gauge-001"],
        "summary": "Flood water threatens evacuation corridors",
        "confidence_level": "high",
        "generated_at": generated_at.isoformat(),
        "valid_until": (generated_at + timedelta(hours=48)).isoformat(),
        "status": "active",
        "incident_scope_key": scope_key,
        "tenant_id": "live",
        "hazard_map": {
            "affected_area": FLOOD_AREA,
            "severity_level": "high",
            "hazard_type": "flood",
            "confidence_score": 0.75,
            "time_horizon": "48h",
            "population_estimate": 10000,
        },
    }
    return EvacuationProcessingPipeline(
        config=EvacuationConfig(),
        road_network=road_network,
        cosmos_assessments_container=_Store({"assess-flood": assessment}),
        cosmos_recommendations_container=_Store({"rec-flood": recommendation}),
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

    def test_flood_dispositions_reconcile_every_zone(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        assert len(plan.zone_dispositions) == len(plan.zones)
        assert sum(disposition.affected_population for disposition in plan.zone_dispositions) == plan.total_population
        assert all(
            disposition.evacuating_population + disposition.remaining_population == disposition.affected_population
            for disposition in plan.zone_dispositions
        )

    def test_flood_blocked_and_deficit_populations_remain_explicit(self, pipeline):
        plan = pipeline.process_handoff(_make_flood_handoff())
        incomplete = [
            disposition
            for disposition in plan.zone_dispositions
            if disposition.disposition != ZoneDispositionType.evacuation
        ]
        assert incomplete
        assert all(disposition.remaining_population > 0 for disposition in incomplete)
        if any(phase.clearance_blocked for phase in plan.phases):
            assert plan.estimated_completion_minutes is None
        assert plan.confidence_score < 0.75 * 0.8

    def test_flood_used_road_closure_creates_safe_linked_version(self, pipeline):
        from tests.unit.test_evacuation_endpoints import _FakePlansStore

        initial = pipeline.process_handoff(_make_flood_handoff())
        assert initial is not None
        used_route = next(route for route in initial.routes if route.waypoints)
        closed_edge = used_route.waypoints[0]
        source = initial.model_dump(mode="json")
        source.update({"id": initial.plan_id, "_etag": "source-v1"})
        store = _FakePlansStore()
        store.docs = {
            initial.plan_id: source,
            "inc-flood-001_plan_counter": {
                "id": "inc-flood-001_plan_counter",
                "current_version": 1,
                "incident_scope_key": initial.incident_scope_key,
                "_etag": "counter-v1",
            },
        }
        agent = EvacuationAgent(
            config=EvacuationConfig(),
            road_network=pipeline._road_network,
            cosmos_plans_container=store,
        )
        result = agent.process_replan(
            incident_id=initial.incident_id,
            current_plan=source,
            new_road_closures=[closed_edge],
        )
        assert result["new_plan_id"] == "ep-inc-flood-001-v2"
        replanned = store.docs[result["new_plan_id"]]
        assert replanned["source_plan_id"] == initial.plan_id
        assert all(closed_edge not in route["waypoints"] for route in replanned["routes"])
        assert store.docs[initial.plan_id]["routes"] == source["routes"]
