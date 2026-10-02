import asyncio
import inspect
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker
from opentelemetry import trace

from apps.api.app.repositories.cosmos_scope import simulation_scope
from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion import telemetry as tel
from apps.ingestion.simulation.generators.historical_overlay import HistoricalOverlay
from apps.ingestion.simulation.scenario_source_matrix import (
    source_matrix_for_scenario,
    validate_source_region,
)

logger = logging.getLogger(__name__)


class SimulationClock(Protocol):
    def now(self) -> float: ...

    async def sleep_until(self, target_time: float) -> None: ...


class RealSimulationClock:
    def now(self) -> float:
        return time.monotonic()

    async def sleep_until(self, target_time: float) -> None:
        delay = target_time - self.now()
        if delay > 0:
            await asyncio.sleep(delay)


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
    current_phase: str = ""
    source_progress_ratio: dict[str, float] = field(default_factory=dict)
    source_signal_counts: dict[str, int] = field(default_factory=dict)
    random_seed: int | None = None
    random_version: str = "python-random-v1"
    signals_generated: int = 0
    failed_signals: int = 0

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if self.time_compression_ratio <= 0:
            raise ValueError("time_compression_ratio must be > 0")
        if self.random_seed is None:
            self.random_seed = int(self.run_id[:8], 16)


