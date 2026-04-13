"""Cosmos DB repository for the ``emergency-plans`` container.

Partition key: ``/region_id``

Provides CRUD + query operations for emergency plan documents used by
the planning agent and plan lifecycle management.

FRs: FR-006, FR-007 | Research: R-002
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmergencyPlanRepository:
    """Tenant-scoped emergency-plan read/write operations against the ``emergency-plans`` Cosmos DB container."""

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._client = cosmos_client
        self._db_name = database_name
        self._container_name = "emergency-plans"
        self._in_memory: dict[str, dict[str, Any]] = {}

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_plan(self, plan_doc: dict) -> dict:
        """Upsert an emergency plan document by plan_id."""
        container = self._get_container()
        if container:
            plan_doc.setdefault("id", plan_doc.get("plan_id", ""))
            container.upsert_item(plan_doc)
        else:
            key = plan_doc.get("plan_id", plan_doc.get("id", ""))
            self._in_memory[key] = plan_doc
        return plan_doc

    async def get_plan(self, plan_id: str, region_id: str) -> dict | None:
        """Read a single plan by id with partition key ``region_id``."""
        container = self._get_container()
        if container:
            try:
                return container.read_item(plan_id, partition_key=region_id)
            except Exception:
                return None
        return self._in_memory.get(plan_id)

    async def list_plans(
        self,
        region_id: str | None = None,
        lifecycle_state: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Query plans with optional region and lifecycle-state filters."""
        container = self._get_container()
        if container:
            clauses: list[str] = []
            params: list[dict[str, object]] = []
            if region_id is not None:
                clauses.append("c.region_id = @region_id")
                params.append({"name": "@region_id", "value": region_id})
            if lifecycle_state is not None:
                clauses.append("c.lifecycle_state = @lifecycle_state")
                params.append({"name": "@lifecycle_state", "value": lifecycle_state})
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            query = f"SELECT TOP @limit * FROM c{where} ORDER BY c._ts DESC"
            params.append({"name": "@limit", "value": limit})
            return list(
                container.query_items(
                    query,
                    parameters=params,
                    enable_cross_partition_query=(region_id is None),
                )
            )
        # In-memory fallback
        results = list(self._in_memory.values())
        if region_id is not None:
            results = [d for d in results if d.get("region_id") == region_id]
        if lifecycle_state is not None:
            results = [d for d in results if d.get("lifecycle_state") == lifecycle_state]
        return results[:limit]

    async def update_plan(self, plan_doc: dict) -> dict:
        """Upsert an updated plan document."""
        return await self.create_plan(plan_doc)

    # ------------------------------------------------------------------
    # Hierarchy & lifecycle queries
    # ------------------------------------------------------------------

    async def get_hierarchy(
        self,
        region_id: str,
        hierarchy_level: str | None = None,
    ) -> list[dict]:
        """Return plans for a region, optionally filtered by hierarchy level."""
        container = self._get_container()
        if container:
            clauses = ["c.region_id = @region_id"]
            params: list[dict[str, object]] = [
                {"name": "@region_id", "value": region_id},
            ]
            if hierarchy_level is not None:
                clauses.append("c.hierarchy_level = @hierarchy_level")
                params.append({"name": "@hierarchy_level", "value": hierarchy_level})
            query = "SELECT * FROM c WHERE " + " AND ".join(clauses) + " ORDER BY c.hierarchy_level"
            return list(
                container.query_items(query, parameters=params, partition_key=region_id)
            )
        # In-memory fallback
        results = [
            d for d in self._in_memory.values() if d.get("region_id") == region_id
        ]
        if hierarchy_level is not None:
            results = [d for d in results if d.get("hierarchy_level") == hierarchy_level]
        return results

    async def get_by_lifecycle_state(
        self,
        lifecycle_state: str,
        limit: int = 50,
    ) -> list[dict]:
        """Cross-partition query for plans in a specific lifecycle state."""
        container = self._get_container()
        if container:
            query = (
                "SELECT TOP @limit * FROM c "
                "WHERE c.lifecycle_state = @lifecycle_state "
                "ORDER BY c._ts DESC"
            )
            params: list[dict[str, object]] = [
                {"name": "@lifecycle_state", "value": lifecycle_state},
                {"name": "@limit", "value": limit},
            ]
            return list(
                container.query_items(
                    query,
                    parameters=params,
                    enable_cross_partition_query=True,
                )
            )
        # In-memory fallback
        results = [
            d for d in self._in_memory.values()
            if d.get("lifecycle_state") == lifecycle_state
        ]
        return results[:limit]
