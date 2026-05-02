"""HITL gate + decision listener tests (T046, T048, T048b, T048c)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from apps.agents.maf_runtime.errors import DuplicateDecisionConflictError
from apps.agents.maf_runtime.repositories.workflow_run_repository import WorkflowRunRepository
from apps.agents.maf_runtime.workflow.hitl_request_port import (
    HitlDecisionListener,
    HitlGateExecutor,
    _ServiceBusPublisher,
    build_approval_envelope,
    deterministic_request_id,
)
from apps.agents.maf_runtime.workflow.run_state import WorkflowRunStatus


def test_request_id_is_deterministic() -> None:
    a = deterministic_request_id(incident_id="INC-1", run_id="run-1", step_index=4)
    b = deterministic_request_id(incident_id="INC-1", run_id="run-1", step_index=4)
    c = deterministic_request_id(incident_id="INC-1", run_id="run-1", step_index=5)
    assert a == b
    assert a != c


def test_envelope_carries_maf_metadata() -> None:
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-1-v1", "metadata": {}}
    env = build_approval_envelope(
        draft_alert=draft,
        incident_id="INC-1",
        run_id="run-1",
        step_index=4,
        correlation_id="trace-1",
    )
    md = env["alert"]["payload"]["metadata"]
    assert md["maf_run_id"] == "run-1"
    assert md["maf_source_executor"] == "communication_executor"
    assert md["correlation_id"] == "trace-1"


def _make_run(repo: WorkflowRunRepository, *, incident_id: str = "INC-1") -> str:
    doc = repo.create(incident_id=incident_id, current_step="communication", created_by="t")
    return doc["id"]


def test_hitl_gate_publishes_and_pauses() -> None:
    repo = WorkflowRunRepository()
    run_id = _make_run(repo)
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-1-v1"}
    result = asyncio.run(
        gate.run(
            draft_alert=draft,
            incident_id="INC-1",
            run_id=run_id,
            step_index=4,
            correlation_id="t",
        )
    )
    assert result["parked"] is True
    assert publisher.published[0]["queue"] == "commander-approval-queue"
    after = repo.get(run_id)
    assert after is not None
    assert after["status"] == WorkflowRunStatus.AWAITING_APPROVAL.value
    assert after["pending_request_id"] == result["request_id"]


def test_hitl_gate_idempotent_resume_skips_publish() -> None:
    """T048: when an existing approval_decisions doc is found, no second publish."""
    repo = WorkflowRunRepository()
    run_id = _make_run(repo, incident_id="INC-resume")
    publisher = _ServiceBusPublisher()
    fixed_request_id = deterministic_request_id(incident_id="INC-resume", run_id=run_id, step_index=4)

    def _decision_lookup(req_id: str) -> dict | None:
        return {"decision": "approve", "request_id": req_id} if req_id == fixed_request_id else None

    gate = HitlGateExecutor(
        repo=repo,
        publisher=publisher,
        decision_lookup=_decision_lookup,
    )
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-resume-v1"}
    result = asyncio.run(
        gate.run(
            draft_alert=draft,
            incident_id="INC-resume",
            run_id=run_id,
            step_index=4,
            correlation_id="t",
        )
    )
    assert result["parked"] is False
    assert result["decision"]["decision"] == "approve"
    assert publisher.published == [], "Publish must be skipped when existing decision found"


def test_decision_listener_resumes_run_on_approve() -> None:
    repo = WorkflowRunRepository()
    run_id = _make_run(repo, incident_id="INC-decide")
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-decide-v1"}
    result = asyncio.run(
        gate.run(
            draft_alert=draft,
            incident_id="INC-decide",
            run_id=run_id,
            step_index=4,
            correlation_id="t",
        )
    )
    listener = HitlDecisionListener(repo=repo)
    decision = {
        "request_id": result["request_id"],
        "decision": "approve",
        "approver_identity": "commander-1",
        "correlation_id": "t",
    }
    updated = asyncio.run(listener.on_decision_received(decision))
    assert updated["status"] == WorkflowRunStatus.RUNNING.value


def test_decision_listener_cancels_on_reject() -> None:
    repo = WorkflowRunRepository()
    run_id = _make_run(repo, incident_id="INC-reject")
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-reject-v1"}
    result = asyncio.run(
        gate.run(
            draft_alert=draft,
            incident_id="INC-reject",
            run_id=run_id,
            step_index=4,
            correlation_id="t",
        )
    )
    listener = HitlDecisionListener(repo=repo)
    decision = {
        "request_id": result["request_id"],
        "decision": "reject",
        "approver_identity": "commander-1",
        "correlation_id": "t",
    }
    updated = asyncio.run(listener.on_decision_received(decision))
    assert updated["status"] == WorkflowRunStatus.CANCELLED.value


def test_concurrent_approval_second_decision_conflict() -> None:
    """T048b: two commanders approve the same request — first wins, second raises."""
    repo = WorkflowRunRepository()
    run_id = _make_run(repo, incident_id="INC-concurrent")
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-concurrent-v1"}
    result = asyncio.run(
        gate.run(
            draft_alert=draft,
            incident_id="INC-concurrent",
            run_id=run_id,
            step_index=4,
            correlation_id="t",
        )
    )
    listener = HitlDecisionListener(repo=repo)
    decision_a = {
        "request_id": result["request_id"],
        "decision": "approve",
        "approver_identity": "commander-A",
        "correlation_id": "t-a",
    }
    decision_b = {
        "request_id": result["request_id"],
        "decision": "approve",
        "approver_identity": "commander-B",
        "correlation_id": "t-b",
    }
    asyncio.run(listener.on_decision_received(decision_a))  # first wins
    with pytest.raises(DuplicateDecisionConflictError):
        asyncio.run(listener.on_decision_received(decision_b))


def test_unknown_decision_outcome_raises() -> None:
    repo = WorkflowRunRepository()
    run_id = _make_run(repo, incident_id="INC-unknown")
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    draft = MagicMock()
    draft.model_dump.return_value = {"alert_id": "ca-INC-unknown-v1"}
    result = asyncio.run(
        gate.run(
            draft_alert=draft,
            incident_id="INC-unknown",
            run_id=run_id,
            step_index=4,
            correlation_id="t",
        )
    )
    listener = HitlDecisionListener(repo=repo)
    # Unknown decision raises ValueError but the run remains in AwaitingApproval.
    with pytest.raises(ValueError):
        asyncio.run(listener.on_decision_received({"request_id": result["request_id"], "decision": "telephone"}))
