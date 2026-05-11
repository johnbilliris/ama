"""T-D10 — `handle_signal_event` consumer for the `sim-risk-assessment` consumer group.

Wires the existing :class:`AssessmentProcessingPipeline` to the
``sim-risk-assessment`` Event Hubs consumer group provisioned by T-A10.
Every change-feed envelope flagged ``category=hazard-telemetry`` triggers
a single Risk Assessment fan-out per envelope.

The handler is intentionally side-effect-free apart from the
pipeline call + an idempotency check using the envelope's
``signal_id``. Duplicate consumer-group reads (which Event Hubs
guarantees can happen) are deduped via an in-process LRU cache so a
single signal does not trigger two assessments.

Live integration is gated behind ``@pytest.mark.azure_staging`` because
it requires the deployed Event Hubs namespace.
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_DEDUP_CAPACITY = 10_000


@dataclass
class SignalEnvelope:
    """Minimal envelope surface used by the consumer-group handler."""

    signal_id: str
    simulation_id: str
    tenant_id: str
    category: str
    confidence: float
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessmentReply:
    signal_id: str
    accepted: bool
    duplicate: bool = False
    elapsed_seconds: float = 0.0
    pipeline_result: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# In-process dedup cache for consumer-group offset replay protection.
# ---------------------------------------------------------------------------


class _DedupCache:
    def __init__(self, capacity: int = DEFAULT_DEDUP_CAPACITY) -> None:
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._capacity = capacity
        self._lock = Lock()

    def add_if_new(self, key: str) -> bool:
        """Return ``True`` if newly inserted; ``False`` if already seen."""
        with self._lock:
            if key in self._seen:
                # Refresh recency.
                self._seen.move_to_end(key)
                return False
            self._seen[key] = None
            if len(self._seen) > self._capacity:
                self._seen.popitem(last=False)
            return True


_DEDUP = _DedupCache()


def reset_dedup_for_tests() -> None:
    """Test helper — clears the consumer-group dedup state."""
    global _DEDUP
    _DEDUP = _DedupCache()


# ---------------------------------------------------------------------------
# Public consumer-group entry-point.
# ---------------------------------------------------------------------------


PipelineRunner = Callable[[SignalEnvelope], dict[str, Any]]


async def handle_signal_event(
    envelope: SignalEnvelope,
    *,
    pipeline_runner: PipelineRunner,
) -> RiskAssessmentReply:
    """Handle one ``simulation_synthetic_signals`` change-feed event.

    Per FR-026 the handler:

    * Skips non-``hazard-telemetry`` envelopes (logged, no run).
    * Dedupes on ``(simulation_id, signal_id)`` so duplicate reads from
      Event Hubs replay are safe.
    * Calls ``pipeline_runner(envelope)`` synchronously — the runner is
      thread-safe via the existing :class:`AssessmentProcessingPipeline`.
    """
    if envelope.category != "hazard-telemetry":
        logger.info(
            "risk_assessment.skip_non_hazard signal=%s category=%s",
            envelope.signal_id,
            envelope.category,
        )
        return RiskAssessmentReply(
            signal_id=envelope.signal_id, accepted=False, duplicate=False
        )

    dedup_key = f"{envelope.simulation_id}::{envelope.signal_id}"
    if not _DEDUP.add_if_new(dedup_key):
        logger.info(
            "risk_assessment.dedup signal=%s sim=%s",
            envelope.signal_id,
            envelope.simulation_id,
        )
        return RiskAssessmentReply(
            signal_id=envelope.signal_id, accepted=False, duplicate=True
        )

    start = time.perf_counter()
    try:
        result = pipeline_runner(envelope)
    except Exception:  # noqa: BLE001
        logger.exception(
            "risk_assessment.pipeline_failed signal=%s sim=%s",
            envelope.signal_id,
            envelope.simulation_id,
        )
        return RiskAssessmentReply(
            signal_id=envelope.signal_id, accepted=False, duplicate=False
        )
    elapsed = time.perf_counter() - start
    return RiskAssessmentReply(
        signal_id=envelope.signal_id,
        accepted=True,
        duplicate=False,
        elapsed_seconds=elapsed,
        pipeline_result=result,
    )


__all__ = [
    "RiskAssessmentReply",
    "SignalEnvelope",
    "handle_signal_event",
    "reset_dedup_for_tests",
]
