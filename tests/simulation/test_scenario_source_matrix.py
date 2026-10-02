from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from apps.ingestion.simulation.scenario_source_matrix import activated_sources_for_scenario
from apps.ingestion.simulation.simulation_runner import SimulationRun, SimulationRunner


class _EchoGenerator:
    def __init__(self, source_id: str) -> None:
        self._source_id = source_id

    def generate_signal(self, **_kwargs: object) -> dict[str, object]:
        now = datetime.now(UTC).isoformat()
        return {
            "source": {"dataSourceId": self._source_id, "name": self._source_id, "kind": "authoritative"},
            "category": "weather",
            "occurredAt": now,
            "receivedAt": now,
            "jurisdictionId": "NSW",
            "location": {"type": "Point", "coordinates": [151.21, -33.86], "precisionMeters": 50},
            "payload": {"title": "simulated"},
            "confidenceScore": 0.8,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
            "provenance": {"collectionMethod": "simulation", "sourceUri": "sim://echo"},
        }


def test_flood_matrix_emission_covers_80_percent_of_relevant_ids() -> None:
    relevant_ids = activated_sources_for_scenario("flood")
    assert relevant_ids, "flood matrix must not be empty"

    runner = SimulationRunner(
        scenario={
            "scenario_type": "flood",
            "target_jurisdictions": ["nsw", "vic", "qld", "sa", "wa", "tas", "act", "nt"],
        }
    )
    for source_id in relevant_ids:
        runner.register_generator(source_id, _EchoGenerator(source_id))

    run = SimulationRun(
        scenario_name="matrix-coverage",
        activated_sources=relevant_ids,
        event_phases=[
            {
                "name": "coverage",
                "duration_seconds": 0,
                "sources": relevant_ids,
                "source_cadence_seconds": {source_id: 9999 for source_id in relevant_ids},
            }
        ],
        time_compression_ratio=10.0,
    )
    signals = asyncio.run(runner.start(run))
    emitted_ids = {signal["source"]["dataSourceId"] for signal in signals}
    coverage = len(emitted_ids & set(relevant_ids)) / len(relevant_ids)
    assert coverage >= 0.80


def test_unregistered_source_is_rejected() -> None:
    runner = SimulationRunner(
        scenario={"scenario_type": "flood", "target_jurisdictions": ["nsw"]},
    )
    run = SimulationRun(
        scenario_name="bad-source",
        activated_sources=["not-a-real-source"],
        event_phases=[],
        time_compression_ratio=1.0,
    )
    with pytest.raises(ValueError, match="not registered"):
        asyncio.run(runner.start(run))


def test_non_matching_region_source_is_rejected() -> None:
    runner = SimulationRunner(
        scenario={"scenario_type": "flood", "target_jurisdictions": ["vic"]},
    )
    run = SimulationRun(
        scenario_name="region-mismatch",
        activated_sources=["nsw-ses-flood"],
        event_phases=[],
        time_compression_ratio=1.0,
    )
    with pytest.raises(ValueError, match="not valid for jurisdictions"):
        asyncio.run(runner.start(run))
