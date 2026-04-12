"""Tests for evacuation.timeline — clearance time, phases, shelter-in-place (T034)."""

import pytest
from evacuation.config import EvacuationConfig
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
        assert ct == 0.0


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
            zones, routes, hazard_time_horizon_hours=12.0,
        )
        # Should have shelter-in-place recommendations
        assert len(shelter_recs) > 0
        sip = shelter_recs[0]
        assert sip.recommended is True
        assert sip.zone_number == 1

    def test_emergency_escalation_when_imminent(self):
        te = TimelineEstimator()
        zones = [_make_zone(1, pop=1000)]
        routes = []  # No routes
        phases, shelter_recs, assumptions = te.estimate_timeline(
            zones, routes, hazard_type="bushfire",
            hazard_time_horizon_hours=1.0,  # Imminent
        )
        if shelter_recs:
            sip = shelter_recs[0]
            assert sip.is_emergency_escalation is True


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
            zones, routes,
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
            zones, routes,
            hazard_type="bushfire",
            hazard_time_horizon_hours=100.0,  # Lots of time
        )
        deficit_found = any("TIME DEFICIT" in a for a in assumptions)
        assert deficit_found is False


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
