from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from apps.agents.common.handoffs import AgentHandoffEvent
from packages.domain.src.domain.models.dead_letter_entry import DeadLetterEntry
from packages.domain.src.domain.models.load_test_result import LoadTestResult
from packages.domain.src.domain.models.model_deployment import ModelDeployment


def test_model_deployment_enforces_https_and_budget_bounds() -> None:
    with pytest.raises(ValidationError):
        ModelDeployment(
            deployment_id="dep-1",
            endpoint_url="http://example.org",
            model_name="gpt",
            token_budget_input=100,
            token_budget_output=100,
            timeout_seconds=30,
            purpose="reasoning",
        )

    with pytest.raises(ValidationError):
        ModelDeployment(
            deployment_id="dep-2",
            endpoint_url="https://example.org",
            model_name="gpt",
            token_budget_input=0,
            token_budget_output=100,
            timeout_seconds=30,
            purpose="reasoning",
        )

    with pytest.raises(ValidationError):
        ModelDeployment(
            deployment_id="dep-3",
            endpoint_url="https://example.org",
            model_name="gpt",
            token_budget_input=100,
            token_budget_output=100,
            timeout_seconds=121,
            purpose="reasoning",
        )


def test_dead_letter_entry_enforces_attempt_retry_semantics_and_resolution_transition() -> None:
    entry = DeadLetterEntry(
        entry_id="dlq-1",
        entry_type="handoff_failure",
        correlation_id="corr-1",
        original_payload={"incidentId": "inc-1"},
        failure_reason="delivery failed",
        failure_code="DELIVERY_FAILED",
        attempt_count=3,
        retry_count=2,
        source_service="monitoring",
        target_service="risk",
        tenant_scope_key="live",
        created_at=datetime.now(UTC),
    )
    assert entry.attempt_count == 3
    assert entry.retry_count == 2

    entry.resolve(resolution="replayed", reviewed_by="persona-1")

    with pytest.raises(ValueError):
        entry.resolution = "pending"

    with pytest.raises(ValidationError):
        DeadLetterEntry(
            entry_id="dlq-2",
            entry_type="handoff_failure",
            correlation_id="corr-2",
            original_payload={},
            failure_reason="x",
            failure_code="DELIVERY_FAILED",
            source_service="monitoring",
            target_service="risk",
            tenant_scope_key="live",
            created_at=datetime.now(UTC),
        )


def test_load_test_result_enforces_percentile_order_counts_and_pass_consistency() -> None:
    with pytest.raises(ValidationError):
        LoadTestResult(
            result_id="lt-1",
            scenario_name="scenario",
            executed_at=datetime.now(UTC),
            duration_seconds=30.0,
            concurrent_users=50,
            total_requests=100,
            successful_requests=90,
            failed_requests=10,
            error_rate=10.0,
            p50_latency_ms=100,
            p95_latency_ms=90,
            p99_latency_ms=120,
            throughput_per_second=2.0,
            target_name="read_api_p95_lt_500ms",
            target_threshold=500,
            target_unit="ms",
            passed=True,
        )

    with pytest.raises(ValidationError):
        LoadTestResult(
            result_id="lt-2",
            scenario_name="scenario",
            executed_at=datetime.now(UTC),
            duration_seconds=30.0,
            concurrent_users=50,
            total_requests=100,
            successful_requests=100,
            failed_requests=0,
            error_rate=0.0,
            p50_latency_ms=100,
            p95_latency_ms=200,
            p99_latency_ms=300,
            throughput_per_second=2.0,
            target_name="read_api_p95_lt_150ms",
            target_threshold=150,
            target_unit="ms",
            passed=True,
        )


def test_handoff_event_enforces_confidence_retry_semantics_and_status_transitions() -> None:
    with pytest.raises(ValidationError):
        AgentHandoffEvent(
            handoff_id="h-1",
            incident_id="inc-1",
            source_agent="monitoring",
            target_agent="risk_assessment",
            scope_key="live:inc-1",
            confidence=1.1,
            payload={"incidentId": "inc-1"},
        )

    with pytest.raises(ValidationError):
        AgentHandoffEvent(
            handoff_id="h-2",
            incident_id="inc-1",
            source_agent="monitoring",
            target_agent="risk_assessment",
            scope_key="live:inc-1",
            confidence=0.8,
            payload={"incidentId": "inc-1"},
            attempt_count=2,
            retry_count=0,
        )

    handoff = AgentHandoffEvent(
        handoff_id="h-3",
        incident_id="inc-1",
        source_agent="monitoring",
        target_agent="risk_assessment",
        scope_key="live:inc-1",
        confidence=0.8,
        payload={"incidentId": "inc-1"},
    )
    handoff.mark_delivered()

    with pytest.raises(ValueError):
        handoff.mark_retrying(reason="should fail")
