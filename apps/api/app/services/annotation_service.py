"""Annotation service (feature 026 — US5).

Annotations are stored as :class:`SimulationEvent` documents with
``event_type = "annotation"``. Enforces author-only edit/delete and
participant-or-controller create access.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository

from packages.domain.src.domain.models.simulation_event import SimulationEvent


class AnnotationService:
    def __init__(
        self,
        *,
        event_repository: SimulationEventRepository,
        simulation_repository: SimulationRepository,
    ) -> None:
        self._events = event_repository
        self._sims = simulation_repository

    async def _check_participant(self, tenant_id: str, user_oid: str) -> None:
        tenant = await self._sims.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise LookupError("simulation_not_found")
        if not (tenant.created_by == user_oid or user_oid in tenant.participants):
            raise PermissionError("annotation_access_denied")

    async def create(
        self,
        tenant_id: str,
        *,
        author_oid: str,
        sim_time_offset: float,
        text: str,
    ) -> SimulationEvent:
        await self._check_participant(tenant_id, author_oid)
        seq = self._events.next_sequence(tenant_id)
        event = SimulationEvent(
            tenant_id=tenant_id,
            event_seq=seq,
            event_type="annotation",
            sim_time_offset=sim_time_offset,
            wall_clock_time=datetime.now(UTC),
            payload={
                "text": text,
                "author_oid": author_oid,
                "created_at": datetime.now(UTC).isoformat(),
            },
        )
        return self._events.append_event(event)

    async def update(
        self,
        tenant_id: str,
        *,
        annotation_id: str,
        requesting_user_oid: str,
        text: str,
    ) -> SimulationEvent:
        ann = self._events.get_annotation(tenant_id, annotation_id)
        if ann is None:
            raise LookupError("annotation_not_found")
        if ann.payload.get("author_oid") != requesting_user_oid:
            raise PermissionError("annotation_author_only")
        ann.payload["text"] = text
        ann.payload["updated_at"] = datetime.now(UTC).isoformat()
        return self._events.update_event(ann)

    async def delete(
        self,
        tenant_id: str,
        *,
        annotation_id: str,
        requesting_user_oid: str,
    ) -> None:
        ann = self._events.get_annotation(tenant_id, annotation_id)
        if ann is None:
            raise LookupError("annotation_not_found")
        if ann.payload.get("author_oid") != requesting_user_oid:
            raise PermissionError("annotation_author_only")
        self._events.delete_event(tenant_id, ann.id)
