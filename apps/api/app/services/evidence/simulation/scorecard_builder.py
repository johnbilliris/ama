# Source-derived delta scorecard calculation.

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from statistics import median
from typing import Any, Protocol

from ..measurement.confidence import (
    DEFAULT_MIN_RESAMPLES,
    Statistic,
    bootstrap_ci,
    within_tolerance,
)
from ..measurement.definitions import (
    CAPSTONE_KPI_IDS,
    CAPSTONE_METRIC_BY_ID,
    FORMULA_VERSION,
    MetricDefinition,
)
from ..measurement.imputation import CHAIN_FIELDS, forward_impute
from ..models.scorecard import (
    DEFAULT_TOL_ABS_UNIT,
    DEFAULT_TOL_REL_PCT,
    DeltaScorecard,
    DeterminismCheck,
    KpiDelta,
    RunProvenance,
)
from ..models.signal import CanonicalEventChain
from .orchestrator import (
    EvidenceEventSource,
    EvidenceMetadataError,
    EvidenceObservation,
    RunEvidence,
    RunMode,
    RunPairEvidence,
)
from .repository import scorecard_id_for

FOUR_PLACES = Decimal("0.0001")
MAX_REPETITIONS = 100
MAX_BOOTSTRAP_RESAMPLES = 10_000


class MissingEvidenceSourceError(ValueError):
    def __init__(self, missing: Mapping[str, list[RunMode]]) -> None:
        self.missing = {key: list(value) for key, value in missing.items()}
        detail = ", ".join(f"{key}: {sorted(value)}" for key, value in self.missing.items())
        super().__init__(f"required evidence sources unavailable: {detail}")


class ImputationSignoffRequiredError(PermissionError):
    def __init__(self, share: Decimal) -> None:
        self.share = share
        super().__init__(f"imputed observation share {share:.2%} exceeds 10%; named auditor sign-off required")


@dataclass(frozen=True, slots=True)
class NamedAuditorSignoff:
    approval_id: str
    auditor_id: str


class ImputationSignoffResolver(Protocol):
    def resolve(
        self,
        *,
        scenario_id: str,
        run_pair_id: str,
        scenario_content_hash: str | None,
        imputation_share: Decimal,
    ) -> NamedAuditorSignoff | None: ...


@dataclass(frozen=True, slots=True)
class _Sample:
    key: str
    value: Decimal
    imputed: bool
    source_event_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RunMetric:
    value: Decimal | None
    samples: tuple[_Sample, ...]
    source_event_ids: tuple[str, ...]
    reduced_fidelity: bool
    timestamp_row_count: int = 0
    imputed_row_count: int = 0
    operational_tempo_scale: Decimal | None = None


@dataclass(frozen=True, slots=True)
class _PairMetric:
    definition: MetricDefinition
    baseline: _RunMetric
    assisted: _RunMetric
    absolute_delta: Decimal | None
    percent_delta: Decimal | None
    delta_samples: tuple[_Sample, ...]

    @property
    def missing_modes(self) -> list[RunMode]:
        missing: list[RunMode] = []
        if self.baseline.value is None:
            missing.append("baseline")
        if self.assisted.value is None:
            missing.append("ama_assisted")
        return missing


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _q(value: Decimal | None) -> Decimal | None:
    return value.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP) if value is not None else None


