"""72h watchdog tests (T044, FR-012c)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.agents.maf_runtime.repositories.workflow_run_repository import WorkflowRunRepository
from apps.agents.maf_runtime.workflow.duration_watchdog import scan_once
from apps.agents.maf_runtime.workflow.run_state import WorkflowRunStatus


def _make_run(repo: WorkflowRunRepository, *, incident_id: str, last_step_at: datetime) -> str:
    doc = repo.create(incident_id=incident_id, current_step="risk_assessment", created_by="t")
    # Overwrite last_step_at to the simulated past time.
    doc["last_step_at"] = last_step_at.isoformat()
    repo._in_memory[doc["id"]] = doc  # type: ignore[attr-defined]
    return doc["id"]


def test_just_under_72h_does_not_transition() -> None:
    repo = WorkflowRunRepository()
    now = datetime.now(UTC)
    rid = _make_run(repo, incident_id="INC-young", last_step_at=now - timedelta(hours=71, minutes=59))
    transitioned = scan_once(repo, threshold_hours=72.0, now=now)
    assert transitioned == []
    assert repo.get(rid)["status"] == WorkflowRunStatus.RUNNING.value


def test_over_72h_transitions_to_needs_operator_decision() -> None:
    repo = WorkflowRunRepository()
    now = datetime.now(UTC)
    rid = _make_run(repo, incident_id="INC-old", last_step_at=now - timedelta(hours=73))
    transitioned = scan_once(repo, threshold_hours=72.0, now=now)
    assert len(transitioned) == 1
    assert transitioned[0]["id"] == rid
    assert repo.get(rid)["status"] == WorkflowRunStatus.NEEDS_OPERATOR_DECISION.value
