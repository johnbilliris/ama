"""Pipeline processing benchmarks for all five agents.

Each agent's pipeline is instantiated with mocked external
dependencies (no live Azure services) and driven through its
primary entry point (``process_handoff`` or ``process_signal``).
"""

from __future__ import annotations

import asyncio
import itertools
from unittest.mock import MagicMock

import pytest
from benchmark_helpers import set_benchmark_metadata
from common.handoffs import AgentHandoffEvent


async def _async_noop(h):
    pass


# ── Sample data factories ────────────────────────────────────────────────────


def _make_signal() -> dict:
    """Minimal valid monitoring signal dict."""
    return {
        "source": {"dataSourceId": "bom-nsw", "name": "BoM NSW", "kind": "authoritative"},
        "incidentId": "INC-BENCH-001",
        "category": "fire",
        "occurredAt": "2026-01-01T00:00:00Z",
        "receivedAt": "2026-01-01T00:00:01Z",
        "location": {"type": "Point", "coordinates": [151.2, -33.8]},
        "payload": {"alert_level": "Watch and Act"},
        "confidenceScore": 0.85,
        "freshnessScore": 1.0,
        "validationStatus": "validated",
        "provenance": {"collectionMethod": "api_pull"},
    }


def _make_handoff(
    source: str = "monitoring",
    target: str = "risk_assessment",
    incident_id: str = "INC-BENCH-001",
) -> AgentHandoffEvent:
    """Minimal valid handoff event for pipeline benchmarks."""
    return AgentHandoffEvent(
        handoff_id="bench-handoff-001",
        incident_id=incident_id,
        source_agent=source,
        target_agent=target,
        scope_key=f"live:{incident_id}",
        confidence=0.85,
        payload={
            "category": "fire",
            "sourceKind": "authoritative",
            "signalSummary": {
                "category": "fire",
                "sourceKind": "authoritative",
                "signal_ids": [],
            },
            "hazard_type": "bushfire",
            "severity_level": "high",
            "severity": "high",
            "alert_type": "warning",
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
            "population_estimate": 1000,
            "assessmentId": "assess-bench-001",
            "recommendationId": "rec-bench-001",
            "summary": "Benchmark test handoff",
            "location": {"type": "Point", "coordinates": [151.2, -33.8]},
            "assessment_id": "assess-bench-001",
            "recommendation_id": "rec-bench-001",
        },
        tenant_id="live",
    )


# ── Pipeline fixtures ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def monitoring_pipeline():
    """Monitoring pipeline with mocked dependencies."""
    from monitoring.audit import AuditWriter
    from monitoring.config import MonitoringConfig
    from monitoring.pipeline import SignalProcessingPipeline

    config = MonitoringConfig()
    return SignalProcessingPipeline(
        config=config,
        audit_writer=AuditWriter(config=config, cosmos_client=None),
        deliver_fn=_async_noop,
    )


@pytest.fixture(scope="session")
def risk_pipeline():
    """Risk assessment pipeline with mocked dependencies."""
    from risk_assessment.audit import AuditWriter
    from risk_assessment.config import RiskAssessmentConfig
    from risk_assessment.pipeline import AssessmentProcessingPipeline

    config = RiskAssessmentConfig()
    return AssessmentProcessingPipeline(
        config=config,
        audit_writer=AuditWriter(config=config, cosmos_client=None),
        deliver_fn=_async_noop,
    )


@pytest.fixture(scope="session")
def evacuation_pipeline():
    """Evacuation pipeline with mocked dependencies and sample road network."""
    from evacuation.config import EvacuationConfig
    from evacuation.pipeline import EvacuationProcessingPipeline
    from evacuation.road_network import RoadNetworkLoader

    config = EvacuationConfig()
    road_network = RoadNetworkLoader()
    road_network.load("data/road-networks/far-north-qld-sample.json")
    return EvacuationProcessingPipeline(
        config=config,
        road_network=road_network,
        cosmos_plans_container=None,
        cosmos_decisions_container=None,
        cosmos_assessments_container=None,
    )


@pytest.fixture(scope="session")
def resource_pipeline():
    """Resource allocation pipeline with mocked dependencies."""
    from resource_allocation.audit import AuditWriter
    from resource_allocation.config import ResourceAllocationConfig
    from resource_allocation.dedup import HandoffDeduplicator
    from resource_allocation.inventory import ResourceInventoryManager
    from resource_allocation.matcher import ResourceMatcher
    from resource_allocation.pipeline import AllocationProcessingPipeline
    from resource_allocation.versioning import VersionCounter

    config = ResourceAllocationConfig()
    return AllocationProcessingPipeline(
        config=config,
        dedup=HandoffDeduplicator(window_minutes=10),
        inventory=ResourceInventoryManager(config=config),
        matcher=ResourceMatcher(config=config),
        version_counter=VersionCounter(),
        audit_writer=AuditWriter(config=config),
    )