def _first(values: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        value = values.get(name)
        if value is not None:
            return value
    return None


def _relevant(run: RunEvidence, kpi_id: str) -> list[EvidenceObservation]:
    return [row for row in run.observations if row.eligible_for_rollup and (row.kpi_id is None or row.kpi_id == kpi_id)]


def _reduced(rows: list[EvidenceObservation], *, extra: bool = False) -> bool:
    return extra or any(row.confidence is None or row.confidence < 0.5 for row in rows)


def _event_ids(samples: list[_Sample]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(event_id for sample in samples for event_id in sample.source_event_ids))


def _metric_lives(run: RunEvidence) -> _RunMetric:
    rows = _relevant(run, "lives_saved_lagging")
    samples: list[_Sample] = []
    scales: set[Decimal] = set()
    for row in rows:
        scale = _decimal(
            _first(
                row.values,
                "annual_operational_tempo_scale",
                "operational_tempo_scale_per_year",
                "annualisation_factor",
            )
        )
        if scale is not None and scale > 0:
            scales.add(scale)
        fatalities = _decimal(_first(row.values, "modelled_fatalities", "fatalities", "fatality_count"))
        if fatalities is not None and fatalities >= 0:
            samples.append(_Sample(row.observation_id, fatalities, False, (row.event_id,)))
    if not samples or len(scales) != 1:
        return _RunMetric(None, (), (), True)
    scale = next(iter(scales))
    scaled = [_Sample(sample.key, sample.value * scale, sample.imputed, sample.source_event_ids) for sample in samples]
    return _RunMetric(
        value=sum((sample.value for sample in scaled), Decimal("0")),
        samples=tuple(scaled),
        source_event_ids=_event_ids(scaled),
        reduced_fidelity=_reduced(rows),
        operational_tempo_scale=scale,
    )


def _timestamp_groups(
    run: RunEvidence,
) -> list[tuple[str, CanonicalEventChain, tuple[str, ...], list[EvidenceObservation]]]:
    rows = _relevant(run, "response_time_p1")
    grouped: dict[str, dict[str, Any]] = {}
    group_rows: dict[str, list[EvidenceObservation]] = {}
    event_ids: dict[str, list[str]] = {}
    for row in rows:
        timestamp_values = {field: row.values.get(field) for field in CHAIN_FIELDS if row.values.get(field) is not None}
        if not timestamp_values:
            continue
        current = grouped.setdefault(row.observation_id, {})
        current.update(timestamp_values)
        supplied_imputed = row.values.get("imputed_fields")
        if isinstance(supplied_imputed, list):
            current["imputed_fields"] = [str(value) for value in supplied_imputed]
        group_rows.setdefault(row.observation_id, []).append(row)
        event_ids.setdefault(row.observation_id, []).append(row.event_id)

    output: list[tuple[str, CanonicalEventChain, tuple[str, ...], list[EvidenceObservation]]] = []
    for key in sorted(grouped):
        chain = CanonicalEventChain.model_validate(grouped[key])
        output.append((key, forward_impute(chain), tuple(dict.fromkeys(event_ids[key])), group_rows[key]))
    return output


def _metric_response(run: RunEvidence) -> _RunMetric:
    groups = _timestamp_groups(run)
    samples: list[_Sample] = []
    contributing_rows: list[EvidenceObservation] = []
    imputed_count = 0
    invalid = False
    for key, chain, source_ids, rows in groups:
        contributing_rows.extend(rows)
        if chain.imputed_fields:
            imputed_count += 1
        if chain.call_received_at is None or chain.controlled_at is None:
            invalid = True
            continue
        seconds = Decimal(str((chain.controlled_at - chain.call_received_at).total_seconds()))
        if seconds < 0:
            invalid = True
            continue
        samples.append(_Sample(key, seconds, bool(chain.imputed_fields), source_ids))
    if not samples:
        return _RunMetric(
            None,
            (),
            (),
            True,
            timestamp_row_count=len(groups),
            imputed_row_count=imputed_count,
        )
    return _RunMetric(
        value=Decimal(median([sample.value for sample in samples])),
        samples=tuple(samples),
        source_event_ids=_event_ids(samples),
        reduced_fidelity=_reduced(contributing_rows, extra=invalid or imputed_count > 0),
        timestamp_row_count=len(groups),
        imputed_row_count=imputed_count,
    )


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _metric_evacuation(run: RunEvidence) -> _RunMetric:
    rows = _relevant(run, "evac_lead_lagging")
    samples: list[_Sample] = []
    invalid = False
    for row in rows:
        direct = _decimal(_first(row.values, "evacuation_lead_time_hours", "evacuation_lead_hours"))
        if direct is None:
            completed = _parse_datetime(row.values.get("evacuation_completed_at"))
            impact = _parse_datetime(row.values.get("hazard_impact_at"))
            if completed is not None and impact is not None:
                direct = Decimal(str((impact - completed).total_seconds())) / Decimal("3600")
        if direct is None or direct < 0:
            invalid = True
            continue
        samples.append(_Sample(row.observation_id, direct, False, (row.event_id,)))
    if not samples:
        return _RunMetric(None, (), (), True)
    return _RunMetric(
        value=Decimal(median([sample.value for sample in samples])),
        samples=tuple(samples),
        source_event_ids=_event_ids(samples),
        reduced_fidelity=_reduced(rows, extra=invalid),
    )


def _metric_logistics(run: RunEvidence) -> _RunMetric:
    rows = _relevant(run, "logistics_efficiency")
    samples: list[_Sample] = []
    numerators: list[Decimal] = []
    denominators: list[Decimal] = []
    invalid = False
    for row in rows:
        numerator = _decimal(
            _first(
                row.values,
                "resources_on_task",
                "fulfilled_resource_requests",
                "resources_fulfilled",
                "logistics_numerator",
            )
        )
        denominator = _decimal(
            _first(
                row.values,
                "resources_requested",
                "resource_requests",
                "total_resource_requests",
                "logistics_denominator",
            )
        )
        if numerator is None or denominator is None or numerator < 0 or denominator <= 0:
            invalid = True
            continue
        numerators.append(numerator)
        denominators.append(denominator)
        samples.append(
            _Sample(
                row.observation_id,
                Decimal("100") * numerator / denominator,
                False,
                (row.event_id,),
            )
        )
    if not samples:
        return _RunMetric(None, (), (), True)
    value = Decimal("100") * sum(numerators, Decimal("0")) / sum(denominators, Decimal("0"))
    return _RunMetric(
        value=value,
        samples=tuple(samples),
        source_event_ids=_event_ids(samples),
        reduced_fidelity=_reduced(rows, extra=invalid),
    )


def _metric_economic(run: RunEvidence) -> _RunMetric:
    rows = _relevant(run, "econ_loss_lagging")
    samples: list[_Sample] = []
    invalid = False
    for row in rows:
        loss = _decimal(
            _first(
                row.values,
                "modelled_economic_loss_aud",
                "economic_loss_aud",
                "economic_loss",
            )
        )
        if loss is None or loss < 0:
            invalid = True
            continue
        samples.append(_Sample(row.observation_id, loss, False, (row.event_id,)))
    if not samples:
        return _RunMetric(None, (), (), True)
    return _RunMetric(
        value=sum((sample.value for sample in samples), Decimal("0")),
        samples=tuple(samples),
        source_event_ids=_event_ids(samples),
        reduced_fidelity=_reduced(rows, extra=invalid),
    )


_METRIC_READERS = {
    "lives_saved_lagging": _metric_lives,
    "response_time_p1": _metric_response,
    "evac_lead_lagging": _metric_evacuation,
    "logistics_efficiency": _metric_logistics,
    "econ_loss_lagging": _metric_economic,
}


def _delta(definition: MetricDefinition, baseline: Decimal, assisted: Decimal) -> Decimal:
    if definition.direction == "baseline_minus_assisted":
        return baseline - assisted
    return assisted - baseline


def _paired_samples(
    definition: MetricDefinition,
    baseline: tuple[_Sample, ...],
    assisted: tuple[_Sample, ...],
) -> tuple[_Sample, ...]:
    baseline_by_key = {sample.key: sample for sample in baseline}
    assisted_by_key = {sample.key: sample for sample in assisted}
    common = sorted(baseline_by_key.keys() & assisted_by_key.keys())
    pairs = [(baseline_by_key[key], assisted_by_key[key]) for key in common]
    if not pairs:
        pairs = list(zip(baseline, assisted, strict=False))
    return tuple(
        _Sample(
            key=f"{left.key}:{right.key}",
            value=_delta(definition, left.value, right.value),
            imputed=left.imputed or right.imputed,
            source_event_ids=tuple(dict.fromkeys((*left.source_event_ids, *right.source_event_ids))),
        )
        for left, right in pairs
    )


def _calculate_pair(pair: RunPairEvidence) -> dict[str, _PairMetric]:
    calculated: dict[str, _PairMetric] = {}
    for kpi_id in CAPSTONE_KPI_IDS:
        definition = CAPSTONE_METRIC_BY_ID[kpi_id]
        reader = _METRIC_READERS[kpi_id]
        baseline = reader(pair.baseline)
        assisted = reader(pair.ama_assisted)
        if (
            kpi_id == "lives_saved_lagging"
            and baseline.operational_tempo_scale is not None
            and assisted.operational_tempo_scale is not None
            and baseline.operational_tempo_scale != assisted.operational_tempo_scale
        ):
            raise EvidenceMetadataError("baseline and AMA-assisted annual operational-tempo scales differ")
        absolute: Decimal | None = None
        percent: Decimal | None = None
        if baseline.value is not None and assisted.value is not None:
            absolute = _delta(definition, baseline.value, assisted.value)
            if baseline.value != 0:
                percent = Decimal("100") * absolute / baseline.value
        calculated[kpi_id] = _PairMetric(
            definition=definition,
            baseline=baseline,
            assisted=assisted,
            absolute_delta=absolute,
            percent_delta=percent,
            delta_samples=_paired_samples(definition, baseline.samples, assisted.samples),
        )
    return calculated


def _stable_seed(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode()).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _statistic(kpi_id: str) -> Statistic:
    if kpi_id in {"response_time_p1", "evac_lead_lagging"}:
        return "median"
    if kpi_id in {"lives_saved_lagging", "econ_loss_lagging"}:
        return "sum"
    return "mean"


def _meets_target(metric: _PairMetric) -> bool:
    measured = metric.absolute_delta if metric.definition.target_measure == "absolute_delta" else metric.percent_delta
    return measured is not None and measured >= metric.definition.target_value


def _build_delta(
    metric: _PairMetric,
    *,
    scenario_id: str,
    seed: str,
    run_pair_id: str,
    n_resamples: int,
    force_small_sample: bool,
) -> KpiDelta:
    missing = metric.missing_modes
    source_ids = tuple(dict.fromkeys((*metric.baseline.source_event_ids, *metric.assisted.source_event_ids)))
    if missing:
        return KpiDelta(
            kpi_id=metric.definition.kpi_id,
            definition_version=FORMULA_VERSION,
            formula_version=metric.definition.formula_version,
            formula=metric.definition.formula,
            unit=metric.definition.unit,
            delta_unit=metric.definition.delta_unit,
            calibration_reference=metric.definition.calibration_reference,
            measurement_status="no_signal",
            missing_modes=missing,
            baseline_value=_q(metric.baseline.value),
            ama_assisted_value=_q(metric.assisted.value),
            absolute_delta=None,
            percent_delta=None,
            confidence_band_low=None,
            confidence_band_high=None,
            confidence_method=None,
            meets_target=False,
            small_sample=True,
            reduced_fidelity=True,
            source_event_ids=list(source_ids),
        )

    interval_samples = [sample.value for sample in metric.delta_samples if not sample.imputed]
    band = bootstrap_ci(
        [float(value) for value in interval_samples],
        seed=_stable_seed(
            scenario_id,
            seed,
            run_pair_id,
            metric.definition.kpi_id,
            metric.definition.formula_version,
        ),
        n_resamples=n_resamples,
        statistic=_statistic(metric.definition.kpi_id),
        fallback_point_estimate=float(metric.absolute_delta or Decimal("0")),
    )
    imputed_count = sum(sample.imputed for sample in metric.delta_samples)
    small_sample = force_small_sample or band.label == "small-sample"
    reduced = metric.baseline.reduced_fidelity or metric.assisted.reduced_fidelity or small_sample
    return KpiDelta(
        kpi_id=metric.definition.kpi_id,
        definition_version=FORMULA_VERSION,
        formula_version=metric.definition.formula_version,
        formula=metric.definition.formula,
        unit=metric.definition.unit,
        delta_unit=metric.definition.delta_unit,
        calibration_reference=metric.definition.calibration_reference,
        measurement_status="measured",
        baseline_value=_q(metric.baseline.value),
        ama_assisted_value=_q(metric.assisted.value),
        absolute_delta=_q(metric.absolute_delta),
        percent_delta=_q(metric.percent_delta),
        confidence_band_low=_q(Decimal(str(band.low))),
        confidence_band_high=_q(Decimal(str(band.high))),
        confidence_method=band.method,
        confidence_observation_count=band.n_samples,
        bootstrap_resamples=band.n_resamples,
        imputed_observation_count=imputed_count,
        meets_target=_meets_target(metric),
        small_sample=small_sample,
        reduced_fidelity=reduced,
        source_event_ids=list(source_ids),
    )


def _unique(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _provenance(run: RunEvidence) -> RunProvenance:
    observations = list(run.observations)
    return RunProvenance(
        mode=run.mode,
        source_run_id=run.source_run_id,
        scenario_version=run.scenario_version,
        scenario_content_hash=run.scenario_content_hash,
        seed=run.seed,
        source_event_ids=_unique([row.event_id for row in observations]),
        event_timestamps=list(dict.fromkeys(row.event_timestamp for row in observations)),
        confidence_values=[
            value
            for row in observations
            if row.confidence is not None and (value := _q(Decimal(str(row.confidence)))) is not None
        ],
        signal_ids=_unique([row.signal_id for row in observations]),
        model_output_ids=_unique([row.model_output_id for row in observations]),
        recommendation_ids=_unique([row.recommendation_id for row in observations]),
        human_decision_ids=_unique([row.human_decision_id for row in observations]),
        outcome_ids=_unique([row.outcome_id for row in observations]),
        component_versions=_unique([row.component_version for row in observations]),
        rejected_event_ids=list(run.rejected_event_ids),
    )


def _missing(calculations: Mapping[str, _PairMetric]) -> dict[str, list[RunMode]]:
    return {kpi_id: metric.missing_modes for kpi_id, metric in calculations.items() if metric.missing_modes}


def _determinism(
    repetitions: list[dict[str, _PairMetric]],
) -> DeterminismCheck | None:
    if len(repetitions) < 2:
        return None
    reference = repetitions[0]
    total = 0
    within = 0
    for repeated in repetitions[1:]:
        for kpi_id in CAPSTONE_KPI_IDS:
            total += 1
            left = reference[kpi_id].absolute_delta
            right = repeated[kpi_id].absolute_delta
            if left is None or right is None:
                if left is None and right is None and reference[kpi_id].missing_modes == repeated[kpi_id].missing_modes:
                    within += 1
                continue
            if within_tolerance(
                float(right),
                float(left),
                rel_pct=DEFAULT_TOL_REL_PCT,
                abs_unit=DEFAULT_TOL_ABS_UNIT,
            ):
                within += 1
    return DeterminismCheck(
        repetition_count=total,
        within_tolerance_count=within,
        diverged=within < total,
    )


def build_scorecard(
    *,
    scenario_id: str,
    seed: str,
    run_pair_id: str,
    event_source: EvidenceEventSource,
    repetitions: int = 1,
    allow_degraded_mode: bool = True,
    source_run_ids: Mapping[RunMode, str] | None = None,
    signoff_resolver: ImputationSignoffResolver | None = None,
    n_resamples: int = DEFAULT_MIN_RESAMPLES,
    correlation_id: str = "",
) -> DeltaScorecard:
    if not 1 <= repetitions <= MAX_REPETITIONS:
        raise ValueError(f"repetitions must be between 1 and {MAX_REPETITIONS}")
    if not 1 <= n_resamples <= MAX_BOOTSTRAP_RESAMPLES:
        raise ValueError(f"n_resamples must be between 1 and {MAX_BOOTSTRAP_RESAMPLES}")

    pairs: list[RunPairEvidence] = []
    calculations: list[dict[str, _PairMetric]] = []
    for repetition_index in range(repetitions):
        pair = event_source.load_run_pair(
            scenario_id=scenario_id,
            seed=seed,
            run_pair_id=run_pair_id,
            source_run_ids=source_run_ids,
            repetition_index=repetition_index,
        )
        calculated = _calculate_pair(pair)
        missing = _missing(calculated)
        if missing and not allow_degraded_mode:
            raise MissingEvidenceSourceError(missing)
        pairs.append(pair)
        calculations.append(calculated)

    canonical_pair = pairs[0]
    canonical = calculations[0]
    timestamp_rows = sum(
        metric.baseline.timestamp_row_count + metric.assisted.timestamp_row_count for metric in canonical.values()
    )
    imputed_rows = sum(
        metric.baseline.imputed_row_count + metric.assisted.imputed_row_count for metric in canonical.values()
    )
    imputation_share = Decimal(imputed_rows) / Decimal(timestamp_rows) if timestamp_rows else Decimal("0")

    signoff: NamedAuditorSignoff | None = None
    if imputation_share > Decimal("0.10"):
        if signoff_resolver is not None:
            signoff = signoff_resolver.resolve(
                scenario_id=scenario_id,
                run_pair_id=run_pair_id,
                scenario_content_hash=canonical_pair.scenario_content_hash,
                imputation_share=imputation_share,
            )
        if signoff is None or not signoff.approval_id or not signoff.auditor_id:
            raise ImputationSignoffRequiredError(imputation_share)

    deltas = [
        _build_delta(
            canonical[kpi_id],
            scenario_id=scenario_id,
            seed=seed,
            run_pair_id=run_pair_id,
            n_resamples=n_resamples,
            force_small_sample=imputation_share > Decimal("0.10"),
        )
        for kpi_id in CAPSTONE_KPI_IDS
    ]
    return DeltaScorecard(
        id=scorecard_id_for(run_pair_id),
        scenario_id=scenario_id,
        scenario_version=canonical_pair.scenario_version,
        scenario_content_hash=canonical_pair.scenario_content_hash,
        seed=seed,
        run_pair_id=run_pair_id,
        idempotency_key=f"run_pair:{run_pair_id}",
        kpi_deltas=deltas,
        run_provenance=[_provenance(canonical_pair.baseline), _provenance(canonical_pair.ama_assisted)],
        determinism=_determinism(calculations),
        imputation_share=_q(imputation_share) or Decimal("0"),
        auditor_signoff_id=signoff.approval_id if signoff else None,
        auditor_id=signoff.auditor_id if signoff else None,
        reduced_fidelity=any(delta.reduced_fidelity for delta in deltas),
        created_at=datetime.now(UTC),
        correlation_id=correlation_id,
    )
