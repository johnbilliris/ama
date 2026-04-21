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
            "sim.synthetic_delivery tenant=%s channel=%s reason=%s", tenant_id, channel, block_reason
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
