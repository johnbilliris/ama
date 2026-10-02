"""Tests for evacuation.timeline — clearance time, phases, shelter-in-place (T034)."""

import math
from datetime import UTC, datetime

import pytest
from evacuation.config import EvacuationConfig
from evacuation.models import (
    PhaseTransitionTrigger,
    TransportPriority,
    TransportRequirement,
    VulnerabilityCategory,
    ZoneDispositionType,
)
from evacuation.timeline import TimelineEstimator


def _make_zone(zone_number, pop=5000, vuln=750):
    return {
        "zone_number": zone_number,
        "population_estimate": pop,
        "vulnerable_population": vuln,
    }


def _make_route(zone_id, distance_km=10.0, capacity=500):
    return {
        "zone_id": str(zone_id),
        "distance_km": distance_km,
        "capacity_vehicles_per_hour": capacity,
    }


def _transition_fixture_route(capacity=100):
    return {
        **_make_route(1, distance_km=1, capacity=capacity),
        "waypoints": ["shared-edge"],
        "allocated_population": 200,
        "evacuation_load_vehicles_per_hour": 50,
        "zone_shared_capacity_vehicles_per_hour": capacity,
    }


# ---------------------------------------------------------------------------
# Clearance time formula
# ---------------------------------------------------------------------------


class TestClearanceTimeFormula:
    def test_basic_clearance_time(self):
        """Formula: (population / road_capacity) × distance_km × 60."""
        te = TimelineEstimator()
        # 1000 people, 500 veh/hr capacity, 10 km → (1000/500) × 10 × 60 = 1200 min
        ct = te._compute_clearance_time(
            population=1000,
            road_capacity=500,
            distance_km=10.0,
        )
        assert ct == pytest.approx(1200.0)

    def test_zero_population(self):
        te = TimelineEstimator()
        ct = te._compute_clearance_time(population=0, road_capacity=500, distance_km=10.0)
        assert ct == 0.0

    def test_zero_capacity(self):
        te = TimelineEstimator()
        ct = te._compute_clearance_time(population=100, road_capacity=0, distance_km=10.0)
        assert math.isinf(ct)


# ---------------------------------------------------------------------------
# 1.5× buffer for vulnerable populations
# ---------------------------------------------------------------------------


class TestVulnerableBuffer:
    def test_buffer_multiplier_applied(self):
        te = TimelineEstimator()
        base = te._compute_clearance_time(
            population=1000,
            road_capacity=500,
            distance_km=10.0,
            buffer_multiplier=1.0,
        )
        buffered = te._compute_clearance_time(
            population=1000,
            road_capacity=500,
            distance_km=10.0,
            buffer_multiplier=1.5,
        )
        assert buffered == pytest.approx(base * 1.5)

    def test_default_config_buffer_is_1_5(self):
        cfg = EvacuationConfig()
        assert cfg.vulnerable_population_buffer == 1.5


# ---------------------------------------------------------------------------
# 5-phase sequence
# ---------------------------------------------------------------------------


