"""Contract tests for evacuation reproducibility (T046)."""


from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


def _make_handoff(handoff_id="hf-repro", incident_id="inc-repro"):
    return AgentHandoffEvent(
        handoff_id=handoff_id,
        incident_id=incident_id,
        source_agent="risk_assessment",
        target_agent="evacuation",
        scope_key=f"live:{incident_id}",
        confidence=0.85,
        payload={
            "assessmentId": "assess-repro",
            "recommendationId": "rec-repro",
            "hazard_type": "bushfire",
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


def _make_pipeline():
    road_network = RoadNetworkLoader()
    road_network.load(SAMPLE_FILE)
    return EvacuationProcessingPipeline(
        config=EvacuationConfig(),
        road_network=road_network,
    )


# ---------------------------------------------------------------------------
# Identical inputs produce identical routes
# ---------------------------------------------------------------------------


class TestReproducibility:
    def test_identical_inputs_produce_identical_routes(self):
        """Two pipeline runs with identical inputs should produce identical route sets."""
        pipeline1 = _make_pipeline()
        pipeline2 = _make_pipeline()

        plan1 = pipeline1.process_handoff(_make_handoff(handoff_id="hf-repro-1"))
        plan2 = pipeline2.process_handoff(_make_handoff(handoff_id="hf-repro-2"))

        assert plan1 is not None
        assert plan2 is not None

        # Route count must match
        assert len(plan1.routes) == len(plan2.routes)

        # Route distances and travel times must match
        distances_1 = sorted(r.distance_km for r in plan1.routes)
        distances_2 = sorted(r.distance_km for r in plan2.routes)
        assert distances_1 == distances_2

        travel_1 = sorted(r.estimated_travel_minutes for r in plan1.routes)
        travel_2 = sorted(r.estimated_travel_minutes for r in plan2.routes)
        assert travel_1 == travel_2

    def test_zone_computation_deterministic(self):
        """Zone computation should produce identical results for same inputs."""
        pipeline1 = _make_pipeline()
        pipeline2 = _make_pipeline()

        plan1 = pipeline1.process_handoff(_make_handoff(handoff_id="hf-z1"))
        plan2 = pipeline2.process_handoff(_make_handoff(handoff_id="hf-z2"))

        assert plan1 is not None
        assert plan2 is not None

        # Same number of zones with same populations
        assert len(plan1.zones) == len(plan2.zones)
        pops_1 = sorted(z.population_estimate for z in plan1.zones)
        pops_2 = sorted(z.population_estimate for z in plan2.zones)
        assert pops_1 == pops_2


# ---------------------------------------------------------------------------
# Configuration version captured
# ---------------------------------------------------------------------------


class TestConfigurationVersionCaptured:
    def test_data_snapshot_includes_road_network_version(self):
        pipeline = _make_pipeline()
        plan = pipeline.process_handoff(_make_handoff(handoff_id="hf-cfg-1"))
        assert plan is not None
        assert plan.data_snapshot is not None
        assert plan.data_snapshot.road_network_version != ""

    def test_config_hash_is_deterministic(self):
        cfg = EvacuationConfig()
        h1 = cfg.compute_config_hash()
        h2 = cfg.compute_config_hash()
        assert h1 == h2
