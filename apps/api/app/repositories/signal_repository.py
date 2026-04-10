import logging
from typing import Any

logger = logging.getLogger(__name__)


class SignalRepository:
    """Tenant-scoped signal read/write operations against the `signals` Cosmos DB container."""

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._client = cosmos_client
        self._db_name = database_name
        self._container_name = "signals"
        self._in_memory: dict[str, dict[str, Any]] = {}

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    async def create_signal(self, signal_doc: dict[str, Any], tenant_id: str) -> dict[str, Any]:
        signal_doc["scope"] = tenant_id
        container = self._get_container()
        if container:
            container.upsert_item(signal_doc)
        else:
            key = f"{tenant_id}:{signal_doc.get('id', '')}"
            self._in_memory[key] = signal_doc
        return signal_doc

    async def get_signal(
        self, signal_id: str, tenant_id: str, partition_key: str
    ) -> dict[str, Any] | None:
        container = self._get_container()
        if container:
            try:
                return container.read_item(signal_id, partition_key=partition_key)
            except Exception:
                return None
        return self._in_memory.get(f"{tenant_id}:{signal_id}")

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.scope = @scope ORDER BY c._ts DESC OFFSET @offset LIMIT @limit"
            params = [
                {"name": "@scope", "value": tenant_id},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit},
            ]
            items = list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.scope = @scope"
            total = list(
                container.query_items(
                    count_query,
                    parameters=[{"name": "@scope", "value": tenant_id}],
                    enable_cross_partition_query=True,
                )
            )[0]
            return items, total
        tenant_signals = [
            v for k, v in self._in_memory.items() if k.startswith(f"{tenant_id}:")
        ]
        total = len(tenant_signals)
        return tenant_signals[offset : offset + limit], total

    async def count_by_tenant(self, tenant_id: str) -> int:
        container = self._get_container()
        if container:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.scope = @scope"
            return list(
                container.query_items(
                    query,
                    parameters=[{"name": "@scope", "value": tenant_id}],
                    enable_cross_partition_query=True,
                )
            )[0]
        return sum(1 for k in self._in_memory if k.startswith(f"{tenant_id}:"))