class TestFivePhaseSequence:
    def test_five_phases_produced(self):
        te = TimelineEstimator()
        zones = [_make_zone(1), _make_zone(2), _make_zone(3)]
        routes = [
            _make_route(1),
            _make_route(2),
            _make_route(3),
        ]
        phases, _, _ = te.estimate_timeline(zones, routes)
        assert len(phases) == 5

    def test_phase_numbers_sequential(self):
        te = TimelineEstimator()
        zones = [_make_zone(1), _make_zone(2), _make_zone(3)]
        routes = [_make_route(1), _make_route(2), _make_route(3)]
        phases, _, _ = te.estimate_timeline(zones, routes)
        assert [p.phase_number for p in phases] == [1, 2, 3, 4, 5]

    def test_phase_zone_assignments(self):
        """Phases follow: Z1-vuln, Z1-gen, Z2-vuln, Z2-gen, Z3-all."""
        te = TimelineEstimator()
        zones = [_make_zone(1), _make_zone(2), _make_zone(3)]
        routes = [_make_route(1), _make_route(2), _make_route(3)]
        phases, _, _ = te.estimate_timeline(zones, routes)
        assert phases[0].zone_ids == ["1"]
        assert phases[1].zone_ids == ["1"]
        assert phases[2].zone_ids == ["2"]
        assert phases[3].zone_ids == ["2"]
        assert phases[4].zone_ids == ["3"]

    def test_phases_have_population(self):
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=10000, vuln=1500)]
        routes = [_make_route(1)]
        phases, _, _ = te.estimate_timeline(zones, routes)
        # Phase 1: Zone 1 vulnerable (1500)
        assert phases[0].population_moved == 1500
        # Phase 2: Zone 1 general (10000 - 1500 = 8500)
        assert phases[1].population_moved == 8500

    def test_transport_requests_link_only_to_mandatory_vulnerable_phases(self):
        estimator = TimelineEstimator()
        requests = [
            TransportRequirement(
                requirement_id="tr-zone-1",
                category=VulnerabilityCategory.mobility_impaired,
                vehicle_type="wheelchair_accessible_vehicle",
                quantity_required=10,
                estimated_individuals=40,
                priority_level=TransportPriority.immediate,
                origin_zone=1,
                phase_number=1,
            ),
            TransportRequirement(
                requirement_id="tr-zone-2",
                category=VulnerabilityCategory.medical_dependent,
                vehicle_type="ambulance",
                quantity_required=3,
                estimated_individuals=5,
                priority_level=TransportPriority.critical,
                origin_zone=2,
                phase_number=3,
            ),
        ]

        phases, _, _ = estimator.estimate_timeline(
            [_make_zone(1), _make_zone(2), _make_zone(3)],
            [_make_route(1), _make_route(2), _make_route(3)],
            [request.model_dump(mode="json") for request in requests],
        )

        assert [request.requirement_id for request in phases[0].transport_requirements] == ["tr-zone-1"]
        assert [request.requirement_id for request in phases[2].transport_requirements] == ["tr-zone-2"]
        assert phases[4].transport_requirements == []


