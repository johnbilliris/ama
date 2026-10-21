"""Integration tests for evacuation Service Bus message handling (T055).

Uses mocks — does not require actual Azure Service Bus connection.
"""

import json
import threading
from datetime import UTC, datetime, timedelta

import pytest
from common.handoffs import AgentHandoffEvent
from evacuation.agent import EvacuationAgent, run_consumer
from evacuation.config import EvacuationConfig
from evacuation.models import DecisionType, EvacuationPlan
from evacuation.pipeline import EvacuationProcessingPipeline, TransientHandoffDependencyError
from evacuation.road_network import RoadNetworkLoader

SAMPLE_FILE = "data/road-networks/far-north-qld-sample.json"


# ---------------------------------------------------------------------------
# Mock Service Bus message
# ---------------------------------------------------------------------------


class MockServiceBusMessage:
    """Simulates an Azure Service Bus message."""

    def __init__(self, body, *, delivery_count=1, message_id="message-1"):
        self._body = json.dumps(body) if isinstance(body, dict) else body
        self.delivery_count = delivery_count
        self.message_id = message_id

    def __str__(self):
        return self._body


class MockServiceBusReceiver:
    """Simulates a Service Bus receiver with a list of messages."""

    def __init__(self, messages: list[MockServiceBusMessage]):
        self._messages = messages
        self._completed = []
        self._dead_lettered = []
        self._abandoned = []
        self.complete_error = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __iter__(self):
        return iter(self._messages)

    def complete_message(self, msg):
        if self.complete_error is not None:
            raise self.complete_error
        self._completed.append(msg)

    def dead_letter_message(self, msg, reason):
        self._dead_lettered.append((msg, reason))

    def abandon_message(self, msg):
        self._abandoned.append(msg)


def _run_consumer_once(agent, message, *, receiver=None, lock_renewer=None):
    stop_event = threading.Event()

    class Receiver(MockServiceBusReceiver):
        def receive_messages(self, max_message_count, max_wait_time):
            del max_message_count, max_wait_time
            if self._messages:
                messages = list(self._messages)
                self._messages.clear()
                stop_event.set()
                return messages
            return []

    active_receiver = receiver or Receiver([message])
    if receiver is not None:
        receiver._messages = [message]
        receiver.receive_messages = Receiver.receive_messages.__get__(receiver)

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get_queue_receiver(self, queue_name):
            assert queue_name == "evacuation-handoffs"
            return active_receiver

    run_consumer(
        agent,
        queue_name="evacuation-handoffs",
        stop_event=stop_event,
        service_bus_client=Client(),
        lock_renewer=lock_renewer,
    )
    return active_receiver


class _Store:
    def __init__(self, documents):
        self.documents = documents

    def read_item(self, item, partition_key):
        document = self.documents[item]
        assert partition_key == document["incident_scope_key"]
        return document


