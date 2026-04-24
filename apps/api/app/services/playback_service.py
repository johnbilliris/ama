"""Playback service (feature 026 — US3).

Read-only access to recorded :class:`SimulationEvent` / :class:`PlaybackSnapshot`
documents for after-action review. Enforces participant/controller access
control and paginates the event stream via a stable ``event_seq`` cursor.
"""

from __future__ import annotations

import logging
from typing import Any

from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository

logger = logging.getLogger(__name__)


class PlaybackService:
    def __init__(
        self,
        *,
        event_repository: SimulationEventRepository,
        simulation_repository: SimulationRepository,
    ) -> None:
        self._events = event_repository
        self._sims = simulation_repository

    # ------------------------------------------------------------------
    # access control
    # ------------------------------------------------------------------

    async def check_access(self, tenant_id: str, user_oid: str) -> bool:
        tenant = await self._sims.get_by_tenant_id(tenant_id)
        if tenant is None:
            return False
        return tenant.created_by == user_oid or user_oid in tenant.participants

    # ------------------------------------------------------------------
    # query
    # ------------------------------------------------------------------

    async def get_events(
        self,
        tenant_id: str,
        *,
        requesting_user_oid: str,
        after_seq: int = 0,
        limit: int = 200,
        include_annotations: bool = True,
    ) -> dict[str, Any]:
        tenant = await self._sims.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise LookupError("simulation_not_found")
        if not (tenant.created_by == requesting_user_oid or requesting_user_oid in tenant.participants):
            raise PermissionError("playback_access_denied")

        events = self._events.list_events(
            tenant_id,
            after_seq=after_seq,
            limit=limit,
            include_annotations=include_annotations,
        )
        total = self._events.count_events(tenant_id)
        has_more = len(events) == limit and (
            events and events[-1].event_seq < total
        )
        next_cursor = events[-1].event_seq if events and has_more else None
        return {
            "events": [e.model_dump(mode="json") for e in events],
            "has_more": has_more,
            "next_cursor": next_cursor,
            "total_events": total,
            "playback_status": tenant.playback_status or "full",
        }

    async def get_snapshots(
        self,
        tenant_id: str,
        *,
        requesting_user_oid: str,
        before_sim_time: float | None = None,
    ) -> dict[str, Any]:
        tenant = await self._sims.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise LookupError("simulation_not_found")
        if not (tenant.created_by == requesting_user_oid or requesting_user_oid in tenant.participants):
            raise PermissionError("playback_access_denied")

        if before_sim_time is not None:
            snap = self._events.get_nearest_snapshot(tenant_id, before_sim_time)
            return {"snapshots": [snap.model_dump(mode="json")] if snap else []}
        return {
            "snapshots": [
                s.model_dump(mode="json") for s in self._events.list_snapshots(tenant_id)
            ]
        }