class TestModeledPhaseTransitions:
    def test_population_threshold_wins_and_starts_next_phase(self):
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
        )

        first = phases[0]
        second = phases[1]
        assert first.clearance_minutes == pytest.approx(60)
        assert first.population_transition_threshold == 50
        assert first.population_transition_offset_minutes == pytest.approx(90)
        assert first.time_transition_offset_minutes == pytest.approx(132)
        assert first.selected_transition_trigger == (PhaseTransitionTrigger.population_threshold)
        assert first.selected_transition_offset_minutes == pytest.approx(90)
        assert second.start_offset_minutes == pytest.approx(90)

    def test_time_threshold_wins_when_factor_is_earlier(self):
        config = EvacuationConfig(phase_transition_time_factor=0.25)
        phases, _, _ = TimelineEstimator(config).estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
        )

        assert phases[0].selected_transition_trigger == (PhaseTransitionTrigger.time_threshold)
        assert phases[0].selected_transition_offset_minutes == pytest.approx(75)
        assert phases[1].start_offset_minutes == pytest.approx(75)

    def test_population_percentage_changes_persisted_start(self):
        default_phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
        )
        early_phases, _, _ = TimelineEstimator(EvacuationConfig(phase_transition_population_pct=25)).estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
        )

        assert default_phases[1].start_offset_minutes == pytest.approx(90)
        assert early_phases[1].start_offset_minutes == pytest.approx(75)

    def test_shared_edge_delays_overlap_when_capacity_would_be_exceeded(self):
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
            corridor_loads=[
                {
                    "edge_id": "shared-edge",
                    "capacity_vehicles_per_hour": 40,
                    "current_traffic_load_vehicles_per_hour": 0,
                }
            ],
        )

        assert phases[0].selected_transition_offset_minutes == pytest.approx(90)
        assert phases[0].completion_offset_minutes == pytest.approx(120)
        assert phases[1].start_offset_minutes == pytest.approx(120)
        assert phases[1].transition_delay_minutes == pytest.approx(30)

    def test_safe_shared_capacity_allows_modeled_overlap(self):
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
            corridor_loads=[
                {
                    "edge_id": "shared-edge",
                    "capacity_vehicles_per_hour": 100,
                    "current_traffic_load_vehicles_per_hour": 0,
                }
            ],
        )

        assert phases[1].start_offset_minutes == pytest.approx(90)
        assert phases[1].transition_delay_minutes == 0

    def test_transport_buffer_applies_only_to_linked_population(self):
        request = TransportRequirement(
            requirement_id="tr-1",
            category=VulnerabilityCategory.mobility_impaired,
            vehicle_type="wheelchair_accessible_vehicle",
            estimated_individuals=40,
            quantity_required=10,
            priority_level=TransportPriority.immediate,
            origin_zone=1,
            phase_number=1,
            destination_resolved=True,
        )
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
            [request.model_dump(mode="json")],
        )

        assert phases[0].buffered_transport_population == 40
        assert phases[0].buffer_multiplier == pytest.approx(1.2)
        assert phases[0].clearance_minutes == pytest.approx(72)
        assert phases[1].buffered_transport_population == 0
        assert phases[1].buffer_multiplier == 1.0
        assert phases[1].clearance_minutes == pytest.approx(60)

    def test_zero_population_phase_has_zero_chronology(self):
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=100, vuln=0)],
            [_transition_fixture_route()],
        )

        phase = phases[0]
        assert phase.estimated_population == 0
        assert phase.is_empty is True
        assert phase.duration_minutes == 0
        assert phase.completion_offset_minutes == phase.start_offset_minutes
        assert phase.selected_transition_offset_minutes == phase.start_offset_minutes
        assert phase.selected_transition_trigger == PhaseTransitionTrigger.zero_population

    def test_phase_persists_route_allocation_and_shared_capacity_snapshot(self):
        route = {
            **_transition_fixture_route(),
            "route_id": "route-1",
            "allocated_population": 200,
        }
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [route],
        )

        assert phases[0].route_allocation_snapshot == {"route-1": 200}
        assert phases[0].zone_shared_capacity_vehicles_per_hour == 100

    def test_typed_timestamps_are_anchored_and_timezone_aware(self):
        anchor = datetime(2026, 1, 1, tzinfo=UTC)
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
            timeline_anchor=anchor,
        )

        assert phases[0].starts_at == anchor.replace(hour=1)
        assert phases[0].completes_at == anchor.replace(hour=2)
        assert phases[0].transition_at == anchor.replace(hour=1, minute=30)

    def test_plan_completion_is_maximum_overlapping_completion(self):
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
        )

        assert phases[0].completion_offset_minutes == pytest.approx(120)
        assert phases[1].completion_offset_minutes == pytest.approx(150)
        assert TimelineEstimator.plan_completion_minutes(phases) == 150

    def test_shared_cross_zone_edge_delays_lower_priority_phase(self):
        routes = [
            {
                **_transition_fixture_route(),
                "zone_id": "1",
                "allocated_population": 200,
            },
            {
                **_transition_fixture_route(),
                "zone_id": "2",
                "allocated_population": 200,
            },
        ]
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [
                _make_zone(1, pop=200, vuln=100),
                _make_zone(2, pop=200, vuln=100),
            ],
            routes,
            corridor_loads=[
                {
                    "edge_id": "shared-edge",
                    "capacity_vehicles_per_hour": 40,
                    "current_traffic_load_vehicles_per_hour": 0,
                }
            ],
        )

        assert phases[1].completion_offset_minutes == pytest.approx(180)
        assert phases[2].start_offset_minutes == pytest.approx(180)
        assert phases[2].transition_delay_minutes == pytest.approx(30)

    def test_disjoint_cross_zone_corridors_can_overlap(self):
        routes = [
            {
                **_transition_fixture_route(),
                "zone_id": "1",
                "waypoints": ["zone-1-edge"],
                "allocated_population": 200,
            },
            {
                **_transition_fixture_route(),
                "zone_id": "2",
                "waypoints": ["zone-2-edge"],
                "allocated_population": 200,
            },
        ]
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [
                _make_zone(1, pop=200, vuln=100),
                _make_zone(2, pop=200, vuln=100),
            ],
            routes,
            corridor_loads=[
                {
                    "edge_id": "zone-1-edge",
                    "capacity_vehicles_per_hour": 40,
                    "current_traffic_load_vehicles_per_hour": 0,
                },
                {
                    "edge_id": "zone-2-edge",
                    "capacity_vehicles_per_hour": 40,
                    "current_traffic_load_vehicles_per_hour": 0,
                },
            ],
        )

        assert phases[2].start_offset_minutes < phases[1].completion_offset_minutes
        assert phases[2].transition_delay_minutes == 0
        assert [phase.start_offset_minutes for phase in phases] == sorted(
            phase.start_offset_minutes for phase in phases
        )

    def test_unresolved_transport_population_is_not_buffered(self):
        request = TransportRequirement(
            requirement_id="tr-unresolved",
            category=VulnerabilityCategory.mobility_impaired,
            vehicle_type="wheelchair_accessible_vehicle",
            estimated_individuals=40,
            quantity_required=10,
            origin_zone=1,
            phase_number=1,
            destination_resolved=False,
            unresolved_destination_reason="capacity exhausted",
        )
        phases, _, _ = TimelineEstimator().estimate_timeline(
            [_make_zone(1, pop=200, vuln=100)],
            [_transition_fixture_route()],
            [request.model_dump(mode="json")],
        )

        assert phases[0].buffered_transport_population == 0
        assert phases[0].buffer_multiplier == 1.0
        assert phases[0].clearance_minutes == pytest.approx(60)


