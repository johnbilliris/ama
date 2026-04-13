"""Cosmos DB repository for the ``recovery-catalogue`` container.

Partition key: ``/domain``

Read-heavy catalogue of recovery outcomes, activities, and indicators
sourced from the AIDR National Disaster Recovery Monitoring & Evaluation
framework. Seeded by ``scripts/seed_loader.py``.

FRs: FR-029 | Research: R-008
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RecoveryCatalogueRepository:
    """Read/write operations against the ``recovery-catalogue`` Cosmos DB container."""

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._client = cosmos_client
        self._db_name = database_name
        self._container_name = "recovery-catalogue"
        self._in_memory: dict[str, dict[str, Any]] = {}

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    # ------------------------------------------------------------------
    # Outcomes
    # ------------------------------------------------------------------

    async def get_outcome(self, outcome_id: str, domain: str) -> dict | None:
        """Read a single outcome by id with partition key ``domain``."""
        container = self._get_container()
        if container:
            try:
                return container.read_item(outcome_id, partition_key=domain)
            except Exception:
                return None
        return self._in_memory.get(outcome_id)

    async def list_outcomes(
        self,
        domain: str | None = None,
        objective_type: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query outcomes with optional domain and objective-type filters."""
        container = self._get_container()
        if container:
            clauses = ["c.kind = 'outcome'"]
            params: list[dict[str, object]] = []
            if domain is not None:
                clauses.append("c.domain = @domain")
                params.append({"name": "@domain", "value": domain})
            if objective_type is not None:
                clauses.append("c.objective_type = @objective_type")
                params.append({"name": "@objective_type", "value": objective_type})
            query = (
                f"SELECT TOP @limit * FROM c WHERE "
                + " AND ".join(clauses)
                + " ORDER BY c.domain, c.outcome_id"
            )
            params.append({"name": "@limit", "value": limit})
            return list(
                container.query_items(
                    query,
                    parameters=params,
                    enable_cross_partition_query=(domain is None),
                )
            )
        # In-memory fallback
        results = [d for d in self._in_memory.values() if d.get("kind") == "outcome"]
        if domain is not None:
            results = [d for d in results if d.get("domain") == domain]
        if objective_type is not None:
            results = [d for d in results if d.get("objective_type") == objective_type]
        return results[:limit]

    # ------------------------------------------------------------------
    # Activities & Indicators for a given outcome
    # ------------------------------------------------------------------

    async def get_activities_for_outcome(self, outcome_id: str, domain: str) -> list[dict]:
        """Return all activity documents linked to a specific outcome."""
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c "
                "WHERE c.kind = 'activity' AND c.outcome_id = @outcome_id"
            )
            params: list[dict[str, object]] = [
                {"name": "@outcome_id", "value": outcome_id},
            ]
            return list(
                container.query_items(query, parameters=params, partition_key=domain)
            )
        return [
            d for d in self._in_memory.values()
            if d.get("kind") == "activity" and d.get("outcome_id") == outcome_id
        ]

    async def get_indicators_for_outcome(self, outcome_id: str, domain: str) -> list[dict]:
        """Return all indicator documents linked to a specific outcome."""
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c "
                "WHERE c.kind = 'indicator' AND c.outcome_id = @outcome_id"
            )
            params: list[dict[str, object]] = [
                {"name": "@outcome_id", "value": outcome_id},
            ]
            return list(
                container.query_items(query, parameters=params, partition_key=domain)
            )
        return [
            d for d in self._in_memory.values()
            if d.get("kind") == "indicator" and d.get("outcome_id") == outcome_id
        ]

    # ------------------------------------------------------------------
    # Domain summary
    # ------------------------------------------------------------------

    async def get_domain_summary(self, domain: str) -> dict:
        """Return counts of outcomes, activities, and indicators for a domain."""
        container = self._get_container()
        if container:
            query = (
                "SELECT c.kind, COUNT(1) AS cnt FROM c "
                "WHERE c.domain = @domain "
                "GROUP BY c.kind"
            )
            params: list[dict[str, object]] = [
                {"name": "@domain", "value": domain},
            ]
            rows = list(
                container.query_items(query, parameters=params, partition_key=domain)
            )
            summary = {"domain": domain, "outcomes": 0, "activities": 0, "indicators": 0}
            for row in rows:
                kind = row.get("kind", "")
                if kind in summary:
                    summary[kind] = row.get("cnt", 0)
            return summary
        # In-memory fallback
        domain_items = [d for d in self._in_memory.values() if d.get("domain") == domain]
        return {
            "domain": domain,
            "outcomes": sum(1 for d in domain_items if d.get("kind") == "outcome"),
            "activities": sum(1 for d in domain_items if d.get("kind") == "activity"),
            "indicators": sum(1 for d in domain_items if d.get("kind") == "indicator"),
        }

    # ------------------------------------------------------------------
    # Seed / upsert
    # ------------------------------------------------------------------

    async def upsert_catalogue_item(self, item_doc: dict) -> dict:
        """Upsert a single catalogue item — used by the seed loader."""
        container = self._get_container()
        if container:
            item_doc.setdefault("id", item_doc.get("outcome_id") or item_doc.get("activity_id") or item_doc.get("indicator_id", ""))
            container.upsert_item(item_doc)
        else:
            key = item_doc.get("id", item_doc.get("outcome_id") or item_doc.get("activity_id") or item_doc.get("indicator_id", ""))
            self._in_memory[key] = item_doc
        return item_doc
