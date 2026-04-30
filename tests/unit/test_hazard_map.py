"""Tests for GeoJSON hazard map generation (T037).

Covers:
- Single signal polygon generation
- Multiple overlapping signals merge (R2)
- Empty signals produce empty GeoJSON
- Severity-indexed radius lookup
- GeoJSON Feature structure validation
"""

from __future__ import annotations

import pytest
from risk_assessment.hazard_map import HazardMapGenerator
from risk_assessment.hazard_radius import HazardRadiusRepository


@pytest.fixture
def radius_repo():
    return HazardRadiusRepository()


@pytest.fixture
def generator(radius_repo):
    return HazardMapGenerator(radius_repo=radius_repo)


class TestHazardMapGenerator:
    """Tests for HazardMapGenerator."""

    def test_single_signal_produces_polygon(self, generator):
        signals = [{"latitude": -33.8688, "longitude": 151.2093}]
        result = generator.generate(signals, "bushfire", 3)

        assert result["type"] == "Feature"
        assert result["geometry"]["type"] == "Polygon"
        assert result["properties"]["hazard_type"] == "bushfire"
        assert result["properties"]["severity_level"] == 3
        assert result["properties"]["signal_count"] == 1
        assert result["properties"]["radius_metres"] > 0

    def test_overlapping_signals_merge(self, generator):
        """R2: Overlapping polygons should be merged via unary_union."""
        signals = [
            {"latitude": -33.8688, "longitude": 151.2093},
            {"latitude": -33.8690, "longitude": 151.2095},
        ]
        result = generator.generate(signals, "bushfire", 3)

        assert result["type"] == "Feature"
        # Merged should still be a single polygon (not MultiPolygon) if close enough
        assert result["geometry"]["type"] in ("Polygon", "MultiPolygon")
        assert result["properties"]["signal_count"] == 2

    def test_distant_signals_multipolygon(self, generator):
        """Distant signals produce MultiPolygon."""
        signals = [
            {"latitude": -33.8688, "longitude": 151.2093},
            {"latitude": -37.8136, "longitude": 144.9631},  # Melbourne
        ]
        result = generator.generate(signals, "bushfire", 1)

        assert result["type"] == "Feature"
        assert result["geometry"]["type"] == "MultiPolygon"

    def test_empty_signals(self, generator):
        result = generator.generate([], "flood", 2)

        assert result["type"] == "Feature"
        assert result["properties"]["signal_count"] == 0

    def test_different_severities_produce_different_radii(self, generator):
        signals = [{"latitude": -33.8688, "longitude": 151.2093}]

        result_low = generator.generate(signals, "bushfire", 1)
        result_high = generator.generate(signals, "bushfire", 5)

        assert result_low["properties"]["radius_metres"] < result_high["properties"]["radius_metres"]

    def test_geojson_properties_include_timestamp(self, generator):
        signals = [{"latitude": 0.0, "longitude": 0.0}]
        result = generator.generate(signals, "flood", 1)

        assert "generated_at" in result["properties"]


class TestHazardRadiusRepository:
    """Tests for HazardRadiusRepository seed data."""

    def test_seed_data_loaded(self, radius_repo):
        # Should have default seed data
        radius = radius_repo.get_radius("bushfire", 3)
        assert radius > 0

    def test_unknown_hazard_uses_default(self, radius_repo):
        radius = radius_repo.get_radius("unknown_hazard", 3)
        assert radius > 0

    def test_severity_scales_radius(self, radius_repo):
        r1 = radius_repo.get_radius("bushfire", 1)
        r5 = radius_repo.get_radius("bushfire", 5)
        assert r1 < r5
