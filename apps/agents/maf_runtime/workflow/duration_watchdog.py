"""72h duration watchdog (T044, FR-012c).

Periodic task — runs every 5 minutes inside the agents Container App. Scans
``workflow_runs`` for documents in a non-terminal state (``Running`` or
``AwaitingApproval``) where ``last_step_at`` is older than the configured
threshold (default 72h). For every match:

1. Transitions the run to ``NeedsOperatorDecision`` via the repository (which
   validates the transition through the FR-011b state machine).
2. Emits an operator-visible warning log — Application Insights alert rule
   (T068-style) catches the ``workflow.duration_cap_exceeded`` event.

Configurable via env vars:
- ``MAF_DURATION_CAP_HOURS`` (default 72)
- ``MAF_WATCHDOG_INTERVAL_SECONDS`` (default 300)
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from ..repositories.workflow_run_repository import WorkflowRunRepository
from .run_state import WorkflowRunStatus

logger = logging.getLogger(__name__)


def _hours_threshold() -> float:
    return float(os.environ.get("MAF_DURATION_CAP_HOURS", "72"))


def _interval_seconds() -> float:
    return float(os.environ.get("MAF_WATCHDOG_INTERVAL_SECONDS", "300"))


def _is_overdue(doc: dict[str, Any], *, threshold_hours: float, now: datetime) -> bool:
    if not doc.get("is_active"):
        return False
    last_step = doc.get("last_step_at")
    if not last_step:
        return False
    try:
        when = datetime.fromisoformat(str(last_step))
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
    except Exception:  # noqa: BLE001
        return False
    return (now - when) > timedelta(hours=threshold_hours)


def scan_once(
    repo: WorkflowRunRepository,
    *,
    threshold_hours: float | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Run a single watchdog pass; return the list of run documents transitioned."""
    threshold = threshold_hours if threshold_hours is not None else _hours_threshold()
    now_dt = now or datetime.now(UTC)
    transitioned: list[dict[str, Any]] = []
    # Scan both active states.
    for status in (WorkflowRunStatus.RUNNING.value, WorkflowRunStatus.AWAITING_APPROVAL.value):
        for doc in repo.list(status=status, limit=200):
            if _is_overdue(doc, threshold_hours=threshold, now=now_dt):
                try:
                    updated = repo.update_status(
                        doc["id"],
                        WorkflowRunStatus.NEEDS_OPERATOR_DECISION,
                        correlation_id=f"watchdog-{int(now_dt.timestamp())}",
                    )
                    transitioned.append(updated)
                    logger.warning(
                        "workflow.duration_cap_exceeded run_id=%s incident_id=%s last_step_at=%s threshold_hours=%s",
                        doc["id"],
                        doc.get("incident_id"),
                        doc.get("last_step_at"),
                        threshold,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("watchdog: failed to transition run %s", doc.get("id"))
    return transitioned


async def run_forever(repo: WorkflowRunRepository | None = None) -> None:  # pragma: no cover - long-running
    """Container-Apps entry point. Sleeps ``MAF_WATCHDOG_INTERVAL_SECONDS`` between scans."""
    repo = repo or WorkflowRunRepository()
    interval = _interval_seconds()
    logger.info("duration_watchdog started interval=%.0fs threshold_hours=%.1f", interval, _hours_threshold())
    while True:
        try:
            transitioned = scan_once(repo)
            if transitioned:
                logger.info("duration_watchdog transitioned %d run(s)", len(transitioned))
        except Exception:  # noqa: BLE001
            logger.exception("duration_watchdog scan failed; will retry")
        await asyncio.sleep(interval)


__all__ = ["scan_once", "run_forever"]
