"""Contract tests — handoff event acceptance from upstream agents."""


import pytest
from common.handoffs import AgentHandoffEvent, build_handoff


class TestHandoffContract:
    """Verify handoff events match the communication agent's intake contract."""

    def _make_handoff(self, **overrides) -> AgentHandoffEvent:
        defaults = {
            "handoff_id": "handoff-test-001",
            "source_agent": "risk_assessment",
            "target_agent": "communication",
            "incident_id": "INC-2025-001",
            "scope_key": "INC-2025-001",
            "confidence": 0.95,
            "payload": {
                "hazard_type": "cyclone",
                "urgency": "immediate",
                "affected_zones": [{"zone_id": "z1", "zone_level": 1, "population": 500}],
                "severity": "extreme",
                "summary": "Category 5 cyclone approaching",
            },
        }
        defaults.update(overrides)
        return AgentHandoffEvent(**defaults)

    def test_valid_handoff_from_risk_assessment(self):
        event = self._make_handoff()
        assert event.target_agent == "communication"
        assert event.source_agent == "risk_assessment"

    def test_valid_handoff_from_evacuation(self):
        event = self._make_handoff(source_agent="evacuation")
        assert event.source_agent == "evacuation"

    def test_handoff_contains_incident_id(self):
        event = self._make_handoff()
        assert event.incident_id == "INC-2025-001"

    def test_handoff_payload_has_hazard_type(self):
        event = self._make_handoff()
        assert event.payload["hazard_type"] == "cyclone"

    def test_handoff_payload_has_affected_zones(self):
        event = self._make_handoff()
        zones = event.payload["affected_zones"]
        assert len(zones) >= 1
        assert zones[0]["zone_id"] == "z1"

    def test_handoff_payload_has_urgency(self):
        event = self._make_handoff()
        assert event.payload["urgency"] == "immediate"

    def test_missing_target_agent_rejected(self):
        """AgentHandoffEvent requires target_agent — omitting it raises ValidationError."""
        with pytest.raises(Exception):
            AgentHandoffEvent(
                handoff_id="handoff-bad-001",
                source_agent="risk_assessment",
                incident_id="INC-2025-001",
                scope_key="INC-2025-001",
                confidence=0.9,
                payload={"hazard_type": "cyclone"},
                # target_agent intentionally omitted
            )

    def test_build_handoff_produces_valid_structure(self):
        event = build_handoff(
            source_agent="risk_assessment",
            target_agent="communication",
            incident_id="INC-2025-002",
            scope_key="INC-2025-002",
            confidence=0.9,
            payload={"hazard_type": "bushfire", "urgency": "watch"},
        )
        assert event.target_agent == "communication"
        assert event.incident_id == "INC-2025-002"
        assert event.handoff_id.startswith("handoff-")
