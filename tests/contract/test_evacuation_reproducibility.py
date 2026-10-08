"""Contract tests for evacuation reproducibility (T046)."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"
AREA = {
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
}


class _UpstreamStore:
    def __init__(self, document):
        self.document = document

    def read_item(self, item, partition_key):
        assert item in {"assess-repro", "rec-repro"}
        assert partition_key == self.document["incident_scope_key"]
        return self.document


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
            "affected_area": AREA,
            "population_estimate": 5000,
        },
    )


def _make_pipeline(
    *,
    config=None,
    population_data=None,
    facility_data=None,
):
    road_network = RoadNetworkLoader(
        now=lambda: datetime(2026, 4, 16, 1, tzinfo=UTC),
    )
    road_network.load(SAMPLE_FILE)
    generated_at = datetime.now(UTC)
    recommendation = {
        "recommendation_id": "rec-repro",
        "incident_id": "inc-repro",
        "type": "evacuation",
        "summary": "Evacuate affected communities",
        "explanation": "Route-risk threshold exceeded",
        "required_approval_level": "incident_commander",
        "assessment_id": "assess-repro",
        "confidence_score": 0.85,
        "severity_level": "high",
        "incident_scope_key": "live:inc-repro",
        "tenant_id": "live",
    }
    assessment = {
        "hazard_assessment_id": "assess-repro",
        "incident_id": "inc-repro",
        "assessment_type": "route_risk",
        "input_signal_ids": ["signal-repro"],
        "summary": "Bushfire threatens evacuation corridors",
        "confidence_level": "high",
        "generated_at": generated_at.isoformat(),
        "valid_until": (generated_at + timedelta(hours=4)).isoformat(),
        "status": "active",
        "incident_scope_key": "live:inc-repro",
        "tenant_id": "live",
        "hazard_map": {
            "affected_area": AREA,
            "severity_level": "high",
            "hazard_type": "bushfire",
            "confidence_score": 0.85,
            "time_horizon": "4h",
            "population_estimate": 5000,
        },
    }
    return EvacuationProcessingPipeline(
        config=config or EvacuationConfig(),
        road_network=road_network,
        cosmos_assessments_container=_UpstreamStore(assessment),
        cosmos_recommendations_container=_UpstreamStore(recommendation),
        population_data=population_data,
        facility_data=facility_data,
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

        assert plan1.deterministic_replay_projection() == plan2.deterministic_replay_projection()

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

    def test_reordered_reference_inputs_produce_exact_same_plan(self):
        population_data = [
            {
                "area_id": "west",
                "boundary": AREA,
                "population_estimate": 2_000,
                "vulnerable_population_estimate": 300,
            },
            {
                "area_id": "east",
                "boundary": AREA,
                "population_estimate": 3_000,
                "vulnerable_population_estimate": 450,
            },
        ]
        facility_data = [
            {
                "facility_id": "clinic-a",
                "name": "Clinic A",
                "vulnerability_category": "medical_dependent",
                "capacity": 8,
                "coordinates": {"lat": -16.925, "lng": 145.775},
            },
            {
                "facility_id": "school-b",
                "name": "School B",
                "vulnerability_category": "children_schools_childcare",
                "capacity": 40,
                "coordinates": {"lat": -16.93, "lng": 145.77},
            },
        ]
        first = _make_pipeline(
            population_data=population_data,
            facility_data=facility_data,
        ).process_handoff(_make_handoff(handoff_id="hf-order-1"))
        second = _make_pipeline(
            population_data=list(reversed(population_data)),
            facility_data=list(reversed(facility_data)),
        ).process_handoff(_make_handoff(handoff_id="hf-order-2"))

        assert first is not None
        assert second is not None
        assert first.phases
        assert first.transport_requirements
        assert first.deterministic_replay_projection() == second.deterministic_replay_projection()

    def test_fresh_processes_ignore_python_hash_seed(self):
        script = """
