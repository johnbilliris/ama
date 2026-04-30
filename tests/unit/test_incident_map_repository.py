"""Unit tests for IncidentMapRepository.

Tests dynamic filter composition, pagination, rehearsal exclusion,
location-required filter, keyword search, year range, and empty results.
"""

import pytest
from app.repositories.incident_map_repository import IncidentMapRepository

# ── Test fixtures ──


_UNSET = object()


def _make_incident(
    incident_id: str = "inc-001",
    title: str = "Test Incident",
    incident_type: str = "bushfire",
    status: str = "active",
    severity: str = "warning",
    pprr_phase: str | None = "response",
    started_at: str = "2024-01-15T08:30:00Z",
    location: dict | None | object = _UNSET,
    incident_level: int = 2,
) -> dict:
    return {
        "incident_id": incident_id,
        "kind": "disaster",
        "title": title,
        "incident_type": incident_type,
        "status": status,
        "severity": severity,
        "affected_jurisdiction_ids": ["nsw"],
        "participating_organisation_ids": [],
        "owning_framework_ids": [],
        "started_at": started_at,
        "pprr_phase": pprr_phase,
        "incident_level": incident_level,
        "location": {"type": "Point", "coordinates": [151.2, -33.8]} if location is _UNSET else location,
    }


SAMPLE_INCIDENTS = [
    _make_incident(
        incident_id="inc-001",
        title="Sydney Bushfire",
        incident_type="bushfire",
        severity="warning",
        status="active",
        pprr_phase="response",
        started_at="2024-01-15T08:30:00Z",
    ),
    _make_incident(
        incident_id="inc-002",
        title="Brisbane Flood",
        incident_type="flood",
        severity="advisory",
        status="monitoring",
        pprr_phase="preparedness",
        started_at="2023-06-20T14:00:00Z",
        location={"type": "Point", "coordinates": [153.0, -27.5]},
    ),
    _make_incident(
        incident_id="inc-003",
        title="Melbourne Storm",
        incident_type="storm",
        severity="watch",
        status="stabilising",
        pprr_phase="recovery",
        started_at="2024-03-10T10:00:00Z",
        location={"type": "Point", "coordinates": [144.9, -37.8]},
    ),
    # Rehearsal — should be excluded
    _make_incident(
        incident_id="inc-004",
        title="Rehearsal Exercise",
        status="rehearsal",
        started_at="2024-02-01T09:00:00Z",
    ),
    # No location — should be excluded from mapped, counted in unmapped
    _make_incident(
        incident_id="inc-005",
        title="Darwin Cyclone",
        incident_type="cyclone",
        severity="emergency",
        status="active",
        started_at="2024-04-05T06:00:00Z",
        location=None,
    ),
]


@pytest.fixture
def repo() -> IncidentMapRepository:
    r = IncidentMapRepository()
    r.seed(SAMPLE_INCIDENTS)
    return r


# ── Tests ──


