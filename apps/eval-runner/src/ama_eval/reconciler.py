"""Reconciler — sweeps for orphaned deployments tagged eval-runId.

Runs as a scheduled Container Apps Job per Bicep schedule.
Exits with non-zero if any orphan was found and could not be cleaned.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ama_eval_core.audit import AuditAction

log = logging.getLogger(__name__)


@dataclass
class Orphan:
    resourceId: str
    deploymentName: str
    runId: str | None
    ageMinutes: int


@dataclass
class ReconcileContext:
    list_deployments: Callable[[], Iterable[dict]]
    delete_deployment: Callable[[str], None]
    is_run_terminal: Callable[[str], bool]
    audit_emit: Callable[..., None] = lambda **_: None
    grace_minutes: int = 30


def find_orphans(ctx: ReconcileContext) -> list[Orphan]:
    """Identify deployments tagged with eval-runId whose run has terminated."""
    now = datetime.now(UTC)
    orphans: list[Orphan] = []
    for d in ctx.list_deployments():
        tags = d.get("tags") or {}
        run_id = tags.get("eval-runId")
        if not run_id:
            continue
        created_str = d.get("createdAt") or tags.get("eval-createdAt")
        try:
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00")) if created_str else now
        except Exception:
            created = now
        age = (now - created) // timedelta(minutes=1)
        if age < ctx.grace_minutes:
            continue
        if ctx.is_run_terminal(run_id):
            orphans.append(
                Orphan(
                    resourceId=d.get("id", ""),
                    deploymentName=d.get("name", ""),
                    runId=run_id,
                    ageMinutes=int(age),
                )
            )
    return orphans


def reconcile(ctx: ReconcileContext) -> int:
    """Find + delete orphans. Returns count of orphans cleaned."""
    orphans = find_orphans(ctx)
    cleaned = 0
    for o in orphans:
        try:
            ctx.delete_deployment(o.deploymentName)
            ctx.audit_emit(
                action=AuditAction.infra_orphan_cleaned.value,
                principal="reconciler",
                subject_type="deployment",
                subject_id=o.deploymentName,
                run_id=o.runId,
                metadata={"ageMinutes": o.ageMinutes, "resourceId": o.resourceId},
            )
            cleaned += 1
        except Exception as exc:
            log.error("failed to clean orphan %s: %s", o.deploymentName, exc)
            ctx.audit_emit(
                action=AuditAction.infra_orphan_clean_failed.value,
                principal="reconciler",
                subject_type="deployment",
                subject_id=o.deploymentName,
                run_id=o.runId,
                metadata={"error": str(exc)},
            )
    return cleaned


__all__ = ["Orphan", "ReconcileContext", "find_orphans", "reconcile"]
