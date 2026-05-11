import asyncio

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
