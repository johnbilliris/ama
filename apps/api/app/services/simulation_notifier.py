"""Tenant-visible lifecycle notices for simulation participants and coordinators.

AUD-023 requires that an idle-expiry warning is an actual delivery with named
recipients, not a log line. Delivery is fail-closed: when the transport raises,
the caller must not mark the notice as sent, so the next scheduler tick retries.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

NOTICE_DOCUMENT_TYPE = "simulation_notice"


def build_expiry_notice(
    tenant: Any,
    *,
    now: datetime,
    lead_time_seconds: float,
) -> dict[str, Any]:
    """Build the persisted notice payload for an idle-expiry warning."""
    expires_at = tenant.expires_at
    coordinator = tenant.created_by
    recipients = sorted(
        {coordinator, *tenant.participants}
        | {
            assignment.oid
            for assignment in getattr(tenant, "participant_assignments", [])
            if assignment.role in {"coordinator", "administrator"}
        }
    )
    expires_iso = expires_at.isoformat() if expires_at is not None else ""
    return {
        "id": f"{tenant.tenant_id}:notice:idle_expiry:{expires_iso}",
        "document_type": NOTICE_DOCUMENT_TYPE,
        "tenant_id": tenant.tenant_id,
        "scenario_id": tenant.scenario_id,
        "notice_type": "idle_expiry_warning",
        "status": tenant.status,
        "coordinator_oid": coordinator,
        "recipients": recipients,
        "expires_at": expires_iso,
        "lead_time_seconds": max(0.0, lead_time_seconds),
        "advance_notice_met": lead_time_seconds >= 24 * 3600,
        "created_at": now.isoformat(),
        "message": (f"Simulation {tenant.tenant_id} is idle and will be archived automatically at {expires_iso}."),
    }


class SimulationNotifier:
    """Transport for tenant-visible lifecycle notices."""

    async def deliver(self, notice: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class OutboxSimulationNotifier(SimulationNotifier):
    """Persist notices as tenant-scoped documents so participants can read them.

    The document is the outbox record; a downstream transport can claim it.
    Any storage failure propagates so the caller can retry on the next tick.
    """

    def __init__(self, simulation_repository: Any):
        self._repo = simulation_repository

    async def deliver(self, notice: dict[str, Any]) -> dict[str, Any]:
        record = dict(notice)
        record.setdefault("delivered_at", datetime.now(UTC).isoformat())
        record["delivery_state"] = "delivered"
        stored = await self._repo.upsert_document(record)
        logger.info(
            "simulation_notice_delivered tenant_id=%s type=%s recipients=%d",
            record.get("tenant_id"),
            record.get("notice_type"),
            len(record.get("recipients", [])),
        )
        return stored
