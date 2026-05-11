"""T-J22 — Tests for the paired-exercise harness.

The harness is byte-deterministic — replays produce identical pairs
given the same base seed. These tests pin the contract.
"""

from __future__ import annotations

import math

from tests.simulation.paired_exercise_harness import (
    CONTROL_SEED_FLIP,
    make_scenarios,
    mean_and_95ci,
    run_pair,
    run_paired_exercises,
    to_ndjson_record,
)


def test_make_scenarios_count_and_determinism() -> None:
    """30 pairs is the canonical SC-002/003/004/005/011 sample."""
    a = make_scenarios(num_pairs=30)
    b = make_scenarios(num_pairs=30)
    assert len(a) == 30
    # Byte-deterministic: same seed → same scenarios.
    assert [s.seed for s in a] == [s.seed for s in b]
    assert [s.hazard for s in a] == [s.hazard for s in b]


def test_run_pair_treatment_seed_differs_from_control() -> None:
    scenarios = make_scenarios(num_pairs=1)
    pair = run_pair(scenarios[0])
    assert pair.treatment.seed != pair.control.seed
    assert pair.treatment.seed == scenarios[0].seed
    assert pair.control.seed == scenarios[0].seed ^ CONTROL_SEED_FLIP


def test_run_pair_replays_byte_deterministic() -> None:
    s = make_scenarios(num_pairs=1)[0]
    p1 = run_pair(s)
    p2 = run_pair(s)
    assert p1 == p2  # frozen dataclass equality


def test_treatment_arm_response_time_at_least_halves() -> None:
    """SC-002 — Capstone 50 % response-time cut realises across 30 pairs."""
    pairs = run_paired_exercises(num_pairs=30)
    # Mean treatment response time must be ≤50 % of control mean.
    mean_treat = sum(p.treatment.response_time_seconds for p in pairs) / len(pairs)
    mean_ctrl = sum(p.control.response_time_seconds for p in pairs) / len(pairs)
    assert mean_treat <= 0.5 * mean_ctrl, (
        f"SC-002 broken: mean treatment={mean_treat:.1f}s vs control={mean_ctrl:.1f}s"
    )


def test_treatment_arm_zero_thread_collapses() -> None:
    """SC-011 — affinity ladder byte-deterministic, zero collapses on treatment."""
    pairs = run_paired_exercises(num_pairs=30)
    for p in pairs:
        assert p.treatment.thread_collapse_events == 0


def test_treatment_arm_realises_30pct_economic_loss_reduction() -> None:
    """SC-005 — mean economic-loss reduction ≥ 30 % across 30 pairs."""
    pairs = run_paired_exercises(num_pairs=30)
    deltas_pct = [p.economic_loss_delta_pct for p in pairs]
    mean, lo, _hi = mean_and_95ci(deltas_pct)
    assert mean >= 0.30, (
        f"SC-005 broken: mean economic-loss reduction={mean:.3f} < 0.30"
    )
    # Two-sided 95 % CI excludes 0 (i.e. signed reduction is strictly positive).
    assert lo > 0, f"SC-005 95 % CI low={lo:.3f} not > 0"


def test_treatment_arm_realises_30pct_reallocation_reduction() -> None:
    """SC-004 — mean reallocation reduction ≥ 30 %."""
    pairs = run_paired_exercises(num_pairs=30)
    deltas = [p.reallocation_reduction_pct for p in pairs]
    mean = sum(deltas) / len(deltas)
    assert mean >= 0.30


def test_to_ndjson_record_keys() -> None:
    pairs = run_paired_exercises(num_pairs=1)
    rec = to_ndjson_record(pairs[0])
    expected_keys = {
        "pair_id",
        "scenario_hazard",
        "scenario_jurisdiction",
        "duration_hours",
        "seed",
        "treatment_response_time_s",
        "control_response_time_s",
        "treatment_evac_at_s",
        "control_evac_at_s",
        "treatment_reallocations",
        "control_reallocations",
        "treatment_thread_collapses",
        "control_thread_collapses",
        "treatment_loss_m",
        "control_loss_m",
        "delta_loss_m",
        "delta_pct",
    }
    assert expected_keys.issubset(rec.keys())


def test_mean_and_95ci_handles_empty_and_single() -> None:
    assert mean_and_95ci([]) == (0.0, 0.0, 0.0)
    assert mean_and_95ci([3.0]) == (3.0, 3.0, 3.0)
    mean, lo, hi = mean_and_95ci([1.0, 2.0, 3.0])
    assert math.isclose(mean, 2.0, abs_tol=1e-9)
    assert lo < mean < hi
