"""Tests for evacuation.transport — vehicle types, quantities, priorities (T031)."""

from evacuation.models import (
    TransportCoordinationStatus,
    TransportExclusionReason,
    VulnerabilityCategory,
)
from evacuation.transport import (
    _PRIORITY_ORDER,
    PRIORITY_MAP,
    VEHICLE_TYPE_MAP,
    TransportCoordinator,
)


def _make_facility(category, capacity=20, name="Test Facility", lat=-16.92, lng=145.77):
    return {
        "facility_id": f"facility-{name.lower().replace(' ', '-')}",
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
    def test_40_wheelchair_users_create_10_accessible_vehicle_request(self):
        result = TransportCoordinator().coordinate_transport(
            [_make_zone()],
            [_make_facility("mobility_impaired", capacity=40, name="Access Centre")],
            [_make_assembly_area()],
            "live:inc-001",
        )

        request = result.requirements[0]
        assert request.estimated_individuals == 40
        assert request.quantity_required == 10
        assert request.vehicle_type == "wheelchair_accessible_vehicle"
        assert request.priority_level.value == "immediate"
        assert request.origin_zone == 1
        assert request.phase_number == 1
        assert request.pickup_location == {"lat": -16.92, "lng": 145.77}
        assert request.destination_assembly_area_id == "aa-1"
        assert request.dispatch_authorized is False

    def test_200_students_create_four_bus_request(self):
        result = TransportCoordinator().coordinate_transport(
            [_make_zone()],
            [
                _make_facility(
                    "children_schools_childcare",
                    capacity=200,
                    name="District School",
                )
            ],
            [_make_assembly_area()],
            "live:inc-001",
        )

        request = result.requirements[0]
        assert request.estimated_individuals == 200
        assert request.quantity_required == 4
        assert request.vehicle_type == "bus"
        assert request.priority_level.value == "high"
        assert "child_supervision" in request.special_considerations

    def test_requirement_id_and_resource_payload_are_stable_and_structured(self):
        coordinator = TransportCoordinator()
        arguments = (
            [_make_zone()],
            [_make_facility("medical_dependent", capacity=5, name="Clinic")],
            [_make_assembly_area()],
            "tenant-a:inc-001",
        )

        first = coordinator.coordinate_transport(*arguments).requirements[0]
        second = coordinator.coordinate_transport(*arguments).requirements[0]
        payload = first.to_resource_allocation_payload()

        assert first.requirement_id == second.requirement_id
        assert payload == {
            "requirementId": first.requirement_id,
            "vehicleType": "ambulance",
            "quantity": 3,
            "pickupLocation": {"lat": -16.92, "lon": 145.77},
            "priority": "critical",
            "estimatedIndividuals": 5,
            "facilityId": "facility-clinic",
            "facilityName": "Clinic",
            "destinationAssemblyAreaId": "aa-1",
            "destinationAssemblyAreaName": "Assembly aa-1",
            "destinationRouteId": "",
            "destinationResolved": True,
            "unresolvedDestinationReason": None,
            "originZone": 1,
            "phaseNumber": 1,
            "specialConsiderations": [
                "medical_equipment",
                "oxygen_supply",
                "continuous_monitoring",
            ],
            "countBasis": "facility_capacity",
            "dispatchAuthorized": False,
        }

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
    def test_unavailable_registry_is_distinct_from_authoritative_empty(self):
        coordinator = TransportCoordinator()

        unavailable = coordinator.coordinate_transport(
            [_make_zone()],
            None,
            [_make_assembly_area()],
        )
        empty = coordinator.coordinate_transport(
            [_make_zone()],
            [],
            [_make_assembly_area()],
        )

        assert unavailable.status == TransportCoordinationStatus.unavailable
        assert empty.status == TransportCoordinationStatus.complete
        assert unavailable.assumptions != empty.assumptions

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
        facilities = [
            {
                "vulnerability_category": "unknown_category",
                "capacity": 10,
                "name": "Unknown",
                "coordinates": {"lat": -16.92, "lng": 145.77},
            }
        ]
        reqs = tc.compute_transport_requirements(zones, facilities, [_make_assembly_area()])
        assert reqs == []

    def test_facility_outside_all_memberships_is_not_assigned(self):
        tc = TransportCoordinator()
        facilities = [
            _make_facility(
                "medical_dependent",
                capacity=5,
                lat=0,
                lng=0,
            )
        ]

        reqs = tc.compute_transport_requirements(
            [_make_zone()],
            facilities,
            [_make_assembly_area()],
        )

        assert reqs == []

    def test_outside_facility_is_retained_as_excluded_inventory(self):
        result = TransportCoordinator().coordinate_transport(
            [_make_zone()],
            [
                _make_facility(
                    "medical_dependent",
                    capacity=5,
                    name="Remote Clinic",
                    lat=0,
                    lng=0,
                )
            ],
            [_make_assembly_area()],
        )

        assert result.requirements == []
        assert result.exclusions[0].reason == (TransportExclusionReason.outside_affected_area)
        assert result.exclusions[0].estimated_individuals == 5

    def test_zone_three_facility_is_advisory_not_mandatory(self):
        result = TransportCoordinator().coordinate_transport(
            [_make_zone(zone_number=3)],
            [
                _make_facility(
                    "children_schools_childcare",
                    capacity=200,
                    name="Advisory School",
                )
            ],
            [_make_assembly_area()],
        )

        assert result.requirements == []
        assert result.exclusions[0].reason == TransportExclusionReason.advisory_only
        assert result.exclusions[0].zone_number == 3
        assert result.identified_population_by_zone == {3: 200}

    def test_invalid_location_is_not_mislabeled_outside_area(self):
        facility = _make_facility("elderly_aged_care", capacity=60)
        facility["coordinates"] = {"lat": "unknown", "lng": 145.77}

        result = TransportCoordinator().coordinate_transport(
            [_make_zone()],
            [facility],
            [_make_assembly_area()],
        )

        assert result.exclusions[0].reason == TransportExclusionReason.invalid_location

    def test_uncovered_vulnerable_population_is_explicit(self):
        result = TransportCoordinator().coordinate_transport(
            [_make_zone()],
            [_make_facility("medical_dependent", capacity=50)],
            [_make_assembly_area()],
        )

        assert result.uncovered_vulnerable_population_by_zone == {1: 700}
        assert result.status == TransportCoordinationStatus.partial
        assert "700 vulnerable people" in result.assumptions[0]

    def test_route_backed_farther_accessible_destination_is_selected(self):
        coordinator = TransportCoordinator()
        near = _make_assembly_area("near", lat=-16.92, lng=145.77)
        near["accessibility_features"] = []
        far = _make_assembly_area("far", lat=-16.80, lng=145.70)
        far["accessibility_features"] = ["wheelchair_accessible"]
        allocations = [
            {
                "zone_number": 1,
                "assembly_area_id": "near",
                "assigned_vulnerable_population": 40,
            },
            {
                "zone_number": 1,
                "assembly_area_id": "far",
                "assigned_vulnerable_population": 40,
            },
        ]
        routes = [
            {
                "origin_zone": 1,
                "destination_assembly_area": "near",
                "allocated_population": 40,
                "estimated_travel_time_loaded_min": 5,
                "total_distance_km": 2,
                "vehicle_suitability": {
                    "standard": True,
                    "heavy": True,
                    "accessible": True,
                },
            },
            {
                "origin_zone": 1,
                "destination_assembly_area": "far",
                "allocated_population": 40,
                "estimated_travel_time_loaded_min": 15,
                "total_distance_km": 8,
                "vehicle_suitability": {
                    "standard": True,
                    "heavy": True,
                    "accessible": True,
                },
            },
        ]

        result = coordinator.coordinate_transport(
            [_make_zone()],
            [_make_facility("mobility_impaired", capacity=40)],
            [near, far],
            "live:inc-001",
            allocations,
            routes,
        )

        assert result.requirements[0].destination_assembly_area_id == "far"
        assert result.requirements[0].destination_resolved is True

    def test_no_compatible_destination_keeps_unresolved_request(self):
        area = _make_assembly_area("near")
        area["accessibility_features"] = []
        result = TransportCoordinator().coordinate_transport(
            [_make_zone()],
            [_make_facility("mobility_impaired", capacity=40)],
            [area],
            "live:inc-001",
            [
                {
                    "zone_number": 1,
                    "assembly_area_id": "near",
                    "assigned_vulnerable_population": 40,
                }
            ],
            [
                {
                    "origin_zone": 1,
                    "destination_assembly_area": "near",
                    "allocated_population": 40,
                    "vehicle_suitability": {
                        "standard": True,
                        "heavy": True,
                        "accessible": True,
                    },
                }
            ],
        )

        assert len(result.requirements) == 1
        assert result.requirements[0].destination_resolved is False
        assert result.requirements[0].destination_assembly_area_id == ""
        assert result.requirements[0].unresolved_destination_reason
        assert result.exclusions == []
        assert result.status == TransportCoordinationStatus.partial
        assert any("unresolved destination" in assumption for assumption in result.assumptions)

    def test_shared_boundary_facility_uses_highest_priority_zone(self):
        tc = TransportCoordinator()
        facility = _make_facility(
            "medical_dependent",
            capacity=5,
            lat=0.5,
            lng=1,
        )
        zones = [
            {
                "zone_number": 1,
                "membership_boundary": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            },
            {
                "zone_number": 2,
                "membership_boundary": {
                    "type": "Polygon",
                    "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
                },
            },
        ]

        requirements = tc.compute_transport_requirements(
            zones,
            [facility],
            [_make_assembly_area()],
        )

        assert len(requirements) == 1
        assert "Zone: 1" in requirements[0].notes


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
