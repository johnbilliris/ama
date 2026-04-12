"""Contract tests for handoff intake structure.

Verifies AgentHandoffEvent schema validation for both risk_assessment and evacuation sources.
"""

from __future__ import annotations

from common.handoffs import AgentHandoffEvent


class TestHandoffIntakeSchema:
    """Verify inbound handoff event schema per contracts/allocation-pipeline.md."""

    def test_risk_assessment_handoff_schema(self):
        handoff = AgentHandoffEvent(
            handoff_id="h-001",
            incident_id="inc001",
            source_agent="risk_assessment",
            target_agent="resource_allocation",
            scope_key="live:inc001",
            confidence=0.85,
            payload={
                "recommendationId": "rec-inc001-ra-001",
                "summary": "Flood impacts requiring water tankers",
                "assessmentId": "ha-inc001-v1",
            },
            tenant_id="live",
        )
        assert handoff.source_agent == "risk_assessment"
        assert handoff.target_agent == "resource_allocation"
        assert handoff.payload["recommendationId"] == "rec-inc001-ra-001"
        assert handoff.payload["summary"] != ""
        assert handoff.payload["assessmentId"] == "ha-inc001-v1"

    def test_evacuation_handoff_schema(self):
        handoff = AgentHandoffEvent(
            handoff_id="h-002",
            incident_id="inc001",
            source_agent="evacuation",
            target_agent="resource_allocation",
            scope_key="live:inc001",
            confidence=0.80,
            payload={
                "transportRequirements": [
                    {
                        "requirementId": "tr-001",
                        "vehicleType": "wheelchair_accessible",
                        "quantity": 4,
                        "pickupLocation": {"lat": -27.4698, "lon": 153.0251},
                        "priority": "critical",
                    },
                ],
                "evacuationPlanId": "ep-inc001-v3",
            },
            tenant_id="live",
        )
        assert handoff.source_agent == "evacuation"
        reqs = handoff.payload["transportRequirements"]
        assert len(reqs) == 1
        assert reqs[0]["vehicleType"] == "wheelchair_accessible"
        assert handoff.payload["evacuationPlanId"] == "ep-inc001-v3"

    def test_tenant_id_propagation(self):
        handoff = AgentHandoffEvent(
            handoff_id="h-003",
            incident_id="inc001",
            source_agent="risk_assessment",
            target_agent="resource_allocation",
            scope_key="sim-123:inc001",
            confidence=0.90,
            payload={"recommendationId": "rec-001", "summary": "test", "assessmentId": "ha-001"},
            tenant_id="sim-123",
        )
        assert handoff.tenant_id == "sim-123"

    def test_default_tenant_is_live(self):
        handoff = AgentHandoffEvent(
            handoff_id="h-004",
            incident_id="inc001",
            source_agent="risk_assessment",
            target_agent="resource_allocation",
            scope_key="live:inc001",
            confidence=0.90,
            payload={"recommendationId": "r1", "summary": "s", "assessmentId": "a1"},
        )
        assert handoff.tenant_id == "live"
