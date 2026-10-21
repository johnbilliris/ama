from __future__ import annotations

import asyncio

from apps.ingestion.simulation.generators.weather_generator import WeatherGenerator
from apps.ingestion.simulation.simulation_runner import SimulationRun, SimulationRunner


class _ManifestRepo:
    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}

    async def upsert_document(self, document: dict) -> dict:
        self.docs[str(document["id"])] = dict(document)
        return document

    async def get_document(self, *, document_type: str, document_id: str) -> dict | None:
        doc = self.docs.get(document_id)
        if doc is None:
            return None
        if doc.get("document_type") != document_type:
            return None
        return dict(doc)


def _build_run(run_id: str) -> SimulationRun:
    return SimulationRun(
        run_id=run_id,
        scenario_name="manifest-test",
        activated_sources=["bom-warnings"],
        event_phases=[
            {
                "name": "phase",
                "duration_seconds": 0,
                "sources": ["bom-warnings"],
            }
        ],
        time_compression_ratio=10.0,
    )


def test_fresh_instance_replays_exact_sequence_from_persisted_manifest() -> None:
    repo = _ManifestRepo()
    runner_a = SimulationRunner(
        scenario={"scenario_type": "severe_storm", "target_jurisdictions": ["nsw"]},
        pipeline_dependencies={"simulation_repository": repo},
    )
    runner_a.register_generator("bom-warnings", WeatherGenerator())

    run = _build_run("a1b2c3d4")
    original = asyncio.run(runner_a.start(run))

    runner_b = SimulationRunner(
        scenario={"scenario_type": "severe_storm", "target_jurisdictions": ["nsw"]},
        pipeline_dependencies={"simulation_repository": repo},
    )
    replayed = asyncio.run(runner_b.replay_from_manifest(run.run_id))
    assert replayed == original


def test_reused_runner_resets_state_between_starts() -> None:
    runner = SimulationRunner(scenario={"scenario_type": "severe_storm", "target_jurisdictions": ["nsw"]})
    runner.register_generator("bom-warnings", WeatherGenerator())

    run_a = _build_run("aa11aa11")
    run_b = _build_run("bb22bb22")
    signals_a = asyncio.run(runner.start(run_a))
    signals_b = asyncio.run(runner.start(run_b))

    assert run_a.run_id != run_b.run_id
    assert signals_a
    assert signals_b
    # No cross-run spillover for the second start result.
    assert all(sig["provenance"].get("simulationRunId") == run_b.run_id for sig in signals_b)


def test_concurrent_runs_have_isolated_manifests() -> None:
    repo = _ManifestRepo()
    runner = SimulationRunner(
        scenario={"scenario_type": "severe_storm", "target_jurisdictions": ["nsw"]},
        pipeline_dependencies={"simulation_repository": repo},
    )
    runner.register_generator("bom-warnings", WeatherGenerator())

    async def _run(run_id: str) -> tuple[str, int]:
        run = _build_run(run_id)
        await runner.start(run)
        replay = await runner.replay_from_manifest(run_id)
        return run_id, len(replay)

    async def _drive() -> list[tuple[str, int]]:
        return await asyncio.gather(_run("cc33cc33"), _run("dd44dd44"))

    results = asyncio.run(_drive())
    assert {run_id for run_id, _ in results} == {"cc33cc33", "dd44dd44"}
    assert all(count >= 1 for _, count in results)
