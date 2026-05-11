"""Spec-039 Phase 5: deterministic per-feed RNG.

The :func:`seeded_rng` helper returns a :class:`random.Random` whose state
is fully derived from ``(scenario_id, seed, source_shape)`` so every feed
emits a reproducible-but-distinct stream from the same scenario.
"""

from __future__ import annotations

import hashlib
import random


def seeded_rng(scenario_id: str, seed: int, source_shape: str) -> random.Random:
    """Return a deterministic :class:`random.Random` for a given feed."""
    if not scenario_id:
        raise ValueError("scenario_id must be non-empty")
    if seed < 0 or seed > (1 << 64) - 1:
        raise ValueError("seed must fit in 64-bit unsigned range")
    msg = f"{scenario_id}|{int(seed)}|{source_shape}".encode()
    digest = hashlib.sha256(msg).digest()
    rng = random.Random()
    # Seed with the full 32 bytes — Random.seed accepts int from bytes.
    rng.seed(int.from_bytes(digest, "big"), version=2)
    return rng


__all__ = ["seeded_rng"]
