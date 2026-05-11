"""Cascade affinity ladder (T-D03 / FR-057 / data-model.md:268-288).

Byte-deterministic 5-step ladder that selects the most-related existing
thread when the cascade-fan-out would otherwise spawn a 6th thread (cap
exceeded — see :mod:`thread_cap_service`):

1. **Jurisdiction match** — prefer threads whose jurisdiction code equals
   the trigger's jurisdiction.
2. **Hazard-class match** — prefer threads whose hazard class equals the
   trigger's hazard class.
3. **Cascade-origin-thread preference** — prefer the thread that
   originated the cascade chain (``origin_cascade_id``).
4. **Most-recent-mutation timestamp** — newest wins (largest
   ``last_mutated_at`` UTC).
5. **Thread-creation-id ascending** — oldest wins (smallest
   ``thread_creation_id``) — final tiebreaker.

The ladder is *pure*: callers supply the candidate threads; tests pin
behaviour with synthetic inputs. ``select`` always returns the chosen
thread plus the ladder step (1..5) on which the match was made — both
mirrored onto the ``cascade.degraded_to_annotation`` audit envelope's
``affinity_step`` field.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple


@dataclass(frozen=True)
class CandidateThread:
    """Thread eligible for absorbing a cascade fan-out."""

    thread_id: str
    jurisdiction_code: str | None
    hazard_class: str | None
    origin_cascade_id: str | None
    last_mutated_at: datetime
    thread_creation_id: str


@dataclass(frozen=True)
class CascadeTrigger:
    """The cascade event whose fan-out exceeded the thread cap."""

    jurisdiction_code: str | None
    hazard_class: str | None
    origin_cascade_id: str | None


class LadderResult(NamedTuple):
    chosen: CandidateThread
    step: int


def select(
    *,
    trigger: CascadeTrigger,
    candidates: list[CandidateThread],
) -> LadderResult | None:
    """Apply the 5-step ladder and return the chosen thread (or ``None``)."""
    if not candidates:
        return None

    # Step 1 — jurisdiction match.
    if trigger.jurisdiction_code is not None:
        step1 = [c for c in candidates if c.jurisdiction_code == trigger.jurisdiction_code]
        if len(step1) == 1:
            return LadderResult(step1[0], step=1)
        if step1:
            candidates = step1
            step_so_far = 1
        else:
            step_so_far = 0
    else:
        step_so_far = 0

    # Step 2 — hazard-class match.
    if trigger.hazard_class is not None:
        step2 = [c for c in candidates if c.hazard_class == trigger.hazard_class]
        if len(step2) == 1:
            return LadderResult(step2[0], step=2)
        if step2:
            candidates = step2
            step_so_far = max(step_so_far, 2)

    # Step 3 — cascade-origin-thread preference.
    if trigger.origin_cascade_id is not None:
        step3 = [c for c in candidates if c.origin_cascade_id == trigger.origin_cascade_id]
        if len(step3) == 1:
            return LadderResult(step3[0], step=3)
        if step3:
            candidates = step3
            step_so_far = max(step_so_far, 3)

    # Step 4 — most-recent-mutation timestamp.
    max_mutated = max(c.last_mutated_at for c in candidates)
    step4 = [c for c in candidates if c.last_mutated_at == max_mutated]
    if len(step4) == 1:
        return LadderResult(step4[0], step=max(4, step_so_far))
    candidates = step4

    # Step 5 — thread-creation-id ascending (oldest wins).
    candidates.sort(key=lambda c: c.thread_creation_id)
    return LadderResult(candidates[0], step=5)
