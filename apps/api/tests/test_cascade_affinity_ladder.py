"""Phase D — cascade affinity ladder tests (T-D03 / FR-057)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from apps.api.app.services.simulation.cascade_affinity_ladder import (
    CandidateThread,
    CascadeTrigger,
    select,
)


def _ts(offset_seconds: int) -> datetime:
    return datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(seconds=offset_seconds)


def _candidate(
    thread_id: str,
    *,
    jurisdiction: str | None = None,
    hazard: str | None = None,
    origin: str | None = None,
    mutated_offset: int = 0,
    creation_id: str | None = None,
) -> CandidateThread:
    return CandidateThread(
        thread_id=thread_id,
        jurisdiction_code=jurisdiction,
        hazard_class=hazard,
        origin_cascade_id=origin,
        last_mutated_at=_ts(mutated_offset),
        thread_creation_id=creation_id or thread_id,
    )


def test_step1_jurisdiction_match_wins_uniquely() -> None:
    trig = CascadeTrigger(jurisdiction_code="AU-NSW", hazard_class=None, origin_cascade_id=None)
    cands = [
        _candidate("t1", jurisdiction="AU-VIC"),
        _candidate("t2", jurisdiction="AU-NSW"),
    ]
    res = select(trigger=trig, candidates=cands)
    assert res is not None
    assert res.chosen.thread_id == "t2"
    assert res.step == 1


def test_step2_hazard_match_resolves_jurisdiction_tie() -> None:
    trig = CascadeTrigger(
        jurisdiction_code="AU-NSW",
        hazard_class="bushfire",
        origin_cascade_id=None,
    )
    cands = [
        _candidate("t1", jurisdiction="AU-NSW", hazard="flood"),
        _candidate("t2", jurisdiction="AU-NSW", hazard="bushfire"),
    ]
    res = select(trigger=trig, candidates=cands)
    assert res is not None
    assert res.chosen.thread_id == "t2"
    assert res.step == 2


def test_step3_origin_cascade_resolves_after_jurisdiction_and_hazard() -> None:
    trig = CascadeTrigger(
        jurisdiction_code="AU-NSW",
        hazard_class="bushfire",
        origin_cascade_id="origin-X",
    )
    cands = [
        _candidate("t1", jurisdiction="AU-NSW", hazard="bushfire", origin="origin-Y"),
        _candidate("t2", jurisdiction="AU-NSW", hazard="bushfire", origin="origin-X"),
    ]
    res = select(trigger=trig, candidates=cands)
    assert res is not None
    assert res.chosen.thread_id == "t2"
    assert res.step == 3


def test_step4_most_recent_mutation_wins_when_others_tie() -> None:
    trig = CascadeTrigger(
        jurisdiction_code="AU-NSW",
        hazard_class="bushfire",
        origin_cascade_id="origin-X",
    )
    cands = [
        _candidate(
            "t1",
            jurisdiction="AU-NSW",
            hazard="bushfire",
            origin="origin-X",
            mutated_offset=10,
        ),
        _candidate(
            "t2",
            jurisdiction="AU-NSW",
            hazard="bushfire",
            origin="origin-X",
            mutated_offset=20,
        ),
    ]
    res = select(trigger=trig, candidates=cands)
    assert res is not None
    assert res.chosen.thread_id == "t2"
    assert res.step == 4


def test_step5_creation_id_ascending_final_tiebreaker() -> None:
    trig = CascadeTrigger(
        jurisdiction_code="AU-NSW",
        hazard_class="bushfire",
        origin_cascade_id="origin-X",
    )
    cands = [
        _candidate(
            "t1",
            jurisdiction="AU-NSW",
            hazard="bushfire",
            origin="origin-X",
            mutated_offset=10,
            creation_id="01H...B",
        ),
        _candidate(
            "t2",
            jurisdiction="AU-NSW",
            hazard="bushfire",
            origin="origin-X",
            mutated_offset=10,
            creation_id="01H...A",
        ),
    ]
    res = select(trigger=trig, candidates=cands)
    assert res is not None
    assert res.chosen.thread_id == "t2"
    assert res.step == 5


def test_empty_candidates_returns_none() -> None:
    trig = CascadeTrigger(jurisdiction_code=None, hazard_class=None, origin_cascade_id=None)
    assert select(trigger=trig, candidates=[]) is None


@pytest.mark.parametrize("seed", list(range(20)))
def test_deterministic_across_random_input_orderings(seed: int) -> None:
    """FR-057 byte-determinism: same input set → same chosen thread regardless of order."""
    import random

    rng = random.Random(seed)
    trig = CascadeTrigger(
        jurisdiction_code="AU-NSW",
        hazard_class="bushfire",
        origin_cascade_id="origin-X",
    )
    base = [
        _candidate(
            f"t{i}",
            jurisdiction=rng.choice(["AU-NSW", "AU-VIC"]),
            hazard=rng.choice(["bushfire", "flood"]),
            origin=rng.choice(["origin-X", "origin-Y"]),
            mutated_offset=rng.randint(0, 100),
            creation_id=f"01H{i:04d}",
        )
        for i in range(8)
    ]
    shuffled = list(base)
    rng.shuffle(shuffled)
    canonical = select(trigger=trig, candidates=base)
    perturbed = select(trigger=trig, candidates=shuffled)
    assert canonical is not None and perturbed is not None
    assert canonical.chosen.thread_id == perturbed.chosen.thread_id
    assert canonical.step == perturbed.step
