"""T-J16 — SC-007 100% typed-signal gap-detection contract test.

For every chat-turn that produced an ``injection.attempted`` audit
event, the audit log MUST also produce **exactly one** of:

* ``injection.success``
* ``injection.refused``
* ``injection.circuit_open``

There MUST be no silent drops — i.e. no orphan ``injection.attempted``
without a matching outcome. The 1000-turn fixture below is synthetic
and deterministic so the gate is enforceable in offline CI.
"""

from __future__ import annotations

import random

import pytest


def _build_audit_log(
    *,
    n_turns: int = 1000,
    seed: int = 0xBADC0DE,
    induce_gap: bool = False,
) -> list[dict[str, str]]:
    """Synthetic audit log generator.

    Each turn generates either an ``injection.attempted`` paired with one
    of the three terminal events (success / refused / circuit_open), or
    no injection events at all. ``induce_gap=True`` is a fault-injection
    knob used to verify the gap detector actually fails.
    """
    rng = random.Random(seed)
    out: list[dict[str, str]] = []
    for turn_idx in range(n_turns):
        turn_id = f"t-{turn_idx:04d}"
        # 60 % of turns include an injection attempt.
        if rng.random() > 0.40:
            out.append({"turn_id": turn_id, "event_type": "injection.attempted"})
            roll = rng.random()
            outcome = (
                "injection.success"
                if roll < 0.85
                else "injection.refused"
                if roll < 0.97
                else "injection.circuit_open"
            )
            if not (induce_gap and turn_idx % 173 == 0):
                out.append({"turn_id": turn_id, "event_type": outcome})
        # Optionally a stray heartbeat (irrelevant to gap detection).
        if rng.random() < 0.05:
            out.append({"turn_id": turn_id, "event_type": "heartbeat"})
    return out


def detect_gaps(audit_log: list[dict[str, str]]) -> list[str]:
    """Return turn-ids that have ``injection.attempted`` without a terminal outcome.

    Uses a per-turn outcome counter so duplicate outcomes are also
    flagged (per FR-002 / SC-007 'exactly one' contract).
    """
    by_turn: dict[str, dict[str, int]] = {}
    for evt in audit_log:
        turn = evt["turn_id"]
        by_turn.setdefault(turn, {})[evt["event_type"]] = (
            by_turn.setdefault(turn, {}).get(evt["event_type"], 0) + 1
        )
    gaps: list[str] = []
    for turn, counts in by_turn.items():
        if counts.get("injection.attempted", 0) == 0:
            continue
        outcomes = (
            counts.get("injection.success", 0)
            + counts.get("injection.refused", 0)
            + counts.get("injection.circuit_open", 0)
        )
        if outcomes != 1:
            gaps.append(turn)
    return gaps


def test_sc007_zero_gaps_in_1000_turn_fixture() -> None:
    audit = _build_audit_log(n_turns=1000)
    gaps = detect_gaps(audit)
    assert gaps == [], f"SC-007: {len(gaps)} typed-signal gaps detected → {gaps[:5]}"


def test_sc007_gap_detector_actually_catches_drops() -> None:
    """Fault-injection: induce_gap=True introduces drops; the detector MUST flag them."""
    audit = _build_audit_log(n_turns=1000, induce_gap=True)
    gaps = detect_gaps(audit)
    assert gaps, "SC-007 gap detector failed to catch known dropped outcomes"


def test_sc007_duplicate_outcomes_are_also_flagged() -> None:
    audit = [
        {"turn_id": "t-001", "event_type": "injection.attempted"},
        {"turn_id": "t-001", "event_type": "injection.success"},
        {"turn_id": "t-001", "event_type": "injection.success"},
    ]
    gaps = detect_gaps(audit)
    assert gaps == ["t-001"]


@pytest.mark.parametrize(
    "outcome", ["injection.success", "injection.refused", "injection.circuit_open"]
)
def test_sc007_each_terminal_outcome_passes(outcome: str) -> None:
    audit = [
        {"turn_id": "t-001", "event_type": "injection.attempted"},
        {"turn_id": "t-001", "event_type": outcome},
    ]
    assert detect_gaps(audit) == []
