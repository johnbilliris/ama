"""Simulation: flood scenario allocation.

End-to-end pipeline test with realistic flood resource demands.
"""

from __future__ import annotations

import pytest

from common.handoffs import AgentHandoffEvent

from resource_allocation.audit import AuditWriter
from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.dedup import HandoffDeduplicator
from resource_allocation.inventory import ResourceInventoryManager
from resource_allocation.matcher import ResourceMatcher
from resource_allocation.models import (
    ConfidenceLevel,
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
    UrgencyLevel,
)
from resource_allocation.pipeline import AllocationProcessingPipeline
from resource_allocation.versioning import VersionCounter


def _build_flood_inventory():
    """Build a realistic flood-scenario inventory."""
    return [
        ResourceInventoryItem(
            resource_id="veh-wt-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="water_tanker",
            capabilities=["water_delivery", "firefighting_support"],
            location={"lat": -27.4698, "lon": 153.0251},  # Brisbane CBD
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="veh-wt-002",
            resource_type=ResourceType.vehicle,
            resource_sub_type="water_tanker",
            capabilities=["water_delivery"],
            location={"lat": -27.5, "lon": 153.05},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="veh-amb-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="ambulance",
            capabilities=["medical_transport", "patient_stabilization"],
            location={"lat": -27.47, "lon": 153.03},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="per-para-001",
            resource_type=ResourceType.personnel,
            resource_sub_type="paramedic",
            capabilities=["medical_treatment", "triage", "patient_stabilization"],
            location={"lat": -27.48, "lon": 153.04},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="per-para-002",
            resource_type=ResourceType.personnel,
            resource_sub_type="paramedic",
            capabilities=["medical_treatment", "triage"],
            location={"lat": -27.55, "lon": 153.06},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="sup-med-001",
            resource_type=ResourceType.supply,
            resource_sub_type="medical_kit",
            capabilities=["medical_treatment"],
            location={"lat": -27.48, "lon": 153.02},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="fac-evac-001",
            resource_type=ResourceType.facility,
            resource_sub_type="evacuation_centre",
            capabilities=["shelter", "mass_care"],
            location={"lat": -27.43, "lon": 153.0},
            status=ResourceStatus.available,
        ),
    ]


def _make_flood_handoff():
    return AgentHandoffEvent(
        handoff_id="h-flood-001",
        incident_id="inc-flood-brisbane-2024",
        source_agent="risk_assessment",
        target_agent="resource_allocation",
        scope_key="live:inc-flood-brisbane-2024",
        confidence=0.9,
        payload={
            "recommendationId": "rec-flood-001",
            "summary": (
                "Major flooding in Brisbane CBD requires water tankers for "
                "supply distribution, medical teams for displaced persons "
                "triage, and ambulance transport for elderly evacuees."
            ),
            "assessmentId": "ha-flood-001",
        },
        tenant_id="live",
    )


class TestFloodScenario:
    def test_plan_generated_for_flood(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_flood_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan is not None
        assert plan.incident_id == "inc-flood-brisbane-2024"

    def test_flood_plan_has_assignments(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_flood_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan = pipeline.process_handoff(_make_flood_handoff())
        assert len(plan.assignments) > 0, "Flood scenario should have resource assignments"

    def test_flood_plan_has_reasonable_confidence(self):
        config = ResourceAllocationConfig()
        inventory = ResourceInventoryManager(config=config)
        for r in _build_flood_inventory():
            inventory.add_resource(r)

        pipeline = AllocationProcessingPipeline(
            config=config,
            dedup=HandoffDeduplicator(window_minutes=10),
            inventory=inventory,
            matcher=ResourceMatcher(config=config),
            version_counter=VersionCounter(),
            audit_writer=AuditWriter(config=config),
        )

        plan = pipeline.process_handoff(_make_flood_handoff())
        assert plan.confidence_score >= 0.3, "Flood plan should have reasonable confidence"
