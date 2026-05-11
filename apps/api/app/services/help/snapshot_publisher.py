"""spec-038 T-AA053 — snapshot publisher (FR-011a/b/c).

Orchestrates: dual-approval validation → emit SnapshotRecord → invoke the
ingest-runner snapshot loader → swing alias → emit ``audit.snapshot_published``.
Rollback is a paired operation that re-binds the alias to a prior snapshot
within the FR-011c 5-min SLO.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from ama_domain import Approver, SnapshotRecord
from app.observability.audit import emit_audit_event
from app.repositories import help_repositories as repo
from app.services.help.snapshot_indexer import build_index, swing_alias

logger = logging.getLogger(__name__)


# FR-011c — 5-minute rollback SLO (seconds).
ROLLBACK_SLO_SECONDS = 300


def _validate_dual_approval(approvers: list[Approver]) -> None:
    """Final defence-in-depth — Pydantic also enforces this at construction."""
    identities = {a.identity for a in approvers}
    roles = {a.role for a in approvers}
    if len(identities) < 2:
        raise ValueError("FR-011b: at least two distinct approver identities required")
    if "help_content_owner" not in roles:
        raise ValueError("FR-011b: a help_content_owner must approve")
    if not (roles & {"safety_lead", "governance_lead"}):
        raise ValueError("FR-011b: a safety_lead or governance_lead must approve")


def publish_snapshot(record: SnapshotRecord) -> SnapshotRecord:
    """Publish ``record``, swing the alias, emit the audit event."""
    _validate_dual_approval(record.approvers)
    started = time.perf_counter()
    build_index(record.ai_search_index_name, record.sources)
    swing_alias(record.ai_search_index_name)
    persisted = repo.append_snapshot_record(record.model_dump(mode="json"))
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    emit_audit_event(
        "audit.snapshot_published",
        {
            "snapshot_id": record.id,
            "tenant_id": record.tenant_id,
            "index_name": record.ai_search_index_name,
            "approvers": [a.identity for a in record.approvers],
            "elapsed_ms": elapsed_ms,
        },
    )
    logger.info("snapshot %s published in %d ms", record.id, elapsed_ms)
    return SnapshotRecord.model_validate(persisted)


def rollback_snapshot(
    restored_snapshot_id: str, previous_snapshot_id: str, actor_id: str, change_reason: str
) -> dict[str, Any]:
    """FR-011c — re-bind alias to ``restored_snapshot_id`` (must already exist)."""
    started = time.perf_counter()
    index_name = f"help-corpus-{restored_snapshot_id}"
    swing_alias(index_name)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    if elapsed_ms / 1000 > ROLLBACK_SLO_SECONDS:
        logger.error("rollback SLO breach: %d ms", elapsed_ms)
    emit_audit_event(
        "audit.snapshot_rollback",
        {
            "previous_snapshot_id": previous_snapshot_id,
            "restored_snapshot_id": restored_snapshot_id,
            "actor_id": actor_id,
            "change_reason": change_reason,
            "elapsed_ms": elapsed_ms,
            "slo_breach": elapsed_ms / 1000 > ROLLBACK_SLO_SECONDS,
        },
    )
    return {
        "restored_snapshot_id": restored_snapshot_id,
        "previous_snapshot_id": previous_snapshot_id,
        "elapsed_ms": elapsed_ms,
        "rolled_back_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


__all__ = ["publish_snapshot", "rollback_snapshot", "ROLLBACK_SLO_SECONDS"]
