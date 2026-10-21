"""spec-038 — emit ingest audit events for the snapshot pipeline."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from app.observability.audit import emit_audit_event
except Exception:  # pragma: no cover

    def emit_audit_event(name: str, payload: dict[str, Any]) -> None:
        logger.info("AUDIT(stub) %s %s", name, payload)


def emit_admission_outcome(
    *,
    snapshot_id: str,
    accepted: list[dict[str, Any]] | None = None,
    rejected: list[dict[str, Any]] | None = None,
) -> None:
    if rejected:
        emit_audit_event(
            "audit.snapshot_admission_rejected",
            {
                "snapshot_id": snapshot_id,
                "rejected": [r["source_id"] for r in rejected],
                "reason": "above-OFFICIAL classification",
            },
        )
    if accepted:
        emit_audit_event(
            "audit.snapshot_admission_accepted",
            {"snapshot_id": snapshot_id, "count": len(accepted)},
        )


__all__ = ["emit_admission_outcome"]
