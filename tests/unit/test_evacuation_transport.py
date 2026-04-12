"""Tests for evacuation.transport — vehicle types, quantities, priorities (T031)."""



from evacuation.models import VulnerabilityCategory
from evacuation.transport import (
    _PRIORITY_ORDER,
    PRIORITY_MAP,
    VEHICLE_TYPE_MAP,
    TransportCoordinator,
)


def _make_facility(category, capacity=20, name="Test Facility", lat=-16.92, lng=145.77):
    return {
        "vulnerability_category": category,
        "capacity": capacity,
        "name": name,
        "coordinates": {"lat": lat, "lng": lng},
    }


def _make_zone(zone_number=1, lat=-16.92, lng=145.77, size=0.1):
    return {
        "zone_number": zone_number,
        "boundary": {
            "type": "Polygon",
            "coordinates": [
                [
                    [lng - size, lat - size],
                    [lng + size, lat - size],
                    [lng + size, lat + size],
                    [lng - size, lat + size],
                    [lng - size, lat - size],
                ]
            ],
        },
        "population_estimate": 5000,
        "vulnerable_population": 750,
    }


def _make_assembly_area(aa_id="aa-1", lat=-16.85, lng=145.70):
    return {
        "assembly_area_id": aa_id,
        "name": f"Assembly {aa_id}",
        "coordinates": {"lat": lat, "lng": lng},
    }


# ---------------------------------------------------------------------------
# Vehicle type mapping for all 4 vulnerability categories
# ---------------------------------------------------------------------------


class TestVehicleTypeMapping:
    def test_mobility_impaired(self):
        assert VEHICLE_TYPE_MAP["mobility_impaired"] == "wheelchair_accessible_vehicle"

    def test_medical_dependent(self):
        assert VEHICLE_TYPE_MAP["medical_dependent"] == "ambulance"

    def test_elderly_aged_care(self):
        assert VEHICLE_TYPE_MAP["elderly_aged_care"] == "accessible_bus"

    def test_children_schools_childcare(self):
        assert VEHICLE_TYPE_MAP["children_schools_childcare"] == "bus"

    def test_all_categories_have_vehicle_type(self):
        for cat in VulnerabilityCategory:
            assert cat.value in VEHICLE_TYPE_MAP

    def test_compute_transport_mobility_impaired(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("mobility_impaired")]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].vehicle_type == "wheelchair_accessible_vehicle"

    def test_compute_transport_medical_dependent(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("medical_dependent")]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].vehicle_type == "ambulance"

    def test_compute_transport_elderly(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("elderly_aged_care")]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].vehicle_type == "accessible_bus"

    def test_compute_transport_children(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("children_schools_childcare")]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].vehicle_type == "bus"


# ---------------------------------------------------------------------------
# Vehicle count estimation (ceiling division)
# ---------------------------------------------------------------------------


class TestVehicleCountEstimation:
    def test_ceiling_division_exact(self):
        """50 people ÷ 50 per bus = 1 bus."""
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("children_schools_childcare", capacity=50)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].quantity_required == 1

    def test_ceiling_division_remainder(self):
        """51 people ÷ 50 per bus = 2 buses (ceiling)."""
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("children_schools_childcare", capacity=51)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].quantity_required == 2

    def test_small_capacity_vehicle(self):
        """8 people ÷ 4 per wheelchair vehicle = 2 vehicles."""
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("mobility_impaired", capacity=8)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].quantity_required == 2

    def test_ambulance_ceiling(self):
        """5 people ÷ 2 per ambulance = 3 ambulances (ceiling)."""
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("medical_dependent", capacity=5)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].quantity_required == 3

    def test_single_person(self):
        """1 person should require at least 1 vehicle."""
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("medical_dependent", capacity=1)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        assert len(reqs) > 0
        assert reqs[0].quantity_required >= 1


# ---------------------------------------------------------------------------
# Missing facility data returns empty list
# ---------------------------------------------------------------------------


class TestMissingFacilityData:
    def test_empty_facilities(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        reqs = tc.compute_transport_requirements(zones, [], [_make_assembly_area()])
        assert reqs == []

    def test_zero_capacity_facility(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("medical_dependent", capacity=0)]
        reqs = tc.compute_transport_requirements(zones, facilities, [_make_assembly_area()])
        assert reqs == []

    def test_unknown_category_skipped(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [{
            "vulnerability_category": "unknown_category",
            "capacity": 10,
            "name": "Unknown",
            "coordinates": {"lat": -16.92, "lng": 145.77},
        }]
        reqs = tc.compute_transport_requirements(zones, facilities, [_make_assembly_area()])
        assert reqs == []


# ---------------------------------------------------------------------------
# Priority ordering: critical > immediate > high
# ---------------------------------------------------------------------------


class TestPriorityOrdering:
    def test_priority_map_values(self):
        assert PRIORITY_MAP["medical_dependent"] == "critical"
        assert PRIORITY_MAP["mobility_impaired"] == "immediate"
        assert PRIORITY_MAP["elderly_aged_care"] == "immediate"
        assert PRIORITY_MAP["children_schools_childcare"] == "high"

    def test_priority_order(self):
        assert _PRIORITY_ORDER["critical"] < _PRIORITY_ORDER["immediate"]
        assert _PRIORITY_ORDER["immediate"] < _PRIORITY_ORDER["high"]

    def test_medical_sorted_first(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [
            _make_facility("children_schools_childcare", capacity=10),
            _make_facility("medical_dependent", capacity=5),
            _make_facility("mobility_impaired", capacity=8),
        ]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        if len(reqs) >= 2:
            # Medical (critical) should come before children (high)
            categories = [r.category.value for r in reqs]
            med_idx = categories.index("medical_dependent")
            child_idx = categories.index("children_schools_childcare")
            assert med_idx < child_idx


# ---------------------------------------------------------------------------
# Notes field populated
# ---------------------------------------------------------------------------


class TestNotesField:
    def test_notes_contain_priority(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("medical_dependent", capacity=5)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        if reqs:
            assert "Priority: critical" in reqs[0].notes

    def test_notes_contain_zone_number(self):
        tc = TransportCoordinator()
        zones = [_make_zone()]
        facilities = [_make_facility("medical_dependent", capacity=5)]
        assembly_areas = [_make_assembly_area()]

        reqs = tc.compute_transport_requirements(zones, facilities, assembly_areas)
        if reqs:
            assert "Zone:" in reqs[0].notes
