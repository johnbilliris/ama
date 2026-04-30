"""Tests for named location resolution (T028-T030)."""

from __future__ import annotations

import pytest
from risk_assessment.named_locations import (
    LocationResolutionError,
    NamedLocation,
    NamedLocationRepository,
)


class TestNamedLocationRepository:
    """Tests for in-memory named location lookups."""

    @pytest.fixture
    def repo(self):
        repo = NamedLocationRepository()
        repo.upsert(
            NamedLocation(
                location_id="sensor-001",
                display_name="Katoomba Fire Station",
                latitude=-33.7139,
                longitude=150.3112,
            )
        )
        repo.upsert(
            NamedLocation(
                location_id="sensor-002",
                display_name="Penrith Council",
                latitude=-33.7507,
                longitude=150.6875,
            )
        )
        return repo

    def test_resolve_known_location(self, repo):
        lat, lon = repo.resolve("sensor-001")
        assert lat == pytest.approx(-33.7139)
        assert lon == pytest.approx(150.3112)

    def test_resolve_unknown_raises(self, repo):
        with pytest.raises(LocationResolutionError):
            repo.resolve("nonexistent")

    def test_list_all(self, repo):
        locations = repo.list_all()
        assert len(locations) == 2

    def test_upsert_overwrites(self, repo):
        repo.upsert(
            NamedLocation(
                location_id="sensor-001",
                display_name="Updated Name",
                latitude=-33.72,
                longitude=150.32,
            )
        )
        lat, lon = repo.resolve("sensor-001")
        assert lat == pytest.approx(-33.72)
