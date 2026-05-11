"""Pillar C — Delta scorecard builder (T-C07, FR-015/016/027)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from ..measurement.confidence import bootstrap_ci, within_tolerance
from ..models.scorecard import (
    DEFAULT_TOL_ABS_UNIT,
    DEFAULT_TOL_REL_PCT,
    DeltaScorecard,
    DeterminismCheck,
    KpiDelta,
)
from .orchestrator import synthesise_pair

CAPSTONE_KPI_IDS = (
    "lives_saved_lagging",
    "response_time_p1",
    "evac_lead_lagging",
    "logistics_efficiency",
    "econ_loss_lagging",
)


def _delta(baseline: float, ama: float) -> tuple[float, float]:
    abs_d = ama - baseline
    pct = (abs_d / baseline * 100.0) if baseline else 0.0
    return abs_d, pct


def _meets_target(kpi_id: str, ama: float, baseline: float) -> bool:
    """Lower-is-better for response_time; higher-is-better for the others."""
    if kpi_id == "response_time_p1":
        return ama < baseline
    return ama > baseline


def build_scorecard(
    *,
    scenario_id: str,
    seed: str,
    run_pair_id: str,
    repetitions: int = 1,
    reduced_fidelity: bool = False,
    correlation_id: str = "",
) -> DeltaScorecard:
    deltas: list[KpiDelta] = []
    per_kpi_runs: dict[str, list[tuple[float, float]]] = {}
    for kpi in CAPSTONE_KPI_IDS:
        runs: list[tuple[float, float]] = []
        for rep in range(max(1, repetitions)):
            rep_seed = f"{seed}#{rep}"
            b, a = synthesise_pair(seed=rep_seed, scenario_id=scenario_id, kpi_id=kpi)
            runs.append((b, a))
        per_kpi_runs[kpi] = runs
        # Use the first run as the canonical scorecard value; CI from all reps.
        baseline_v, ama_v = runs[0]
        abs_d, pct = _delta(baseline_v, ama_v)
        ci = bootstrap_ci([a for _, a in runs], seed=hash(seed + kpi) & 0xFFFFFFFF)
        deltas.append(
            KpiDelta(
                kpi_id=kpi,
                baseline_value=Decimal(f"{baseline_v:.4f}"),
                ama_assisted_value=Decimal(f"{ama_v:.4f}"),
                absolute_delta=Decimal(f"{abs_d:.4f}"),
                percent_delta=Decimal(f"{pct:.4f}"),
                confidence_band_low=Decimal(f"{ci.low:.4f}"),
                confidence_band_high=Decimal(f"{ci.high:.4f}"),
                confidence_method=ci.method,
                meets_target=_meets_target(kpi, ama_v, baseline_v),
                small_sample=(ci.label == "small-sample"),
                reduced_fidelity=reduced_fidelity,
            )
        )

    # Determinism check across repetitions of AMA-assisted value (FR-016).
    determinism: DeterminismCheck | None = None
    if repetitions >= 2:
        within = 0
        total = 0
        for kpi, runs in per_kpi_runs.items():
            ref_ama = runs[0][1]
            for b, a in runs[1:]:
                total += 1
                if within_tolerance(
                    a,
                    ref_ama,
                    rel_pct=DEFAULT_TOL_REL_PCT,
                    abs_unit=DEFAULT_TOL_ABS_UNIT,
                ):
                    within += 1
        determinism = DeterminismCheck(
            repetition_count=total,
            within_tolerance_count=within,
            diverged=(within < total),
        )

    return DeltaScorecard(
        id=secrets.token_hex(13),
        scenario_id=scenario_id,
        seed=seed,
        run_pair_id=run_pair_id,
        kpi_deltas=deltas,
        determinism=determinism,
        reduced_fidelity=reduced_fidelity,
        created_at=datetime.now(UTC),
        correlation_id=correlation_id,
    )
