"""Tests for the operational Evacuation Agent composition root."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta

import evacuation.runtime as runtime_module
import pytest
from common.handoffs import AgentHandoffEvent
from evacuation.config import EvacuationConfig
from evacuation.runtime import (
    ThreadedDependencyHealthMonitor,
    ThreadedPlanLifecycleSweeper,
    ThreadedServiceBusConsumer,
    build_application,
)
from fastapi.testclient import TestClient


class _Consumer:
    def __init__(self):
        self.started = 0
        self.stopped = 0

    def start(self):
        self.started += 1

    def stop(self):
        self.stopped += 1


class _Container:
    pass


def _containers():
    return {
        "plans": _Container(),
        "decisions": _Container(),
        "assessments": _Container(),
        "recommendations": _Container(),
    }


class TestBuildApplication:
    def test_configures_telemetry_before_composing_runtime(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            runtime_module,
            "configure_telemetry",
            lambda: calls.append("configured") or True,
        )

        build_application(containers={})

        assert calls == ["configured"]

    def test_loads_shipped_graph_reference_data_and_all_stores(self):
        containers = _containers()
        app = build_application(containers=containers)
        agent = app.state.agent
        assert agent._road_network.is_loaded
        assert agent._road_network.node_count == 50
        assert agent._pipeline._cosmos_plans is containers["plans"]
        assert agent._pipeline._cosmos_decisions is containers["decisions"]
        assert agent._pipeline._cosmos_assessments is containers["assessments"]
        assert agent._pipeline._cosmos_recommendations is containers["recommendations"]
        assert agent._pipeline._population_data
        assert len(agent._pipeline._facility_data) == 15

    def test_fastapi_lifespan_starts_and_stops_consumer(self):
        consumer = _Consumer()
        app = build_application(containers={}, consumer=consumer)
        with TestClient(app) as client:
            assert consumer.started == 1
            assert consumer.stopped == 0
            assert client.get("/health").status_code == 200
        assert consumer.stopped == 1

    def test_missing_road_network_starts_in_generic_guidance_mode(self, tmp_path):
        config = EvacuationConfig(road_network_file_path=str(tmp_path / "missing.json"))
        app = build_application(config, containers={})

        assert app.state.agent._road_network.is_loaded is False
        assert app.state.agent._road_network.last_refresh_failed is True

    def test_missing_reference_data_starts_with_unknown_needs(self, tmp_path):
        config = EvacuationConfig(population_data_file_path=str(tmp_path / "missing.json"))
        app = build_application(config, containers={})

        assert app.state.agent._pipeline._population_data_available is False
        assert app.state.agent._pipeline._facility_data_available is False
        assert app.state.reference_data["metadata"]["load_error"]

    def test_production_requires_all_scoped_containers(self):
        config = EvacuationConfig(
            environment="production",
            azure_servicebus_namespace="namespace.servicebus.windows.net",
        )
        with pytest.raises(RuntimeError, match="plans, decisions, assessments, recommendations"):
            build_application(config, containers={})

    def test_production_requires_broker(self):
        config = EvacuationConfig(environment="production")
        with pytest.raises(RuntimeError, match="Service Bus namespace"):
            build_application(config, containers=_containers())

    def test_configured_application_reaches_deterministic_pipeline(self):
        scope_key = "simulation:inc-runtime"
        now = datetime.now(UTC)

        class Store:
            def __init__(self, documents=None):
                self.documents = documents or {}
                self.etag = 0

            def read_item(self, item, partition_key):
                if item not in self.documents:
                    raise RuntimeError("404 NotFound")
                document = self.documents[item]
                assert partition_key == document["incident_scope_key"]
                return document

            def create_item(self, body):
                if body["id"] in self.documents:
                    raise RuntimeError("409 Conflict")
                self.etag += 1
                document = dict(body)
                document["_etag"] = f"etag-{self.etag}"
                self.documents[body["id"]] = document
                return document

            def replace_item(
                self,
                item,
                body,
                etag=None,
                match_condition=None,
                if_match=None,
            ):
                del match_condition
                current = self.documents[item]
                expected = etag or if_match
                if expected != current.get("_etag"):
                    raise RuntimeError("412 PreconditionFailed")
                self.etag += 1
                document = dict(body)
                document["_etag"] = f"etag-{self.etag}"
                self.documents[item] = document
                return document

        recommendation = {
            "recommendation_id": "rec-runtime",
            "incident_id": "inc-runtime",
            "type": "evacuation",
            "summary": "Evacuate the affected area",
            "explanation": "Route risk exceeds threshold",
            "required_approval_level": "incident_commander",
            "assessment_id": "assess-runtime",
            "confidence_score": 0.8,
            "severity_level": "high",
            "incident_scope_key": scope_key,
            "tenant_id": "simulation",
        }
        assessment = {
            "hazard_assessment_id": "assess-runtime",
            "incident_id": "inc-runtime",
            "assessment_type": "route_risk",
            "input_signal_ids": ["signal-runtime"],
            "summary": "Flood threatens local roads",
            "confidence_level": "high",
            "generated_at": now.isoformat(),
            "valid_until": (now + timedelta(hours=12)).isoformat(),
            "status": "active",
            "incident_scope_key": scope_key,
            "tenant_id": "simulation",
            "hazard_map": {
                "affected_area": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [145.73, -16.94],
                            [145.79, -16.94],
                            [145.79, -16.89],
                            [145.73, -16.89],
                            [145.73, -16.94],
                        ]
                    ],
                },
                "severity_level": "high",
                "hazard_type": "flood",
                "confidence_score": 0.8,
                "time_horizon": "12h",
                "population_estimate": 1000,
            },
        }
        plans = Store()
        decisions = Store()
        app = build_application(
            containers={
                "plans": plans,
                "decisions": decisions,
                "assessments": Store({"assess-runtime": assessment}),
                "recommendations": Store({"rec-runtime": recommendation}),
            }
        )
        handoff = AgentHandoffEvent(
            handoff_id="hf-runtime",
            incident_id="inc-runtime",
            source_agent="risk_assessment",
            target_agent="evacuation",
            scope_key=scope_key,
            tenant_id="simulation",
            confidence=0.8,
            payload={
                "assessmentId": "assess-runtime",
                "recommendationId": "rec-runtime",
            },
        )
        plan = app.state.agent.process_handoff(handoff)
        assert plan is not None
        assert plan.zones and plan.phases and plan.zone_dispositions
        assert plans.documents[plan.plan_id]["incident_scope_key"] == scope_key
        assert any(record.get("plan_id") == plan.plan_id for record in decisions.documents.values())

    def test_two_application_replicas_commit_one_plan_for_same_handoff(self):
        from tests.unit.test_evacuation_dedup import _DurableClaimStore
        from tests.unit.test_evacuation_pipeline import _assessment, _make_handoff, _recommendation, _Store

        plans = _DurableClaimStore()

        class Decisions:
            def __init__(self):
                self.documents = []

            def create_item(self, body):
                self.documents.append(body)
                return body

        decisions = Decisions()
        containers = {
            "plans": plans,
            "decisions": decisions,
            "assessments": _Store({"assess-001": _assessment()}),
            "recommendations": _Store({"rec-001": _recommendation()}),
        }
        first_app = build_application(containers=containers)
        second_app = build_application(containers=containers)
        handoff = _make_handoff(handoff_id="hf-replica")

        first_plan = first_app.state.agent.process_handoff(handoff)
        second_plan = second_app.state.agent.process_handoff(handoff)

        assert first_plan is not None
        assert second_plan is None
        persisted_plans = [
            document for document in plans.documents.values() if document.get("id", "").startswith("ep-")
        ]
        assert [document["plan_id"] for document in persisted_plans] == [first_plan.plan_id]
        duplicate_audits = [
            document for document in decisions.documents if document["decision_type"] == "duplicate_discarded"
        ]
        assert len(duplicate_audits) == 1
        assert first_plan.plan_id in duplicate_audits[0]["decision_rationale"]


class TestThreadedConsumerLifecycle:
    def test_start_and_stop_owns_consumer_thread(self):
        started = threading.Event()

        def target(**kwargs):
            started.set()
            kwargs["stop_event"].wait()

        config = EvacuationConfig(
            azure_servicebus_namespace="namespace.servicebus.windows.net",
        )
        consumer = ThreadedServiceBusConsumer(object(), config, target=target)
        consumer.start()
        assert started.wait(timeout=1)
        consumer.stop()
        assert consumer._thread is None


class TestDependencyHealthMonitor:
    def test_slow_probe_is_bounded_and_updates_cached_offline_state(self):
        release = threading.Event()
        probe_finished = threading.Event()

        class Client:
            def generate_response(self, **kwargs):
                del kwargs
                try:
                    release.wait(timeout=2)
                    return {"text": "late"}
                finally:
                    probe_finished.set()

        class Agent:
            _llm_client = Client()

            def __init__(self):
                self.updates = []

            def update_llm_health(self, **values):
                self.updates.append(values)

        agent = Agent()
        monitor = ThreadedDependencyHealthMonitor(
            agent,
            probe_timeout_seconds=0.05,
        )

        started = datetime.now(UTC)
        monitor.probe_once()
        elapsed = (datetime.now(UTC) - started).total_seconds()
        release.set()
        assert probe_finished.wait(timeout=1)
        assert monitor._probe_thread is not None
        monitor._probe_thread.join(timeout=1)

        assert elapsed < 0.2
        assert not monitor._probe_thread.is_alive()
        assert len(agent.updates) == 1
        assert agent.updates[-1]["status"] == "offline"


class TestThreadedConsumerIdempotency:
    def test_start_is_idempotent(self):
        started = threading.Event()

        def target(**kwargs):
            started.set()
            kwargs["stop_event"].wait()

        config = EvacuationConfig(
            azure_servicebus_namespace="namespace.servicebus.windows.net",
        )
        consumer = ThreadedServiceBusConsumer(object(), config, target=target)
        consumer.start()
        assert started.wait(timeout=1)
        thread = consumer._thread
        consumer.start()
        assert consumer._thread is thread
        consumer.stop()


class TestThreadedPlanLifecycleSweeper:
    def test_start_runs_sweep_and_stop_joins_thread(self):
        swept = threading.Event()

        class Agent:
            def expire_all_due_plans(self):
                swept.set()
                return []

        config = EvacuationConfig(plan_lifecycle_sweep_seconds=60)
        sweeper = ThreadedPlanLifecycleSweeper(Agent(), config)
        sweeper.start()
        assert swept.wait(timeout=1)
        sweeper.stop()
        assert sweeper._thread is None
