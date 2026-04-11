"""Integration tests for evacuation Service Bus message handling (T055).

Uses mocks — does not require actual Azure Service Bus connection.
"""

import json

import pytest

from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.models import EvacuationPlan
from evacuation.pipeline import EvacuationProcessingPipeline
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


# ---------------------------------------------------------------------------
# Mock Service Bus message
# ---------------------------------------------------------------------------


class MockServiceBusMessage:
    """Simulates an Azure Service Bus message."""

    def __init__(self, body: dict):
        self._body = json.dumps(body)

    def __str__(self):
        return self._body


class MockServiceBusReceiver:
    """Simulates a Service Bus receiver with a list of messages."""

    def __init__(self, messages: list[MockServiceBusMessage]):
        self._messages = messages
        self._completed = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __iter__(self):
        return iter(self._messages)

    def complete_message(self, msg):
        self._completed.append(msg)


# ---------------------------------------------------------------------------
# Message deserialisation
# ---------------------------------------------------------------------------


class TestMessageDeserialisation:
    def test_valid_handoff_from_message(self):
        """Deserialise a Service Bus message body into AgentHandoffEvent."""
        payload = {
            "handoff_id": "hf-sb-001",
            "incident_id": "inc-sb-001",
            "source_agent": "risk_assessment",
            "target_agent": "evacuation",
            "scope_key": "live:inc-sb-001",
            "confidence": 0.85,
            "payload": {
                "assessmentId": "assess-sb",
                "recommendationId": "rec-sb",
                "hazard_type": "bushfire",
            },
        }
        msg = MockServiceBusMessage(payload)
        body = str(msg)
        data = json.loads(body)
        handoff = AgentHandoffEvent.model_validate(data)

        assert handoff.handoff_id == "hf-sb-001"
        assert handoff.source_agent == "risk_assessment"
        assert handoff.target_agent == "evacuation"

    def test_invalid_message_raises(self):
        """Malformed message should raise validation error."""
        msg = MockServiceBusMessage({"bad": "data"})
        body = str(msg)
        data = json.loads(body)
        with pytest.raises(Exception):
            AgentHandoffEvent.model_validate(data)


# ---------------------------------------------------------------------------
# End-to-end message handling
# ---------------------------------------------------------------------------


class TestEndToEndMessageHandling:
    def test_process_message_produces_plan(self):
        """Process a handoff event from a Service Bus message through the pipeline."""
        road_network = RoadNetworkLoader()
        road_network.load(SAMPLE_FILE)

        pipeline = EvacuationProcessingPipeline(
            config=EvacuationConfig(),
            road_network=road_network,
        )

        payload = {
            "handoff_id": "hf-sb-e2e",
            "incident_id": "inc-sb-e2e",
            "source_agent": "risk_assessment",
            "target_agent": "evacuation",
            "scope_key": "live:inc-sb-e2e",
            "confidence": 0.80,
            "payload": {
                "assessmentId": "assess-sb-e2e",
                "recommendationId": "rec-sb-e2e",
                "hazard_type": "cyclone",
                "severity_level": "high",
                "affected_area": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [145.75, -16.95],
                            [145.80, -16.95],
                            [145.80, -16.90],
                            [145.75, -16.90],
                            [145.75, -16.95],
                        ]
                    ],
                },
                "population_estimate": 5000,
            },
        }

        msg = MockServiceBusMessage(payload)
        body = str(msg)
        data = json.loads(body)
        handoff = AgentHandoffEvent.model_validate(data)

        plan = pipeline.process_handoff(handoff)
        assert plan is not None
        assert isinstance(plan, EvacuationPlan)
        assert plan.incident_id == "inc-sb-e2e"

    def test_duplicate_message_discarded(self):
        """Duplicate messages should be discarded by the dedup logic."""
        road_network = RoadNetworkLoader()
        road_network.load(SAMPLE_FILE)

        pipeline = EvacuationProcessingPipeline(
            config=EvacuationConfig(),
            road_network=road_network,
        )

        payload = {
            "handoff_id": "hf-sb-dup",
            "incident_id": "inc-sb-dup",
            "source_agent": "risk_assessment",
            "target_agent": "evacuation",
            "scope_key": "live:inc-sb-dup",
            "confidence": 0.80,
            "payload": {"hazard_type": "flood"},
        }

        handoff = AgentHandoffEvent.model_validate(payload)
        plan1 = pipeline.process_handoff(handoff)
        plan2 = pipeline.process_handoff(handoff)  # Same handoff_id

        assert plan1 is not None
        assert plan2 is None  # Duplicate discarded


# ---------------------------------------------------------------------------
# Receiver mock simulation
# ---------------------------------------------------------------------------


class TestReceiverSimulation:
    def test_receiver_processes_multiple_messages(self):
        """Simulate processing multiple messages from a receiver."""
        road_network = RoadNetworkLoader()
        road_network.load(SAMPLE_FILE)

        pipeline = EvacuationProcessingPipeline(
            config=EvacuationConfig(),
            road_network=road_network,
        )

        messages = []
        for i in range(3):
            payload = {
                "handoff_id": f"hf-sb-batch-{i}",
                "incident_id": f"inc-sb-batch-{i}",
                "source_agent": "risk_assessment",
                "target_agent": "evacuation",
                "scope_key": f"live:inc-sb-batch-{i}",
                "confidence": 0.80,
                "payload": {"hazard_type": "bushfire"},
            }
            messages.append(MockServiceBusMessage(payload))

        receiver = MockServiceBusReceiver(messages)
        plans = []

        with receiver:
            for msg in receiver:
                body = str(msg)
                data = json.loads(body)
                handoff = AgentHandoffEvent.model_validate(data)
                plan = pipeline.process_handoff(handoff)
                if plan:
                    plans.append(plan)
                    receiver.complete_message(msg)

        assert len(plans) == 3
        assert len(receiver._completed) == 3