class SimulationSourcePipeline(IngestionPipelineBase):
    def __init__(
        self,
        *,
        source_id: str,
        run_id: str,
        schema_validator: Draft202012Validator,
        pipeline_dependencies: dict[str, Any] | None = None,
    ) -> None:
        deps = pipeline_dependencies or {}
        super().__init__(
            pipeline_id=f"simulation-{run_id}-{source_id}",
            data_source_ids=[source_id],
            poll_interval_seconds=1,
            trust_tier="tier_7_derived_computed",
            expected_update_seconds=60,
            schema_validator=schema_validator,
            scope=simulation_scope(run_id),
            allow_simulation_scope=True,
            **deps,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        return []

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        envelope = raw_payload.get("envelope")
        if not isinstance(envelope, dict):
            raise ValueError("simulation envelope payload is required")
        return envelope

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        envelope = raw_payload.get("envelope") if isinstance(raw_payload.get("envelope"), dict) else {}
        source = envelope.get("source") if isinstance(envelope.get("source"), dict) else {}
        data_source_id = str(source.get("dataSourceId", self.data_source_ids[0]))
        occurred_at = str(envelope.get("occurredAt", ""))
        signal_id = str(envelope.get("signalId", envelope.get("id", "")))
        return f"simulation:{data_source_id}:{signal_id}:{occurred_at}"


class _NullSignalRepository:
    async def save(self, signal: Any, *, scope: str = "live") -> None:
        return None


class _SignalRepositoryAdapter:
    def __init__(self, repository: Any) -> None:
        self._repository = repository
        self._save_signature = inspect.signature(repository.save)

    async def save(self, signal: Any, *, scope: str = "live") -> None:
        payload = signal.model_dump(mode="json") if hasattr(signal, "model_dump") else signal
        if "scope" in self._save_signature.parameters:
            await self._repository.save(signal, scope=scope)
            return
        await self._repository.save(payload)


class SimulationRunner:
    """Orchestrates simulation runs by iterating through scenario phases and generating signals."""

    def __init__(
        self,
        signal_repository: Any = None,
        scenario: dict[str, Any] | None = None,
        pipeline_dependencies: dict[str, Any] | None = None,
        clock: SimulationClock | None = None,
    ):
        adapted_repository = (
            _SignalRepositoryAdapter(signal_repository) if signal_repository is not None else _NullSignalRepository()
        )
        self._signal_repository = adapted_repository
        self._scenario = scenario or {}
        self._generators: dict[str, Any] = {}
        self._generated_envelopes_by_run: dict[str, list[dict[str, Any]]] = {}
        dependency_copy = dict(pipeline_dependencies or {})
        self._manifest_repository = dependency_copy.pop("simulation_repository", None)
        self._pipeline_dependencies = dependency_copy
        if "signal_repository" not in self._pipeline_dependencies:
            self._pipeline_dependencies["signal_repository"] = adapted_repository
        self._schema_validator = _default_schema_validator()
        self._simulation_pipelines: dict[tuple[str, str], SimulationSourcePipeline] = {}
        self._clock: SimulationClock = clock or RealSimulationClock()
        self._overlay = HistoricalOverlay()
        self._overlay_by_run_source: dict[tuple[str, str], list[dict[str, Any]]] = {}
        self._run_manifests: dict[str, dict[str, Any]] = {}

    def register_generator(self, source_id: str, generator: Any) -> None:
        self._generators[source_id] = generator

    async def start(self, run: SimulationRun) -> list[dict[str, Any]]:
        self._generated_envelopes_by_run[run.run_id] = []
        scenario_type = str(self._scenario.get("scenario_type", "")).strip()
        if scenario_type:
            for source_id in run.activated_sources:
                validate_source_region(
                    source_id,
                    scenario_type,
                    list(self._scenario.get("target_jurisdictions", [])),
                )
        run.status = "running"
        run.started_at = datetime.now(UTC).isoformat()
        run.current_phase = ""
        run.source_progress_ratio = {source_id: 0.0 for source_id in run.activated_sources}
        run.source_signal_counts = {source_id: 0 for source_id in run.activated_sources}
        run.signals_generated = 0
        run.failed_signals = 0
        tel.simulation_runs.add(
            1,
            tel.tenant_attributes(
                {"simulation.scenario": run.scenario_name},
                tenant_id=simulation_scope(run.run_id),
            ),
        )
        logger.info("Simulation %s started: %s", run.run_id, run.scenario_name)

        with tel.tracer.start_as_current_span(
            "simulation.run",
            attributes=tel.tenant_attributes(
                {
                    "simulation.run_id": run.run_id,
                    "simulation.scenario": run.scenario_name,
                    "simulation.phase_count": len(run.event_phases),
                    "simulation.time_compression": run.time_compression_ratio,
                },
                tenant_id=simulation_scope(run.run_id),
            ),
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
                signals = self._generated_envelopes_by_run.get(run.run_id, [])
                span.set_attribute("simulation.signals_generated", len(signals))
                logger.info("Simulation %s completed with %d signals", run.run_id, len(signals))

            self._persist_run_manifest(run)

        return list(self._generated_envelopes_by_run.get(run.run_id, []))

    async def generate_phase_signals(self, phase: dict[str, Any], run: SimulationRun) -> None:
        phase_name = phase.get("name", "unknown")
        duration_seconds = float(phase.get("duration_seconds", 60))
        sources = phase.get("sources", run.activated_sources)
        if not isinstance(sources, list):
            raise ValueError("phase sources must be a list")
        run.current_phase = phase_name

        with tel.tracer.start_as_current_span(
            "simulation.phase",
            attributes=tel.tenant_attributes(
                {
                    "simulation.run_id": run.run_id,
                    "simulation.phase": phase_name,
                    "simulation.source_count": len(sources),
                },
                tenant_id=simulation_scope(run.run_id),
            ),
        ):
            phase_start = time.monotonic()
            logger.info("Simulation %s entering phase: %s", run.run_id, phase_name)
            phase_params = phase.get("params", {})
            source_params = phase.get("source_params", {})
            cadence_map = phase.get("source_cadence_seconds", {})

            for source_id in sources:
                if source_id not in run.source_signal_counts:
                    run.source_signal_counts[source_id] = 0
                if source_id not in run.source_progress_ratio:
                    run.source_progress_ratio[source_id] = 0.0

            phase_start_real = self._clock.now()
            source_due_times: dict[str, float] = {}
            source_cadence: dict[str, float] = {}
            for source_id in sources:
                cadence = float(cadence_map.get(source_id, self._default_cadence_seconds(source_id)))
                if cadence <= 0:
                    raise ValueError(f"cadence must be > 0 for source {source_id}")
                source_cadence[source_id] = cadence
                source_due_times[source_id] = 0.0

            first_tick = True
            while run.status == "running":
                elapsed_sim = (self._clock.now() - phase_start_real) * run.time_compression_ratio
                if elapsed_sim > duration_seconds + 1e-9 and not first_tick:
                    break

                eligible_sources = [sid for sid in sources if elapsed_sim + 1e-9 >= source_due_times[sid]]
                first_tick = False

                for source_id in eligible_sources:
                    generator = self._generators.get(source_id)
                    if generator is None:
                        source_due_times[source_id] += source_cadence[source_id]
                        continue

                    try:
                        merged_params = dict(phase_params)
                        if isinstance(source_params, dict) and isinstance(source_params.get(source_id), dict):
                            merged_params.update(source_params[source_id])
                        overlay_signals = self._overlay_signals_for_source(source_id, run)
                        if overlay_signals:
                            generated_signals = [dict(item) for item in overlay_signals]
                        else:
                            generated_signals = self._generate_signals_for_source(
                                source_id, generator, merged_params, run
                            )
                        for signal in generated_signals:
                            self._tag_simulation_provenance(signal, run, source_id)
                            await self._ingest_simulation_signal(source_id, signal, run)
                            self._generated_envelopes_by_run.setdefault(run.run_id, []).append(signal)
                            run.signals_generated += 1
                            run.source_signal_counts[source_id] = run.source_signal_counts.get(source_id, 0) + 1

                        tel.simulation_signals_generated.add(
                            len(generated_signals),
                            tel.tenant_attributes(
                                {"simulation.run_id": run.run_id, "simulation.source_id": source_id},
                                tenant_id=simulation_scope(run.run_id),
                            ),
                        )
                    except Exception:
                        run.failed_signals += 1
                        run.status = "failed"
                        logger.exception("Generator %s failed in phase %s", source_id, phase_name)
                        raise

                    if overlay_signals:
                        source_due_times[source_id] = duration_seconds + source_cadence[source_id]
                    else:
                        source_due_times[source_id] += source_cadence[source_id]
                    run.source_progress_ratio[source_id] = min(
                        1.0,
                        source_due_times[source_id] / max(duration_seconds, 1.0),
                    )

                if run.status != "running":
                    break

                next_due_sim = min(source_due_times.values()) if source_due_times else duration_seconds
                if next_due_sim > duration_seconds:
                    break
                next_due_real = phase_start_real + (next_due_sim / run.time_compression_ratio)
                await self._sleep_interruptible(run, next_due_real)

            for source_id in sources:
                run.source_progress_ratio[source_id] = (
                    1.0 if run.status != "failed" else run.source_progress_ratio[source_id]
                )

            tel.simulation_phase_duration.record(
                (time.monotonic() - phase_start) * 1000,
                tel.tenant_attributes(
                    {"simulation.run_id": run.run_id, "simulation.phase": phase_name},
                    tenant_id=simulation_scope(run.run_id),
                ),
            )

    async def stop(self, run: SimulationRun) -> None:
        run.status = "aborted"
        run.stopped_at = datetime.now(UTC).isoformat()
        logger.info("Simulation %s aborted", run.run_id)

    async def _sleep_interruptible(self, run: SimulationRun, target_time: float) -> None:
        # Keep sleeps short so abort signals can stop long cadences quickly.
        while run.status == "running":
            now = self._clock.now()
            if now >= target_time:
                return
            await self._clock.sleep_until(min(target_time, now + 0.25))

    def _generate_signals_for_source(
        self,
        source_id: str,
        generator: Any,
        params: dict[str, Any],
        run: SimulationRun,
    ) -> list[dict[str, Any]]:
        if hasattr(generator, "generate_signal"):
            return [generator.generate_signal(**params)]
        if hasattr(generator, "generate_batch"):
            batch_params = dict(params)
            source_seed = sum(ord(ch) for ch in source_id)
            batch_params.setdefault("random_seed", int(run.random_seed or 0) ^ source_seed)
            batch_params.setdefault("rng_version", run.random_version)
            batch_params.setdefault("misinfo_ratio", params.get("misinformation_ratio", 0.15))
            return list(generator.generate_batch(**batch_params))
        if hasattr(generator, "generate_warning"):
            return [generator.generate_warning(**params)]
        if hasattr(generator, "generate_observation"):
            source_cfg = self._scenario_source_types().get(source_id, {})
            configured_source_id = source_cfg.get("dataSourceId", source_id)
            source_type = source_cfg.get("type", "unknown")
            observation_params = dict(params)
            observation_params.setdefault("source_id", configured_source_id)
            observation_params.setdefault("source_type", source_type)
            return [generator.generate_observation(**observation_params)]
        return []

    def _scenario_source_types(self) -> dict[str, dict[str, str]]:
        scenario_type = str(self._scenario.get("scenario_type", "")).strip()
        if scenario_type:
            matrix = source_matrix_for_scenario(scenario_type)
            return {
                source_id: {
                    "dataSourceId": source_id,
                    "type": str(config.get("type", "unknown")),
                    "kind": str(config.get("kind", "unknown")),
                }
                for source_id, config in matrix.items()
            }
        matrix = self._scenario.get("source_matrix")
        if isinstance(matrix, dict):
            return {str(k): v for k, v in matrix.items() if isinstance(v, dict)}
        return {}

    def _default_cadence_seconds(self, source_id: str) -> float:
        scenario_type = str(self._scenario.get("scenario_type", "")).strip()
        if scenario_type:
            matrix = source_matrix_for_scenario(scenario_type)
            config = matrix.get(source_id)
            if isinstance(config, dict):
                try:
                    return float(config.get("cadenceSeconds", 60.0))
                except (TypeError, ValueError):
                    return 60.0
        defaults = {
            "bom-warnings": 60.0,
            "bom-radar": 300.0,
            "bom-observations": 300.0,
            "bom-river-gauges": 300.0,
            "bom-flood-warnings": 120.0,
            "twitter-disaster": 30.0,
            "nsw-rfs-fires-near-me": 60.0,
            "ga-sentinel-hotspots": 3600.0,
            "himawari-satellite": 600.0,
        }
        return defaults.get(source_id, 60.0)

    def _overlay_signals_for_source(self, source_id: str, run: SimulationRun) -> list[dict[str, Any]]:
        scenario_path = str(self._scenario.get("historical_overlay_path", "")).strip()
        if not scenario_path:
            return []
        key = (run.run_id, source_id)
        if key in self._overlay_by_run_source:
            return self._overlay_by_run_source[key]

        loaded = self._overlay.load(scenario_path)
        perturbed = self._overlay.apply_perturbation(
            loaded,
            location_shift=tuple(self._scenario.get("historical_overlay_location_shift", (0.0, 0.0))),
            time_shift=float(self._scenario.get("historical_overlay_time_shift_hours", 0.0)),
            severity_scale=float(self._scenario.get("historical_overlay_severity_scale", 1.0)),
        )
        filtered = [
            signal
            for signal in perturbed
            if isinstance(signal, dict)
            and isinstance(signal.get("source"), dict)
            and str(signal["source"].get("dataSourceId", "")) == source_id
        ]
        if not filtered:
            raise ValueError(f"historical overlay did not contain source {source_id}")
        self._overlay_by_run_source[key] = filtered
        return filtered

    def _tag_simulation_provenance(self, envelope: dict[str, Any], run: SimulationRun, source_id: str) -> None:
        provenance = envelope.get("provenance", {})
        provenance["collectionMethod"] = "simulation"
        provenance["simulationRunId"] = run.run_id
        envelope["provenance"] = provenance
        source = envelope.get("source") if isinstance(envelope.get("source"), dict) else {}
        source.setdefault("dataSourceId", source_id)
        envelope["source"] = source

    async def _ingest_simulation_signal(self, source_id: str, envelope: dict[str, Any], run: SimulationRun) -> None:
        key = (run.run_id, source_id)
        pipeline = self._simulation_pipelines.get(key)
        if pipeline is None:
            pipeline = SimulationSourcePipeline(
                source_id=source_id,
                run_id=run.run_id,
                schema_validator=self._schema_validator,
                pipeline_dependencies=self._pipeline_dependencies,
            )
            self._simulation_pipelines[key] = pipeline

        result = await pipeline._process_payload({"envelope": envelope})
        if not result.accepted:
            raise RuntimeError(f"simulation signal was not accepted: {result.status} ({result.reason})")

    @property
    def generated_envelopes(self) -> list[dict[str, Any]]:
        combined: list[dict[str, Any]] = []
        for values in self._generated_envelopes_by_run.values():
            combined.extend(values)
        return combined

    async def replay_from_manifest(self, run_id: str, *, allow_partial: bool = False) -> list[dict[str, Any]]:
        manifest = self._run_manifests.get(run_id)
        if manifest is None:
            simulation_repo = self._manifest_repository
            if simulation_repo is not None and hasattr(simulation_repo, "get_document"):
                maybe = simulation_repo.get_document(
                    document_type="spec006_simulation_run_manifest",
                    document_id=f"manifest-{run_id}",
                )
                if inspect.isawaitable(maybe):
                    manifest = await maybe
                elif isinstance(maybe, dict):
                    manifest = maybe
        if manifest is None:
            raise ValueError(f"run manifest not found for run_id={run_id}")
        status = str(manifest.get("status", ""))
        if status == "aborted" and not allow_partial:
            raise ValueError("run was aborted; replay is partial and requires allow_partial=True")
        sequence = manifest.get("signalSequence", [])
        if not isinstance(sequence, list):
            raise ValueError("run manifest signal sequence is invalid")
        return [dict(item) for item in sequence if isinstance(item, dict)]

    def _persist_run_manifest(self, run: SimulationRun) -> None:
        signals = self._generated_envelopes_by_run.get(run.run_id, [])
        ordered_ids: list[str] = []
        for index, signal in enumerate(signals):
            signal_id = str(signal.get("signalId", "")).strip() or str(signal.get("id", "")).strip()
            if not signal_id:
                signal_id = f"sim-signal-{index:06d}"
            ordered_ids.append(signal_id)

        manifest = {
            "id": f"manifest-{run.run_id}",
            "document_type": "spec006_simulation_run_manifest",
            "runId": run.run_id,
            "scope": simulation_scope(run.run_id),
            "status": run.status,
            "scenario": {
                "name": run.scenario_name,
                "type": self._scenario.get("scenario_type"),
                "version": self._scenario.get("scenario_version", "v1"),
                "targetRegion": self._scenario.get("target_region"),
                "targetJurisdictions": self._scenario.get("target_jurisdictions", []),
                "activatedSources": run.activated_sources,
                "historicalOverlayPath": self._scenario.get("historical_overlay_path"),
            },
            "model": {
                "modelVersion": self._scenario.get("model_version", "UNVERIFIED"),
                "modelConfigVersion": self._scenario.get("model_config_version", "UNVERIFIED"),
                "calibrationStatus": self._scenario.get("calibration_status", "UNVERIFIED"),
            },
            "effectiveRatios": {
                "timeCompressionRatio": run.time_compression_ratio,
                "misinformationRatio": self._scenario.get("misinformation_ratio", 0.15),
            },
            "clock": {
                "randomSeed": run.random_seed,
                "randomVersion": run.random_version,
                "startedAt": run.started_at,
                "stoppedAt": run.stopped_at,
            },
            "orderedSignalIds": ordered_ids,
            "downstreamDecisionRefs": self._scenario.get("downstream_decision_refs", []),
            "signalSequence": signals,
        }
        self._run_manifests[run.run_id] = manifest

        simulation_repo = self._manifest_repository
        if simulation_repo is not None and hasattr(simulation_repo, "upsert_document"):
            try:
                maybe = simulation_repo.upsert_document(manifest)
                if inspect.isawaitable(maybe):
                    # Persist best-effort without failing simulation completion paths.
                    loop = asyncio.get_running_loop()
                    loop.create_task(maybe)
            except Exception:
                logger.warning("failed to persist run manifest for run_id=%s", run.run_id, exc_info=True)


def _default_schema_validator() -> Draft202012Validator:
    schema_path = Path("packages/schemas/signal-envelope.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema=schema, format_checker=FormatChecker())
