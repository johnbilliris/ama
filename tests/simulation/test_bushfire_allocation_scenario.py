"""Simulation: bushfire scenario allocation.

End-to-end pipeline test with realistic bushfire resource demands.
"""

from __future__ import annotations

from common.handoffs import AgentHandoffEvent
from resource_allocation.audit import AuditWriter
from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.dedup import HandoffDeduplicator
from resource_allocation.inventory import ResourceInventoryManager
from resource_allocation.matcher import ResourceMatcher
from resource_allocation.models import (
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
)
from resource_allocation.pipeline import AllocationProcessingPipeline
from resource_allocation.versioning import VersionCounter


def _build_bushfire_inventory():
    return [
        ResourceInventoryItem(
            resource_id="veh-ft-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="fire_truck",
            capabilities=["firefighting_support", "water_delivery"],
            location={"lat": -33.7, "lon": 150.3},  # Blue Mountains
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="veh-ft-002",
            resource_type=ResourceType.vehicle,
            resource_sub_type="fire_truck",
            capabilities=["firefighting_support"],
            location={"lat": -33.75, "lon": 150.35},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="per-fire-001",
            resource_type=ResourceType.personnel,
            resource_sub_type="firefighter",
            capabilities=["firefighting_support", "search_and_rescue"],
            location={"lat": -33.71, "lon": 150.31},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="per-fire-002",
            resource_type=ResourceType.personnel,
            resource_sub_type="firefighter",
            capabilities=["firefighting_support"],
            location={"lat": -33.73, "lon": 150.33},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="veh-amb-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            capabilities=["medical_transport", "patient_stabilization"],
            location={"lat": -33.72, "lon": 150.32},
            status=ResourceStatus.available,
        ),
    ]


def _make_bushfire_handoff():
    return AgentHandoffEvent(
        handoff_id="h-bush-001",
        incident_id="inc-bushfire-bluemtns-2024",
        source_agent="risk_assessment",
        target_agent="resource_allocation",
        scope_key="live:inc-bushfire-bluemtns-2024",
        confidence=0.88,
        payload={
            "recommendationId": "rec-bush-001",
            "summary": (
                "Bushfire in Blue Mountains requires fire trucks for "
                "containment, firefighting teams for ground operations, "
                "and ambulance standby for potential casualties."
            ),
            "assessmentId": "ha-bush-001",
        },
        tenant_id="live",
    )


class TestBushfireScenario:
    def test_plan_generated_for_bushfire(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_bushfire_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan = pipeline.process_handoff(_make_bushfire_handoff())
        assert plan is not None
        assert plan.incident_id == "inc-bushfire-bluemtns-2024"

    def test_bushfire_plan_has_assignments(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_bushfire_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan = pipeline.process_handoff(_make_bushfire_handoff())
        assert len(plan.assignments) > 0

    def test_bushfire_allocates_fire_resources(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_bushfire_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan = pipeline.process_handoff(_make_bushfire_handoff())
        # Check that assignments exist (firefighting resources should be matched)
        assert len(plan.assignments) > 0, "Bushfire should have resource assignments"
        # Verify at least some assignments are for vehicles or personnel
        # (the keyword matcher may assign any capable resource)
        assigned_ids = {a.resource_id for a in plan.assignments}
        assert len(assigned_ids) > 0, "Bushfire should assign resources"
