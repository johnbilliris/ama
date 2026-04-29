"""Audit-event vocabulary + emitter for the LLM Evaluation Framework.

Every mutating operation in api/runner emits an AuditEvent through `AuditEmitter`.
The Cosmos-backed emitter lives in `apps/api/app/repositories/eval/audit_repository.py`;
this module provides the vocabulary (AuditAction enum), the protocol, and a fast
in-memory test double.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4

from .models import AuditEvent, AuditEventSubject


class AuditAction(StrEnum):
    """Enumerates every audit action emitted by the framework.

    Bound to data-model.md §AuditEvent. New actions MUST be added here and reflected
    in the audit-event JSON Schema before being emitted.
    """

    # Dataset lifecycle
    dataset_draft_created = "dataset.draft.created"
    dataset_case_added = "dataset.case.added"
    dataset_case_approved = "dataset.case.approved"
    dataset_case_rejected = "dataset.case.rejected"
    dataset_published = "dataset.published"
    dataset_cases_read = "dataset.cases.read"

    # Metric / judge lifecycle
    metric_drafted = "metric.drafted"
    metric_activated = "metric.activated"
    metric_retired = "metric.retired"
    judge_registered = "judge.registered"
    judge_approved = "judge.approved"

    # Run lifecycle
    run_queued = "run.queued"
    run_started = "run.started"
    run_progress = "run.progress"
    run_completed = "run.completed"
    run_failed = "run.failed"
    run_cancelled = "run.cancelled"
    run_partial_preserved = "run.partial.preserved"

    # Infra lifecycle (FR-016..FR-020)
    infra_provisioning_started = "infra.provisioning.started"
    infra_provisioned = "infra.provisioned"
    infra_deprovisioned = "infra.deprovisioned"
    infra_orphan_pending = "infra.orphans.pending"
    infra_orphan_cleaned = "infra.orphan.cleaned"
    infra_orphan_clean_failed = "infra.orphan.clean.failed"
    infra_policy_violated = "infra.policy.violated"

    # Scorecard / trace access
    scorecard_read = "scorecard.read"
    scorecard_trace_read = "scorecard.trace.read"
    scorecard_export = "scorecard.export"
    evidence_bundle_export = "evidence.bundle.export"

    # Gate
    gate_check_requested = "gate.check.requested"
    gate_pass = "gate.pass"
    gate_fail = "gate.fail"
    gate_override_applied = "gate.override.applied"

    # Policy
    policy_published = "policy.published"

    # Cost
    cost_estimated = "cost.estimated"
    cost_reconciled = "cost.reconciled"


class AuditEmitter(Protocol):
    """Protocol implemented by Cosmos-backed and in-memory emitters."""

    def emit(self, event: AuditEvent) -> AuditEvent: ...


def make_event(
    *,
    action: str | AuditAction,
    principal: str,
    subject_type: str,
    subject_id: str,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Helper to construct an AuditEvent with consistent timestamps + ids."""
    now = datetime.now(UTC)
    return AuditEvent(
        auditId=str(uuid4()),
        action=action.value if isinstance(action, AuditAction) else action,
        principal=principal,
        timestamp=now,
        subject=AuditEventSubject(type=subject_type, id=subject_id),  # type: ignore[arg-type]
        runId=run_id,
        metadata=metadata or {},
        writtenAt=now,
    )


class InMemoryAuditEmitter:
    """Thread-safe in-memory AuditEmitter for tests + dev fallback."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = threading.Lock()

    def emit(self, event: AuditEvent) -> AuditEvent:
        with self._lock:
            self._events.append(event)
        return event

    def events(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)

    def filter(self, *, action: str | None = None, run_id: str | None = None) -> Iterable[AuditEvent]:
        return [
            e for e in self.events() if (action is None or e.action == action) and (run_id is None or e.runId == run_id)
        ]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


__all__ = ["AuditAction", "AuditEmitter", "InMemoryAuditEmitter", "make_event"]
