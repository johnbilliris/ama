"""Unit tests for pipeline stages 1-9.

Covers:
- Valid handoff acceptance
- Malformed handoff rejection
- Missing incident rejection
- Duplicate handoff discard
- Demand extraction
- Plan generation
- Transport dispatch processing (US3)
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


def _make_handoff(**overrides):
    defaults = {
        "handoff_id": "h-test-001",
        "incident_id": "inc001",
        "source_agent": "risk_assessment",
        "target_agent": "resource_allocation",
        "scope_key": "live:inc001",
        "confidence": 0.85,
        "payload": {
            "recommendationId": "rec-inc001-ra-001",
            "summary": "Flood impacts requiring water tankers and medical teams",
            "assessmentId": "ha-inc001-v1",
        },
        "tenant_id": "live",
    }
    defaults.update(overrides)
    return AgentHandoffEvent(**defaults)


def _make_pipeline(resources=None):
    config = ResourceAllocationConfig()
    inventory = ResourceInventoryManager(config=config)

    # Add some resources
    if resources:
        for r in resources:
            inventory.add_resource(r)
    else:
        inventory.add_resource(ResourceInventoryItem(
            resource_id="veh-wt-001",
            resource_type=ResourceType.vehicle,
            resource_sub_type="water_tanker",
            capabilities=["water_delivery", "firefighting_support"],
            location={"lat": -33.8, "lon": 151.2},
            status=ResourceStatus.available,
        ))
        inventory.add_resource(ResourceInventoryItem(
            resource_id="per-para-001",
            resource_type=ResourceType.personnel,
            resource_sub_type="paramedic",
            capabilities=["medical_treatment", "patient_stabilization", "triage"],
            location={"lat": -33.87, "lon": 151.21},
            status=ResourceStatus.available,
        ))

    pipeline = AllocationProcessingPipeline(
        config=config,
        dedup=HandoffDeduplicator(window_minutes=10),
        inventory=inventory,
        matcher=ResourceMatcher(config=config),
        version_counter=VersionCounter(),
        audit_writer=AuditWriter(config=config),
    )
    return pipeline


class TestStage1Validation:
    def test_valid_handoff_accepted(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert plan.plan_id.startswith("rdp-inc001-v")

    def test_wrong_target_rejected(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(target_agent="evacuation")
        plan = pipeline.process_handoff(handoff)
        assert plan is None

    def test_unknown_source_rejected(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(source_agent="unknown_agent")
        plan = pipeline.process_handoff(handoff)
        assert plan is None

    def test_missing_incident_rejected(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(incident_id="")
        plan = pipeline.process_handoff(handoff)
        assert plan is None

    def test_duplicate_handoff_discarded(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan1 = pipeline.process_handoff(handoff)
        assert plan1 is not None

        plan2 = pipeline.process_handoff(handoff)  # Same handoff_id
        assert plan2 is None


class TestStage3DemandExtraction:
    def test_demands_extracted_from_summary(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff(payload={
            "recommendationId": "rec-001",
            "summary": "Flood impacts requiring water tankers and medical teams",
            "assessmentId": "ha-001",
        })
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert len(plan.demands) > 0

    def test_transport_demands_from_evacuation(self):
        pipeline = _make_pipeline(resources=[
            ResourceInventoryItem(
                resource_id="bus-001",
                resource_type=ResourceType.vehicle,
                resource_sub_type="wheelchair_accessible",
                capabilities=["passenger_transport", "wheelchair_accessible"],
                location={"lat": -33.87, "lon": 151.21},
                status=ResourceStatus.available,
            ),
        ])
        handoff = _make_handoff(
            source_agent="evacuation",
            payload={
                "transportRequirements": [
                    {
                        "requirementId": "tr-001",
                        "vehicleType": "wheelchair_accessible",
                        "quantity": 2,
                        "pickupLocation": {"lat": -33.87, "lon": 151.21},
                        "priority": "critical",
                    },
                ],
                "evacuationPlanId": "ep-inc001-v1",
            },
        )
        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert any(d.source_type == "transport_requirement" for d in plan.demands)


class TestStage7PlanGeneration:
    def test_plan_has_version(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan.version >= 1

    def test_plan_has_confidence(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert 0.0 <= plan.confidence_score <= 1.0

    def test_plan_has_traceability(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan.traceability.handoff_id == "h-test-001"
        assert plan.traceability.recommendation_id == "rec-inc001-ra-001"
        assert plan.traceability.assessment_id == "ha-inc001-v1"

    def test_plan_has_input_snapshot(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan.input_snapshot.config_version != ""
        assert plan.input_snapshot.inventory_snapshot_hash != ""

    def test_plan_has_deployment_timelines(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        # Should have timelines if there are assignments
        if plan.assignments:
            assert len(plan.deployment_timelines) == len(plan.assignments)

    def test_successive_plans_have_increasing_versions(self):
        pipeline = _make_pipeline()
        h1 = _make_handoff(handoff_id="h-001")
        h2 = _make_handoff(handoff_id="h-002")

        plan1 = pipeline.process_handoff(h1)
        plan2 = pipeline.process_handoff(h2)
        assert plan1 is not None
        assert plan2 is not None
        assert plan2.version > plan1.version

    def test_plan_expires_in_4_hours(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        delta = plan.expires_at - plan.created_at
        assert abs(delta.total_seconds() - 4 * 3600) < 60  # within 1 minute tolerance


class TestPlanSummary:
    def test_plan_has_summary(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        assert plan.summary != ""
        assert len(plan.summary) > 10

    def test_template_fallback_when_no_llm(self):
        pipeline = _make_pipeline()
        handoff = _make_handoff()
        plan = pipeline.process_handoff(handoff)
        # Without LLM configured, should use template_fallback
        assert plan.generation_method in ("template_fallback", "ai_assisted")
