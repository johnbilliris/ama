"""Unit tests for resource inventory manager.

Covers:
- Static inventory loading from JSON
- State machine valid transitions
- State machine invalid transitions rejected
- Operational flags (rotation, replenishment, mechanical)
- Eligible resource filtering
- Bulk release on incident closure
- Utilisation metrics computation
"""

from __future__ import annotations

import json
import os

from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.inventory import ResourceInventoryManager
from resource_allocation.models import (
    ResourceDemand,
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
)


class TestInventoryLoading:
    def test_load_from_json(self, tmp_path):
        data = {
            "resources": [
                {
                    "resource_id": "res-001",
                    "resource_type": "vehicle",
                    "resource_sub_type": "ambulance",
                    "capabilities": ["medical_transport"],
                    "location": {"lat": -33.87, "lon": 151.21},
                    "status": "available",
                },
            ]
        }
        path = tmp_path / "inventory.json"
        path.write_text(json.dumps(data))

        mgr = ResourceInventoryManager()
        items = mgr.load_from_json(str(path))
        assert len(items) == 1
        assert items[0].resource_id == "res-001"
        assert mgr.resource_count == 1

    def test_load_nonexistent_file(self):
        mgr = ResourceInventoryManager()
        items = mgr.load_from_json("/nonexistent/path.json")
        assert items == []

    def test_load_sample_inventory(self):
        sample_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "data", "resource-inventories", "sample-inventory.json",
        )
        if os.path.exists(sample_path):
            mgr = ResourceInventoryManager()
            items = mgr.load_from_json(sample_path)
            assert len(items) > 0


class TestStateMachine:
    """Test valid and invalid state transitions."""

    def _make_mgr_with_resource(self, status=ResourceStatus.available):
        mgr = ResourceInventoryManager()
        resource = ResourceInventoryItem(
            resource_id="res-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            capabilities=["medical_transport"],
            location={"lat": -33.87, "lon": 151.21},
            status=status,
        )
        mgr.add_resource(resource)
        return mgr

    def test_available_to_reserved(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.available)
        assert mgr.transition_status("res-001", ResourceStatus.reserved)
        assert mgr.get_resource("res-001").status == ResourceStatus.reserved

    def test_available_to_assigned(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.available)
        assert mgr.transition_status("res-001", ResourceStatus.assigned, "inc001")
        resource = mgr.get_resource("res-001")
        assert resource.status == ResourceStatus.assigned
        assert resource.assigned_incident_id == "inc001"

    def test_assigned_to_en_route(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.assigned)
        assert mgr.transition_status("res-001", ResourceStatus.en_route)

    def test_en_route_to_deployed(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.en_route)
        assert mgr.transition_status("res-001", ResourceStatus.deployed)

    def test_deployed_to_returning(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.deployed)
        assert mgr.transition_status("res-001", ResourceStatus.returning)

    def test_returning_to_available(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.returning)
        assert mgr.transition_status("res-001", ResourceStatus.available)

    def test_active_to_unavailable(self):
        """States that can transition to unavailable per state machine."""
        for status in [ResourceStatus.assigned, ResourceStatus.en_route,
                       ResourceStatus.deployed, ResourceStatus.returning,
                       ResourceStatus.reserved]:
            mgr = self._make_mgr_with_resource(status)
            assert mgr.transition_status("res-001", ResourceStatus.unavailable), \
                f"{status} → unavailable should be valid"

    def test_available_to_unavailable_rejected(self):
        """available → unavailable is NOT a valid transition."""
        mgr = self._make_mgr_with_resource(ResourceStatus.available)
        assert not mgr.transition_status("res-001", ResourceStatus.unavailable)

    # Invalid transitions
    def test_available_to_deployed_rejected(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.available)
        assert not mgr.transition_status("res-001", ResourceStatus.deployed)

    def test_available_to_returning_rejected(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.available)
        assert not mgr.transition_status("res-001", ResourceStatus.returning)

    def test_deployed_to_assigned_rejected(self):
        mgr = self._make_mgr_with_resource(ResourceStatus.deployed)
        assert not mgr.transition_status("res-001", ResourceStatus.assigned)

    def test_nonexistent_resource_rejected(self):
        mgr = ResourceInventoryManager()
        assert not mgr.transition_status("nonexistent", ResourceStatus.assigned)


