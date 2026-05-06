"""Offline-queue overflow repository (spec-035 T031).

Tracks ``queue_overflow`` events emitted when the Service Worker drops a
displaced routine entry that never made it back. Persists synthetic envelopes
into the audit ledger via the ``AuditRepository``.

Per [`research.md` § R-007](../../../../specs/035-webapp-capstone-closure/research.md#r-007--offline-queue-tiering),
displaced entries that exhausted the 30-day grace window are appended with
``outcome=queue_overflow`` so the operator-runbook surface them in the
audit-list view.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


@dataclass
class OfflineQueueOverflowRepository:
    audit_repository: AuditRepository

    async def record(
        self,
        *,
        persona_id: str,
        client_correlation_id: str,
        captured_ts: str,
        route: str,
        reason: str,
    ) -> dict[str, Any]:
        synthetic = {
            "outcome": "queue_overflow",
            "personaId": persona_id,
            "appRole": "field-coordinator",
            "operatorIdentity": persona_id,
            "route": route,
            "requestHash": f"sha256:overflow:{client_correlation_id}",
            "timestamp": captured_ts,
            "extensionEnvelope": {
                "reason": reason,
                "client_correlation_id": client_correlation_id,
            },
        }
        try:
            return await self.audit_repository.append(
                synthetic,
                correlation_id=client_correlation_id,
            )
        except Exception:
            logger.exception("queue_overflow audit append failed for %s", client_correlation_id)
            raise


__all__ = ["OfflineQueueOverflowRepository"]
