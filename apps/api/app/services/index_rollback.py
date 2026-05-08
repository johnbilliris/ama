"""F-A7 (T170) — Blue-green index-rollback orchestrator (FR-RAG-IDX-09; SC-019;
ADR-16; Plan §F-A7.3..§F-A7.4).

Publishes ``index_rollback`` events to Service Bus when a parity-gate failure
is detected, gates execution on a manual Release Manager approval (Pass 2
Q-P2-08 manual operator action class), enforces a 5-minute SLO timer from
the moment the alias flip is requested, and on completion appends an audit
record carrying:

* ``old_index_name``           — the index queries WERE pinned to.
* ``new_index_name``           — the index the alias is being flipped TO.
* ``parity_gate_failure_reason`` — short slug describing why the rollback
  was needed (e.g. ``schema-drift-detected``, ``recall@10-regression``).
* ``release_manager_id``       — the human approver (must NOT be a service
  principal — Pass 2 Q-P2-08 prohibits automated approvals).
* ``completed_at``             — UTC ISO-8601 timestamp of the alias-flip
  acknowledgement; the SLO check is ``completed_at - timer_started_at <= 5min``.

The on-call channel is paged via the existing alert pipeline (Application
Insights → Alert Rule → Action Group → PagerDuty). This module focuses on
the deterministic state machine; the alert wiring is bicep-side
(``infra/modules/alert-rules.bicep``).

This module is constructor-injectable for hermetic tests:

* ``service_bus_publisher`` — async callable ``(topic, payload) -> None``.
* ``audit_writer``            — async callable ``(record) -> None``.
* ``approval_oracle``         — async callable ``(rollback_request) -> str``;
  returns the ``release_manager_id`` (manual gate). Tests inject an immediate
  approval; production wires this to the operator console + Entra group
  membership check.
* ``now_fn``                  — clock seam for SLO timer tests.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants & errors
# --------------------------------------------------------------------------- #


SLO_BUDGET_SECONDS: float = 5 * 60.0
"""5-minute Service Level Objective per SC-019 / Plan §F-A7.4."""


SERVICE_BUS_TOPIC: str = "index_rollback"


class IndexRollbackError(RuntimeError):
    """Raised on any rollback orchestration failure — fail-closed."""


class IndexRollbackSLOBreach(IndexRollbackError):
    """Raised when ``completed_at - timer_started_at > 5min``.

    Per FR-RAG-IDX-09, the SLO breach DOES NOT abort the rollback (it has
    already happened — old index is still queryable for 7 days). Instead,
    the breach is logged as an audit event so the on-call review can
    investigate why the pipeline took longer than budget.
    """


# --------------------------------------------------------------------------- #
# Request / event envelopes
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class IndexRollbackRequest:
    """Caller-supplied envelope describing the rollback need."""

    old_index_name: str
    new_index_name: str
    parity_gate_failure_reason: str
    correlation_id: str
    requested_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


@dataclass(frozen=True)
class IndexRollbackEvent:
    """Service-Bus payload published on every state transition."""

    correlation_id: str
    old_index_name: str
    new_index_name: str
    parity_gate_failure_reason: str
    state: str  # "requested" | "approved" | "completed" | "slo_breach"
    timestamp: datetime
    release_manager_id: str | None = None


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #


class IndexRollbackOrchestrator:
    """Coordinates the manual-approval + 5-min SLO + audit-emission pipeline."""

    def __init__(
        self,
        *,
        service_bus_publisher: Callable[[str, dict[str, Any]], Awaitable[None]],
        audit_writer: Callable[[dict[str, Any]], Awaitable[None]],
        approval_oracle: Callable[[IndexRollbackRequest], Awaitable[str]],
        alias_flipper: Callable[[str, str], Awaitable[None]],
        now_fn: Callable[[], datetime] = lambda: datetime.now(tz=UTC),
        slo_budget_seconds: float = SLO_BUDGET_SECONDS,
    ) -> None:
        self._publish = service_bus_publisher
        self._audit = audit_writer
        self._approval = approval_oracle
        self._flip = alias_flipper
        self._now = now_fn
        self._slo_budget_seconds = slo_budget_seconds

    async def trigger(self, request: IndexRollbackRequest) -> IndexRollbackEvent:
        """Run the rollback state machine end-to-end.

        Returns the terminal ``IndexRollbackEvent`` (``state == "completed"``
        on success, ``state == "slo_breach"`` if the alias flip exceeded the
        budget — both are audited, the alias has flipped either way).
        """
        timer_started_at = self._now()

        # 1. Publish "requested" event (notifies the operator console).
        requested = IndexRollbackEvent(
            correlation_id=request.correlation_id,
            old_index_name=request.old_index_name,
            new_index_name=request.new_index_name,
            parity_gate_failure_reason=request.parity_gate_failure_reason,
            state="requested",
            timestamp=timer_started_at,
        )
        await self._publish(SERVICE_BUS_TOPIC, _event_to_payload(requested))

        # 2. Manual Release Manager approval (Pass 2 Q-P2-08).
        release_manager_id = await self._approval(request)
        if not release_manager_id:
            raise IndexRollbackError(
                f"index rollback for {request.correlation_id!r} not approved"
            )
        approved = IndexRollbackEvent(
            correlation_id=request.correlation_id,
            old_index_name=request.old_index_name,
            new_index_name=request.new_index_name,
            parity_gate_failure_reason=request.parity_gate_failure_reason,
            state="approved",
            timestamp=self._now(),
            release_manager_id=release_manager_id,
        )
        await self._publish(SERVICE_BUS_TOPIC, _event_to_payload(approved))

        # 3. Execute the alias flip.
        await self._flip(request.old_index_name, request.new_index_name)

        # 4. Compute SLO + emit terminal event + append audit record.
        completed_at = self._now()
        elapsed = (completed_at - timer_started_at).total_seconds()
        slo_breached = elapsed > self._slo_budget_seconds
        terminal = IndexRollbackEvent(
            correlation_id=request.correlation_id,
            old_index_name=request.old_index_name,
            new_index_name=request.new_index_name,
            parity_gate_failure_reason=request.parity_gate_failure_reason,
            state="slo_breach" if slo_breached else "completed",
            timestamp=completed_at,
            release_manager_id=release_manager_id,
        )
        await self._publish(SERVICE_BUS_TOPIC, _event_to_payload(terminal))

        # Audit append per FR-RAG-IDX-09 acceptance criteria.
        await self._audit(
            {
                "event_type": "index_rollback",
                "correlation_id": request.correlation_id,
                "old_index_name": request.old_index_name,
                "new_index_name": request.new_index_name,
                "parity_gate_failure_reason": request.parity_gate_failure_reason,
                "release_manager_id": release_manager_id,
                "completed_at": completed_at.isoformat(),
                "elapsed_seconds": elapsed,
                "slo_breached": slo_breached,
            }
        )

        if slo_breached:
            logger.warning(
                "index_rollback_slo_breach correlation_id=%s elapsed=%.2fs budget=%.2fs",
                request.correlation_id,
                elapsed,
                self._slo_budget_seconds,
            )

        return terminal


def _event_to_payload(event: IndexRollbackEvent) -> dict[str, Any]:
    return {
        "correlation_id": event.correlation_id,
        "old_index_name": event.old_index_name,
        "new_index_name": event.new_index_name,
        "parity_gate_failure_reason": event.parity_gate_failure_reason,
        "state": event.state,
        "timestamp": event.timestamp.isoformat(),
        "release_manager_id": event.release_manager_id,
    }


# Convenience helper for callers that compute SLO deadlines themselves.
def slo_deadline(timer_started_at: datetime) -> datetime:
    """Return ``timer_started_at + 5min`` (the SC-019 SLO deadline)."""
    return timer_started_at + timedelta(seconds=SLO_BUDGET_SECONDS)


__all__ = [
    "IndexRollbackError",
    "IndexRollbackEvent",
    "IndexRollbackOrchestrator",
    "IndexRollbackRequest",
    "IndexRollbackSLOBreach",
    "SERVICE_BUS_TOPIC",
    "SLO_BUDGET_SECONDS",
    "slo_deadline",
]
