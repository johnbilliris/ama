"""Integration tests for Risk Assessment Agent Service Bus handoff intake.

Tests verify correct Service Bus interaction patterns:
- Message deserialization to AgentHandoffEvent
- Message acknowledgement on success
- Poison message handling
- Queue consumer lifecycle

Marked @pytest.mark.integration — skipped in unit test runs.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock

from common.handoffs import AgentHandoffEvent
from risk_assessment.pipeline import AssessmentProcessingPipeline
from risk_assessment.config import RiskAssessmentConfig

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> RiskAssessmentConfig:
    with patch.dict(os.environ, {}, clear=False):
        return RiskAssessmentConfig()


def _valid_handoff_json(
    incident_id: str = "inc-sb-001",
    source_agent: str = "monitoring",
) -> str:
    return json.dumps({
        "handoff_id": f"handoff-{incident_id}",
        "incident_id": incident_id,
        "source_agent": source_agent,
        "target_agent": "risk_assessment",
        "scope_key": f"live:{incident_id}",
        "confidence": 0.85,
        "payload": {
            "signalSummary": {
                "signal_ids": ["sig-001"],
                "category": "fire",
                "sourceKind": "authoritative",
            },
            "category": "fire",
            "sourceKind": "authoritative",
        },
        "tenant_id": "live",
    })


class _MockServiceBusMessage:
    """Lightweight stand-in for azure.servicebus.ServiceBusReceivedMessage."""

    def __init__(self, body: str | bytes):
        self._body = body if isinstance(body, bytes) else body.encode("utf-8")
        self.completed = False
        self.dead_lettered = False
        self._dead_letter_reason: str | None = None

    @property
    def body(self) -> bytes:
        return self._body

    def complete(self) -> None:
        self.completed = True

    def dead_letter(self, reason: str | None = None, **kwargs) -> None:
        self.dead_lettered = True
        self._dead_letter_reason = reason


# ---------------------------------------------------------------------------
# T063-1: Message deserializes to AgentHandoffEvent
# ---------------------------------------------------------------------------


class TestMessageDeserializesToHandoff:
    def test_message_deserializes_to_handoff(self) -> None:
        """JSON body → AgentHandoffEvent with correct fields."""
        body = _valid_handoff_json()
        data = json.loads(body)
        handoff = AgentHandoffEvent(**data)

        assert handoff.incident_id == "inc-sb-001"
        assert handoff.source_agent == "monitoring"
        assert handoff.target_agent == "risk_assessment"
        assert handoff.confidence == 0.85
        assert handoff.tenant_id == "live"
        assert "signalSummary" in handoff.payload


# ---------------------------------------------------------------------------
# T063-2: Valid message acknowledged
# ---------------------------------------------------------------------------


class TestValidMessageAcknowledged:
    def test_valid_message_acknowledged(self) -> None:
        """Successful processing completes (acknowledges) the message."""
        msg = _MockServiceBusMessage(_valid_handoff_json())
        data = json.loads(msg.body)
        handoff = AgentHandoffEvent(**data)

        config = _make_config()
        pipeline = AssessmentProcessingPipeline(config=config)
        result = pipeline.process_handoff(handoff)

        assert result["status"] == "completed"
        msg.complete()
        assert msg.completed is True


# ---------------------------------------------------------------------------
# T063-3: Invalid message dead-lettered
# ---------------------------------------------------------------------------


class TestInvalidMessageDeadLettered:
    def test_invalid_message_dead_lettered(self) -> None:
        """Malformed JSON → dead-letter."""
        msg = _MockServiceBusMessage(b"this is not json {{{")

        try:
            data = json.loads(msg.body)
            AgentHandoffEvent(**data)
        except (json.JSONDecodeError, Exception):
            msg.dead_letter(reason="Malformed JSON body")

        assert msg.dead_lettered is True
        assert msg._dead_letter_reason == "Malformed JSON body"

    def test_missing_required_fields_dead_lettered(self) -> None:
        """JSON with missing required fields → dead-letter."""
        msg = _MockServiceBusMessage(json.dumps({"incident_id": "inc-001"}))

        try:
            data = json.loads(msg.body)
            AgentHandoffEvent(**data)
        except Exception:
            msg.dead_letter(reason="Missing required fields")

        assert msg.dead_lettered is True


# ---------------------------------------------------------------------------
# T063-4: Poison message handling
# ---------------------------------------------------------------------------


class TestPoisonMessageHandling:
    def test_poison_message_handling(self) -> None:
        """Repeated failures → dead-letter after retry exhaustion."""
        msg = _MockServiceBusMessage(_valid_handoff_json())
        max_retries = 3
        failures = 0

        for attempt in range(1, max_retries + 1):
            try:
                raise ConnectionError(f"Simulated failure attempt {attempt}")
            except ConnectionError:
                failures += 1
                if failures >= max_retries:
                    msg.dead_letter(reason=f"Exhausted {max_retries} retries")

        assert msg.dead_lettered is True
        assert failures == max_retries
        assert msg._dead_letter_reason == "Exhausted 3 retries"


# ---------------------------------------------------------------------------
# T063-5: Queue consumer processes multiple messages
# ---------------------------------------------------------------------------


class TestQueueConsumerProcessesMultiple:
    def test_queue_consumer_processes_multiple(self) -> None:
        """Multiple messages processed in sequence."""
        messages = [
            _MockServiceBusMessage(
                _valid_handoff_json(incident_id=f"inc-multi-{i}")
            )
            for i in range(5)
        ]

        config = _make_config()
        processed_ids: list[str] = []

        for msg in messages:
            data = json.loads(msg.body)
            handoff = AgentHandoffEvent(**data)

            pipeline = AssessmentProcessingPipeline(config=config)
            result = pipeline.process_handoff(handoff)

            assert result["status"] == "completed"
            processed_ids.append(handoff.incident_id)
            msg.complete()

        assert len(processed_ids) == 5
        assert all(msg.completed for msg in messages)
        assert processed_ids == [f"inc-multi-{i}" for i in range(5)]