def _make_pipeline(payloads, *, plans_store=None):
    road_network = RoadNetworkLoader()
    road_network.load(SAMPLE_FILE)
    recommendations = {}
    assessments = {}
    generated_at = datetime.now(UTC)
    for payload in payloads:
        incident_id = payload["incident_id"]
        scope_key = payload["scope_key"]
        assessment_id = payload["payload"]["assessmentId"]
        recommendation_id = payload["payload"]["recommendationId"]
        recommendations[recommendation_id] = {
            "recommendation_id": recommendation_id,
            "incident_id": incident_id,
            "type": "evacuation",
            "summary": "Evacuate affected communities",
            "explanation": "Route-risk threshold exceeded",
            "required_approval_level": "incident_commander",
            "assessment_id": assessment_id,
            "confidence_score": payload["confidence"],
            "severity_level": "high",
            "incident_scope_key": scope_key,
            "tenant_id": "live",
        }
        assessments[assessment_id] = {
            "hazard_assessment_id": assessment_id,
            "incident_id": incident_id,
            "assessment_type": "route_risk",
            "input_signal_ids": [f"signal-{incident_id}"],
            "summary": "Hazard threatens evacuation corridors",
            "confidence_level": "high",
            "generated_at": generated_at.isoformat(),
            "valid_until": (generated_at + timedelta(hours=12)).isoformat(),
            "status": "active",
            "incident_scope_key": scope_key,
            "tenant_id": "live",
            "hazard_map": {
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
                "severity_level": "high",
                "hazard_type": payload["payload"].get("hazard_type", "bushfire"),
                "confidence_score": payload["confidence"],
                "time_horizon": "12h",
                "population_estimate": 5000,
            },
        }
    return EvacuationProcessingPipeline(
        config=EvacuationConfig(),
        road_network=road_network,
        cosmos_plans_container=plans_store,
        cosmos_assessments_container=_Store(assessments),
        cosmos_recommendations_container=_Store(recommendations),
    )


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
        pipeline = _make_pipeline([payload])

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
        payload = {
            "handoff_id": "hf-sb-dup",
            "incident_id": "inc-sb-dup",
            "source_agent": "risk_assessment",
            "target_agent": "evacuation",
            "scope_key": "live:inc-sb-dup",
            "confidence": 0.80,
            "payload": {
                "assessmentId": "assess-sb-dup",
                "recommendationId": "rec-sb-dup",
                "hazard_type": "flood",
            },
        }
        pipeline = _make_pipeline([payload])

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
        messages = []
        payloads = []
        for i in range(3):
            payload = {
                "handoff_id": f"hf-sb-batch-{i}",
                "incident_id": f"inc-sb-batch-{i}",
                "source_agent": "risk_assessment",
                "target_agent": "evacuation",
                "scope_key": f"live:inc-sb-batch-{i}",
                "confidence": 0.80,
                "payload": {
                    "assessmentId": f"assess-sb-batch-{i}",
                    "recommendationId": f"rec-sb-batch-{i}",
                    "hazard_type": "bushfire",
                },
            }
            payloads.append(payload)
            messages.append(MockServiceBusMessage(payload))
        pipeline = _make_pipeline(payloads)

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

    def test_real_consumer_delegates_message_and_stops(self):
        payload = {
            "handoff_id": "hf-consumer",
            "incident_id": "inc-consumer",
            "source_agent": "risk_assessment",
            "target_agent": "evacuation",
            "scope_key": "simulation:inc-consumer",
            "tenant_id": "simulation",
            "confidence": 0.8,
            "payload": {
                "assessmentId": "assess-consumer",
                "recommendationId": "rec-consumer",
            },
        }
        message = MockServiceBusMessage(payload)
        stop_event = threading.Event()

        class Receiver(MockServiceBusReceiver):
            def receive_messages(self, max_message_count, max_wait_time):
                del max_message_count, max_wait_time
                if self._messages:
                    messages = list(self._messages)
                    self._messages.clear()
                    stop_event.set()
                    return messages
                return []

        receiver = Receiver([message])

        class Client:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def get_queue_receiver(self, queue_name):
                assert queue_name == "evacuation-handoffs"
                return receiver

        class Agent:
            def __init__(self):
                self.handoffs = []

            def process_handoff(self, handoff):
                self.handoffs.append(handoff)

        agent = Agent()
        run_consumer(
            agent,
            queue_name="evacuation-handoffs",
            stop_event=stop_event,
            service_bus_client=Client(),
        )
        assert [handoff.handoff_id for handoff in agent.handoffs] == ["hf-consumer"]
        assert receiver._completed == [message]
        assert receiver._dead_lettered == []


