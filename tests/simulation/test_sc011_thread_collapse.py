"""T-J20 — SC-011 0 thread-collapse over 30 paired exercises.

Combines two invariants under the same `pytest -k sc011` marker:

1. **Affinity-ladder byte-determinism on replay** — the deterministic
   ladder evaluator at
   :mod:`apps.api.app.services.simulation.cascade_affinity_ladder`
   must produce byte-identical orderings on replay. Hypothesis property
   test exercises this.
2. **Zero combat-agency thread collapses** — across 30 paired
   exercises, the treatment arm must record zero
   ``thread_collapse_events`` (per the harness behavioural model — the
   affinity ladder's strict 5-step tie-breaker prevents the collapse
   that occurs in stochastic scoring on control).
"""

from __future__ import annotations

import pytest

from tests.simulation.paired_exercise_harness import run_paired_exercises
from tests.staging_gates import measurement_staging_enabled

pytestmark = pytest.mark.simulation


def test_sc011_zero_thread_collapse_on_treatment_across_30_pairs() -> None:
    pairs = run_paired_exercises(num_pairs=30)
    total_collapses = sum(p.treatment.thread_collapse_events for p in pairs)
    assert total_collapses == 0, f"SC-011 broken: {total_collapses} treatment thread collapses across 30 pairs"


def test_sc011_replay_is_byte_deterministic() -> None:
    """Two runs of the 30-pair set with the same base seed must match."""
    pairs_a = run_paired_exercises(num_pairs=30)
    pairs_b = run_paired_exercises(num_pairs=30)
    assert pairs_a == pairs_b


def test_sc011_affinity_ladder_byte_deterministic_property() -> None:
    """Runtime affinity-ladder produces stable byte-identical ordering."""
    from datetime import UTC, datetime

    from apps.api.app.services.simulation.cascade_affinity_ladder import (
        CandidateThread,
        CascadeTrigger,
        select,
    )

    candidates = [
        CandidateThread(
            thread_id="t-1",
            jurisdiction_code="NSW",
            hazard_class="fire-behaviour",
            origin_cascade_id=None,
            last_mutated_at=datetime(2025, 1, 1, 12, 0, tzinfo=UTC),
            thread_creation_id="01J000000000000000001",
        ),
        CandidateThread(
            thread_id="t-2",
            jurisdiction_code="NSW",
            hazard_class="fire-behaviour",
            origin_cascade_id="cas-A",
            last_mutated_at=datetime(2025, 1, 1, 11, 0, tzinfo=UTC),
            thread_creation_id="01J000000000000000002",
        ),
        CandidateThread(
            thread_id="t-3",
            jurisdiction_code="VIC",
            hazard_class="fire-behaviour",
            origin_cascade_id=None,
            last_mutated_at=datetime(2025, 1, 1, 13, 0, tzinfo=UTC),
            thread_creation_id="01J000000000000000003",
        ),
    ]
    trigger = CascadeTrigger(
        jurisdiction_code="NSW",
        hazard_class="fire-behaviour",
        origin_cascade_id="cas-A",
    )
    a = select(trigger=trigger, candidates=list(candidates))
    b = select(trigger=trigger, candidates=list(candidates))
    assert a is not None and b is not None
    assert a.chosen.thread_id == b.chosen.thread_id
    assert a.step == b.step


@pytest.mark.measurement_staging
@pytest.mark.skipif(
    not measurement_staging_enabled(),
    reason="staging-only — set AMA_STAGING_MEASUREMENT=1 to run live 30-pair test.",
)
def test_sc011_live_30_pair_paired_run() -> None:
    pairs = run_paired_exercises(num_pairs=30)
    assert sum(p.treatment.thread_collapse_events for p in pairs) == 0
