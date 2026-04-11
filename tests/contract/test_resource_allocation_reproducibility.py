"""Contract tests for reproducibility (US7).

Verifies that the same handoff + inventory + config produces identical plans.
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
    ResourceInventoryItem,
    ResourceStatus,
    ResourceType,
)
from resource_allocation.pipeline import AllocationProcessingPipeline
from resource_allocation.versioning import VersionCounter


def _make_handoff(handoff_id="h-repr-001"):
    return AgentHandoffEvent(
        handoff_id=handoff_id,
        incident_id="inc001",
        source_agent="risk_assessment",
        target_agent="resource_allocation",
        scope_key="sim-test:inc001",
        confidence=0.85,
        payload={
            "recommendationId": "rec-001",
            "summary": "Flood impacts requiring water tankers and medical teams",
            "assessmentId": "ha-001",
        },
        tenant_id="sim-test",
    )


def _make_inventory():
    return [
        ResourceInventoryItem(
            resource_id="veh-wt-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="water_tanker",
            capabilities=["water_delivery"],
            location={"lat": -33.8, "lon": 151.2},
            status=ResourceStatus.available,
        ),
        ResourceInventoryItem(
            resource_id="per-para-001",
            resource_type=ResourceType.personnel,
            resource_sub_type="paramedic",
            capabilities=["medical_treatment", "triage"],
            location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.available,
        ),
    ]


def _make_pipeline(resources):
    config = ResourceAllocationConfig()
    inventory = ResourceInventoryManager(config=config)
    for r in resources:
        inventory.add_resource(r)

    return AllocationProcessingPipeline(
        config=config,
        dedup=HandoffDeduplicator(window_minutes=10),
        inventory=inventory,
        matcher=ResourceMatcher(config=config),
        version_counter=VersionCounter(),
        audit_writer=AuditWriter(config=config),
    )


class TestReproducibility:
    """Given the same inputs, plans should be deterministic (excluding timestamps)."""

    def test_same_handoff_same_inventory_same_config(self):
        resources = _make_inventory()

        # Run pipeline twice with fresh state
        pipeline1 = _make_pipeline(resources)
        plan1 = pipeline1.process_handoff(_make_handoff(handoff_id="h-repr-001"))

        pipeline2 = _make_pipeline(resources)
        plan2 = pipeline2.process_handoff(_make_handoff(handoff_id="h-repr-002"))

        assert plan1 is not None
        assert plan2 is not None

        # Same incident → same demands → same assignments
        assert len(plan1.demands) == len(plan2.demands)
        assert len(plan1.assignments) == len(plan2.assignments)
        assert len(plan1.unmet_demands) == len(plan2.unmet_demands)

        # Same scores
        if plan1.assignments and plan2.assignments:
            scores1 = sorted(a.score for a in plan1.assignments)
            scores2 = sorted(a.score for a in plan2.assignments)
            for s1, s2 in zip(scores1, scores2):
                assert abs(s1 - s2) < 1e-9, f"Scores differ: {s1} vs {s2}"

        # Same confidence
        assert abs(plan1.confidence_score - plan2.confidence_score) < 1e-9

    def test_input_snapshot_captures_config_hash(self):
        pipeline = _make_pipeline(_make_inventory())
        plan = pipeline.process_handoff(_make_handoff())
        assert plan.input_snapshot.config_version != ""

    def test_input_snapshot_captures_inventory_hash(self):
        pipeline = _make_pipeline(_make_inventory())
        plan = pipeline.process_handoff(_make_handoff())
        assert plan.input_snapshot.inventory_snapshot_hash != ""
        assert len(plan.input_snapshot.inventory_snapshot_hash) > 0