class TestBrokerSettlement:
    @staticmethod
    def _payload():
        return {
            "handoff_id": "hf-settlement",
            "incident_id": "inc-settlement",
            "source_agent": "risk_assessment",
            "target_agent": "evacuation",
            "scope_key": "simulation:inc-settlement",
            "tenant_id": "simulation",
            "confidence": 0.8,
            "payload": {
                "assessmentId": "assess-settlement",
                "recommendationId": "rec-settlement",
            },
        }

    def test_validated_receipt_records_latency_and_renews_lock(self, monkeypatch):
        latencies = []

        class Histogram:
            def record(self, value, attributes=None):
                latencies.append((value, attributes))

        monkeypatch.setattr("evacuation.agent.tel.handoff_acknowledgement_latency", Histogram())

        class Renewer:
            def __init__(self):
                self.registrations = []

            def register(self, receiver, message, max_lock_renewal_duration):
                self.registrations.append((receiver, message, max_lock_renewal_duration))

        class Agent:
            def process_handoff(self, handoff):
                assert handoff.handoff_id == "hf-settlement"
                return object()

        renewer = Renewer()
        message = MockServiceBusMessage(self._payload())
        receiver = _run_consumer_once(Agent(), message, lock_renewer=renewer)
        assert len(renewer.registrations) == 1
        assert renewer.registrations[0][2] == 300
        assert latencies and latencies[0][0] < 5000
        assert receiver._completed == [message]

    def test_malformed_json_is_audited_and_dead_lettered(self):
        network = RoadNetworkLoader()
        network.load(SAMPLE_FILE)
        agent = EvacuationAgent(road_network=network)
        message = MockServiceBusMessage("{broken", message_id="poison-1")
        receiver = _run_consumer_once(agent, message)
        assert receiver._completed == []
        assert receiver._abandoned == []
        assert receiver._dead_lettered == [(message, "InvalidHandoffPayload")]
        audit = agent._pipeline.audit_writer._buffer[-1].record
        assert audit.handoff_id == "poison-1"
        assert audit.decision_type == DecisionType.handoff_rejected
        assert "Poison handoff payload" in audit.decision_rationale

    def test_lock_renewal_failure_abandons_without_processing(self):
        class Agent:
            calls = 0

            def process_handoff(self, handoff):
                self.calls += 1

        class Renewer:
            def register(self, receiver, message, max_lock_renewal_duration):
                raise TimeoutError("lock renewal unavailable")

        agent = Agent()
        message = MockServiceBusMessage(self._payload())
        receiver = _run_consumer_once(agent, message, lock_renewer=Renewer())
        assert agent.calls == 0
        assert receiver._abandoned == [message]
        assert receiver._completed == []
        assert receiver._dead_lettered == []

    @pytest.mark.parametrize(
        "error",
        [TransientHandoffDependencyError("Cosmos timeout"), TimeoutError("network timeout")],
    )
    def test_transient_failure_is_abandoned_for_redelivery(self, error):
        class Agent:
            def process_handoff(self, handoff):
                raise error

        message = MockServiceBusMessage(self._payload(), delivery_count=1)
        receiver = _run_consumer_once(Agent(), message)
        assert receiver._abandoned == [message]
        assert receiver._completed == []
        assert receiver._dead_lettered == []

    def test_transient_retry_exhaustion_dead_letters(self):
        class Agent:
            def process_handoff(self, handoff):
                raise TransientHandoffDependencyError("Cosmos timeout")

        message = MockServiceBusMessage(self._payload(), delivery_count=3)
        receiver = _run_consumer_once(Agent(), message)
        assert receiver._abandoned == []
        assert receiver._completed == []
        assert receiver._dead_lettered == [(message, "TransientRetriesExhausted")]

    def test_permanent_failure_is_audited_and_dead_lettered(self):
        class Agent:
            def __init__(self):
                self.rejections = []

            def process_handoff(self, handoff):
                raise ValueError("invalid permanent state")

            def record_intake_rejection(self, **kwargs):
                self.rejections.append(kwargs)

        agent = Agent()
        message = MockServiceBusMessage(self._payload())
        receiver = _run_consumer_once(agent, message)
        assert receiver._dead_lettered == [(message, "PermanentProcessingFailure")]
        assert agent.rejections[0]["handoff_id"] == "hf-settlement"
        assert "invalid permanent state" in agent.rejections[0]["reason"]

    def test_duplicate_result_completes_without_a_second_plan(self):
        class Agent:
            def __init__(self):
                self.calls = 0

            def process_handoff(self, handoff):
                self.calls += 1
                return object() if self.calls == 1 else None

        agent = Agent()
        first = MockServiceBusMessage(self._payload(), message_id="delivery-1")
        second = MockServiceBusMessage(self._payload(), message_id="delivery-2")
        first_receiver = _run_consumer_once(agent, first)
        second_receiver = _run_consumer_once(agent, second)
        assert first_receiver._completed == [first]
        assert second_receiver._completed == [second]
        assert agent.calls == 2

    def test_completion_connection_loss_leaves_message_for_redelivery(self):
        class Agent:
            def process_handoff(self, handoff):
                return object()

        message = MockServiceBusMessage(self._payload())
        receiver = MockServiceBusReceiver([message])
        receiver.complete_error = ConnectionError("settlement response lost")
        _run_consumer_once(Agent(), message, receiver=receiver)
        assert receiver._completed == []
        assert receiver._abandoned == []
        assert receiver._dead_lettered == []

    def test_lost_completion_response_recovers_on_fresh_replica(self):
        from tests.unit.test_evacuation_dedup import _DurableClaimStore

        payload = self._payload()
        payload["tenant_id"] = "live"
        payload["scope_key"] = "live:inc-settlement"
        plans = _DurableClaimStore()
        first_pipeline = _make_pipeline([payload], plans_store=plans)
        second_pipeline = _make_pipeline([payload], plans_store=plans)

        class Agent:
            def __init__(self, pipeline):
                self.pipeline = pipeline

            def process_handoff(self, handoff):
                return self.pipeline.process_handoff(handoff)

            def release_handoff_claim(self, handoff, reason):
                self.pipeline._release_handoff_claim(
                    handoff,
                    f"{handoff.tenant_id}:{handoff.incident_id}",
                    reason,
                )

        first_message = MockServiceBusMessage(payload, message_id="delivery-1")
        failed_receiver = MockServiceBusReceiver([first_message])
        failed_receiver.complete_error = ConnectionError("settlement response lost")
        _run_consumer_once(Agent(first_pipeline), first_message, receiver=failed_receiver)
        assert failed_receiver._completed == []

        replay_message = MockServiceBusMessage(payload, delivery_count=2, message_id="delivery-2")
        replay_receiver = _run_consumer_once(Agent(second_pipeline), replay_message)
        assert replay_receiver._completed == [replay_message]
        persisted_plans = [
            document for document in plans.documents.values() if document.get("id", "").startswith("ep-")
        ]
        assert len(persisted_plans) == 1
        assert persisted_plans[0]["version"] == 1


