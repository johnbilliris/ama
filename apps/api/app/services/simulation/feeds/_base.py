"""Spec-038 Phase 5: shared helpers for the 13 feed shape modules.

Provides:

  * ``JURISDICTIONS`` — the canonical set we permit on the ``--jurisdiction``
    CLI flag (8 states/territories + ``au`` for nationwide synthetic feeds).
  * :func:`build_record` — assembles a :class:`CanonicalRecord` with the
    spec-038 envelope filled in (``simulated``/``fictitious``/``residency``
    are constants; warning-class ``test_marker`` is enforced separately by
    the JSON schema).
  * :data:`WARNING_TEST_MARKER` — the literal FR-046 / F-001 string that
    every warning-shaped body MUST contain.
"""

from __future__ import annotations

from typing import Any, Final

from ._canonical import SimulatedClock, correlation_id
from ._models import CanonicalRecord

JURISDICTIONS: Final[tuple[str, ...]] = (
    "nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act", "au"
)
WARNING_TEST_MARKER: Final[str] = "TEST — DO NOT BROADCAST"


def build_record(
    *,
    scenario_id: str,
    seed: int,
    source_shape: str,
    feed_version: str,
    timestamp: str,
    ordinal: int,
    body: dict[str, Any],
) -> CanonicalRecord:
    """Assemble the spec-038 envelope around a feed-specific ``body``."""
    return CanonicalRecord(
        simulated=True,
        fictitious=True,
        residency="AU",
        scenario_id=scenario_id,
        seed=seed,
        source_shape=source_shape,
        timestamp=timestamp,
        feed_version=feed_version,
        correlation_id=correlation_id(scenario_id, seed, ordinal),
        body=body,
    )


def ensure_clock(clock: SimulatedClock | None, scenario_id: str, seed: int) -> SimulatedClock:
    return clock if clock is not None else SimulatedClock(scenario_id, seed)


def validate_jurisdiction(jurisdiction: str) -> str:
    j = jurisdiction.lower()
    if j not in JURISDICTIONS:
        raise ValueError(
            f"jurisdiction {jurisdiction!r} not in {JURISDICTIONS}"
        )
    return j


__all__ = [
    "JURISDICTIONS",
    "WARNING_TEST_MARKER",
    "build_record",
    "ensure_clock",
    "validate_jurisdiction",
]
