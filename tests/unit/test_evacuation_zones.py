"""Tests for evacuation.zones — zone computation, classification, capacity (T015)."""

import pytest
from evacuation.zones import (
    ZONE_CAPACITY_FACTORS,
    HazardZoneInput,
    ZoneComputer,
)
from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform


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


def _unit_hazard_geojson():
    return {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    }


def _population_area(name, min_x, min_y, max_x, max_y, population, vulnerable):
    return {
        "area_name": name,
        "boundary": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_x, min_y],
                    [max_x, min_y],
                    [max_x, max_y],
                    [min_x, max_y],
                    [min_x, min_y],
                ]
            ],
        },
        "population_estimate": population,
        "vulnerable_population_estimate": vulnerable,
    }


def _one_degree_radius(_hazard_type, _severity_level):
    return 111_320


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

    def test_fallback_vulnerable_population_is_15_pct(self):
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        for zone in zones:
            expected_vuln = int(zone.population_estimate * 0.15)
            assert zone.vulnerable_population == expected_vuln

    def test_outer_zones_have_larger_population(self):
        """The exclusive Zone 3 ring is larger than the inner hazard area."""
        zc = ZoneComputer()
        zones = zc.compute_zones(_simple_hazard_geojson())
        assert zones[2].population_estimate >= zones[0].population_estimate

    def test_authoritative_cohorts_are_assigned_once_with_exact_vulnerability(self):
        zc = ZoneComputer(radius_lookup=_one_degree_radius)
        population_data = [
            _population_area("inner", 0.2, 0.2, 0.8, 0.8, 100, 7),
            _population_area("middle", 1.1, 0.2, 1.3, 0.8, 200, 40),
            _population_area("outer", 2.1, 0.2, 2.3, 0.8, 300, 90),
        ]

        zones = zc.compute_zones(_unit_hazard_geojson(), population_data)

        assert [zone.population_estimate for zone in zones] == [100, 200, 300]
        assert [zone.vulnerable_population for zone in zones] == [7, 40, 90]
        assert sum(zone.population_estimate for zone in zones) == 600
        assert all(zone.membership_boundary for zone in zones)

    def test_split_cohort_uses_priority_stable_rounding_and_conserves_counts(self):
        zc = ZoneComputer(radius_lookup=_one_degree_radius)
        split = _population_area("split", 0.5, 0.2, 1.5, 0.8, 101, 11)

        zones = zc.compute_zones(_unit_hazard_geojson(), [split])

        assert [zone.population_estimate for zone in zones] == [51, 50, 0]
        assert [zone.vulnerable_population for zone in zones] == [6, 5, 0]

    def test_hole_population_is_excluded_from_zone_one(self):
        zc = ZoneComputer(radius_lookup=_one_degree_radius)
        hazard = {
            "type": "Polygon",
            "coordinates": [
                [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                [[0.4, 0.4], [0.6, 0.4], [0.6, 0.6], [0.4, 0.6], [0.4, 0.4]],
            ],
        }
        population = _population_area("hole", 0.45, 0.45, 0.55, 0.55, 25, 5)

        zones = zc.compute_zones(hazard, [population])

        assert [zone.population_estimate for zone in zones] == [0, 25, 0]
        assert [zone.vulnerable_population for zone in zones] == [0, 5, 0]


# ---------------------------------------------------------------------------
# Road segment zone classification
# ---------------------------------------------------------------------------


class TestEdgeZoneClassification:
    def test_edge_fully_inside_zone_1(self):
        zc = ZoneComputer()
        # Line fully inside the hazard polygon
        line = LineString([(145.76, -16.94), (145.78, -16.92)])

        zone_1_poly = Polygon(
            [
                (145.75, -16.95),
                (145.80, -16.95),
                (145.80, -16.90),
                (145.75, -16.90),
                (145.75, -16.95),
            ]
        )
        zone_2_poly = zone_1_poly.buffer(0.05)
        zone_3_poly = zone_2_poly.buffer(0.05)

        zone_polys = [(1, zone_1_poly), (2, zone_2_poly), (3, zone_3_poly)]
        result = zc.classify_edge_zone(line, zone_polys)
        assert result == 1

    def test_edge_outside_all_zones(self):
        zc = ZoneComputer()
        # Line far from the hazard
        line = LineString([(150.0, -20.0), (150.1, -20.1)])

        zone_1_poly = Polygon(
            [
                (145.75, -16.95),
                (145.80, -16.95),
                (145.80, -16.90),
                (145.75, -16.90),
                (145.75, -16.95),
            ]
        )
        zone_polys = [(1, zone_1_poly)]
        result = zc.classify_edge_zone(line, zone_polys)
        assert result is None

    def test_partial_overlap_returns_highest_severity(self):
        """If a line partially overlaps Zone 1, it should be classified as Zone 1."""
        zc = ZoneComputer()
        # Line that crosses the edge of Zone 1
        line = LineString([(145.79, -16.93), (145.85, -16.93)])

        zone_1_poly = Polygon(
            [
                (145.75, -16.95),
                (145.80, -16.95),
                (145.80, -16.90),
                (145.75, -16.90),
                (145.75, -16.95),
            ]
        )
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
                    [145.75, -16.95],
                    [145.80, -16.95],
                    [145.80, -16.90],
                    [145.75, -16.90],
                    [145.75, -16.95],
                ]
            ],
        }
        hazard_2 = {
            "type": "Polygon",
            "coordinates": [
                [
                    [145.78, -16.93],
                    [145.83, -16.93],
                    [145.83, -16.88],
                    [145.78, -16.88],
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

    def test_disjoint_hazards_preserve_multipolygon_union(self):
        zc = ZoneComputer(radius_lookup=lambda *_: 1000)
        hazards = [
            HazardZoneInput(_unit_hazard_geojson(), "bushfire", "high", "a-1"),
            HazardZoneInput(
                {
                    "type": "Polygon",
                    "coordinates": [[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]],
                },
                "flood",
                "moderate",
                "a-2",
            ),
        ]

        zones = zc.compute_zones_multi_hazard(hazards)

        assert shape(zones[0].boundary).geom_type == "MultiPolygon"
        merged = shape(zc.merge_affected_areas(hazards))
        assert merged.equals(shape(zones[0].boundary))

    def test_mixed_profiles_union_each_zone_level(self):
        calls = []

        def radius_lookup(hazard_type, severity_level):
            calls.append((hazard_type, severity_level))
            return 1000 if hazard_type == "flood" else 5000

        zc = ZoneComputer(radius_lookup=radius_lookup)
        hazards = [
            HazardZoneInput(_unit_hazard_geojson(), "flood", "moderate"),
            HazardZoneInput(_unit_hazard_geojson(), "cyclone", "critical"),
        ]

        zones = zc.compute_zones_multi_hazard(hazards)

        assert calls == [("flood", 2), ("cyclone", 4)]
        assert shape(zones[1].boundary).area > shape(zones[0].boundary).area

    def test_overlap_uses_lowest_zone_number(self):
        zc = ZoneComputer(radius_lookup=lambda *_: 20_000)
        hazards = [
            HazardZoneInput(_unit_hazard_geojson(), "flood", "moderate"),
            HazardZoneInput(
                {
                    "type": "Polygon",
                    "coordinates": [[[1.1, 0.2], [1.3, 0.2], [1.3, 0.8], [1.1, 0.8], [1.1, 0.2]]],
                },
                "cyclone",
                "critical",
            ),
        ]

        zones = zc.compute_zones_multi_hazard(hazards)
        overlap_line = LineString([(1.15, 0.4), (1.25, 0.6)])

        assert shape(zones[0].boundary).covers(overlap_line)
        assert not shape(zones[1].membership_boundary).intersects(overlap_line)
        assert (
            zc.classify_edge_zone(
                overlap_line,
                zc.get_zone_polygons(zones),
            )
            == 1
        )

    def test_invalid_or_empty_hazard_is_rejected(self):
        zc = ZoneComputer()
        invalid = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],
        }
        empty = {"type": "Polygon", "coordinates": []}

        for geometry in (invalid, empty):
            try:
                zc.compute_zones_multi_hazard([geometry])
            except ValueError as exc:
                assert "valid and non-empty" in str(exc)
            else:
                raise AssertionError("Invalid hazard geometry was accepted")

    def test_metric_buffer_is_equivalent_at_different_latitudes(self):
        zc = ZoneComputer(radius_lookup=lambda *_: 5000)

        def metric_radius(zone_boundary, longitude, latitude):
            local_crs = CRS.from_proj4(
                f"+proj=aeqd +lat_0={latitude} +lon_0={longitude} +datum=WGS84 +units=m +no_defs"
            )
            forward = Transformer.from_crs("EPSG:4326", local_crs, always_xy=True).transform
            projected = transform(forward, shape(zone_boundary))
            return projected.exterior.distance(transform(forward, Point(longitude, latitude)))

        equator = {"type": "Polygon", "coordinates": [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0.001], [0, 0]]]}
        high_latitude = {
            "type": "Polygon",
            "coordinates": [[[0, 60], [0.001, 60], [0.001, 60.001], [0, 60.001], [0, 60]]],
        }
        equator_zone = zc.compute_zones(equator)[1]
        high_latitude_zone = zc.compute_zones(high_latitude)[1]

        equator_radius = metric_radius(equator_zone.boundary, 0.0005, 0.0005)
        latitude_radius = metric_radius(high_latitude_zone.boundary, 0.0005, 60.0005)
        assert equator_radius == pytest.approx(latitude_radius, rel=0.01)


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
