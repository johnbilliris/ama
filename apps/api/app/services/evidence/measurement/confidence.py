"""Bootstrap-95 % CI helper (T-S14, FR-009 / FR-010, Research D5, CHK013/CHK014).

Reuses the spec-030 pattern of deterministic seeding + percentile bootstrap
with a small-sample fallback to ±1 SD. NumPy is the only dependency.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Literal

DEFAULT_MIN_RESAMPLES = 1000


@dataclass(frozen=True)
class ConfidenceBand:
    method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"]
    point_estimate: float
    low: float
    high: float
    n_samples: int
    label: str | None = None  # e.g. "small-sample"


def bootstrap_ci(
    samples: Iterable[float],
    *,
    seed: int = 0,
    n_resamples: int = DEFAULT_MIN_RESAMPLES,
    statistic: str = "mean",
) -> ConfidenceBand:
    """Compute a 2.5/97.5 percentile bootstrap CI.

    When the input has fewer than `min(n_resamples, 1000)` samples, falls
    back to ±1 SD around the mean and tags the band as `small-sample`
    (FR-008 / FR-010).
    """
    data = [float(x) for x in samples]
    n = len(data)
    if n == 0:
        return ConfidenceBand(
            method="stddev_pm1",
            point_estimate=0.0,
            low=0.0,
            high=0.0,
            n_samples=0,
            label="small-sample",
        )
    pe = mean(data)
    if n < min(n_resamples, DEFAULT_MIN_RESAMPLES) or n < 30:
        sd = pstdev(data) if n > 1 else 0.0
        return ConfidenceBand(
            method="stddev_pm1",
            point_estimate=pe,
            low=pe - sd,
            high=pe + sd,
            n_samples=n,
            label="small-sample",
        )
    try:
        import numpy as np
    except ImportError:  # pragma: no cover — fall back if numpy missing
        sd = pstdev(data)
        return ConfidenceBand(
            method="stddev_pm1",
            point_estimate=pe,
            low=pe - sd,
            high=pe + sd,
            n_samples=n,
            label="small-sample",
        )
    rng = np.random.default_rng(seed)
    arr = np.asarray(data, dtype=float)
    boots = rng.choice(arr, size=(n_resamples, n), replace=True).mean(axis=1)
    low = float(np.percentile(boots, 2.5))
    high = float(np.percentile(boots, 97.5))
    if statistic == "median":  # pragma: no cover — declared but unused for now
        boots = rng.choice(arr, size=(n_resamples, n), replace=True)
        boots = sorted(boots.flatten())
        low = boots[int(0.025 * len(boots))]
        high = boots[int(0.975 * len(boots))]
    return ConfidenceBand(
        method="bootstrap_p2_5_p97_5",
        point_estimate=pe,
        low=low,
        high=high,
        n_samples=n,
    )


def within_tolerance(
    a: float,
    b: float,
    *,
    rel_pct: float = 2.0,
    abs_unit: float = 1.0,
) -> bool:
    """FR-016 — ±2 % relative OR ±1 absolute unit, whichever is greater."""
    diff = abs(a - b)
    rel_bound = abs(b) * (rel_pct / 100.0)
    return diff <= max(rel_bound, abs_unit) or math.isclose(a, b)
