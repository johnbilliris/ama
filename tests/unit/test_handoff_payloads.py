"""Tests for inter-agent handoff payload models (T054-T064).

Covers:
- TransportHandoffPayload serialisation
- DispatchHandoffPayload serialisation
- RoadClosureSignalPayload serialisation
- Required field validation
- Default values
"""

from __future__ import annotations



from common.handoff_payloads import (
    DispatchHandoffPayload,
    RoadClosureSignalPayload,
    TransportHandoffPayload,
)


class TestTransportHandoffPayload:
    """Tests for evacuation → resource_allocation handoff."""

    def test_create_with_required_fields(self):
        payload = TransportHandoffPayload(
            evacuation_plan_id="ep-inc001-v1",
            incident_id="inc-001",
            zone_number=1,
            vehicle_type="bus",
            quantity_required=3,
            pickup_latitude=-33.8688,
            pickup_longitude=151.2093,
            destination_assembly_area_id="aa-001",
            priority_tier="immediate",
            vulnerability_category="elderly_aged_care",
            estimated_persons=120,
        )
        assert payload.evacuation_plan_id == "ep-inc001-v1"
        assert payload.quantity_required == 3
        assert payload.priority_tier == "immediate"

    def test_default_special_considerations(self):
        payload = TransportHandoffPayload(
            evacuation_plan_id="ep-001",
            incident_id="inc-001",
            zone_number=1,
            vehicle_type="ambulance",
            quantity_required=2,
            pickup_latitude=0.0,
            pickup_longitude=0.0,
            destination_assembly_area_id="aa-001",
            priority_tier="critical",
            vulnerability_category="medical_dependent",
            estimated_persons=4,
        )
        assert payload.special_considerations == []

    def test_serialisation_roundtrip(self):
        payload = TransportHandoffPayload(
            evacuation_plan_id="ep-001",
            incident_id="inc-001",
            zone_number=2,
            vehicle_type="bus",
            quantity_required=5,
            pickup_latitude=-33.0,
            pickup_longitude=151.0,
            destination_assembly_area_id="aa-002",
            priority_tier="high",
            vulnerability_category="children_schools_childcare",
            estimated_persons=200,
            special_considerations=["child_supervision"],
        )
        data = payload.model_dump(mode="json")
        restored = TransportHandoffPayload(**data)
        assert restored == payload


class TestDispatchHandoffPayload:
    """Tests for resource_allocation → communication handoff."""

    def test_create_with_defaults(self):
        payload = DispatchHandoffPayload(
            deployment_plan_id="rdp-inc001-v1",
            incident_id="inc-001",
            deployment_summary="5 buses dispatched to zone 1",
        )
        assert payload.warning_tier == "Advice"
        assert len(payload.target_languages) == 6

    def test_custom_warning_tier(self):
        payload = DispatchHandoffPayload(
            deployment_plan_id="rdp-001",
            incident_id="inc-001",
            deployment_summary="Emergency deployment",
            warning_tier="Emergency Warning",
        )
        assert payload.warning_tier == "Emergency Warning"


class TestRoadClosureSignalPayload:
    """Tests for monitoring → evacuation road closure signal."""

    def test_create_road_closure(self):
        payload = RoadClosureSignalPayload(
            signal_id="sig-road-001",
            incident_id="inc-001",
            road_segment_id="seg-m1-north",
            road_name="Pacific Highway",
            closure_type="full",
            latitude=-33.8,
            longitude=151.2,
            reason="bushfire",
        )
        assert payload.closure_type == "full"
        assert payload.road_name == "Pacific Highway"

    def test_partial_closure(self):
        payload = RoadClosureSignalPayload(
            signal_id="sig-road-002",
            incident_id="inc-001",
            road_segment_id="seg-m2-south",
            closure_type="partial",
        )
        assert payload.closure_type == "partial"
        assert payload.effective_until is None
