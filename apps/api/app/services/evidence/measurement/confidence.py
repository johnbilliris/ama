# Deterministic confidence bands for evidence scorecards.

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean, median, pstdev
from typing import Literal

DEFAULT_MIN_RESAMPLES = 1000
Statistic = Literal["mean", "median", "sum"]


@dataclass(frozen=True)
class ConfidenceBand:
    method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"]
    point_estimate: float
    low: float
    high: float
    n_samples: int
    n_resamples: int = 0
    label: str | None = None


def _point_estimate(data: list[float], statistic: Statistic) -> float:
    if statistic == "median":
        return float(median(data))
    if statistic == "sum":
        return float(sum(data))
    return float(mean(data))


def _small_sample_band(
    data: list[float],
    *,
    statistic: Statistic,
    fallback_point_estimate: float | None,
) -> ConfidenceBand:
    point = (
        float(fallback_point_estimate)
        if fallback_point_estimate is not None
        else (_point_estimate(data, statistic) if data else 0.0)
    )
    deviation = pstdev(data) if len(data) > 1 else 0.0
    return ConfidenceBand(
        method="stddev_pm1",
        point_estimate=point,
        low=point - deviation,
        high=point + deviation,
        n_samples=len(data),
        label="small-sample",
    )


def bootstrap_ci(
    samples: Iterable[float],
    *,
    seed: int = 0,
    n_resamples: int = DEFAULT_MIN_RESAMPLES,
    statistic: Statistic = "mean",
    fallback_point_estimate: float | None = None,
) -> ConfidenceBand:
    # A bootstrap may draw at least 1000 resamples from a small raw sample.
    # Fallback depends on available observations and requested resamples, not
    # on an incorrect requirement for 1000 raw observations.
    data = [float(value) for value in samples if math.isfinite(float(value))]
    if len(data) < 2 or n_resamples < DEFAULT_MIN_RESAMPLES:
        return _small_sample_band(
            data,
            statistic=statistic,
            fallback_point_estimate=fallback_point_estimate,
        )

    try:
        import numpy as np
    except ImportError:  # pragma: no cover
        return _small_sample_band(
            data,
            statistic=statistic,
            fallback_point_estimate=fallback_point_estimate,
        )

    rng = np.random.default_rng(seed)
    values = np.asarray(data, dtype=float)
    draws = rng.choice(values, size=(n_resamples, len(values)), replace=True)
    if statistic == "median":
        estimates = np.median(draws, axis=1)
    elif statistic == "sum":
        estimates = np.sum(draws, axis=1)
    else:
        estimates = np.mean(draws, axis=1)
    return ConfidenceBand(
        method="bootstrap_p2_5_p97_5",
        point_estimate=_point_estimate(data, statistic),
        low=float(np.percentile(estimates, 2.5)),
        high=float(np.percentile(estimates, 97.5)),
        n_samples=len(data),
        n_resamples=n_resamples,
    )


def within_tolerance(
    a: float,
    b: float,
    *,
    rel_pct: float = 2.0,
    abs_unit: float = 1.0,
) -> bool:
    # FR-016 uses the greater of the relative and absolute bounds.
    diff = abs(a - b)
    rel_bound = abs(b) * (rel_pct / 100.0)
    return diff <= max(rel_bound, abs_unit) or math.isclose(a, b)
