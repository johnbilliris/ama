"""Cosmos DB repository for recorded ``SimulationEvent`` / ``PlaybackSnapshot``.

Feature 026-sim-warp-playback introduces the ``sim-events`` container
partitioned by ``/tenant_id`` that stores:

* every recorded simulation event in a monotonic per-tenant sequence,
* periodic playback snapshots used to accelerate scrub, and
* annotation events (authored during after-action review).

Mirrors the pattern of :class:`app.repositories.simulation_repository`:
when ``COSMOS_ENDPOINT`` is set we talk to Cosmos; otherwise an
in-memory dict keyed by ``tenant_id`` keeps unit/contract tests working
without infrastructure.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from packages.domain.src.domain.models.simulation_event import (
    PlaybackSnapshot,
    SignalSchedulerState,
    SimulationEvent,
)

logger = logging.getLogger(__name__)

_CONTAINER = "sim-events"
_DEFAULT_DB = "disaster-hub"


def _build_cosmos_client() -> Any:
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


class SimulationEventRepository:
    """Append-only storage for simulation events plus snapshot retrieval."""

    def __init__(
        self,
        cosmos_client: Any | None = None,
        database_name: str | None = None,
    ) -> None:
        self._db_name = database_name or os.environ.get("COSMOS_DATABASE", _DEFAULT_DB)
        self._container_name = _CONTAINER
        self._events: dict[str, list[SimulationEvent]] = {}
        self._snapshots: dict[str, list[PlaybackSnapshot]] = {}
        self._scheduler_states: dict[str, SignalSchedulerState] = {}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "SimulationEventRepository: Cosmos init failed (%s); "
                    "falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            self._client = None

    def _get_container(self) -> Any | None:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    # ------------------------------------------------------------------
    # sequence bookkeeping
    # ------------------------------------------------------------------

    def next_sequence(self, tenant_id: str) -> int:
        container = self._get_container()
        if container is None:
            return len(self._events.get(tenant_id, [])) + 1
        query = (
            "SELECT VALUE MAX(c.event_seq) FROM c "
            "WHERE c.document_type = 'simulation_event' AND c.tenant_id = @tid"
        )
        try:
            items = list(
                container.query_items(
                    query,
                    parameters=[{"name": "@tid", "value": tenant_id}],
                    partition_key=tenant_id,
                )
            )
            current = items[0] if items and items[0] is not None else 0
            return int(current) + 1
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "next_sequence: Cosmos query failed (%s); using in-memory counter",
                exc,
            )
            return len(self._events.get(tenant_id, [])) + 1

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------

    def append_event(self, event: SimulationEvent) -> SimulationEvent:
        container = self._get_container()
        if container is None:
            self._events.setdefault(event.tenant_id, []).append(event)
            return event
        try:
            container.upsert_item(event.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "append_event: Cosmos write failed (%s); caching event in-memory",
                exc,
            )
            self._events.setdefault(event.tenant_id, []).append(event)
        return event

    def list_events(
        self,
        tenant_id: str,
        *,
        after_seq: int = 0,
        limit: int = 200,
        include_annotations: bool = True,
    ) -> list[SimulationEvent]:
        container = self._get_container()
        if container is None:
            events = sorted(
                self._events.get(tenant_id, []),
                key=lambda e: e.event_seq,
            )
            events = [e for e in events if e.event_seq > after_seq]
            if not include_annotations:
                events = [e for e in events if e.event_type != "annotation"]
            return events[:limit]

        filters = ["c.document_type = 'simulation_event'", "c.tenant_id = @tid", "c.event_seq > @seq"]
        params: list[dict[str, Any]] = [
            {"name": "@tid", "value": tenant_id},
            {"name": "@seq", "value": after_seq},
        ]
        if not include_annotations:
            filters.append("c.event_type != 'annotation'")
        query = (
            f"SELECT TOP @limit * FROM c WHERE {' AND '.join(filters)} "
            "ORDER BY c.event_seq ASC"
        )
        params.append({"name": "@limit", "value": limit})
        try:
            items = list(
                container.query_items(
                    query, parameters=params, partition_key=tenant_id
                )
            )
            return [SimulationEvent.model_validate(i) for i in items]
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_events: Cosmos query failed (%s)", exc)
            return []

    def count_events(self, tenant_id: str) -> int:
        container = self._get_container()
        if container is None:
            return len(self._events.get(tenant_id, []))
        query = (
            "SELECT VALUE COUNT(1) FROM c "
            "WHERE c.document_type = 'simulation_event' AND c.tenant_id = @tid"
        )
        try:
            items = list(
                container.query_items(
                    query,
                    parameters=[{"name": "@tid", "value": tenant_id}],
                    partition_key=tenant_id,
                )
            )
            return int(items[0]) if items else 0
        except Exception as exc:  # noqa: BLE001
            logger.warning("count_events: Cosmos query failed (%s)", exc)
            return 0

    def update_event(self, event: SimulationEvent) -> SimulationEvent:
        container = self._get_container()
        if container is None:
            bucket = self._events.setdefault(event.tenant_id, [])
            for idx, existing in enumerate(bucket):
                if existing.id == event.id:
                    bucket[idx] = event
                    return event
            bucket.append(event)
            return event
        try:
            container.upsert_item(event.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("update_event: Cosmos write failed (%s)", exc)
        return event

    def delete_event(self, tenant_id: str, event_id: str) -> bool:
        container = self._get_container()
        if container is None:
            bucket = self._events.get(tenant_id, [])
            for idx, existing in enumerate(bucket):
                if existing.id == event_id:
                    bucket.pop(idx)
                    return True
            return False
        try:
            container.delete_item(item=event_id, partition_key=tenant_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("delete_event: Cosmos delete failed (%s)", exc)
            return False

    def get_annotation(self, tenant_id: str, annotation_id: str) -> SimulationEvent | None:
        container = self._get_container()
        if container is None:
            for ev in self._events.get(tenant_id, []):
                if ev.event_type == "annotation" and ev.id == annotation_id:
                    return ev
            return None
        query = (
            "SELECT * FROM c WHERE c.document_type = 'simulation_event' "
            "AND c.tenant_id = @tid AND c.event_type = 'annotation' "
            "AND c.id = @aid"
        )
        try:
            items = list(
                container.query_items(
                    query,
                    parameters=[
                        {"name": "@tid", "value": tenant_id},
                        {"name": "@aid", "value": annotation_id},
                    ],
                    partition_key=tenant_id,
                )
            )
            if items:
                return SimulationEvent.model_validate(items[0])
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_annotation: Cosmos query failed (%s)", exc)
            return None

    # ------------------------------------------------------------------
    # snapshots
    # ------------------------------------------------------------------

    def save_snapshot(self, snapshot: PlaybackSnapshot) -> PlaybackSnapshot:
        container = self._get_container()
        if container is None:
            self._snapshots.setdefault(snapshot.tenant_id, []).append(snapshot)
            return snapshot
        try:
            container.upsert_item(snapshot.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("save_snapshot: Cosmos write failed (%s)", exc)
            self._snapshots.setdefault(snapshot.tenant_id, []).append(snapshot)
        return snapshot

    def list_snapshots(self, tenant_id: str) -> list[PlaybackSnapshot]:
        container = self._get_container()
        if container is None:
            return sorted(
                self._snapshots.get(tenant_id, []),
                key=lambda s: s.sim_time_offset,
            )
        query = (
            "SELECT * FROM c WHERE c.document_type = 'playback_snapshot' "
            "AND c.tenant_id = @tid ORDER BY c.sim_time_offset ASC"
        )
        try:
            items = list(
                container.query_items(
                    query,
                    parameters=[{"name": "@tid", "value": tenant_id}],
                    partition_key=tenant_id,
                )
            )
            return [PlaybackSnapshot.model_validate(i) for i in items]
        except Exception as exc:  # noqa: BLE001
            logger.warning("list_snapshots: Cosmos query failed (%s)", exc)
            return []

    def get_nearest_snapshot(
        self, tenant_id: str, before_sim_time: float
    ) -> PlaybackSnapshot | None:
        snapshots = [
            s for s in self.list_snapshots(tenant_id) if s.sim_time_offset <= before_sim_time
        ]
        return snapshots[-1] if snapshots else None

    # ------------------------------------------------------------------
    # scheduler state
    # ------------------------------------------------------------------

    def get_scheduler_state(self, tenant_id: str) -> SignalSchedulerState | None:
        container = self._get_container()
        if container is None:
            return self._scheduler_states.get(tenant_id)
        query = (
            "SELECT * FROM c WHERE c.document_type = 'signal_scheduler_state' "
            "AND c.tenant_id = @tid"
        )
        try:
            items = list(
                container.query_items(
                    query,
                    parameters=[{"name": "@tid", "value": tenant_id}],
                    partition_key=tenant_id,
                )
            )
            return SignalSchedulerState.model_validate(items[0]) if items else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("get_scheduler_state: Cosmos query failed (%s)", exc)
            return None

    def save_scheduler_state(self, state: SignalSchedulerState) -> SignalSchedulerState:
        container = self._get_container()
        if container is None:
            self._scheduler_states[state.tenant_id] = state
            return state
        try:
            container.upsert_item(state.model_dump(mode="json"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("save_scheduler_state: Cosmos write failed (%s)", exc)
            self._scheduler_states[state.tenant_id] = state
        return state
