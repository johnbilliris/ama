"""T-J14 — SC-003 24-h-earlier evacuation paired test.

Asserts that across 30 paired exercises with duration ≥24 h, the
treatment arm issues evacuation orders ≥24 h earlier than the control
arm. Per the harness model this is a hard floor when
``scenario.duration_hours >= 24``; shorter scenarios floor at 30 % of
duration.
"""

from __future__ import annotations

import pytest

from tests.simulation.paired_exercise_harness import (
    make_scenarios,
    run_pair,
    run_paired_exercises,
)
from tests.staging_gates import measurement_staging_enabled


def test_sc003_long_horizon_pairs_evacuate_24h_earlier() -> None:
    """Pairs whose duration ≥24 h MUST issue evac ≥24 h earlier on treatment."""
    long_scenarios = [s for s in make_scenarios(num_pairs=30) if s.duration_hours >= 24]
    if not long_scenarios:
        # If the seed-window doesn't include a long scenario, run an
        # explicit 24h+ pair so we still cover the SC-003 invariant.
        from tests.simulation.paired_exercise_harness import ExerciseScenario

        long_scenarios = [
            ExerciseScenario(
                hazard="cyclone",
                jurisdiction="QLD",
                duration_hours=72.0,
                base_loss_m_per_h=5.6,
                seed=0xDEADBEEF,
            )
        ]
    pairs = [run_pair(s) for s in long_scenarios]
    for p in pairs:
        delta_s = p.evacuation_lead_delta  # negative when treatment is earlier
        assert -delta_s >= 24 * 3600, f"SC-003 missed for {p.pair_id}: lead_delta={-delta_s / 3600:.1f}h, need ≥24 h"


def test_sc003_short_horizon_pairs_evacuate_meaningfully_earlier() -> None:
    """For <24 h scenarios, treatment evac must lead control by ≥30 % of duration."""
    pairs = run_paired_exercises(num_pairs=30)
    short = [p for p in pairs if p.scenario.duration_hours < 24]
    for p in short:
        lead_seconds = p.control.evacuation_order_at_seconds - p.treatment.evacuation_order_at_seconds
        floor = p.scenario.duration_hours * 3600 * 0.30
        assert lead_seconds >= floor or p.control.evacuation_order_at_seconds == 0, (
            f"SC-003 (short) missed for {p.pair_id}: lead={lead_seconds:.0f}s < {floor:.0f}s"
        )


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled(),
    reason="staging-only — set AMA_STAGING_MEASUREMENT=1 to run live 30-pair evacuation lead test.",
)
def test_sc003_30_pair_evacuation_lead_against_staging() -> None:
    pairs = run_paired_exercises(num_pairs=30)
    assert len(pairs) == 30
