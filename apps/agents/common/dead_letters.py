"""Dead-letter persistence and redelivery poller (FR-003a).

Persists failed handoffs to Cosmos DB and provides automatic redelivery
when target agents recover. Terminal `permanently_failed` state after
3 auto + 1 manual redelivery failures.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Iterable
from datetime import UTC, datetime
from typing import Protocol

import httpx
from pydantic import BaseModel, Field


class DeadLetterCosmosContainer(Protocol):
    def upsert_item(self, *, body: dict[str, object]) -> object: ...

    def read_item(self, *, item: str, partition_key: str) -> object: ...

    def query_items(
        self,
        *,
        query: str,
        parameters: list[dict[str, object]],
        enable_cross_partition_query: bool,
    ) -> Iterable[object]: ...


class RedeliveryCallback(Protocol):
    def __call__(self, entry: DeadLetterEntry) -> Awaitable[object]: ...


class HealthCheckCallback(Protocol):
    def __call__(self, agent_name: str) -> Awaitable[bool]: ...


logger = logging.getLogger(__name__)

_POLL_INTERVAL = int(os.environ.get("DEAD_LETTER_POLL_INTERVAL_SECONDS", "30"))
_MAX_AUTO_REDELIVER = 3


class DeadLetterEntry(BaseModel):
    """Represents a failed handoff persisted for redelivery."""

    handoff_id: str
    incident_id: str
    source_agent: str
    target_agent: str
    scope_key: str
    confidence: float
    payload: dict[str, object]
    tenant_id: str = "live"
    status: str = "dead_lettered"
    failure_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    failed_at: datetime | None = None
    retry_count: int = 0

    # FR-003a / R14 extensions
    auto_redeliver_attempts: int = 0
    manual_redeliver_attempts: int = 0
    failure_reasons: list[str] = Field(default_factory=list)
    permanently_failed_at: datetime | None = None


class DeadLetterStore:
    """Cosmos DB-backed dead-letter store."""

    def __init__(self, cosmos_container: DeadLetterCosmosContainer | None = None) -> None:
        self._container = cosmos_container
        self._in_memory: dict[str, DeadLetterEntry] = {}

    def persist(self, entry: DeadLetterEntry) -> str:
        """Persist a dead-letter entry. Returns the handoff_id."""
        if self._container is not None:
            doc = entry.model_dump(mode="json")
            doc["id"] = entry.handoff_id
            self._container.upsert_item(body=doc)
        else:
            self._in_memory[entry.handoff_id] = entry
        return entry.handoff_id

    def get(self, handoff_id: str) -> DeadLetterEntry | None:
        """Retrieve a dead-letter entry by handoff_id."""
        if self._container is not None:
            try:
                doc = self._container.read_item(
                    item=handoff_id,
                    partition_key=handoff_id,
                )
                if not isinstance(doc, dict):
                    raise TypeError("Dead-letter read returned a non-document value")
                return DeadLetterEntry(**doc)
            except Exception:
                return None
        return self._in_memory.get(handoff_id)

    def query(
        self,
        *,
        incident_id: str | None = None,
        target_agent: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[DeadLetterEntry], int]:
        """Query dead-letter entries with optional filters."""
        if self._container is not None:
            conditions = ["1=1"]
            params: list[dict[str, object]] = []
            if incident_id:
                conditions.append("c.incident_id = @incident_id")
                params.append({"name": "@incident_id", "value": incident_id})
            if target_agent:
                conditions.append("c.target_agent = @target_agent")
                params.append({"name": "@target_agent", "value": target_agent})
            if status:
                conditions.append("c.status = @status")
                params.append({"name": "@status", "value": status})

            where_clause = " AND ".join(conditions)
            count_query = f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"
            count_rows = list(
                self._container.query_items(
                    query=count_query,
                    parameters=params,
                    enable_cross_partition_query=True,
                )
            )
            total_value = count_rows[0]
            if not isinstance(total_value, int):
                raise TypeError("Dead-letter count query must return an integer")
            total = total_value

            query_str = f"SELECT * FROM c WHERE {where_clause} ORDER BY c.failed_at DESC OFFSET {offset} LIMIT {limit}"
            items = []
            for doc in self._container.query_items(
                query=query_str,
                parameters=params,
                enable_cross_partition_query=True,
            ):
                if not isinstance(doc, dict):
                    raise TypeError("Dead-letter query returned a non-document row")
                items.append(DeadLetterEntry(**doc))
            return items, total

        # In-memory fallback
        entries = list(self._in_memory.values())
        if incident_id:
            entries = [e for e in entries if e.incident_id == incident_id]
        if target_agent:
            entries = [e for e in entries if e.target_agent == target_agent]
        if status:
            entries = [e for e in entries if e.status == status]
        total = len(entries)
        return entries[offset : offset + limit], total

    def update(self, entry: DeadLetterEntry) -> None:
        """Update an existing dead-letter entry."""
        self.persist(entry)

    def mark_permanently_failed(self, entry: DeadLetterEntry, reason: str) -> None:
        """Transition to permanently_failed terminal state (R14)."""
        entry.status = "permanently_failed"
        entry.permanently_failed_at = datetime.now(UTC)
        entry.failure_reasons.append(reason)
        self.update(entry)


class DeadLetterRedeliveryPoller:
    """Background service polling for recovered agents and redelivering dead-lettered handoffs."""

    def __init__(
        self,
        store: DeadLetterStore,
        deliver_fn: RedeliveryCallback | None = None,
        health_check_fn: HealthCheckCallback | None = None,
        poll_interval: int = _POLL_INTERVAL,
    ) -> None:
        self._store = store
        self._deliver_fn = deliver_fn
        self._health_check_fn = health_check_fn or self._default_health_check
        self._poll_interval = poll_interval
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._known_agents: set[str] = {
            "monitoring",
            "risk_assessment",
            "evacuation",
            "resource_allocation",
            "communication",
        }

    async def start(self) -> None:
        """Start the background polling loop."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Dead-letter redelivery poller started (interval=%ds)", self._poll_interval)

    async def stop(self) -> None:
        """Gracefully stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Dead-letter redelivery poller stopped")

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                await self._check_and_redeliver()
            except Exception:
                logger.exception("Error in dead-letter redelivery poll cycle")
            await asyncio.sleep(self._poll_interval)

    async def _check_and_redeliver(self) -> None:
        """Check agent health and redeliver dead-lettered entries."""
        for agent_name in self._known_agents:
            if await self._health_check_fn(agent_name):
                entries, _ = self._store.query(
                    target_agent=agent_name,
                    status="dead_lettered",
                )
                for entry in entries:
                    if entry.auto_redeliver_attempts >= _MAX_AUTO_REDELIVER:
                        continue
                    await self._attempt_redeliver(entry)

    async def _attempt_redeliver(self, entry: DeadLetterEntry) -> None:
        """Attempt to redeliver a single dead-letter entry."""
        if entry.status == "permanently_failed":
            return
        entry.auto_redeliver_attempts += 1
        backoff = min(30 * (2**entry.auto_redeliver_attempts), 300)

        try:
            if self._deliver_fn:
                entry.status = "pending"
                self._store.update(entry)
                await self._deliver_fn(entry)
                entry.status = "delivered"
                self._store.update(entry)
                logger.info(
                    "dead_letter_redelivered",
                    extra={
                        "handoff_id": entry.handoff_id,
                        "target_agent": entry.target_agent,
                        "auto_attempt": entry.auto_redeliver_attempts,
                    },
                )
        except Exception as exc:
            reason = f"Auto: {exc} (attempt {entry.auto_redeliver_attempts})"
            entry.failure_reasons.append(reason)
            entry.status = "dead_lettered"
            entry.failure_reason = str(exc)

            # R14: permanently fail after 3 auto + 1 manual
            if entry.auto_redeliver_attempts >= _MAX_AUTO_REDELIVER and entry.manual_redeliver_attempts >= 1:
                self._store.mark_permanently_failed(entry, reason)
                logger.error(
                    "dead_letter_permanently_failed",
                    extra={
                        "handoff_id": entry.handoff_id,
                        "auto_attempts": entry.auto_redeliver_attempts,
                        "manual_attempts": entry.manual_redeliver_attempts,
                    },
                )
            else:
                self._store.update(entry)
                logger.warning(
                    "dead_letter_redeliver_failed",
                    extra={
                        "handoff_id": entry.handoff_id,
                        "attempt": entry.auto_redeliver_attempts,
                        "backoff_seconds": backoff,
                    },
                )

    @staticmethod
    async def _default_health_check(agent_name: str) -> bool:
        """Check if target agent is healthy via HTTP health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"http://{agent_name}:8000/health")
                return resp.status_code == 200
        except Exception:
            return False
