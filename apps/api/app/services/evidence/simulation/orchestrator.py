# Evidence adapter over the existing SimulationEventRepository playback seam.

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, Protocol, runtime_checkable

RunMode = Literal["baseline", "ama_assisted"]
MAX_EVENTS_PER_SOURCE = 10_000


class EvidenceSourceError(ValueError):
    pass


class EvidenceMetadataError(EvidenceSourceError):
    pass


@runtime_checkable
class SimulationEventReader(Protocol):
    def list_events(
        self,
        tenant_id: str,
        *,
        after_seq: int = 0,
        limit: int = 200,
        include_annotations: bool = True,
    ) -> Sequence[Any]: ...


@dataclass(frozen=True, slots=True)
class EvidenceObservation:
    event_id: str
    source_run_id: str
    event_seq: int
    mode: RunMode
    scenario_id: str
    scenario_version: str
    scenario_content_hash: str
    seed: str
    run_pair_id: str
    event_timestamp: datetime
    confidence: float | None
    kpi_id: str | None
    observation_id: str
    component_version: str | None
    signal_id: str | None
    model_output_id: str | None
    recommendation_id: str | None
    human_decision_id: str | None
    outcome_id: str | None
    eligible_for_rollup: bool
    values: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class RunEvidence:
    mode: RunMode
    source_run_id: str
    seed: str
    observations: tuple[EvidenceObservation, ...] = ()
    rejected_event_ids: tuple[str, ...] = ()

    @property
    def scenario_version(self) -> str | None:
        versions = {row.scenario_version for row in self.observations}
        if len(versions) > 1:
            raise EvidenceMetadataError(f"mode {self.mode} contains multiple scenario versions")
        return next(iter(versions), None)

    @property
    def scenario_content_hash(self) -> str | None:
        hashes = {row.scenario_content_hash for row in self.observations}
        if len(hashes) > 1:
            raise EvidenceMetadataError(f"mode {self.mode} contains multiple scenario content hashes")
        return next(iter(hashes), None)


@dataclass(frozen=True, slots=True)
class RunPairEvidence:
    scenario_id: str
    seed: str
    run_pair_id: str
    baseline: RunEvidence
    ama_assisted: RunEvidence

    @property
    def scenario_version(self) -> str | None:
        versions = {
            value for value in (self.baseline.scenario_version, self.ama_assisted.scenario_version) if value is not None
        }
        if len(versions) > 1:
            raise EvidenceMetadataError("baseline and AMA-assisted scenario versions differ")
        return next(iter(versions), None)

    @property
    def scenario_content_hash(self) -> str | None:
        hashes = {
            value
            for value in (self.baseline.scenario_content_hash, self.ama_assisted.scenario_content_hash)
            if value is not None
        }
        if len(hashes) > 1:
            raise EvidenceMetadataError("baseline and AMA-assisted scenario content hashes differ")
        return next(iter(hashes), None)


@runtime_checkable
class EvidenceEventSource(Protocol):
    def load_run_pair(
        self,
        *,
        scenario_id: str,
        seed: str,
        run_pair_id: str,
        source_run_ids: Mapping[RunMode, str] | None = None,
        repetition_index: int = 0,
    ) -> RunPairEvidence: ...


def _normalise_mode(value: Any) -> RunMode | None:
    normalised = str(value or "").strip().lower().replace("-", "_")
    if normalised == "baseline":
        return "baseline"
    if normalised in {"ama", "assisted", "ama_assisted"}:
        return "ama_assisted"
    return None


