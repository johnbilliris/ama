"""Cosmos DB repository for the /api/v1/incidents/map endpoint.

Builds dynamic queries that always exclude rehearsal-status incidents and
require a valid GeoJSON Point location.  Supports multi-value filters for
incident_type, severity, status, and pprr_phase (OR within category, AND
across categories).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IncidentMapRepository:
    """Tenant-scoped read-only queries against the `incidents` Cosmos DB container."""

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._client = cosmos_client
        self._db_name = database_name
        self._container_name = "incidents"
        self._in_memory: list[dict[str, Any]] = []

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    # ── Query builder ──────────────────────────────────────────────────────

    @staticmethod
    def _build_query(
        *,
        incident_types: list[str] | None = None,
        severities: list[str] | None = None,
        statuses: list[str] | None = None,
        pprr_phases: list[str] | None = None,
        keyword: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        count_only: bool = False,
        unmapped_only: bool = False,
        offset: int = 0,
        limit: int = 200,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Return (query_string, parameters) for the Cosmos DB SQL API."""

        if count_only:
            select = "SELECT VALUE COUNT(1) FROM c"
        else:
            select = "SELECT * FROM c"

        clauses: list[str] = []
        params: list[dict[str, Any]] = []

        # Always exclude rehearsal
        clauses.append("c.status != 'rehearsal'")

        # Location filter
        if unmapped_only:
            clauses.append("(NOT IS_DEFINED(c.location) OR c.location IS NULL)")
        else:
            clauses.append("IS_DEFINED(c.location)")
            clauses.append("c.location.type = 'Point'")

        # Dynamic multi-value filters (ARRAY_CONTAINS for OR within category)
        if incident_types:
            clauses.append("ARRAY_CONTAINS(@types, c.incident_type)")
            params.append({"name": "@types", "value": incident_types})

        if severities:
            clauses.append("ARRAY_CONTAINS(@severities, c.severity)")
            params.append({"name": "@severities", "value": severities})

        if statuses:
            clauses.append("ARRAY_CONTAINS(@statuses, c.status)")
            params.append({"name": "@statuses", "value": statuses})

        if pprr_phases:
            clauses.append("ARRAY_CONTAINS(@phases, c.pprr_phase)")
            params.append({"name": "@phases", "value": pprr_phases})

        if keyword:
            clauses.append("CONTAINS(LOWER(c.title), LOWER(@keyword))")
            params.append({"name": "@keyword", "value": keyword})

        if year_start is not None:
            clauses.append("DateTimePart('yyyy', c.started_at) >= @year_start")
            params.append({"name": "@year_start", "value": year_start})

        if year_end is not None:
            clauses.append("DateTimePart('yyyy', c.started_at) <= @year_end")
            params.append({"name": "@year_end", "value": year_end})

        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query = f"{select}{where}"

        if not count_only:
            query += " ORDER BY c.started_at DESC"
            query += " OFFSET @offset LIMIT @limit"
            params.append({"name": "@offset", "value": offset})
            params.append({"name": "@limit", "value": limit})

        return query, params

    # ── Public API ─────────────────────────────────────────────────────────

    async def query_incidents(
        self,
        *,
        incident_types: list[str] | None = None,
        severities: list[str] | None = None,
        statuses: list[str] | None = None,
        pprr_phases: list[str] | None = None,
        keyword: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        page: int = 1,
        page_size: int = 200,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return (items, total_count) for the mapped-incidents query."""

        offset = (page - 1) * page_size

        container = self._get_container()
        if container is None:
            # In-memory fallback for development / tests
            return self._query_in_memory(
                incident_types=incident_types,
                severities=severities,
                statuses=statuses,
                pprr_phases=pprr_phases,
                keyword=keyword,
                year_start=year_start,
                year_end=year_end,
                offset=offset,
                limit=page_size,
            )

        # Main query
        query, params = self._build_query(
            incident_types=incident_types,
            severities=severities,
            statuses=statuses,
            pprr_phases=pprr_phases,
            keyword=keyword,
            year_start=year_start,
            year_end=year_end,
            offset=offset,
            limit=page_size,
        )
        items = list(
            container.query_items(
                query, parameters=params, enable_cross_partition_query=True
            )
        )

        # Count query
        count_query, count_params = self._build_query(
            incident_types=incident_types,
            severities=severities,
            statuses=statuses,
            pprr_phases=pprr_phases,
            keyword=keyword,
            year_start=year_start,
            year_end=year_end,
            count_only=True,
        )
        total = list(
            container.query_items(
                count_query,
                parameters=count_params,
                enable_cross_partition_query=True,
            )
        )[0]

        return items, total

    async def count_unmapped(
        self,
        *,
        incident_types: list[str] | None = None,
        severities: list[str] | None = None,
        statuses: list[str] | None = None,
        pprr_phases: list[str] | None = None,
        keyword: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
    ) -> int:
        """Count incidents matching the filters but missing valid location."""

        container = self._get_container()
        if container is None:
            return self._count_unmapped_in_memory(
                incident_types=incident_types,
                severities=severities,
                statuses=statuses,
                pprr_phases=pprr_phases,
                keyword=keyword,
                year_start=year_start,
                year_end=year_end,
            )

        query, params = self._build_query(
            incident_types=incident_types,
            severities=severities,
            statuses=statuses,
            pprr_phases=pprr_phases,
            keyword=keyword,
            year_start=year_start,
            year_end=year_end,
            count_only=True,
            unmapped_only=True,
        )
        result = list(
            container.query_items(
                query, parameters=params, enable_cross_partition_query=True
            )
        )
        return result[0] if result else 0

    # ── In-memory fallback ─────────────────────────────────────────────────

    def seed(self, docs: list[dict[str, Any]]) -> None:
        """Seed in-memory store for development and tests."""
        self._in_memory = list(docs)

    def _matches_filters(
        self,
        doc: dict[str, Any],
        *,
        incident_types: list[str] | None,
        severities: list[str] | None,
        statuses: list[str] | None,
        pprr_phases: list[str] | None,
        keyword: str | None,
        year_start: int | None,
        year_end: int | None,
    ) -> bool:
        if doc.get("status") == "rehearsal":
            return False
        if incident_types and doc.get("incident_type") not in incident_types:
            return False
        if severities and doc.get("severity") not in severities:
            return False
        if statuses and doc.get("status") not in statuses:
            return False
        if pprr_phases and doc.get("pprr_phase") not in pprr_phases:
            return False
        if keyword and keyword.lower() not in (doc.get("title") or "").lower():
            return False
        started = doc.get("started_at", "")
        if isinstance(started, str) and len(started) >= 4:
            try:
                year = int(started[:4])
            except ValueError:
                year = 0
        else:
            year = 0
        if year_start is not None and year < year_start:
            return False
        if year_end is not None and year > year_end:
            return False
        return True

    def _query_in_memory(
        self, *, offset: int, limit: int, **filters: Any
    ) -> tuple[list[dict[str, Any]], int]:
        has_location = [
            d
            for d in self._in_memory
            if d.get("location") and d["location"].get("type") == "Point"
            and self._matches_filters(d, **filters)
        ]
        has_location.sort(key=lambda d: d.get("started_at", ""), reverse=True)
        return has_location[offset : offset + limit], len(has_location)

    def _count_unmapped_in_memory(self, **filters: Any) -> int:
        return sum(
            1
            for d in self._in_memory
            if (not d.get("location") or d["location"].get("type") != "Point")
            and self._matches_filters(d, **filters)
        )
