"""Contract tests: LLM telemetry metric instruments (US8).

Verifies all 9 metric instruments are created with correct names.
"""

from __future__ import annotations


class TestLLMTelemetryInstruments:
    """Verify all LLM telemetry instruments are defined."""

    def test_risk_assessment_llm_metrics(self) -> None:
        from apps.agents.risk_assessment.telemetry import metrics

        assert hasattr(metrics, "llm_call_count")
        assert hasattr(metrics, "llm_call_duration")
        assert hasattr(metrics, "llm_tokens_input")
        assert hasattr(metrics, "llm_tokens_output")
        assert hasattr(metrics, "llm_fallback_count")
        assert hasattr(metrics, "llm_error_count")
        assert hasattr(metrics, "llm_circuit_breaker_state_change")
        assert hasattr(metrics, "llm_budget_exceeded")
        assert hasattr(metrics, "llm_confidence_below_threshold")

    def test_evacuation_llm_metrics(self) -> None:
        from apps.agents.evacuation import telemetry

        assert hasattr(telemetry, "llm_call_count")
        assert hasattr(telemetry, "llm_call_duration")
        assert hasattr(telemetry, "llm_tokens_input")
        assert hasattr(telemetry, "llm_tokens_output")
        assert hasattr(telemetry, "llm_fallback_count")
        assert hasattr(telemetry, "llm_error_count")
        assert hasattr(telemetry, "llm_circuit_breaker_state_change")
        assert hasattr(telemetry, "llm_budget_exceeded")
        assert hasattr(telemetry, "llm_confidence_below_threshold")

    def test_monitoring_llm_metrics(self) -> None:
        from apps.agents.monitoring import telemetry

        assert hasattr(telemetry, "llm_call_count")
        assert hasattr(telemetry, "llm_call_duration")
        assert hasattr(telemetry, "llm_tokens_input")
        assert hasattr(telemetry, "llm_tokens_output")
        assert hasattr(telemetry, "llm_fallback_count")
        assert hasattr(telemetry, "llm_error_count")
        assert hasattr(telemetry, "llm_circuit_breaker_state_change")
        assert hasattr(telemetry, "llm_budget_exceeded")
        assert hasattr(telemetry, "llm_confidence_below_threshold")

    def test_communication_llm_metrics(self) -> None:
        from apps.agents.communication import telemetry

        assert hasattr(telemetry, "llm_call_count")
        assert hasattr(telemetry, "llm_call_duration")
        assert hasattr(telemetry, "llm_tokens_input")
        assert hasattr(telemetry, "llm_tokens_output")
        assert hasattr(telemetry, "llm_fallback_count")
        assert hasattr(telemetry, "llm_error_count")
        assert hasattr(telemetry, "llm_circuit_breaker_state_change")
        assert hasattr(telemetry, "llm_budget_exceeded")
        assert hasattr(telemetry, "llm_confidence_below_threshold")

    def test_resource_allocation_llm_metrics(self) -> None:
        from apps.agents.resource_allocation.telemetry import metrics

        assert hasattr(metrics, "llm_call_count")
        assert hasattr(metrics, "llm_call_duration")
        assert hasattr(metrics, "llm_tokens_input")
        assert hasattr(metrics, "llm_tokens_output")
        assert hasattr(metrics, "llm_fallback_count")
        assert hasattr(metrics, "llm_error_count")
        assert hasattr(metrics, "llm_circuit_breaker_state_change")
        assert hasattr(metrics, "llm_budget_exceeded")
        assert hasattr(metrics, "llm_confidence_below_threshold")

    def test_no_op_metrics_callable(self) -> None:
        """No-op metrics should accept .add() and .record() without error."""
        from apps.agents.monitoring import telemetry

        # Should not raise
        telemetry.llm_call_count.add(1, {"agent": "monitoring", "deployment": "test", "outcome": "success"})
        telemetry.llm_call_duration.record(100.0, {"agent": "monitoring", "deployment": "test"})
        telemetry.llm_tokens_input.add(50, {"agent": "monitoring", "deployment": "test"})