# ---------------------------------------------------------------------------
# Mobilisation time defaults per hazard type
# ---------------------------------------------------------------------------


class TestMobilisationTimeDefaults:
    def test_bushfire_mobilisation(self):
        te = TimelineEstimator()
        zones = [_make_zone(1)]
        routes = [_make_route(1)]
        phases, _, _ = te.estimate_timeline(zones, routes, hazard_type="bushfire")
        # Phase 1 starts after mobilisation time (60 min for bushfire)
        assert phases[0].start_offset_minutes == 60

    def test_tsunami_mobilisation(self):
        te = TimelineEstimator()
        zones = [_make_zone(1)]
        routes = [_make_route(1)]
        phases, _, _ = te.estimate_timeline(zones, routes, hazard_type="tsunami")
        assert phases[0].start_offset_minutes == 30

    def test_cyclone_mobilisation(self):
        te = TimelineEstimator()
        zones = [_make_zone(1)]
        routes = [_make_route(1)]
        phases, _, _ = te.estimate_timeline(zones, routes, hazard_type="cyclone")
        assert phases[0].start_offset_minutes == 120


# ---------------------------------------------------------------------------
# Shelter-in-place decision
# ---------------------------------------------------------------------------


class TestShelterInPlace:
    def test_shelter_recommended_when_no_routes_and_time_available(self):
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=1000)]
        routes = []  # No routes!
        phases, shelter_recs, assumptions = te.estimate_timeline(
            zones,
            routes,
            hazard_time_horizon_hours=12.0,
        )
        # Should have shelter-in-place recommendations
        assert len(shelter_recs) > 0
        sip = shelter_recs[0]
        assert sip.recommended is True
        assert sip.zone_number == 1
        assert sip.disposition == ZoneDispositionType.shelter_in_place
        assert sip.remaining_population == 1000
        assert sip.shelter_requirements.building
        assert sip.shelter_requirements.supplies
        assert sip.shelter_requirements.communication
        zone_phases = [phase for phase in phases if phase.zone_ids == ["1"]]
        assert all(phase.duration_minutes is None for phase in zone_phases)
        assert all(phase.clearance_blocked for phase in zone_phases)
        assert sum(phase.population_remaining for phase in zone_phases) == 1000

    def test_emergency_escalation_when_imminent(self):
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=1000)]
        routes = []  # No routes
        phases, shelter_recs, assumptions = te.estimate_timeline(
            zones,
            routes,
            hazard_type="bushfire",
            hazard_time_horizon_hours=1.0,  # Imminent
        )
        assert len(shelter_recs) == 1
        sip = shelter_recs[0]
        assert sip.is_emergency_escalation is True
        assert sip.disposition == ZoneDispositionType.emergency_escalation
        assert sip.urgency == "maximum"
        assert sip.evacuating_population == 0
        assert sip.remaining_population == 1000

    def test_unknown_no_route_horizon_escalates_fail_closed(self):
        te = TimelineEstimator()
        _, dispositions, _ = te.estimate_timeline(
            [_make_zone(1, pop=1000)],
            [],
            hazard_time_horizon_hours=None,
        )
        assert dispositions[0].disposition == ZoneDispositionType.emergency_escalation

    def test_zero_capacity_route_is_blocked_not_instant(self):
        te = TimelineEstimator()
        phases, dispositions, _ = te.estimate_timeline(
            [_make_zone(1, pop=1000)],
            [_make_route(1, capacity=0)],
            hazard_time_horizon_hours=12,
        )
        assert dispositions[0].disposition == ZoneDispositionType.shelter_in_place
        assert any(phase.duration_minutes is None for phase in phases if phase.zone_ids == ["1"])