class TestBrokerReconnect:
    def test_receive_connection_loss_reconnects_and_processes(self):
        payload = TestBrokerSettlement._payload()
        message = MockServiceBusMessage(payload)
        stop_event = threading.Event()

        class FailingReceiver(MockServiceBusReceiver):
            def receive_messages(self, max_message_count, max_wait_time):
                del max_message_count, max_wait_time
                raise ConnectionError("broker disconnected")

        class RecoveryReceiver(MockServiceBusReceiver):
            def receive_messages(self, max_message_count, max_wait_time):
                del max_message_count, max_wait_time
                messages = list(self._messages)
                self._messages.clear()
                stop_event.set()
                return messages

        failing = FailingReceiver([])
        recovery = RecoveryReceiver([message])

        class Client:
            def __init__(self):
                self.receiver_count = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def get_queue_receiver(self, queue_name):
                self.receiver_count += 1
                return failing if self.receiver_count == 1 else recovery

        class Agent:
            def __init__(self):
                self.handoffs = []

            def process_handoff(self, handoff):
                self.handoffs.append(handoff)

        client = Client()
        agent = Agent()
        run_consumer(
            agent,
            stop_event=stop_event,
            service_bus_client=client,
            reconnect_delay_seconds=0,
        )
        assert client.receiver_count == 2
        assert [handoff.handoff_id for handoff in agent.handoffs] == ["hf-settlement"]
        assert recovery._completed == [message]

    def test_stop_during_connection_loss_cancels_reconnect(self):
        stop_event = threading.Event()

        class Receiver(MockServiceBusReceiver):
            def receive_messages(self, max_message_count, max_wait_time):
                del max_message_count, max_wait_time
                stop_event.set()
                raise ConnectionError("broker disconnected")

        receiver = Receiver([])

        class Client:
            calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def get_queue_receiver(self, queue_name):
                self.calls += 1
                return receiver

        client = Client()
        run_consumer(
            object(),
            stop_event=stop_event,
            service_bus_client=client,
            reconnect_delay_seconds=0,
        )
        assert client.calls == 1

    def test_reconnect_budget_is_bounded(self):
        class Receiver(MockServiceBusReceiver):
            def receive_messages(self, max_message_count, max_wait_time):
                del max_message_count, max_wait_time
                raise ConnectionError("broker disconnected")

        receiver = Receiver([])

        class Client:
            calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def get_queue_receiver(self, queue_name):
                self.calls += 1
                return receiver

        class Agent:
            def __init__(self):
                self.states = []
                self.depth = 0

            def update_queue_health(self, **values):
                self.states.append(values["status"])

            def change_queue_depth(self, delta):
                self.depth += delta

        client = Client()
        agent = Agent()
        run_consumer(
            agent,
            service_bus_client=client,
            max_reconnect_attempts=3,
            reconnect_delay_seconds=0,
        )
        assert client.calls == 3
        assert agent.states[-1] == "offline"
        assert "reconnecting" in agent.states
        assert agent.depth == 0
