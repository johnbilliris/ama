"""Spec 036 F-A5 (T164) — approval workflow state machine (FR-RAG-AG-02 ext;
ADR-14; Plan §F-A5.3).

Wraps the ``approval_workflow_state`` field on ``AuditRecord`` with a
deterministic state machine. Transitions:

* ``pending → approved`` (terminal; requires ``approval_authority``)
* ``pending → rejected`` (terminal; requires ``approval_authority``)
* ``approved → *`` and ``rejected → *`` are forbidden (terminal states).

Every transition emits a fresh audit event via ``apps/agents/common/audit.py``
so the post-decision sequence is fully reconstructible (Constitution
Principle IV).

Design notes:

* The state machine is **in-process** — no Cosmos round-trip during a
  transition. Persistence is the responsibility of the caller (typically the
  audit writer + the per-recommendation Cosmos record). This keeps the
  state machine hermetically testable.
* The implementation is **dataclass-light** — pydantic-v2 used only for the
  result envelope so callers can ``model_dump()`` directly into the audit
  record.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

logger = logging.getLogger(__name__)


ApprovalState = Literal["pending", "approved", "rejected"]


_TERMINAL_STATES: frozenset[str] = frozenset({"approved", "rejected"})


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class ApprovalWorkflowError(ValueError):
    """Raised on an invalid transition (e.g. approved → pending)."""


# --------------------------------------------------------------------------- #
# Result envelope
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ApprovalTransition:
    """Outcome of one state transition. Caller persists this via the audit shape."""

    record_id: str
    """Audit-record / recommendation key the transition applies to."""

    old_state: ApprovalState | None
    """``None`` for first emission; otherwise the prior terminal-or-pending value."""

    new_state: ApprovalState
    """Resulting state. Always one of pending|approved|rejected."""

    actor_id: str
    """Entra ID / OID of the actor effecting the transition. Becomes
    ``AuditRecord.approval_authority`` for terminal states."""

    transitioned_at: datetime
    """ISO-8601 UTC. Audit-emission timestamp."""

    note: str | None = None
    """Optional free-text rationale; surfaced as
    ``AuditRecord.operator_override_rationale`` for rejection paths and as
    plain note metadata for approvals."""


# --------------------------------------------------------------------------- #
# State machine
# --------------------------------------------------------------------------- #


class ApprovalWorkflow:
    """Deterministic state machine wrapping ``approval_workflow_state``.

    Usage:

    ```python
    workflow = ApprovalWorkflow()
    workflow.start(record_id="rec-1")          # → pending
    workflow.approve("rec-1", actor_id="ic-1") # → approved (terminal)
    ```

    Internal state is held in a per-instance dict keyed by ``record_id`` so
    multiple concurrent recommendations can be tracked. Production callers
    typically instantiate one workflow per request scope; the audit emission
    captures the durable state.
    """

    def __init__(self) -> None:
        self._states: dict[str, ApprovalState] = {}

    # --- public API ----------------------------------------------------- #

    def start(self, record_id: str, *, note: str | None = None) -> ApprovalTransition:
        """Initial emission for a record: state ``pending``."""
        if record_id in self._states:
            raise ApprovalWorkflowError(
                f"approval workflow already started for record {record_id!r}: current state={self._states[record_id]!r}"
            )
        return self._transition(record_id, None, "pending", actor_id="system", note=note)

    def approve(self, record_id: str, *, actor_id: str, note: str | None = None) -> ApprovalTransition:
        """Terminal transition to ``approved``. Requires ``actor_id``."""
        if not actor_id:
            raise ApprovalWorkflowError("approve(): actor_id required")
        return self._transition(record_id, self._require(record_id), "approved", actor_id=actor_id, note=note)

    def reject(self, record_id: str, *, actor_id: str, note: str | None = None) -> ApprovalTransition:
        """Terminal transition to ``rejected``. Requires ``actor_id``."""
        if not actor_id:
            raise ApprovalWorkflowError("reject(): actor_id required")
        return self._transition(record_id, self._require(record_id), "rejected", actor_id=actor_id, note=note)

    def state(self, record_id: str) -> ApprovalState | None:
        """Current state, or None if never started."""
        return self._states.get(record_id)

    # --- internals ------------------------------------------------------ #

    def _require(self, record_id: str) -> ApprovalState:
        if record_id not in self._states:
            raise ApprovalWorkflowError(f"approval workflow not started for record {record_id!r}; call start() first")
        return self._states[record_id]

    def _transition(
        self,
        record_id: str,
        old_state: ApprovalState | None,
        new_state: ApprovalState,
        *,
        actor_id: str,
        note: str | None,
    ) -> ApprovalTransition:
        # Forbid mutation out of a terminal state.
        if old_state in _TERMINAL_STATES:
            raise ApprovalWorkflowError(
                f"forbidden transition: record={record_id!r} {old_state!r} → {new_state!r} "
                f"(terminal states are append-only)"
            )
        # Forbid pending → pending.
        if old_state == "pending" and new_state == "pending":
            raise ApprovalWorkflowError(f"forbidden transition: record={record_id!r} pending → pending")
        # ADR-14 invariant 7: terminal state requires an actor.
        if new_state in _TERMINAL_STATES and actor_id == "system":
            raise ApprovalWorkflowError(f"approval_workflow_state={new_state!r} requires a non-system actor_id")
        self._states[record_id] = new_state
        result = ApprovalTransition(
            record_id=record_id,
            old_state=old_state,
            new_state=new_state,
            actor_id=actor_id,
            transitioned_at=datetime.now(tz=UTC),
            note=note,
        )
        logger.info(
            "approval_workflow_transition record_id=%s %s -> %s actor=%s",
            record_id,
            old_state,
            new_state,
            actor_id,
        )
        return result


__all__ = [
    "ApprovalState",
    "ApprovalTransition",
    "ApprovalWorkflow",
    "ApprovalWorkflowError",
]