class TestQueryIncidents:
    @pytest.mark.asyncio
    async def test_returns_only_located_non_rehearsal(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents()
        assert total == 3  # inc-001, inc-002, inc-003 (rehearsal and no-location excluded)
        ids = {i["incident_id"] for i in items}
        assert "inc-004" not in ids  # rehearsal
        assert "inc-005" not in ids  # no location

    @pytest.mark.asyncio
    async def test_filter_by_incident_type(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(incident_types=["bushfire"])
        assert total == 1
        assert items[0]["incident_id"] == "inc-001"

    @pytest.mark.asyncio
    async def test_filter_by_multiple_types(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(incident_types=["bushfire", "flood"])
        assert total == 2

    @pytest.mark.asyncio
    async def test_filter_by_severity(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(severities=["advisory"])
        assert total == 1
        assert items[0]["incident_id"] == "inc-002"

    @pytest.mark.asyncio
    async def test_filter_by_status(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(statuses=["active"])
        assert total == 1
        assert items[0]["incident_id"] == "inc-001"

    @pytest.mark.asyncio
    async def test_filter_by_pprr_phase(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(pprr_phases=["recovery"])
        assert total == 1
        assert items[0]["incident_id"] == "inc-003"

    @pytest.mark.asyncio
    async def test_filter_by_keyword(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(keyword="sydney")
        assert total == 1
        assert items[0]["incident_id"] == "inc-001"

    @pytest.mark.asyncio
    async def test_keyword_case_insensitive(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(keyword="BRISBANE")
        assert total == 1
        assert items[0]["incident_id"] == "inc-002"

    @pytest.mark.asyncio
    async def test_filter_by_year_range(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(year_start=2024)
        assert total == 2  # inc-001 (2024) and inc-003 (2024), not inc-002 (2023)

    @pytest.mark.asyncio
    async def test_filter_by_year_end(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(year_end=2023)
        assert total == 1
        assert items[0]["incident_id"] == "inc-002"

    @pytest.mark.asyncio
    async def test_pagination_offset_limit(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(page=1, page_size=1)
        assert len(items) == 1
        assert total == 3

    @pytest.mark.asyncio
    async def test_pagination_page_2(self, repo: IncidentMapRepository):
        items_p1, _ = await repo.query_incidents(page=1, page_size=2)
        items_p2, _ = await repo.query_incidents(page=2, page_size=2)
        assert len(items_p1) == 2
        assert len(items_p2) == 1
        assert items_p1[0]["incident_id"] != items_p2[0]["incident_id"]

    @pytest.mark.asyncio
    async def test_empty_results(self, repo: IncidentMapRepository):
        items, total = await repo.query_incidents(incident_types=["tsunami"])
        assert total == 0
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_order_by_started_at_desc(self, repo: IncidentMapRepository):
        items, _ = await repo.query_incidents()
        dates = [i["started_at"] for i in items]
        assert dates == sorted(dates, reverse=True)

    @pytest.mark.asyncio
    async def test_combined_filters_and_logic(self, repo: IncidentMapRepository):
        """AND logic: type=bushfire AND status=active → only inc-001."""
        items, total = await repo.query_incidents(incident_types=["bushfire"], statuses=["active"])
        assert total == 1
        assert items[0]["incident_id"] == "inc-001"


class TestCountUnmapped:
    @pytest.mark.asyncio
    async def test_unmapped_count(self, repo: IncidentMapRepository):
        count = await repo.count_unmapped()
        assert count == 1  # inc-005 has no location (inc-004 is rehearsal)

    @pytest.mark.asyncio
    async def test_unmapped_count_with_filters(self, repo: IncidentMapRepository):
        count = await repo.count_unmapped(incident_types=["cyclone"])
        assert count == 1

    @pytest.mark.asyncio
    async def test_unmapped_count_no_match(self, repo: IncidentMapRepository):
        count = await repo.count_unmapped(incident_types=["bushfire"])
        assert count == 0


class TestBuildQuery:
    def test_base_query_no_filters(self):
        query, params = IncidentMapRepository._build_query()
        assert "c.status != 'rehearsal'" in query
        assert "IS_DEFINED(c.location)" in query
        assert "ORDER BY c.started_at DESC" in query

    def test_count_only_query(self):
        query, params = IncidentMapRepository._build_query(count_only=True)
        assert query.startswith("SELECT VALUE COUNT(1)")
        assert "ORDER BY" not in query

    def test_unmapped_query(self):
        query, params = IncidentMapRepository._build_query(unmapped_only=True)
        assert "NOT IS_DEFINED(c.location)" in query

    def test_filter_params(self):
        query, params = IncidentMapRepository._build_query(
            incident_types=["bushfire"],
            severities=["warning"],
            keyword="test",
            year_start=2020,
            year_end=2024,
        )
        param_names = {p["name"] for p in params}
        assert "@types" in param_names
        assert "@severities" in param_names
        assert "@keyword" in param_names
        assert "@year_start" in param_names
        assert "@year_end" in param_names
