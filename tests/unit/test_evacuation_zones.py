"""Tests for evacuation.zones — zone computation, classification, capacity (T015)."""

from evacuation.zones import (
    ZONE_CAPACITY_FACTORS,
    ZoneComputer,
)
from shapely.geometry import LineString, Polygon


def _simple_hazard_geojson():
    """Create a simple hazard polygon for testing (Cairns area)."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [145.75, -16.95],
                [145.80, -16.95],
                [145.80, -16.90],
                [145.75, -16.90],
                [145.75, -16.95],
            ]
        ],
    }


# ---------------------------------------------------------------------------
# Zone boundary computation from hazard GeoJSON
# ---------------------------------------------------------------------------


class TestZoneBoundaryComputation:
    def test_compute_zones_returns_three(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        assert len(zones) == 3

    def test_zone_names(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        zone_numbers = [z.zone_number for z in zones]
        assert zone_numbers == [1, 2, 3]

    def test_zone_priorities(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        priorities = [z.evacuation_priority for z in zones]
        assert priorities == ["mandatory", "recommended", "advisory"]

    def test_zone_status_pending(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        for zone in zones:
            assert zone.status == "pending"

    def test_zone_boundary_is_geojson(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        for zone in zones:
            assert "type" in zone.boundary
            assert "coordinates" in zone.boundary

    def test_zone_1_is_hazard_area(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        z1 = zones[0]
        assert z1.zone_number == 1


# ---------------------------------------------------------------------------
# Population estimation
# ---------------------------------------------------------------------------


class TestPopulationEstimation:
    def test_population_positive(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        for zone in zones:
            assert zone.population_estimate > 0

    def test_vulnerable_population_is_15_pct(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        for zone in zones:
            expected_vuln = int(zone.population_estimate * 0.15)
            assert zone.vulnerable_population == expected_vuln

    def test_outer_zones_have_larger_population(self):
        """Zone 3 should have larger population than Zone 1 (larger area)."""
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        assert zones[2].population_estimate >= zones[0].population_estimate


# ---------------------------------------------------------------------------
# Road segment zone classification
# ---------------------------------------------------------------------------


class TestEdgeZoneClassification:
    def test_edge_fully_inside_zone_1(self):
        zc = ZoneComputer()
        # Line fully inside the hazard polygon
        line = LineString([(145.76, -16.94), (145.78, -16.92)])

        zone_1_poly = Polygon([
            (145.75, -16.95), (145.80, -16.95),
            (145.80, -16.90), (145.75, -16.90),
            (145.75, -16.95),
        ])
        zone_2_poly = zone_1_poly.buffer(0.05)
        zone_3_poly = zone_2_poly.buffer(0.05)

        zone_polys = [(1, zone_1_poly), (2, zone_2_poly), (3, zone_3_poly)]
        result = zc.classify_edge_zone(line, zone_polys)
        assert result == 1

    def test_edge_outside_all_zones(self):
        zc = ZoneComputer()
        # Line far from the hazard
        line = LineString([(150.0, -20.0), (150.1, -20.1)])

        zone_1_poly = Polygon([
            (145.75, -16.95), (145.80, -16.95),
            (145.80, -16.90), (145.75, -16.90),
            (145.75, -16.95),
        ])
        zone_polys = [(1, zone_1_poly)]
        result = zc.classify_edge_zone(line, zone_polys)
        assert result is None

    def test_partial_overlap_returns_highest_severity(self):
        """If a line partially overlaps Zone 1, it should be classified as Zone 1."""
        zc = ZoneComputer()
        # Line that crosses the edge of Zone 1
        line = LineString([(145.79, -16.93), (145.85, -16.93)])

        zone_1_poly = Polygon([
            (145.75, -16.95), (145.80, -16.95),
            (145.80, -16.90), (145.75, -16.90),
            (145.75, -16.95),
        ])
        zone_2_poly = zone_1_poly.buffer(0.05)
        zone_3_poly = zone_2_poly.buffer(0.05)

        zone_polys = [(1, zone_1_poly), (2, zone_2_poly), (3, zone_3_poly)]
        result = zc.classify_edge_zone(line, zone_polys)
        # Partial overlap with Zone 1 → Zone 1 (highest severity)
        assert result == 1


# ---------------------------------------------------------------------------
# Capacity factors
# ---------------------------------------------------------------------------


class TestCapacityFactors:
    def test_zone_1_factor(self):
        zc = ZoneComputer()
        assert zc.get_capacity_factor(1) == 0.0

    def test_zone_2_factor(self):
        zc = ZoneComputer()
        assert zc.get_capacity_factor(2) == 0.50

    def test_zone_3_factor(self):
        zc = ZoneComputer()
        assert zc.get_capacity_factor(3) == 0.75

    def test_outside_zones_full_capacity(self):
        zc = ZoneComputer()
        assert zc.get_capacity_factor(99) == 1.0

    def test_capacity_constants(self):
        assert ZONE_CAPACITY_FACTORS[1] == 0.0
        assert ZONE_CAPACITY_FACTORS[2] == 0.50
        assert ZONE_CAPACITY_FACTORS[3] == 0.75


# ---------------------------------------------------------------------------
# Multi-hazard merging via unary_union
# ---------------------------------------------------------------------------


class TestMultiHazardMerging:
    def test_two_overlapping_hazards(self):
        zc = ZoneComputer()
        hazard_1 = {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.75, -16.95], [145.80, -16.95],
                    [145.80, -16.90], [145.75, -16.90],
                    [145.75, -16.95],
                ]
            ],
        }
        hazard_2 = {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.78, -16.93], [145.83, -16.93],
                    [145.83, -16.88], [145.78, -16.88],
                    [145.78, -16.93],
                ]
            ],
        }
        zones = zc.compute_zones_multi_hazard([hazard_1, hazard_2])
        assert len(zones) == 3

    def test_empty_hazard_list(self):
        zc = ZoneComputer()
        zones = zc.compute_zones_multi_hazard([])
        assert zones == []

    def test_single_hazard_same_as_compute_zones(self):
        zc = ZoneComputer()
        single = zc.compute_zones(_simple_hazard_geojson())
        multi = zc.compute_zones_multi_hazard([_simple_hazard_geojson()])
        assert len(single) == len(multi) == 3


# ---------------------------------------------------------------------------
# Zone polygons conversion
# ---------------------------------------------------------------------------


class TestGetZonePolygons:
    def test_converts_zones_to_polygons(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        polys = zc.get_zone_polygons(zones)
        assert len(polys) == 3
        for zone_num, poly in polys:
            assert isinstance(zone_num, int)
            assert poly.is_valid


# ---------------------------------------------------------------------------
# Zone capacity reduction on edges
# ---------------------------------------------------------------------------


class TestZoneCapacityReduction:
    def test_zone_1_edge_closed(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        zone_polys = zc.get_zone_polygons(zones)

        # Edge fully inside Zone 1
        edge = {
            "id": "e-1",
            "capacity_vehicles_per_hour": 500,
            "_geometry": LineString([(145.76, -16.94), (145.78, -16.92)]),
        }
        result = zc.apply_zone_capacity_reduction([edge], zone_polys)
        z1_edge = result[0]
        assert z1_edge["zone_membership"] == 1
        assert z1_edge["capacity_vehicles_per_hour"] == 0
        assert z1_edge["closure_status"] == "closed"

    def test_outside_edge_unchanged(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        zone_polys = zc.get_zone_polygons(zones)

        edge = {
            "id": "e-far",
            "capacity_vehicles_per_hour": 500,
            "_geometry": LineString([(150.0, -20.0), (150.1, -20.1)]),
        }
        result = zc.apply_zone_capacity_reduction([edge], zone_polys)
        assert result[0]["capacity_vehicles_per_hour"] == 500
        assert result[0]["zone_membership"] is None