class TestOperationalFlags:
    def test_rotation_flag(self):
        config = ResourceAllocationConfig()
        mgr = ResourceInventoryManager(config=config)
        resource = ResourceInventoryItem(
            resource_id="res-001",
            resource_type=ResourceType.personnel,
            resource_sub_type="firefighter",
            location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.deployed,
            continuous_deployment_hours=13.0,  # > 12h threshold
        )
        mgr.add_resource(resource)
        flagged = mgr.flag_operational_limits()
        assert len(flagged) == 1
        assert "rotation_needed" in flagged[0].flags

    def test_replenishment_flag(self):
        config = ResourceAllocationConfig()
        mgr = ResourceInventoryManager(config=config)
        resource = ResourceInventoryItem(
            resource_id="sup-001",
            resource_type=ResourceType.supply,
            resource_sub_type="water",
            location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.available,
            capacity=50,
            initial_capacity=500,  # 10% remaining < 20% threshold
        )
        mgr.add_resource(resource)
        flagged = mgr.flag_operational_limits()
        assert len(flagged) == 1
        assert "replenishment_needed" in flagged[0].flags


class TestEligibleResources:
    def test_filters_by_type(self):
        mgr = ResourceInventoryManager()
        mgr.add_resource(ResourceInventoryItem(
            resource_id="amb-001", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", capabilities=["medical_transport"],
            location={"lat": -33.87, "lon": 151.21}, status=ResourceStatus.available,
        ))
        mgr.add_resource(ResourceInventoryItem(
            resource_id="per-001", resource_type=ResourceType.personnel,
            resource_sub_type="paramedic", capabilities=["medical_treatment"],
            location={"lat": -33.87, "lon": 151.21}, status=ResourceStatus.available,
        ))

        demand = ResourceDemand(
            demand_id="d1", incident_id="inc001", source_id="r1",
            source_type="coordination_task", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", required_capabilities=["medical_transport"],
        )
        eligible = mgr.get_eligible_resources(demand)
        assert len(eligible) == 1
        assert eligible[0].resource_id == "amb-001"

    def test_excludes_unavailable(self):
        mgr = ResourceInventoryManager()
        mgr.add_resource(ResourceInventoryItem(
            resource_id="amb-001", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", capabilities=["medical_transport"],
            location={"lat": -33.87, "lon": 151.21}, status=ResourceStatus.unavailable,
        ))

        demand = ResourceDemand(
            demand_id="d1", incident_id="inc001", source_id="r1",
            source_type="coordination_task", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
        )
        eligible = mgr.get_eligible_resources(demand)
        assert len(eligible) == 0

    def test_returning_is_eligible(self):
        mgr = ResourceInventoryManager()
        mgr.add_resource(ResourceInventoryItem(
            resource_id="amb-001", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", capabilities=["medical_transport"],
            location={"lat": -33.87, "lon": 151.21}, status=ResourceStatus.returning,
        ))

        demand = ResourceDemand(
            demand_id="d1", incident_id="inc001", source_id="r1",
            source_type="coordination_task", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
        )
        eligible = mgr.get_eligible_resources(demand)
        assert len(eligible) == 1


class TestBulkRelease:
    def test_release_incident_resources(self):
        mgr = ResourceInventoryManager()
        mgr.add_resource(ResourceInventoryItem(
            resource_id="res-001", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.assigned, assigned_incident_id="inc001",
        ))
        mgr.add_resource(ResourceInventoryItem(
            resource_id="res-002", resource_type=ResourceType.vehicle,
            resource_sub_type="bus", location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.assigned, assigned_incident_id="inc002",
        ))

        released = mgr.release_incident_resources("inc001")
        assert released == 1
        assert mgr.get_resource("res-001").status == ResourceStatus.available
        assert mgr.get_resource("res-002").status == ResourceStatus.assigned


class TestUtilisation:
    def test_compute_utilisation(self):
        mgr = ResourceInventoryManager()
        mgr.add_resource(ResourceInventoryItem(
            resource_id="r1", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", location={"lat": 0, "lon": 0},
            status=ResourceStatus.available,
        ))
        mgr.add_resource(ResourceInventoryItem(
            resource_id="r2", resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance", location={"lat": 0, "lon": 0},
            status=ResourceStatus.deployed,
        ))

        util = mgr.compute_utilisation()
        assert util["total"] == 2
        assert util["available"] == 1
        assert util["deployed"] == 1
        assert util["utilisation_percent"] == 50.0

    def test_empty_utilisation(self):
        mgr = ResourceInventoryManager()
        util = mgr.compute_utilisation()
        assert util["total"] == 0
        assert util["utilisation_percent"] == 0.0
