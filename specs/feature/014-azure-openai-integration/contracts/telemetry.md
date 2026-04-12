# Contract: LLM Telemetry Metrics

**Feature**: 014-azure-openai-integration
**Module**: `apps/agents/*/telemetry.py` (all 5 agents)
**Date**: 2026-04-16

## Overview

LLM-specific telemetry metrics emitted via the existing OpenTelemetry integration. Each agent's `telemetry.py` is extended with LLM metric instruments. The metrics follow the existing pattern: optional OpenTelemetry with no-op fallback when the `opentelemetry` package is not installed.

## Metrics Specification

### Counters

| Metric Name | Labels | Description | FR Reference |
|-------------|--------|-------------|--------------|
| `llm.call.count` | `agent`, `deployment`, `outcome` | Total LLM API calls. `outcome` ∈ {`success`, `failure`, `timeout`} | FR-016 |
| `llm.tokens.input` | `agent`, `deployment` | Cumulative input (prompt) tokens consumed | FR-009, FR-016 |
| `llm.tokens.output` | `agent`, `deployment` | Cumulative output (completion) tokens consumed | FR-009, FR-016 |
| `llm.fallback.count` | `agent`, `fallback_type` | Fallback events. `fallback_type` ∈ {`template`, `safety`} | FR-007, FR-016 |
| `llm.error.count` | `agent`, `error_category` | Error events. `error_category` ∈ {`transient_429`, `transient_503`, `auth`, `deployment_not_found`, `timeout`, `other`} | FR-016 |
| `llm.circuit_breaker.state_change` | `agent`, `from_state`, `to_state` | Circuit breaker state transitions | FR-016 (extended) |
| `llm.budget.exceeded` | `agent` | Monthly budget threshold breach events | FR-021 |
| `llm.confidence.below_threshold` | `agent` | Safety-critical outputs flagged for human review | FR-011, FR-016 |

### Histograms

| Metric Name | Labels | Unit | Buckets | Description | FR Reference |
|-------------|--------|------|---------|-------------|--------------|
| `llm.call.duration_ms` | `agent`, `deployment` | milliseconds | `[100, 250, 500, 1000, 2500, 5000, 10000, 15000]` | LLM call latency distribution | FR-016 |

## Label Schema

| Label | Type | Values | Description |
|-------|------|--------|-------------|
| `agent` | `string` | `risk-assessment`, `evacuation`, `monitoring`, `communication`, `resource-allocation` | Agent emitting the metric |
| `deployment` | `string` | `gpt-4o-{env}`, `gpt-4o-mini-{env}` | Azure OpenAI deployment name |
| `outcome` | `string` | `success`, `failure`, `timeout` | Call result category |
| `fallback_type` | `string` | `template`, `safety` | Type of fallback triggered |
| `error_category` | `string` | `transient_429`, `transient_503`, `auth`, `deployment_not_found`, `timeout`, `other` | Error classification |
| `from_state` | `string` | `closed`, `open`, `half_open` | Circuit breaker source state |
| `to_state` | `string` | `closed`, `open`, `half_open` | Circuit breaker target state |

## Integration Pattern

Follows the existing telemetry pattern from `apps/agents/risk_assessment/telemetry.py`:

```python
# Detection
_OTEL_AVAILABLE = False
try:
    from opentelemetry.metrics import get_meter
    _OTEL_AVAILABLE = True
except ImportError:
    pass

# Meter creation
_SERVICE_NAME = "{agent-name}-agent"

def _get_meter():
    if _OTEL_AVAILABLE:
        return get_meter(_SERVICE_NAME)
    return _NoOpMeter()

# Instrument creation (module-level singletons)
_meter = _get_meter()

llm_call_counter = _meter.create_counter(
    name="llm.call.count",
    description="Total LLM API calls",
    unit="calls",
)

llm_call_duration = _meter.create_histogram(
    name="llm.call.duration_ms",
    description="LLM call latency",
    unit="ms",
)

# ... additional instruments ...
```

## Usage in LLMCallMixin

The mixin records metrics after each LLM call:

```python
# On successful LLM call:
llm_call_counter.add(1, {"agent": agent_name, "deployment": deployment_id, "outcome": "success"})
llm_call_duration.record(latency_ms, {"agent": agent_name, "deployment": deployment_id})
llm_tokens_input.add(input_tokens, {"agent": agent_name, "deployment": deployment_id})
llm_tokens_output.add(output_tokens, {"agent": agent_name, "deployment": deployment_id})

# On fallback:
llm_fallback_counter.add(1, {"agent": agent_name, "fallback_type": "template"})

# On error:
llm_error_counter.add(1, {"agent": agent_name, "error_category": "transient_429"})
```

## Telemetry Pipeline

```text
Agent Process
  └── OpenTelemetry SDK
       └── OTLP Exporter
            └── Application Insights (via APPLICATIONINSIGHTS_CONNECTION_STRING)
                 └── Log Analytics Workspace
                      └── KQL queries / dashboards / alerts
```

The `APPLICATIONINSIGHTS_CONNECTION_STRING` env var is already set on all Container Apps (see `main.bicep` lines 465, 535).

## No-Op Fallback Contract

When `opentelemetry` is not installed:
- All metric instruments are replaced with no-op stubs
- Zero runtime overhead
- No exceptions from metric calls
- Application behaviour is identical (metrics are silently dropped)

This matches the existing pattern in all agent telemetry modules.

## SC-006 Verification

> Per-agent token usage metrics are available in the telemetry pipeline within 60 seconds of an LLM call.

The OpenTelemetry SDK exports metrics at a configurable interval (default: 60 seconds). The metrics are available in Application Insights / Log Analytics within the export interval. This meets SC-006.