import json
import runpy
namespace = runpy.run_path('tests/contract/test_evacuation_reproducibility.py')
plan = namespace['_make_pipeline']().process_handoff(
    namespace['_make_handoff'](handoff_id='hf-process')
)
print(json.dumps(plan.deterministic_replay_projection(), sort_keys=True))
"""
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            [
                str(Path.cwd() / "apps" / "agents"),
                environment.get("PYTHONPATH", ""),
            ]
        )

        outputs = []
        for seed in ("1", "8675309"):
            environment["PYTHONHASHSEED"] = seed
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            outputs.append(json.loads(result.stdout))

        assert outputs[0] == outputs[1]


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

    def test_semantic_reference_versions_are_order_independent_and_material(self):
        original = [{"id": "a", "population": 10}, {"id": "b", "population": 20}]
        reordered = list(reversed(original))
        changed = [{"id": "a", "population": 11}, {"id": "b", "population": 20}]

        assert EvacuationProcessingPipeline._semantic_collection_version(
            original
        ) == EvacuationProcessingPipeline._semantic_collection_version(reordered)
        assert EvacuationProcessingPipeline._semantic_collection_version(
            original
        ) != EvacuationProcessingPipeline._semantic_collection_version(changed)

    def test_material_config_change_changes_exact_projection(self):
        baseline = _make_pipeline().process_handoff(_make_handoff(handoff_id="hf-config-1"))
        changed = _make_pipeline(
            config=EvacuationConfig(loaded_route_speed_kmh=25),
        ).process_handoff(_make_handoff(handoff_id="hf-config-2"))

        assert baseline is not None
        assert changed is not None
        assert baseline.deterministic_replay_projection() != changed.deterministic_replay_projection()

    def test_same_count_population_and_facility_changes_update_versions(self):
        population = [
            {
                "area_id": "population-1",
                "boundary": AREA,
                "population_estimate": 100,
            }
        ]
        facility = [
            {
                "facility_id": "facility-1",
                "name": "Clinic",
                "vulnerability_category": "medical_dependent",
                "capacity": 8,
                "coordinates": {"lat": -16.925, "lng": 145.775},
            }
        ]
        changed_population = [{**population[0], "population_estimate": 101}]
        changed_facility = [{**facility[0], "capacity": 9}]

        baseline = _make_pipeline(
            population_data=population,
            facility_data=facility,
        ).process_handoff(_make_handoff(handoff_id="hf-data-1"))
        changed = _make_pipeline(
            population_data=changed_population,
            facility_data=changed_facility,
        ).process_handoff(_make_handoff(handoff_id="hf-data-2"))

        assert baseline is not None and baseline.data_snapshot is not None
        assert changed is not None and changed.data_snapshot is not None
        assert baseline.data_snapshot.population_record_count == 1
        assert changed.data_snapshot.population_record_count == 1
        assert baseline.data_snapshot.population_data_version != changed.data_snapshot.population_data_version
        assert baseline.data_snapshot.facility_record_count == 1
        assert changed.data_snapshot.facility_record_count == 1
        assert baseline.data_snapshot.facility_data_version != changed.data_snapshot.facility_data_version

    def test_unavailable_and_verified_empty_reference_data_are_distinct(self):
        unavailable = _make_pipeline().process_handoff(_make_handoff(handoff_id="hf-unavailable"))
        verified_empty = _make_pipeline(
            population_data=[],
            facility_data=[],
        ).process_handoff(_make_handoff(handoff_id="hf-empty"))

        assert unavailable is not None and unavailable.data_snapshot is not None
        assert verified_empty is not None and verified_empty.data_snapshot is not None
        assert unavailable.data_snapshot.population_data_available is False
        assert unavailable.data_snapshot.facility_data_available is False
        assert verified_empty.data_snapshot.population_data_available is True
        assert verified_empty.data_snapshot.facility_data_available is True

    def test_secret_only_configuration_changes_do_not_change_version(self):
        first = EvacuationConfig(
            azure_cosmos_key="cosmos-secret-a",
            azure_servicebus_connection="service-bus-secret-a",
        )
        second = EvacuationConfig(
            azure_cosmos_key="cosmos-secret-b",
            azure_servicebus_connection="service-bus-secret-b",
        )

        assert first.compute_config_hash() == second.compute_config_hash()
        assert "secret" not in first.compute_config_hash()

    def test_same_count_assembly_change_updates_content_version(self):
        road_network = RoadNetworkLoader()
        road_network.load(SAMPLE_FILE)
        original = road_network.get_assembly_areas()
        changed = [area.model_dump(mode="json") for area in original]
        changed[0]["capacity_persons"] += 1

        assert len(original) == len(changed)
        assert EvacuationProcessingPipeline._semantic_collection_version(
            original
        ) != EvacuationProcessingPipeline._semantic_collection_version(changed)

    def test_config_hash_is_deterministic(self):
        cfg = EvacuationConfig()
        h1 = cfg.compute_config_hash()
        h2 = cfg.compute_config_hash()
        assert h1 == h2

    def test_plan_persists_complete_replay_provenance_and_simulation_label(self):
        handoff = _make_handoff(handoff_id="hf-provenance")
        handoff.tenant_id = "simulation"
        handoff.scope_key = "simulation:inc-repro"
        pipeline = _make_pipeline()
        pipeline._cosmos_assessments.document["tenant_id"] = "simulation"
        pipeline._cosmos_assessments.document["incident_scope_key"] = handoff.scope_key
        pipeline._cosmos_recommendations.document["tenant_id"] = "simulation"
        pipeline._cosmos_recommendations.document["incident_scope_key"] = handoff.scope_key

        plan = pipeline.process_handoff(handoff)

        assert plan is not None
        assert plan.simulation is True
        assert plan.generation_method == "template_fallback"
        assert plan.configuration_version
        assert plan.hazard_summary is not None
        assert plan.hazard_summary.time_horizon == "4h"
        assert plan.traceability is not None
        assert plan.traceability.recommendation_id == "rec-repro"
        assert plan.traceability.input_signal_ids == ["signal-repro"]
        assert plan.data_snapshot is not None
        assert plan.data_snapshot.assembly_area_record_count == 5
        assert plan.data_snapshot.assembly_area_record_ids
        assert plan.data_snapshot.population_data_available is False
        assert plan.data_snapshot.facility_data_available is False
        assert plan.valid_until == plan.hazard_summary.sources[0].valid_until
        assert plan.population_estimate == plan.total_population
        assert plan.assumptions
        assert all(record.record.simulation for record in pipeline.audit_writer._buffer)
