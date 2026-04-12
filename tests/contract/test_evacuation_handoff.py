"""Contract tests for evacuation handoff — AgentHandoffEvent validation (T022)."""

import pytest
from common.handoffs import AgentHandoffEvent, build_handoff

# ---------------------------------------------------------------------------
# Valid AgentHandoffEvent
# ---------------------------------------------------------------------------


class TestValidHandoffContract:
    def test_valid_handoff_construction(self):
        handoff = AgentHandoffEvent(
            handoff_id="hf-001",
            incident_id="inc-001",
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key="live:inc-001",
            confidence=0.85,
            payload={
                "recommendationId": "rec-001",
                "assessmentId": "assess-001",
            },
        )
        assert handoff.source_agent == "risk_assessment"
        assert handoff.target_agent == "evacuation"
        assert handoff.confidence == 0.85

    def test_build_handoff_helper(self):
        handoff = build_handoff(
            incident_id="inc-002",
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key="live:inc-002",
            payload={
                "recommendationId": "rec-002",
                "assessmentId": "assess-002",
            },
            confidence=0.9,
        )
        assert handoff.handoff_id.startswith("handoff-")
        assert handoff.source_agent == "risk_assessment"
        assert handoff.target_agent == "evacuation"
        assert handoff.status == "pending"

    def test_handoff_has_timestamps(self):
        handoff = AgentHandoffEvent(
            handoff_id="hf-003",
            incident_id="inc-003",
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key="live:inc-003",
            confidence=0.7,
            payload={},
        )
        assert handoff.created_at is not None
        assert handoff.tenant_id == "live"


# ---------------------------------------------------------------------------
# Required payload fields
# ---------------------------------------------------------------------------


class TestRequiredPayloadFields:
    def test_payload_with_recommendation_id(self):
        handoff = AgentHandoffEvent(
            handoff_id="hf-004",
            incident_id="inc-004",
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key="live:inc-004",
            confidence=0.85,
            payload={
                "recommendationId": "rec-004",
                "assessmentId": "assess-004",
            },
        )
        assert "recommendationId" in handoff.payload
        assert "assessmentId" in handoff.payload

    def test_payload_can_include_hazard_data(self):
        handoff = AgentHandoffEvent(
            handoff_id="hf-005",
            incident_id="inc-005",
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key="live:inc-005",
            confidence=0.85,
            payload={
                "recommendationId": "rec-005",
                "assessmentId": "assess-005",
                "hazard_type": "cyclone",
                "severity_level": "high",
                "affected_area": {
                    "type": "Polygon",
                    "coordinates": [
                        [[145.75, -16.95], [145.80, -16.95],
                         [145.80, -16.90], [145.75, -16.90],
                         [145.75, -16.95]]
                    ],
                },
            },
        )
        assert handoff.payload["hazard_type"] == "cyclone"


# ---------------------------------------------------------------------------
# Rejection of malformed handoffs
# ---------------------------------------------------------------------------


class TestMalformedHandoffRejection:
    def test_missing_handoff_id_raises(self):
        with pytest.raises(Exception):
            AgentHandoffEvent(
                incident_id="inc-006",
                source_agent="risk_assessment",
                target_agent="evacuation",
                scope_key="live:inc-006",
                confidence=0.85,
                payload={},
            )

    def test_missing_incident_id_raises(self):
        with pytest.raises(Exception):
            AgentHandoffEvent(
                handoff_id="hf-007",
                source_agent="risk_assessment",
                target_agent="evacuation",
                scope_key="live:",
                confidence=0.85,
                payload={},
            )

    def test_missing_source_agent_raises(self):
        with pytest.raises(Exception):
            AgentHandoffEvent(
                handoff_id="hf-008",
                incident_id="inc-008",
                target_agent="evacuation",
                scope_key="live:inc-008",
                confidence=0.85,
                payload={},
            )

    def test_missing_target_agent_raises(self):
        with pytest.raises(Exception):
            AgentHandoffEvent(
                handoff_id="hf-009",
                incident_id="inc-009",
                source_agent="risk_assessment",
                scope_key="live:inc-009",
                confidence=0.85,
                payload={},
            )

    def test_wrong_target_agent_still_constructs(self):
        """HandoffEvent itself doesn't validate target_agent value —
        that's the pipeline's job."""
        handoff = AgentHandoffEvent(
            handoff_id="hf-010",
            incident_id="inc-010",
            source_agent="risk_assessment",
            target_agent="wrong_agent",
            scope_key="live:inc-010",
            confidence=0.85,
            payload={},
        )
        assert handoff.target_agent == "wrong_agent"
