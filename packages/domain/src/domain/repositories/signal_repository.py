import logging
from datetime import UTC, datetime
from typing import Any

from packages.domain.src.domain.models.signal import Signal

logger = logging.getLogger(__name__)

SIGNALS_STORE: dict[str, Signal] = {}
_SIGNAL_SCOPES: dict[str, str] = {}


class SignalRepository:
    """Cosmos DB signal persistence with hierarchical partition key.

    Partition key: /scope/jurisdictionId/dataSourceId
    - scope: 'live' for operational, 'sim_{runId}' for simulation
    - jurisdictionId: 'national', 'nsw', 'vic', etc.
    - dataSourceId: from seed catalogue

    National signals create fan-out reference records in each affected
    jurisdiction partition.
    """

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._cosmos = cosmos_client
        self._database_name = database_name
        self._container_name = "signals"

    async def save(self, signal: Signal, scope: str = "live") -> None:
        jurisdiction = signal.jurisdiction_id or "national"
        partition_key = f"{scope}/{jurisdiction}/{signal.data_source_id}"

        if self._cosmos:
            container = self._cosmos.get_database_client(self._database_name).get_container_client(
                self._container_name
            )
            doc = signal.model_dump(mode="json")
            doc["id"] = signal.signal_id
            doc["partitionKey"] = partition_key
            doc["scope"] = scope
            await container.upsert_item(doc)
        else:
            SIGNALS_STORE[signal.signal_id] = signal
            _SIGNAL_SCOPES[signal.signal_id] = scope

    async def save_with_fanout(
        self,
        signal: Signal,
        affected_jurisdiction_ids: list[str],
        scope: str = "live",
    ) -> None:
        await self.save(signal, scope)
        for jid in affected_jurisdiction_ids:
            if jid != (signal.jurisdiction_id or "national"):
                ref = signal.model_copy(update={"jurisdiction_id": jid})
                if self._cosmos:
                    await self.save(ref, scope)
                else:
                    ref_key = f"{ref.signal_id}:ref:{jid}"
                    SIGNALS_STORE[ref_key] = ref
                    _SIGNAL_SCOPES[ref_key] = scope

    async def query_by_incident(
        self,
        incident_id: str,
        scope: str = "live",
        limit: int = 100,
    ) -> list[Signal]:
        if self._cosmos:
            container = self._cosmos.get_database_client(self._database_name).get_container_client(
                self._container_name
            )
            query = "SELECT * FROM c WHERE c.incident_id = @incidentId AND c.scope = @scope"
            params = [
                {"name": "@incidentId", "value": incident_id},
                {"name": "@scope", "value": scope},
            ]
            items = container.query_items(query=query, parameters=params, max_item_count=limit)
            return [Signal(**item) async for item in items]
        return [
            s for key, s in SIGNALS_STORE.items()
            if s.incident_id == incident_id
            and _SIGNAL_SCOPES.get(key, "live") == scope
        ][:limit]

    async def query_by_jurisdiction(
        self,
        jurisdiction_id: str,
        scope: str = "live",
        category: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        if self._cosmos:
            conditions = ["c.scope = @scope"]
            params: list[dict] = [{"name": "@scope", "value": scope}]
            if category:
                conditions.append("c.category = @category")
                params.append({"name": "@category", "value": category})
            if since:
                conditions.append("c.occurred_at >= @since")
                params.append({"name": "@since", "value": since.isoformat()})

            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.occurred_at DESC"
            container = self._cosmos.get_database_client(self._database_name).get_container_client(
                self._container_name
            )
            items = container.query_items(
                query=query,
                parameters=params,
                partition_key=[scope, jurisdiction_id],
                max_item_count=limit,
            )
            return [Signal(**item) async for item in items]
        results = [
            s for s in SIGNALS_STORE.values()
            if (s.jurisdiction_id == jurisdiction_id or jurisdiction_id == "national")
            and (category is None or s.category == category)
            and (since is None or s.occurred_at >= since)
        ]
        results.sort(key=lambda s: s.occurred_at, reverse=True)
        return results[:limit]

    async def query_unassociated(
        self,
        jurisdiction_id: str,
        since: datetime | None = None,
        scope: str = "live",
    ) -> list[Signal]:
        if self._cosmos:
            query = (
                "SELECT * FROM c WHERE c.incident_id = null AND c.scope = @scope "
                "AND c.occurred_at >= @since"
            )
            params = [
                {"name": "@scope", "value": scope},
                {"name": "@since", "value": (since or datetime.now(UTC)).isoformat()},
            ]
            container = self._cosmos.get_database_client(self._database_name).get_container_client(
                self._container_name
            )
            items = container.query_items(
                query=query,
                parameters=params,
                partition_key=[scope, jurisdiction_id],
            )
            return [Signal(**item) async for item in items]
        cutoff = since or datetime.min.replace(tzinfo=UTC)
        return [
            s for s in SIGNALS_STORE.values()
            if s.incident_id is None
            and (s.jurisdiction_id == jurisdiction_id or jurisdiction_id == "national")
            and s.occurred_at >= cutoff
        ]

    async def update_incident_id(self, signal_id: str, incident_id: str) -> None:
        if self._cosmos:
            pass
        elif signal_id in SIGNALS_STORE:
            sig = SIGNALS_STORE[signal_id]
            SIGNALS_STORE[signal_id] = sig.model_copy(update={"incident_id": incident_id})