# ---------------------------------------------------------------------------
# Time deficit detection
# ---------------------------------------------------------------------------


class TestTimeDeficitDetection:
    def test_time_deficit_detected(self):
        """When total evacuation exceeds hazard arrival, assumptions should warn."""
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=100_000, vuln=15_000)]
        routes = [_make_route(1, distance_km=50.0, capacity=100)]
        phases, _, assumptions = te.estimate_timeline(
            zones,
            routes,
            hazard_type="bushfire",
            hazard_time_horizon_hours=1.0,  # Only 1 hour
        )
        # Should have a TIME DEFICIT assumption
        deficit_found = any("TIME DEFICIT" in a for a in assumptions)
        assert deficit_found is True

    def test_no_deficit_when_time_sufficient(self):
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=100, vuln=15)]
        routes = [_make_route(1, distance_km=5.0, capacity=1000)]
        phases, _, assumptions = te.estimate_timeline(
            zones,
            routes,
            hazard_type="bushfire",
            hazard_time_horizon_hours=100.0,  # Lots of time
        )
        deficit_found = any("TIME DEFICIT" in a for a in assumptions)
        assert deficit_found is False

    def test_viable_but_slow_route_has_partial_disposition(self):
        te = TimelineEstimator()
        phases, dispositions, assumptions = te.estimate_timeline(
            [_make_zone(1, pop=1000, vuln=100)],
            [_make_route(1, distance_km=20.0, capacity=100)],
            hazard_type="bushfire",
            hazard_time_horizon_hours=2.0,
        )
        disposition = dispositions[0]
        assert disposition.disposition == ZoneDispositionType.partial_evacuation
        assert 0 < disposition.evacuating_population < 1000
        assert disposition.remaining_population > 0
        assert disposition.evacuating_population + disposition.remaining_population == 1000
        assert any("TIME DEFICIT" in assumption for assumption in assumptions)
        assert (
            sum(phase.population_moved for phase in phases if phase.zone_ids == ["1"])
            == disposition.evacuating_population
        )

    def test_each_zone_has_one_reconciled_disposition(self):
        te = TimelineEstimator()
        _, dispositions, _ = te.estimate_timeline(
            [_make_zone(1, pop=100), _make_zone(2, pop=200), _make_zone(3, pop=300)],
            [_make_route(1), _make_route(2)],
            hazard_time_horizon_hours=12,
        )
        assert [disposition.zone_number for disposition in dispositions] == [1, 2, 3]
        assert len({disposition.zone_number for disposition in dispositions}) == 3
        assert sum(disposition.affected_population for disposition in dispositions) == 600

    def test_shared_corridor_capacity_is_not_summed_per_route(self):
        estimator = TimelineEstimator()
        routes = [
            {
                **_make_route(1, distance_km=10, capacity=100),
                "allocated_population": 50,
                "zone_shared_capacity_vehicles_per_hour": 100,
                "waypoints": ["shared", "branch-a"],
            },
            {
                **_make_route(1, distance_km=20, capacity=100),
                "allocated_population": 50,
                "zone_shared_capacity_vehicles_per_hour": 100,
                "waypoints": ["shared", "branch-b"],
            },
        ]

        metrics = estimator._compute_zone_route_metrics(
            [_make_zone(1, pop=100, vuln=10)],
            routes,
        )[1]

        assert metrics["total_capacity"] == 100
        assert metrics["avg_distance_km"] == pytest.approx(15)

    def test_distance_is_weighted_by_assigned_population(self):
        routes = [
            {
                **_make_route(1, distance_km=10, capacity=100),
                "allocated_population": 75,
                "zone_shared_capacity_vehicles_per_hour": 200,
            },
            {
                **_make_route(1, distance_km=30, capacity=100),
                "allocated_population": 25,
                "zone_shared_capacity_vehicles_per_hour": 200,
            },
        ]

        metrics = TimelineEstimator()._compute_zone_route_metrics(
            [_make_zone(1, pop=100, vuln=10)],
            routes,
        )[1]

        assert metrics["avg_distance_km"] == pytest.approx(15)

    def test_disjoint_corridor_max_flow_capacity_is_used(self):
        estimator = TimelineEstimator()
        routes = [
            {
                **_make_route(1, capacity=100),
                "allocated_population": 50,
                "zone_shared_capacity_vehicles_per_hour": 200,
            },
            {
                **_make_route(1, capacity=100),
                "allocated_population": 50,
                "zone_shared_capacity_vehicles_per_hour": 200,
            },
        ]

        metrics = estimator._compute_zone_route_metrics(
            [_make_zone(1, pop=100, vuln=10)],
            routes,
        )[1]

        assert metrics["total_capacity"] == 200

    def test_destination_capacity_shortfall_forces_partial_disposition(self):
        estimator = TimelineEstimator()
        zone = _make_zone(1, pop=100, vuln=20)
        zone["unallocated_route_population"] = 40
        zone["unallocated_vulnerable_population"] = 10
        route = {
            **_make_route(1, distance_km=1, capacity=1000),
            "allocated_population": 60,
            "zone_shared_capacity_vehicles_per_hour": 1000,
        }

        phases, dispositions, assumptions = estimator.estimate_timeline(
            [zone],
            [route],
            hazard_time_horizon_hours=12,
        )

        disposition = dispositions[0]
        assert disposition.disposition == ZoneDispositionType.partial_evacuation
        assert disposition.evacuating_population == 60
        assert disposition.remaining_population == 40
        assert sum(phase.population_moved for phase in phases if phase.zone_ids == ["1"]) == 60
        assert any("DESTINATION CAPACITY GAP" in item for item in assumptions)


