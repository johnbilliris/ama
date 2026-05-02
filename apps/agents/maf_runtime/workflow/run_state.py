"""Workflow Run state model (FR-011b) — 7 canonical states + transition rules.

The state set and allowed transitions are defined in
``specs/033-maf-adoption/data-model.md §2.1``. This module is the single
authoritative implementation; ``WorkflowRunRepository.update_status`` (T016) and
the operator API (T025/T051) MUST consult it before persisting a transition.
"""

from __future__ import annotations

from enum import StrEnum

from ..errors import InvalidStateTransitionError

__all__ = [
    "WorkflowRunStatus",
    "TERMINAL_STATES",
    "ACTIVE_STATES",
    "ALLOWED_TRANSITIONS",
    "validate_transition",
    "is_terminal",
    "is_active",
]


class WorkflowRunStatus(StrEnum):
    """Canonical 7-state model (FR-011b). Stored as a string in Cosmos."""

    RUNNING = "Running"
    AWAITING_APPROVAL = "AwaitingApproval"
    NEEDS_OPERATOR_DECISION = "NeedsOperatorDecision"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    SUPERSEDED = "Superseded"


TERMINAL_STATES: frozenset[WorkflowRunStatus] = frozenset(
    {
        WorkflowRunStatus.COMPLETED,
        WorkflowRunStatus.FAILED,
        WorkflowRunStatus.CANCELLED,
        WorkflowRunStatus.SUPERSEDED,
    }
)


ACTIVE_STATES: frozenset[WorkflowRunStatus] = frozenset(
    {
        WorkflowRunStatus.RUNNING,
        WorkflowRunStatus.AWAITING_APPROVAL,
    }
)


# Allowed transitions per data-model.md §2.1. Source -> set of permitted targets.
ALLOWED_TRANSITIONS: dict[WorkflowRunStatus, frozenset[WorkflowRunStatus]] = {
    WorkflowRunStatus.RUNNING: frozenset(
        {
            WorkflowRunStatus.AWAITING_APPROVAL,
            WorkflowRunStatus.NEEDS_OPERATOR_DECISION,
            WorkflowRunStatus.COMPLETED,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
            WorkflowRunStatus.SUPERSEDED,
        }
    ),
    WorkflowRunStatus.AWAITING_APPROVAL: frozenset(
        {
            WorkflowRunStatus.RUNNING,
            WorkflowRunStatus.NEEDS_OPERATOR_DECISION,
            WorkflowRunStatus.CANCELLED,
            WorkflowRunStatus.SUPERSEDED,
        }
    ),
    WorkflowRunStatus.NEEDS_OPERATOR_DECISION: frozenset(
        {
            WorkflowRunStatus.RUNNING,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
            WorkflowRunStatus.SUPERSEDED,
        }
    ),
    # Terminal states have no outbound transitions.
    WorkflowRunStatus.COMPLETED: frozenset(),
    WorkflowRunStatus.FAILED: frozenset(),
    WorkflowRunStatus.CANCELLED: frozenset(),
    WorkflowRunStatus.SUPERSEDED: frozenset(),
}


def is_terminal(status: WorkflowRunStatus | str) -> bool:
    return WorkflowRunStatus(status) in TERMINAL_STATES


def is_active(status: WorkflowRunStatus | str) -> bool:
    return WorkflowRunStatus(status) in ACTIVE_STATES


def validate_transition(
    from_state: WorkflowRunStatus | str,
    to_state: WorkflowRunStatus | str,
    *,
    correlation_id: str,
    run_id: str | None = None,
) -> None:
    """Raise ``InvalidStateTransitionError`` if the transition is not permitted.

    Idempotent same-state transitions (``Running -> Running``) are rejected; the
    repository should detect "no change" and skip the write rather than calling
    this function with identical states.
    """
    src = WorkflowRunStatus(from_state)
    dst = WorkflowRunStatus(to_state)
    if dst not in ALLOWED_TRANSITIONS.get(src, frozenset()):
        raise InvalidStateTransitionError(
            f"Transition {src.value} -> {dst.value} is not permitted by FR-011b state machine.",
            correlation_id=correlation_id,
            run_id=run_id,
            details={"from_state": src.value, "to_state": dst.value},
        )
