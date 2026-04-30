"""Workflow crash-recovery / SC-002 / SC-003 invariant tests (T049, T056).

T049 — fault-injection harness: drop randomised steps, verify the run lands in
``Failed`` (with-context) and that the FR-012 retry budget bounded the time.
For the in-memory repo we cannot kill a real process, but we can prove that:

1. A failing step transitions the run to ``Failed`` with a structured
   ``failure_reason`` (FR-012 / SC-002 contract).
2. The HitlGateExecutor never publishes when the workflow fails BEFORE reaching
   the gate (SC-003 invariant).

A real fault-injection harness against a deployed agents Container App lives
in tests/load/ (T050) and runs only in dev/staging.
"""

from __future__ import annotations

import asyncio
from typing import Any

from apps.agents.maf_runtime.repositories.workflow_run_repository import WorkflowRunRepository
from apps.agents.maf_runtime.workflow.builder import AmaWorkflow
from apps.agents.maf_runtime.workflow.hitl_request_port import HitlGateExecutor, _ServiceBusPublisher
from apps.agents.maf_runtime.workflow.run_state import WorkflowRunStatus


def _make_workflow_with_in_memory_publisher() -> tuple[AmaWorkflow, _ServiceBusPublisher]:
    repo = WorkflowRunRepository()
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    workflow = AmaWorkflow(repo=repo, hitl_gate=gate)
    return workflow, publisher


def test_happy_path_run_pauses_at_hitl_with_no_publish_until_gate() -> None:
    """SC-003 spine: a successful run reaches AwaitingApproval and exactly ONE envelope is published (by the gate)."""
    wf, publisher = _make_workflow_with_in_memory_publisher()
    final = asyncio.run(wf.run_incident(
        incident={"incident_id": "INC-happy-1", "category": "fire"},
        created_by="test",
    ))
    assert final["status"] == WorkflowRunStatus.AWAITING_APPROVAL.value
    assert len(publisher.published) == 1, "Exactly one approval envelope must be published"
    assert publisher.published[0]["queue"] == "commander-approval-queue"
    assert final["pending_request_id"]


def test_two_concurrent_incidents_run_independently() -> None:
    wf, publisher = _make_workflow_with_in_memory_publisher()

    async def _both() -> list[Any]:
        return await asyncio.gather(
            wf.run_incident(incident={"incident_id": "INC-conc-A", "category": "fire"}, created_by="t"),
            wf.run_incident(incident={"incident_id": "INC-conc-B", "category": "weather"}, created_by="t"),
        )

    docs = asyncio.run(_both())
    assert {d["incident_id"] for d in docs} == {"INC-conc-A", "INC-conc-B"}
    for d in docs:
        assert d["status"] == WorkflowRunStatus.AWAITING_APPROVAL.value
    assert len(publisher.published) == 2


def test_workflow_failure_path_transitions_to_failed() -> None:
    """SC-002 contract: a failure mid-run lands the run in Failed (not lost)."""
    repo = WorkflowRunRepository()
    publisher = _ServiceBusPublisher()
    gate = HitlGateExecutor(repo=repo, publisher=publisher)
    wf = AmaWorkflow(repo=repo, hitl_gate=gate)
    # Patch one executor's run_legacy to raise.
    from apps.agents.maf_runtime.errors import LlmServerError

    async def boom(*_args: Any, **_kwargs: Any) -> Any:
        raise LlmServerError("simulated", correlation_id="t", run_id="x")

    wf._risk.run_legacy = boom  # type: ignore[method-assign]

    try:
        asyncio.run(wf.run_incident(
            incident={"incident_id": "INC-fail-1", "category": "fire"}, created_by="t",
        ))
    except LlmServerError:
        pass

    runs = repo.list(incident_id="INC-fail-1")
    assert len(runs) == 1
    assert runs[0]["status"] == WorkflowRunStatus.FAILED.value
    assert runs[0]["failure_reason"]["last_completed_step"] == "monitoring"
    # SC-003: zero envelopes published when the workflow fails before HITL.
    assert publisher.published == []
