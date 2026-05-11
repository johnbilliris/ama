"""Spec-038 Phase 5 — feed package public surface.

Each feed shape is its own module under this package and exposes:

  * ``SOURCE_SHAPE``: registry id (matches ``source_shapes.json``).
  * ``FEED_VERSION``: schema-pinned envelope version (``v1``).
  * ``emit(scenario_id, seed, *, jurisdiction='nsw', count=5,
    params=None, clock=None) -> Iterator[CanonicalRecord]``.

All randomness is derived deterministically from ``(scenario_id, seed)``
via :func:`_seeded_random.seeded_rng`. No real PII, no real provider
endpoints, no wall-clock — every byte is reproducible (FR-022, CL-4).
"""
