"""Unit tests for the 7-state workflow run state machine (T014, FR-011b)."""

from __future__ import annotations

import pytest

from apps.agents.maf_runtime.errors import InvalidStateTransitionError
from apps.agents.maf_runtime.workflow.run_state import (
    ACTIVE_STATES,
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    WorkflowRunStatus,
    is_active,
    is_terminal,
    validate_transition,
)


def test_seven_canonical_states_exist() -> None:
    expected = {
        "Running", "AwaitingApproval", "NeedsOperatorDecision",
        "Completed", "Failed", "Cancelled", "Superseded",
    }
    assert {s.value for s in WorkflowRunStatus} == expected


def test_terminal_set_matches_spec() -> None:
    assert {s.value for s in TERMINAL_STATES} == {"Completed", "Failed", "Cancelled", "Superseded"}


def test_active_set_matches_spec() -> None:
    assert {s.value for s in ACTIVE_STATES} == {"Running", "AwaitingApproval"}


@pytest.mark.parametrize(
    ("src", "dst"),
    [
        (WorkflowRunStatus.RUNNING, WorkflowRunStatus.AWAITING_APPROVAL),
        (WorkflowRunStatus.RUNNING, WorkflowRunStatus.NEEDS_OPERATOR_DECISION),
        (WorkflowRunStatus.RUNNING, WorkflowRunStatus.COMPLETED),
        (WorkflowRunStatus.RUNNING, WorkflowRunStatus.FAILED),
        (WorkflowRunStatus.RUNNING, WorkflowRunStatus.CANCELLED),
        (WorkflowRunStatus.RUNNING, WorkflowRunStatus.SUPERSEDED),
        (WorkflowRunStatus.AWAITING_APPROVAL, WorkflowRunStatus.RUNNING),
        (WorkflowRunStatus.AWAITING_APPROVAL, WorkflowRunStatus.NEEDS_OPERATOR_DECISION),
        (WorkflowRunStatus.AWAITING_APPROVAL, WorkflowRunStatus.CANCELLED),
        (WorkflowRunStatus.AWAITING_APPROVAL, WorkflowRunStatus.SUPERSEDED),
        (WorkflowRunStatus.NEEDS_OPERATOR_DECISION, WorkflowRunStatus.RUNNING),
        (WorkflowRunStatus.NEEDS_OPERATOR_DECISION, WorkflowRunStatus.FAILED),
        (WorkflowRunStatus.NEEDS_OPERATOR_DECISION, WorkflowRunStatus.CANCELLED),
        (WorkflowRunStatus.NEEDS_OPERATOR_DECISION, WorkflowRunStatus.SUPERSEDED),
    ],
)
def test_allowed_transitions_pass(src: WorkflowRunStatus, dst: WorkflowRunStatus) -> None:
    validate_transition(src, dst, correlation_id="c", run_id="r")


@pytest.mark.parametrize(
    ("src", "dst"),
    [
        (WorkflowRunStatus.COMPLETED, WorkflowRunStatus.RUNNING),
        (WorkflowRunStatus.FAILED, WorkflowRunStatus.RUNNING),
        (WorkflowRunStatus.CANCELLED, WorkflowRunStatus.RUNNING),
        (WorkflowRunStatus.SUPERSEDED, WorkflowRunStatus.RUNNING),
        (WorkflowRunStatus.AWAITING_APPROVAL, WorkflowRunStatus.COMPLETED),  # must go through Running
        (WorkflowRunStatus.NEEDS_OPERATOR_DECISION, WorkflowRunStatus.COMPLETED),  # must go through Running
    ],
)
def test_disallowed_transitions_raise(src: WorkflowRunStatus, dst: WorkflowRunStatus) -> None:
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(src, dst, correlation_id="c", run_id="r")


def test_terminal_states_have_no_outbound_transitions() -> None:
    for terminal in TERMINAL_STATES:
        assert ALLOWED_TRANSITIONS[terminal] == frozenset()


def test_helpers() -> None:
    assert is_active("Running") is True
    assert is_active(WorkflowRunStatus.AWAITING_APPROVAL) is True
    assert is_active("Completed") is False
    assert is_terminal("Completed") is True
    assert is_terminal("Running") is False
