"""T-J15 — SC-004 ≥30 % reallocation reduction harness.

Asserts that across 30 paired exercises the auto-fan-out treatment cuts
last-minute resource reallocations by ≥30 % vs. control (per FR-024 /
FR-025 routing improvements).
"""

from __future__ import annotations

import pytest

from tests.simulation.paired_exercise_harness import run_paired_exercises
from tests.staging_gates import measurement_staging_enabled


def test_sc004_mean_reduction_at_least_30pct() -> None:
    pairs = run_paired_exercises(num_pairs=30)
    deltas = [p.reallocation_reduction_pct for p in pairs]
    mean = sum(deltas) / len(deltas)
    assert mean >= 0.30, f"SC-004 missed: mean reduction={mean:.3f}"


def test_sc004_per_pair_at_least_25_of_30_below_30pct_of_baseline() -> None:
    """At least 25 of 30 pairs realise ≥30 % cut individually."""
    pairs = run_paired_exercises(num_pairs=30)
    hits = sum(1 for p in pairs if p.reallocation_reduction_pct >= 0.30)
    assert hits >= 25, f"SC-004 per-pair cohort: {hits}/30 ≥ 30 % cut"


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled(),
    reason="staging-only — set AMA_STAGING_MEASUREMENT=1 to run 30 live paired exercises.",
)
def test_sc004_live_paired_run() -> None:
    pairs = run_paired_exercises(num_pairs=30)
    assert len(pairs) == 30
