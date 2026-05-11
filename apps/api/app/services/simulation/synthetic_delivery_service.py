"""Synthetic delivery service — records every sim-originated outbound attempt."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from packages.domain.src.domain.models.sim_synthetic_delivery import SimSyntheticDelivery

logger = logging.getLogger(__name__)

Channel = Literal["sms", "email", "broadcast", "social", "cap_push", "http"]
Reason = Literal["sim-egress-blocked", "publication-gate", "http-wrapper-gate"]

# T-B15: map the spec-024 ``Reason`` enum to the ``synthetic-delivery`` audit
# entry's ``block_reason`` enum (audit-envelope.md §3.15).
_AUDIT_BLOCK_REASON_BY_KEY: dict[str, str] = {
    "sim-egress-blocked": "simulation_tenant_egress_blocked",
    "publication-gate": "publication_service_refusal",
    "http-wrapper-gate": "http_wrapper_refusal",
}


class SyntheticDeliveryService:
    def __init__(self, repo: object | None = None) -> None:
        self._repo = repo
        self._memory: list[SimSyntheticDelivery] = []

    async def record_blocked(
        self,
        *,
        tenant_id: str,
        simulation_id: str,
        channel: Channel,
        audience: str,
        payload_bytes: bytes,
        block_reason: Reason,
        intended_url: str | None = None,
        aws_tier: Literal["advice", "watch_and_act", "emergency_warning"] | None = None,
        rendered_chat_text: str | None = None,
    ) -> SimSyntheticDelivery:
        record = SimSyntheticDelivery(
            id=str(uuid4()),
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            channel=channel,
            audience=audience,
            payload_hash=hashlib.sha256(payload_bytes).hexdigest(),
            block_reason=block_reason,
            intended_url=intended_url,
            created_at=datetime.now(UTC),
        )
        if self._repo is not None:
            await self._repo.upsert(record)  # type: ignore[attr-defined]
        else:
            self._memory.append(record)
        logger.info(
            "sim.synthetic_delivery tenant=%s channel=%s reason=%s",
            tenant_id,
            channel,
            block_reason,
        )
        # T-B15 / FR-019 — also emit the canonical typed audit envelope so
        # the gap-free sequence-number guarantee covers every blocked
        # outbound. Failures here MUST NOT cascade — synthetic-delivery is a
        # secondary observability channel.
        try:
            from apps.api.app.services.simulation.audit_writer import (
                get_audit_writer,
            )

            block_reason_audit = _AUDIT_BLOCK_REASON_BY_KEY.get(
                block_reason, "simulation_tenant_egress_blocked"
            )
            details: dict[str, object] = {
                "channel": channel,
                "audience": audience,
                "message_id": f"sim-msg-{record.id[:12].replace('-', '')}",
                "sim_timestamp": record.created_at,
                "block_reason": block_reason_audit,
                "payload_hash": record.payload_hash,
                "watermark_applied": True,
            }
            if aws_tier is not None:
                details["aws_tier"] = aws_tier
            if rendered_chat_text is not None:
                details["rendered_chat_text"] = rendered_chat_text
            await get_audit_writer().write(
                "synthetic-delivery",
                simulation_id=simulation_id,
                actor="synthetic_delivery_service",
                details=details,
            )
        except Exception:  # pragma: no cover - best-effort audit
            logger.exception(
                "sim.synthetic_delivery.audit_failed tenant=%s sim=%s",
                tenant_id,
                simulation_id,
            )
        return record

    async def list_for_tenant(self, tenant_id: str) -> list[SimSyntheticDelivery]:
        if self._repo is not None:
            return await self._repo.list_for_tenant(tenant_id)  # type: ignore[attr-defined]
        return [r for r in self._memory if r.tenant_id == tenant_id]


_default_singleton: SyntheticDeliveryService | None = None


def get_synthetic_delivery_service() -> SyntheticDeliveryService:
    global _default_singleton
    if _default_singleton is None:
        _default_singleton = SyntheticDeliveryService()
    return _default_singleton


def reset_default_singleton_for_tests() -> None:
    """Reset the process-wide singleton — tests only."""
    global _default_singleton
    _default_singleton = None
