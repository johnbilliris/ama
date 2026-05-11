"""Spec-039 Phase 6 — shared base for demo scenarios (T130-T137).

A scenario composes ≥2 feed-shape modules and exposes a uniform contract:

* ``SCENARIO_ID`` — kebab-case id (matches replay sidecar name).
* ``DOMAIN_GROUP`` — one of the 8 spec-039 groups.
* ``PARTICIPATING_PERSONAS`` — tuple of ≥3 persona-ids covered.
* ``PARTICIPATING_FEEDS`` — tuple of ≥2 source-shape ids exercised.
* ``DEFAULT_SEED`` — pinned seed used to commit the replay sidecar.
* ``def emit(seed: int) -> Iterator[CanonicalRecord]`` — yields the
  composed event stream in deterministic order.

The orchestrator interleaves emissions from each feed module
deterministically by sorting on (timestamp, source_shape, correlation_id)
so replays remain byte-identical across re-runs.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Final

from .._canonical import SimulatedClock
from .._models import CanonicalRecord

EmitFn = Callable[..., Iterator[CanonicalRecord]]


def compose(
    scenario_id: str,
    seed: int,
    *,
    feed_calls: list[tuple[EmitFn, dict]],
) -> Iterator[CanonicalRecord]:
    """Run each feed module and yield a deterministically interleaved stream.

    ``feed_calls`` is a list of ``(emit_fn, kwargs)`` tuples. ``scenario_id``
    and ``seed`` are injected automatically; the caller supplies feed-specific
    kwargs (jurisdiction, count, etc.). Each feed gets its own ``SimulatedClock``
    derived from ``(scenario_id|<feed_index>, seed)`` so distinct feeds occupy
    disjoint micro-time bands per FR-026.
    """
    all_records: list[CanonicalRecord] = []
    for idx, (fn, kwargs) in enumerate(feed_calls):
        clk = SimulatedClock(f"{scenario_id}|f{idx}", seed)
        for rec in fn(scenario_id, seed, clock=clk, **kwargs):
            all_records.append(rec)
    # Stable sort: timestamp, source_shape, correlation_id.
    all_records.sort(key=lambda r: (r.timestamp, r.source_shape, r.correlation_id))
    yield from all_records


__all__: Final = ["compose"]
