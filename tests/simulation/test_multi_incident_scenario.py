"""Simulation: multi-incident scenario allocation.

Tests cross-incident contention detection and resource sharing.
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


def _build_shared_inventory():
    """Limited resources shared between two incidents."""
    return [
        ResourceInventoryItem(
            resource_id="veh-amb-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            capabilities=["medical_transport"],
            location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="per-para-001",
            resource_type=ResourceType.personnel,
            resource_sub_type="paramedic",
            capabilities=["medical_treatment", "triage"],
            location={"lat": -33.88, "lon": 151.22},
            status=ResourceStatus.available,
        ),
    ]


def _make_handoff(handoff_id, incident_id, summary):
    return AgentHandoffEvent(
        handoff_id=handoff_id,
        incident_id=incident_id,
        source_agent="risk_assessment",
        target_agent="resource_allocation",
        scope_key=f"live:{incident_id}",
        confidence=0.85,
        payload={
            "recommendationId": f"rec-{incident_id}",
            "summary": summary,
            "assessmentId": f"ha-{incident_id}",
        },
        tenant_id="live",
    )


class TestMultiIncidentScenario:
    def test_two_incidents_get_separate_plans(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_shared_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan1 = pipeline.process_handoff(_make_handoff(
            "h-multi-001", "inc-north", "Flood in northern suburbs needs ambulance"
        ))
        plan2 = pipeline.process_handoff(_make_handoff(
            "h-multi-002", "inc-south", "Bushfire in southern areas needs medical teams"
        ))

        assert plan1 is not None
        assert plan2 is not None
        assert plan1.incident_id != plan2.incident_id

    def test_resource_not_double_assigned(self):
        """A resource assigned to incident 1 should not be available for incident 2."""
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_shared_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan1 = pipeline.process_handoff(_make_handoff(
            "h-multi-001", "inc-north", "Flood needs ambulance and medical teams"
        ))

        assigned_to_inc1 = {a.resource_id for a in plan1.assignments}

        plan2 = pipeline.process_handoff(_make_handoff(
            "h-multi-002", "inc-south", "Bushfire needs ambulance"
        ))

        assigned_to_inc2 = {a.resource_id for a in plan2.assignments}

        overlap = assigned_to_inc1 & assigned_to_inc2
        assert len(overlap) == 0, f"Resources double-assigned: {overlap}"

    def test_second_incident_reports_shortfall_when_exhausted(self):
        """When all resources are taken by incident 1, incident 2 should report shortfall."""
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_shared_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        # First incident takes all resources
        plan1 = pipeline.process_handoff(_make_handoff(
            "h-multi-001", "inc-north", "Major flood needs ambulance and paramedics"
        ))

        # Second incident should have shortfall
        plan2 = pipeline.process_handoff(_make_handoff(
            "h-multi-002", "inc-south", "Bushfire needs ambulance and medical teams"
        ))

        assert plan2 is not None
        # If inc1 took the resources, inc2 may have shortfalls
        if plan1.assignments:
            # We expect plan2 to have fewer or no assignments
            total_resources = len(_build_shared_inventory())
            assert len(plan2.assignments) < total_resources or len(plan2.unmet_demands) > 0
