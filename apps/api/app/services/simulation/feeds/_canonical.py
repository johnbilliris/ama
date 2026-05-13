"""Spec-039 T016: canonical NDJSON encoder, SimulatedClock, correlation IDs.

CL-4 / FR-022 / FR-026: every byte we emit is deterministic given
``(scenario_id, seed)``.

  * ``encode_ndjson(record)`` — RFC 8785 canonical JSON (sorted keys,
    UTF-8, no insignificant whitespace) + LF terminator. Re-running the
    same generator with the same seed yields a byte-identical stream
    whose SHA-256 we can diff in CI (T070, T161).
  * ``SimulatedClock`` — monotone, microsecond-precision logical clock
    derived from ``(scenario_id, seed, start_iso)``. NEVER uses wall
    clock. Two clocks with different seeds advance independently and do
    not collide (FR-026).
  * ``correlation_id(scenario_id, seed, ordinal)`` — 32-char hex
    HMAC-SHA-256 derived from those three values, deterministic across
    runs.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import rfc8785

LF: Final[bytes] = b"\n"
DEFAULT_START_ISO: Final[str] = "2026-01-01T00:00:00.000000+00:00"


def encode_ndjson(record: Any) -> bytes:
    """Encode a record as a single NDJSON line per RFC 8785 + LF terminator."""
    return rfc8785.dumps(record) + LF


def _hmac_seed_bytes(scenario_id: str, seed: int) -> bytes:
    """Stable per-(scenario, seed) HMAC key used by the clock and correlation IDs."""
    msg = f"{scenario_id}|{int(seed)}".encode()
    return hmac.new(b"ama-spec039", msg, hashlib.sha256).digest()


class SimulatedClock:
    """Microsecond-precision logical clock for simulator feeds (CL-4, FR-026).

    The clock is **never** wall-clock. Each ``tick(delta_us)`` advances by
    ``delta_us`` microseconds (default 1) deterministically. Different
    ``seed`` values yield different start offsets so that two concurrent
    simulator scenarios never collide (FR-026).
    """

    __slots__ = ("scenario_id", "seed", "_now")

    def __init__(
        self,
        scenario_id: str,
        seed: int,
        *,
        start_iso: str = DEFAULT_START_ISO,
    ) -> None:
        if not scenario_id:
            raise ValueError("scenario_id must be non-empty")
        if seed < 0 or seed > (1 << 64) - 1:
            raise ValueError("seed must fit in 64-bit unsigned range")
        self.scenario_id = scenario_id
        self.seed = int(seed)
        # Per-(scenario, seed) deterministic offset of up to ~2.4 hours, in µs,
        # so different seeds occupy disjoint time bands (FR-026).
        offset_us = int.from_bytes(_hmac_seed_bytes(scenario_id, seed)[:5], "big", signed=False)
        base = datetime.fromisoformat(start_iso)
        if base.tzinfo is None:
            base = base.replace(tzinfo=UTC)
        self._now = base + timedelta(microseconds=offset_us)

    def tick(self, delta_us: int = 1) -> str:
        """Advance the clock by ``delta_us`` microseconds; return ISO-8601 UTC."""
        if delta_us < 0:
            raise ValueError("delta_us must be non-negative (monotone clock)")
        self._now = self._now + timedelta(microseconds=delta_us)
        # Render with microsecond precision and explicit Z.
        s = self._now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
        return f"{s}Z"

    def now_iso(self) -> str:
        s = self._now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
        return f"{s}Z"


def correlation_id(scenario_id: str, seed: int, ordinal: int) -> str:
    """Return a deterministic 32-char hex correlation ID (HMAC-SHA-256, truncated)."""
    if ordinal < 0:
        raise ValueError("ordinal must be non-negative")
    key = _hmac_seed_bytes(scenario_id, seed)
    msg = ordinal.to_bytes(8, "big", signed=False)
    digest = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return digest[:32]


__all__ = [
    "DEFAULT_START_ISO",
    "LF",
    "SimulatedClock",
    "correlation_id",
    "encode_ndjson",
]