def _normalise_scenario(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _first(mapping: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        value = mapping.get(name)
        if value is not None:
            return value
    return None


def _non_blank(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _confidence(value: Any) -> float | None:
    if isinstance(value, Mapping):
        value = value.get("value")
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if 0.0 <= parsed <= 1.0:
        return parsed
    return None


def _payload_parts(payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = payload.get("evidence") or payload.get("kpi_evidence")
    metadata = dict(evidence) if isinstance(evidence, Mapping) else dict(payload)
    values: dict[str, Any] = {}
    for candidate in (payload, metadata):
        values.update(candidate)
        for key in ("metrics", "measurements", "kpi_payload", "chain", "canonical_event_chain"):
            nested = candidate.get(key)
            if isinstance(nested, Mapping):
                values.update(nested)
    return metadata, values


def _references(metadata: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    references: dict[str, Any] = {}
    for candidate in (payload.get("references"), metadata.get("references")):
        if isinstance(candidate, Mapping):
            references.update(candidate)
    return references


def _event_timestamp(metadata: Mapping[str, Any], values: Mapping[str, Any]) -> datetime | None:
    explicit = _first(metadata, "event_timestamp", "observed_at", "occurred_at")
    parsed = _parse_timestamp(explicit)
    if parsed is not None:
        return parsed
    for name in (
        "call_received_at",
        "dispatched_at",
        "arrived_at",
        "controlled_at",
        "cleared_at",
        "evacuation_completed_at",
        "hazard_impact_at",
        "economic_loss_assessed_at",
    ):
        parsed = _parse_timestamp(values.get(name))
        if parsed is not None:
            return parsed
    return None


@dataclass(slots=True)
class SimulationEventEvidenceAdapter:
    repository: SimulationEventReader
    max_events_per_source: int = MAX_EVENTS_PER_SOURCE
    _cache: dict[str, tuple[Any, ...]] = field(default_factory=dict, init=False, repr=False)

    def _events(self, source_run_id: str) -> tuple[Any, ...]:
        if source_run_id not in self._cache:
            events = self.repository.list_events(
                source_run_id,
                after_seq=0,
                limit=self.max_events_per_source,
                include_annotations=False,
            )
            self._cache[source_run_id] = tuple(events)
        return self._cache[source_run_id]

    def _observation(
        self,
        event: Any,
        *,
        source_run_id: str,
        expected_mode: RunMode,
        scenario_id: str,
        seed: str,
        run_pair_id: str,
        repetition_index: int,
    ) -> EvidenceObservation | None:
        payload = getattr(event, "payload", None)
        if not isinstance(payload, Mapping):
            return None
        metadata, values = _payload_parts(payload)
        repetition = _first(metadata, "repetition_index", "repetition")
        if repetition is not None:
            try:
                if int(repetition) != repetition_index:
                    return None
            except (TypeError, ValueError):
                return None

        mode = _normalise_mode(metadata.get("mode"))
        event_scenario = _normalise_scenario(metadata.get("scenario_id"))
        event_seed = _non_blank(metadata.get("seed"))
        event_run_pair = _non_blank(metadata.get("run_pair_id"))
        scenario_version = _non_blank(metadata.get("scenario_version"))
        content_hash = _non_blank(_first(metadata, "scenario_content_hash", "content_hash"))
        timestamp = _event_timestamp(metadata, values)
        if (
            mode != expected_mode
            or event_scenario != scenario_id
            or event_seed != seed
            or event_run_pair != run_pair_id
            or scenario_version is None
            or content_hash is None
            or timestamp is None
        ):
            return None

        references = _references(metadata, payload)
        recommendation_id = _non_blank(_first(metadata, "recommendation_id") or references.get("recommendation"))
        human_decision_id = _non_blank(
            _first(metadata, "human_decision_id", "decision_id") or references.get("human_decision")
        )
        approval = _first(metadata, "decision_approved", "human_decision_approved")
        approval_status = str(_first(metadata, "approval_status", "decision_status") or "").lower()
        approved = approval is True or approval_status == "approved"
        eligible = recommendation_id is None or (human_decision_id is not None and approved)

        event_id = _non_blank(getattr(event, "id", None))
        if event_id is None:
            return None
        event_seq = int(getattr(event, "event_seq", 0))
        observation_id = _non_blank(_first(metadata, "observation_id", "incident_id", "case_id")) or event_id
        confidence_value = _first(metadata, "confidence", "confidence_score")
        if confidence_value is None:
            confidence_value = _first(values, "confidence", "confidence_score")
        confidence = _confidence(confidence_value)
        return EvidenceObservation(
            event_id=event_id,
            source_run_id=source_run_id,
            event_seq=event_seq,
            mode=mode,
            scenario_id=scenario_id,
            scenario_version=scenario_version,
            scenario_content_hash=content_hash,
            seed=seed,
            run_pair_id=run_pair_id,
            event_timestamp=timestamp,
            confidence=confidence,
            kpi_id=_non_blank(metadata.get("kpi_id")),
            observation_id=observation_id,
            component_version=_non_blank(_first(metadata, "component_version", "producer_version")),
            signal_id=_non_blank(_first(metadata, "signal_id") or references.get("signal")),
            model_output_id=_non_blank(_first(metadata, "model_output_id") or references.get("model_output")),
            recommendation_id=recommendation_id,
            human_decision_id=human_decision_id,
            outcome_id=_non_blank(_first(metadata, "outcome_id") or references.get("outcome")),
            eligible_for_rollup=eligible,
            values=values,
        )

    def _run(
        self,
        *,
        source_run_id: str,
        expected_mode: RunMode,
        scenario_id: str,
        seed: str,
        run_pair_id: str,
        repetition_index: int,
    ) -> RunEvidence:
        observations: list[EvidenceObservation] = []
        rejected: list[str] = []
        for event in self._events(source_run_id):
            observation = self._observation(
                event,
                source_run_id=source_run_id,
                expected_mode=expected_mode,
                scenario_id=scenario_id,
                seed=seed,
                run_pair_id=run_pair_id,
                repetition_index=repetition_index,
            )
            if observation is None:
                payload = getattr(event, "payload", None)
                metadata = _payload_parts(payload)[0] if isinstance(payload, Mapping) else {}
                repetition = _first(metadata, "repetition_index", "repetition")
                same_repetition = repetition is None
                if repetition is not None:
                    try:
                        same_repetition = int(repetition) == repetition_index
                    except (TypeError, ValueError):
                        same_repetition = True
                if _normalise_mode(metadata.get("mode")) == expected_mode and same_repetition:
                    event_id = _non_blank(getattr(event, "id", None))
                    if event_id is not None:
                        rejected.append(event_id)
                continue
            observations.append(observation)
        observations.sort(key=lambda row: (row.event_seq, row.event_id))
        run = RunEvidence(
            mode=expected_mode,
            source_run_id=source_run_id,
            seed=seed,
            observations=tuple(observations),
            rejected_event_ids=tuple(rejected),
        )
        run.scenario_version
        run.scenario_content_hash
        return run

    def load_run_pair(
        self,
        *,
        scenario_id: str,
        seed: str,
        run_pair_id: str,
        source_run_ids: Mapping[RunMode, str] | None = None,
        repetition_index: int = 0,
    ) -> RunPairEvidence:
        normalised_scenario = _normalise_scenario(scenario_id)
        source_ids = dict(source_run_ids or {})
        baseline_source = source_ids.get("baseline", run_pair_id)
        assisted_source = source_ids.get("ama_assisted", run_pair_id)
        pair = RunPairEvidence(
            scenario_id=normalised_scenario,
            seed=seed,
            run_pair_id=run_pair_id,
            baseline=self._run(
                source_run_id=baseline_source,
                expected_mode="baseline",
                scenario_id=normalised_scenario,
                seed=seed,
                run_pair_id=run_pair_id,
                repetition_index=repetition_index,
            ),
            ama_assisted=self._run(
                source_run_id=assisted_source,
                expected_mode="ama_assisted",
                scenario_id=normalised_scenario,
                seed=seed,
                run_pair_id=run_pair_id,
                repetition_index=repetition_index,
            ),
        )
        pair.scenario_version
        pair.scenario_content_hash
        return pair


def default_event_source() -> EvidenceEventSource:
    # This import reuses the same repository instance as simulation playback.
    from app.api.routes.simulations import _event_repo

    return SimulationEventEvidenceAdapter(_event_repo)