# ---------------------------------------------------------------------------
# Shelter recovery check
# ---------------------------------------------------------------------------


class TestShelterRecovery:
    def test_can_recover_with_routes(self):
        te = TimelineEstimator()
        routes = [_make_route(1)]
        assert te.can_recover_from_shelter(1, routes) is True

    def test_cannot_recover_without_routes(self):
        te = TimelineEstimator()
        routes = [_make_route(2)]  # Routes only for zone 2
        assert te.can_recover_from_shelter(1, routes) is False

    def test_reopened_route_changes_shelter_to_evacuation(self):
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=100, vuln=10)]
        _, blocked_dispositions, _ = te.estimate_timeline(
            zones,
            [],
            hazard_time_horizon_hours=12,
        )
        _, reopened_dispositions, _ = te.estimate_timeline(
            zones,
            [_make_route(1, distance_km=1, capacity=1000)],
            hazard_time_horizon_hours=12,
        )
        assert blocked_dispositions[0].disposition == ZoneDispositionType.shelter_in_place
        assert reopened_dispositions[0].disposition == ZoneDispositionType.evacuation
        assert reopened_dispositions[0].remaining_population == 0

    def test_mixed_zones_keep_distinct_dispositions(self):
        te = TimelineEstimator()
        _, dispositions, _ = te.estimate_timeline(
            [
                _make_zone(1, pop=100, vuln=10),
                _make_zone(2, pop=200, vuln=20),
                _make_zone(3, pop=300, vuln=30),
            ],
            [
                _make_route(1, distance_km=1, capacity=1000),
                _make_route(3, distance_km=20, capacity=50),
            ],
            hazard_type="flood",
            hazard_time_horizon_hours=8,
        )
        by_zone = {item.zone_number: item for item in dispositions}
        assert by_zone[1].disposition == ZoneDispositionType.evacuation
        assert by_zone[2].disposition == ZoneDispositionType.shelter_in_place
        assert by_zone[3].disposition == ZoneDispositionType.partial_evacuation
        assert sum(item.affected_population for item in dispositions) == 600
