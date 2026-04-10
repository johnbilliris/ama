import logging
from typing import Any

from packages.domain.src.domain.models.simulation_tenant import SimulationTenant

logger = logging.getLogger(__name__)


class SimulationRepository:
    """Cosmos DB operations for SimulationTenant CRUD against the `simulation` container."""

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._client = cosmos_client
        self._db_name = database_name
        self._container_name = "simulation"
        self._in_memory: dict[str, SimulationTenant] = {}

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    async def create(self, tenant: SimulationTenant) -> SimulationTenant:
        container = self._get_container()
        if container:
            doc = tenant.model_dump(mode="json")
            container.upsert_item(doc)
        else:
            self._in_memory[tenant.tenant_id] = tenant
        return tenant

    async def get_by_tenant_id(self, tenant_id: str) -> SimulationTenant | None:
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE c.tenant_id = @tid AND c.document_type = 'simulation_tenant'"
            )
            items = list(
                container.query_items(query, parameters=[{"name": "@tid", "value": tenant_id}])
            )
            if items:
                return SimulationTenant.model_validate(items[0])
            return None
        return self._in_memory.get(tenant_id)

    async def get_by_participant(self, user_oid: str) -> list[SimulationTenant]:
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE ARRAY_CONTAINS(c.participants, @oid) "
                "AND c.document_type = 'simulation_tenant' "
                "AND c.status IN ('active', 'paused')"
            )
            items = list(
                container.query_items(query, parameters=[{"name": "@oid", "value": user_oid}])
            )
            return [SimulationTenant.model_validate(item) for item in items]
        return [
            t
            for t in self._in_memory.values()
            if user_oid in t.participants and t.status in ("active", "paused")
        ]

    async def list_by_status(
        self, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[SimulationTenant], int]:
        container = self._get_container()
        if container:
            where = "WHERE c.document_type = 'simulation_tenant'"
            params: list[dict[str, Any]] = []
            if status:
                where += " AND c.status = @status"
                params.append({"name": "@status", "value": status})
            count_query = f"SELECT VALUE COUNT(1) FROM c {where}"
            total = list(container.query_items(count_query, parameters=params))[0]
            query = f"SELECT * FROM c {where} ORDER BY c.created_at DESC OFFSET @offset LIMIT @limit"
            params.extend([
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit},
            ])
            items = list(container.query_items(query, parameters=params))
            return [SimulationTenant.model_validate(i) for i in items], total
        tenants = list(self._in_memory.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        total = len(tenants)
        tenants.sort(key=lambda t: t.created_at, reverse=True)
        return tenants[offset : offset + limit], total

    async def count_active(self) -> int:
        container = self._get_container()
        if container:
            query = (
                "SELECT VALUE COUNT(1) FROM c "
                "WHERE c.document_type = 'simulation_tenant' "
                "AND c.status IN ('provisioning', 'active', 'paused')"
            )
            return list(container.query_items(query))[0]
        return sum(
            1
            for t in self._in_memory.values()
            if t.status in ("provisioning", "active", "paused")
        )

    async def update(self, tenant: SimulationTenant) -> SimulationTenant:
        container = self._get_container()
        if container:
            doc = tenant.model_dump(mode="json")
            container.upsert_item(doc)
        else:
            self._in_memory[tenant.tenant_id] = tenant
        return tenant

    async def is_participant(self, tenant_id: str, user_oid: str) -> bool:
        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None:
            return False
        return user_oid in tenant.participants

    async def list_expired(self) -> list[SimulationTenant]:
        """Find active/paused tenants past their expires_at timestamp."""
        container = self._get_container()
        if container:
            from datetime import UTC, datetime

            now = datetime.now(UTC).isoformat()
            query = (
                "SELECT * FROM c WHERE c.document_type = 'simulation_tenant' "
                "AND c.status IN ('active', 'paused') "
                "AND c.expires_at <= @now"
            )
            items = list(
                container.query_items(query, parameters=[{"name": "@now", "value": now}])
            )
            return [SimulationTenant.model_validate(i) for i in items]
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        return [
            t
            for t in self._in_memory.values()
            if t.status in ("active", "paused") and t.expires_at and t.expires_at <= now
        ]