@pytest.fixture(scope="session")
def communication_pipeline():
    """Communication pipeline with mocked translator."""
    from communication.approval import ApprovalWorkflow
    from communication.audit import AuditWriter
    from communication.config import CommunicationConfig
    from communication.dedup import HandoffDeduplicator
    from communication.models import ContentBlock, GenerationMethod
    from communication.pipeline import CommunicationProcessingPipeline
    from communication.repository import CommunicationAlertRepository
    from communication.translator import MultilingualTranslator
    from communication.versioning import VersionCounter

    config = CommunicationConfig()
    repository = CommunicationAlertRepository()
    translator = MagicMock(spec=MultilingualTranslator)
    translator.translate_all.return_value = {
        language: ContentBlock(
            language_code=language,
            title="Emergency warning",
            body="Bushfire at the benchmark location",
            action_items="Follow emergency instructions",
            generation_method=GenerationMethod.template,
        )
        for language in config.supported_languages
    }
    translator.back_translate_and_score.return_value = None

    class _Store:
        def __init__(self, kind: str):
            self.kind = kind

        def read_item(self, item, partition_key):
            incident_id = str(partition_key).removeprefix("live:")
            if self.kind == "incident":
                return {"id": item, "tenant_id": "live", "commander_chain": ["benchmark-commander"]}
            if self.kind == "recommendation":
                return {"id": item, "incident_id": incident_id, "tenant_id": "live"}
            return {
                "id": item,
                "incident_id": incident_id,
                "tenant_id": "live",
                "hazard_type": "bushfire",
                "severity": "high",
                "location": "Benchmark area",
                "zones": [{"id": "benchmark-zone", "level": 1, "population_estimate": 1000}],
            }

    class _Publisher:
        async def publish(self, payload):
            return None

    approval = ApprovalWorkflow(service_bus_client=_Publisher(), alert_repository=repository)
    return CommunicationProcessingPipeline(
        config=config,
        deduplicator=HandoffDeduplicator(window_minutes=30),
        translator=translator,
        version_counter=VersionCounter(config=config),
        audit_writer=AuditWriter(config=config),
        incident_store=_Store("incident"),
        recommendation_store=_Store("recommendation"),
        assessment_store=_Store("assessment"),
        alert_repository=repository,
        approval_workflow=approval,
    )


# ── Benchmark tests ──────────────────────────────────────────────────────────


@pytest.mark.benchmark(group="pipeline")
def test_pipeline_monitoring(benchmark, monitoring_pipeline) -> None:
    set_benchmark_metadata(benchmark, agent="monitoring", metric_type="pipeline", slo_target_s=2.0)
    sample = _make_signal()
    benchmark(lambda: asyncio.run(monitoring_pipeline.process_signal(sample, signal_id="bench-001")))


@pytest.mark.benchmark(group="pipeline")
def test_pipeline_risk(benchmark, risk_pipeline) -> None:
    set_benchmark_metadata(benchmark, agent="risk", metric_type="pipeline", slo_target_s=2.0)
    handoff = _make_handoff(source="monitoring", target="risk_assessment")
    benchmark(risk_pipeline.process_handoff, handoff)


@pytest.mark.benchmark(group="pipeline")
def test_pipeline_evacuation(benchmark, evacuation_pipeline) -> None:
    set_benchmark_metadata(benchmark, agent="evacuation", metric_type="pipeline", slo_target_s=2.0)
    handoff = _make_handoff(source="risk_assessment", target="evacuation")
    benchmark(evacuation_pipeline.process_handoff, handoff)


@pytest.mark.benchmark(group="pipeline")
def test_pipeline_resource(benchmark, resource_pipeline) -> None:
    set_benchmark_metadata(benchmark, agent="resource", metric_type="pipeline", slo_target_s=2.0)
    handoff = _make_handoff(source="risk_assessment", target="resource_allocation")
    benchmark(resource_pipeline.process_handoff, handoff)


@pytest.mark.benchmark(group="pipeline")
def test_pipeline_communication(benchmark, communication_pipeline) -> None:
    set_benchmark_metadata(benchmark, agent="communication", metric_type="pipeline", slo_target_s=2.0)
    sequence = itertools.count(1)

    def run_once():
        index = next(sequence)
        incident_id = f"INC-BENCH-{index:06d}"
        handoff = _make_handoff(source="risk_assessment", target="communication", incident_id=incident_id)
        handoff.handoff_id = f"benchmark-handoff-{index:06d}"
        handoff.payload["recommendationId"] = f"recommendation-{index:06d}"
        handoff.payload["assessmentId"] = f"assessment-{index:06d}"
        handoff.payload["explanation"] = "Benchmark warning rationale"
        alert = communication_pipeline.process_handoff(handoff)
        assert alert is not None
        assert len(alert.content_blocks) == 6
        return alert

    benchmark(run_once)
