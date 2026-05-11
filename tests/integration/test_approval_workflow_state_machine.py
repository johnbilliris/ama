"""T157 — Integration test for the approval workflow state machine
(FR-RAG-AG-02 ext; ADR-14; Plan §F-A5.3).

Exercises:
* ``pending → approved`` and ``pending → rejected`` (canonical paths).
* Forbidden transitions: ``approved → pending``, ``rejected → pending``,
  ``approved → approved``, missing-start, missing-actor.
* ``approval_authority`` requirement for terminal states.
"""

from __future__ import annotations

import pytest


def _import_workflow():
    pytest.importorskip("pydantic")
    from app.services.approval_workflow import (
        ApprovalWorkflow,
        ApprovalWorkflowError,
    )

    return ApprovalWorkflow, ApprovalWorkflowError


def test_pending_to_approved_canonical_path() -> None:
    Workflow, _ = _import_workflow()
    wf = Workflow()
    start = wf.start(record_id="rec-1", note="initial public-warning emission")
    assert start.new_state == "pending"
    assert start.old_state is None
    assert wf.state("rec-1") == "pending"

    final = wf.approve("rec-1", actor_id="ic-nsw-1@ama.local", note="cleared by IC")
    assert final.new_state == "approved"
    assert final.old_state == "pending"
    assert final.actor_id == "ic-nsw-1@ama.local"
    assert wf.state("rec-1") == "approved"


def test_pending_to_rejected_canonical_path() -> None:
    Workflow, _ = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-2")
    final = wf.reject("rec-2", actor_id="pio-vic-1@ama.local", note="awaiting confirmation")
    assert final.new_state == "rejected"
    assert final.old_state == "pending"
    assert wf.state("rec-2") == "rejected"


def test_approved_to_pending_forbidden() -> None:
    Workflow, Err = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-3")
    wf.approve("rec-3", actor_id="ic-nsw-1@ama.local")
    with pytest.raises(Err, match=r"terminal states are append-only"):
        # Use the private transition method to attempt the forbidden flip;
        # the public API doesn't expose pending() since it's the start-only
        # state.
        wf._transition(  # noqa: SLF001 — testing the invariant guard
            "rec-3", "approved", "pending", actor_id="someone", note=None
        )


def test_rejected_to_approved_forbidden() -> None:
    Workflow, Err = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-4")
    wf.reject("rec-4", actor_id="pio-1")
    with pytest.raises(Err, match=r"terminal states are append-only"):
        wf.approve("rec-4", actor_id="ic-1")


def test_double_approve_forbidden() -> None:
    Workflow, Err = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-5")
    wf.approve("rec-5", actor_id="ic-1")
    with pytest.raises(Err, match=r"terminal states are append-only"):
        wf.approve("rec-5", actor_id="ic-2")


def test_approve_without_start_forbidden() -> None:
    Workflow, Err = _import_workflow()
    wf = Workflow()
    with pytest.raises(Err, match=r"not started"):
        wf.approve("rec-missing", actor_id="ic-1")


def test_approve_without_actor_forbidden() -> None:
    """ADR-14 invariant 7: terminal state requires approval_authority."""
    Workflow, Err = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-6")
    with pytest.raises(Err, match=r"actor_id required"):
        wf.approve("rec-6", actor_id="")


def test_double_start_forbidden() -> None:
    Workflow, Err = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-7")
    with pytest.raises(Err, match=r"already started"):
        wf.start(record_id="rec-7")


def test_workflow_supports_multiple_records() -> None:
    Workflow, _ = _import_workflow()
    wf = Workflow()
    wf.start(record_id="rec-a")
    wf.start(record_id="rec-b")
    wf.approve("rec-a", actor_id="ic-1")
    wf.reject("rec-b", actor_id="pio-1")
    assert wf.state("rec-a") == "approved"
    assert wf.state("rec-b") == "rejected"
