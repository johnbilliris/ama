import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from opentelemetry import trace

from apps.ingestion import telemetry as tel

logger = logging.getLogger(__name__)


@dataclass
class SimulationRun:
    run_id: str = ""
    scenario_name: str = ""
    event_phases: list[dict[str, Any]] = field(default_factory=list)
    activated_sources: list[str] = field(default_factory=list)
    time_compression_ratio: float = 10.0
    status: str = "pending"
    created_at: str = ""
    started_at: str | None = None
    stopped_at: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = f"sim-{uuid4().hex[:8]}"
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()


class SimulationRunner:
    """Orchestrates simulation runs by iterating through scenario phases and generating signals."""

    def __init__(self, signal_repository: Any = None, scenario: dict[str, Any] | None = None):
        self._signal_repository = signal_repository
        self._scenario = scenario or {}
        self._generators: dict[str, Any] = {}
        self._generated_envelopes: list[dict[str, Any]] = []

    def register_generator(self, source_id: str, generator: Any) -> None:
        self._generators[source_id] = generator

    async def start(self, run: SimulationRun) -> list[dict[str, Any]]:
        run.status = "running"
        run.started_at = datetime.now(UTC).isoformat()
        tel.simulation_runs.add(1, {"simulation.scenario": run.scenario_name})
        logger.info("Simulation %s started: %s", run.run_id, run.scenario_name)

        with tel.tracer.start_as_current_span(
            "simulation.run",
            attributes={
                "simulation.run_id": run.run_id,
                "simulation.scenario": run.scenario_name,
                "simulation.phase_count": len(run.event_phases),
                "simulation.time_compression": run.time_compression_ratio,
            },
        ) as span:
            try:
                for phase in run.event_phases:
                    if run.status != "running":
                        break
                    await self.generate_phase_signals(phase, run)
            except Exception:
                logger.exception("Simulation %s failed during phase execution", run.run_id)
                run.status = "failed"
                span.set_status(trace.StatusCode.ERROR, "Simulation failed")
                raise

            if run.status == "running":
                run.status = "completed"
                run.stopped_at = datetime.now(UTC).isoformat()
                span.set_attribute("simulation.signals_generated", len(self._generated_envelopes))
                logger.info("Simulation %s completed with %d signals", run.run_id, len(self._generated_envelopes))

        return self._generated_envelopes

    async def generate_phase_signals(self, phase: dict[str, Any], run: SimulationRun) -> None:
        phase_name = phase.get("name", "unknown")
        duration_seconds = phase.get("duration_seconds", 60)
        sources = phase.get("sources", run.activated_sources)

        with tel.tracer.start_as_current_span(
            "simulation.phase",
            attributes={
                "simulation.run_id": run.run_id,
                "simulation.phase": phase_name,
                "simulation.source_count": len(sources),
            },
        ):
            phase_start = time.monotonic()
            logger.info("Simulation %s entering phase: %s", run.run_id, phase_name)

            for source_id in sources:
                generator = self._generators.get(source_id)
                if generator is None:
                    continue

                try:
                    if hasattr(generator, "generate_signal"):
                        signal = generator.generate_signal(**phase.get("params", {}))
                    elif hasattr(generator, "generate_batch"):
                        signals = generator.generate_batch(**phase.get("params", {}))
                        for s in signals:
                            self._tag_simulation_provenance(s, run)
                        self._generated_envelopes.extend(signals)
                        tel.simulation_signals_generated.add(
                            len(signals),
                            {"simulation.run_id": run.run_id, "simulation.source_id": source_id},
                        )
                        if self._signal_repository:
                            for s in signals:
                                await self._signal_repository.save(s)
                        continue
                    elif hasattr(generator, "generate_warning"):
                        signal = generator.generate_warning(**phase.get("params", {}))
                    elif hasattr(generator, "generate_observation"):
                        signal = generator.generate_observation(**phase.get("params", {}))
                    else:
                        continue

                    self._tag_simulation_provenance(signal, run)
                    self._generated_envelopes.append(signal)
                    tel.simulation_signals_generated.add(
                        1,
                        {"simulation.run_id": run.run_id, "simulation.source_id": source_id},
                    )

                    if self._signal_repository:
                        await self._signal_repository.save(signal)

                except Exception:
                    logger.exception("Generator %s failed in phase %s", source_id, phase_name)

            tel.simulation_phase_duration.record(
                (time.monotonic() - phase_start) * 1000,
                {"simulation.run_id": run.run_id, "simulation.phase": phase_name},
            )

            sleep_seconds = duration_seconds / max(run.time_compression_ratio, 0.1)
            await asyncio.sleep(sleep_seconds)

    async def stop(self, run: SimulationRun) -> None:
        run.status = "aborted"
        run.stopped_at = datetime.now(UTC).isoformat()
        logger.info("Simulation %s aborted", run.run_id)

    def _tag_simulation_provenance(self, envelope: dict[str, Any], run: SimulationRun) -> None:
        provenance = envelope.get("provenance", {})
        provenance["collectionMethod"] = "simulation"
        provenance["simulationRunId"] = run.run_id
        envelope["provenance"] = provenance

    @property
    def generated_envelopes(self) -> list[dict[str, Any]]:
        return list(self._generated_envelopes)
