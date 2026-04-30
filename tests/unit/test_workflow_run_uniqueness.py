"""Unit tests for the workflow_run uniqueness invariant (T016, FR-011a)."""

from __future__ import annotations

import pytest

from apps.agents.maf_runtime.errors import ActiveRunAlreadyExistsError
from apps.agents.maf_runtime.repositories.workflow_run_repository import WorkflowRunRepository
from apps.agents.maf_runtime.workflow.run_state import WorkflowRunStatus


def test_can_create_first_active_run_for_incident() -> None:
    repo = WorkflowRunRepository()
    doc = repo.create(incident_id="inc-1", current_step="monitoring", created_by="op")
    assert doc["incident_id"] == "inc-1"
    assert doc["status"] == WorkflowRunStatus.RUNNING.value
    assert doc["is_active"] is True


def test_second_concurrent_active_run_rejected() -> None:
    repo = WorkflowRunRepository()
    repo.create(incident_id="inc-2", current_step="monitoring", created_by="op")
    with pytest.raises(ActiveRunAlreadyExistsError):
        repo.create(incident_id="inc-2", current_step="monitoring", created_by="op")


def test_new_run_after_terminal_succeeds_with_prior_link() -> None:
    repo = WorkflowRunRepository()
    first = repo.create(incident_id="inc-3", current_step="monitoring", created_by="op")
    repo.update_status(first["id"], WorkflowRunStatus.COMPLETED, correlation_id="c")
    # New run for same incident is now allowed (FR-011a) because the prior reached terminal.
    second = repo.create(
        incident_id="inc-3",
        current_step="monitoring",
        created_by="op",
        prior_run_id=first["id"],
    )
    assert second["prior_run_id"] == first["id"]
    assert second["is_active"] is True


def test_running_terminates_to_completed_via_repository() -> None:
    repo = WorkflowRunRepository()
    doc = repo.create(incident_id="inc-4", current_step="monitoring", created_by="op")
    after = repo.update_status(doc["id"], WorkflowRunStatus.COMPLETED, correlation_id="c")
    assert after["status"] == "Completed"
    assert after["is_active"] is False
    assert after["terminal_at"] is not None


def test_awaiting_approval_requires_pending_request_id() -> None:
    repo = WorkflowRunRepository()
    doc = repo.create(incident_id="inc-5", current_step="communication", created_by="op")
    with pytest.raises(ValueError):
        repo.update_status(doc["id"], WorkflowRunStatus.AWAITING_APPROVAL, correlation_id="c")
    after = repo.update_status(
        doc["id"], WorkflowRunStatus.AWAITING_APPROVAL, correlation_id="c", pending_request_id="req-1",
    )
    assert after["pending_request_id"] == "req-1"
    assert after["is_active"] is True
