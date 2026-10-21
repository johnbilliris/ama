import asyncio
from pathlib import Path

import pytest

from apps.ingestion.simulation.generators.flood_generator import FloodGenerator
from apps.ingestion.simulation.generators.weather_generator import WeatherGenerator
from apps.ingestion.simulation.simulation_runner import SimulationRun, SimulationRunner


class InMemorySignalRepository:
    """Simple in-memory signal store for testing."""

    def __init__(self) -> None:
        self.signals: list[dict] = []

    async def save(self, signal: dict) -> None:
        self.signals.append(signal)


class TestSimulationRunner:
    def test_flood_simulation_generates_signals(self) -> None:
        repo = InMemorySignalRepository()
        runner = SimulationRunner(signal_repository=repo)
        runner.register_generator("bom-river-gauges", FloodGenerator())
        runner.register_generator("bom-warnings", WeatherGenerator())

        run = SimulationRun(
            scenario_name="flood-integration-test",
            event_phases=[
                {
                    "name": "warning",
                    "duration_seconds": 0,
                    "sources": ["bom-warnings"],
                    "params": {"scenario_type": "flood", "severity": "warning", "jurisdiction": "nsw"},
                },
                {
                    "name": "minor_flood",
                    "duration_seconds": 0,
                    "sources": ["bom-river-gauges"],
                    "params": {"water_level": 4.0, "gauge_id": "test-gauge"},
                },
            ],
            activated_sources=["bom-river-gauges", "bom-warnings"],
            time_compression_ratio=1000.0,
        )

        signals = asyncio.run(runner.start(run))

        assert run.status == "completed"
        assert len(signals) >= 2
        assert len(repo.signals) >= 2

        # All signals should have simulation provenance
        for signal in signals:
            provenance = signal.get("provenance", {})
            assert provenance.get("collectionMethod") == "simulation"
            assert provenance.get("simulationRunId") == run.run_id

    def test_simulation_can_be_aborted(self) -> None:
        runner = SimulationRunner()
        run = SimulationRun(scenario_name="abort-test")
        asyncio.run(runner.stop(run))
        assert run.status == "aborted"
        assert run.stopped_at is not None

    def test_simulation_isolation_tags_all_signals(self) -> None:
        runner = SimulationRunner()
        runner.register_generator("bom-warnings", WeatherGenerator())

        run = SimulationRun(
            scenario_name="isolation-test",
            event_phases=[
                {
                    "name": "test",
                    "duration_seconds": 0,
                    "sources": ["bom-warnings"],
                    "params": {"scenario_type": "severe_storm", "severity": "warning"},
                },
            ],
            time_compression_ratio=1000.0,
        )

        signals = asyncio.run(runner.start(run))
        # T-AA06 — replace ``len(signals) > 0`` with explicit boundary
        # assertion: the runner MUST emit at least one signal per
        # configured event phase in the run plan.
        expected_min = max(1, len(run.event_phases))
        assert len(signals) >= expected_min, (
            f"runner emitted {len(signals)} signals for {expected_min} phases; expected ≥ phase count"
        )
        # Every signal must be tagged with simulation provenance.
        for signal in signals:
            assert signal["provenance"]["collectionMethod"] == "simulation"
            assert signal["provenance"]["simulationRunId"] == run.run_id

    def test_historical_overlay_replaces_parametric_generation(self) -> None:
        repo = InMemorySignalRepository()
        runner = SimulationRunner(
            signal_repository=repo,
            scenario={
                "historical_overlay_path": "specs/006-data-ingestion-storage/evidence/historical-overlay-sample.json",
                "historical_overlay_time_shift_hours": 1.0,
                "historical_overlay_location_shift": [0.1, -0.1],
            },
        )
        runner.register_generator("bom-river-gauges", FloodGenerator())
        run = SimulationRun(
            scenario_name="overlay",
            event_phases=[{"name": "overlay", "duration_seconds": 0, "sources": ["bom-river-gauges"]}],
            activated_sources=["bom-river-gauges"],
            time_compression_ratio=1.0,
        )

        signals = asyncio.run(runner.start(run))
        assert len(signals) == 3
        for signal in signals:
            assert signal["payload"].get("historicalOverlay") is True
            assert signal["provenance"].get("simulationRunId") == run.run_id

    def test_historical_overlay_missing_file_rejected(self) -> None:
        runner = SimulationRunner(
            scenario={"historical_overlay_path": "specs/006-data-ingestion-storage/evidence/not-found.json"}
        )
        runner.register_generator("bom-river-gauges", FloodGenerator())
        run = SimulationRun(
            scenario_name="overlay-missing",
            event_phases=[{"name": "overlay", "duration_seconds": 0, "sources": ["bom-river-gauges"]}],
            activated_sources=["bom-river-gauges"],
            time_compression_ratio=1.0,
        )
        with pytest.raises(ValueError, match="not found"):
            asyncio.run(runner.start(run))

    def test_historical_overlay_extreme_scale_rejected(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "overlay.json"
        bad_file.write_text(
            """
            {
              "signals": [
                {
                  "source": {"dataSourceId": "bom-river-gauges", "name": "x", "kind": "sensor"},
                  "category": "hydrology",
                  "occurredAt": "2026-01-01T00:00:00+00:00",
                  "receivedAt": "2026-01-01T00:00:00+00:00",
                  "jurisdictionId": "NSW",
                  "location": {"type": "Point", "coordinates": [151.0, -33.8], "precisionMeters": 10},
                  "payload": {"waterLevel": 9.0},
                  "confidenceScore": 0.8,
                  "freshnessScore": 0.8,
                  "validationStatus": "validated",
                  "provenance": {"collectionMethod": "api_pull", "sourceUri": "x", "sourceTimestamp": "2026-01-01T00:00:00+00:00"}
                }
              ]
            }
            """,  # noqa: E501
            encoding="utf-8",
        )

        runner = SimulationRunner(
            scenario={
                "historical_overlay_path": str(bad_file),
                "historical_overlay_severity_scale": 10.0,
            }
        )
        runner.register_generator("bom-river-gauges", FloodGenerator())
        run = SimulationRun(
            scenario_name="overlay-extreme",
            event_phases=[{"name": "overlay", "duration_seconds": 0, "sources": ["bom-river-gauges"]}],
            activated_sources=["bom-river-gauges"],
            time_compression_ratio=1.0,
        )
        with pytest.raises(ValueError, match="severity_scale"):
            asyncio.run(runner.start(run))
