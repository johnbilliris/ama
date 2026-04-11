# Contract: Telemetry and Observability

**Feature**: 010-monitoring-agent  
**Date**: 2026-04-11  
**Type**: Azure Monitor / Application Insights metrics and traces

---

## Metrics (NFR-003)

All metrics are emitted to Azure Application Insights via OpenTelemetry.

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `signal_processing_latency` | Histogram | ms | Time from signal receipt to final decision |
| `escalation_rate` | Counter | count/window | Handoffs created per time window |
| `misinformation_detection_rate` | Counter | count/window | Misinformation classifications per window |
| `degradation_events` | Counter | count | Data source freshness degradation events |
| `handoff_success_rate` | Gauge | ratio | Delivered / (delivered + failed + dead_lettered) |
| `signal_validation_failures_total` | Counter | count | Signals rejected at boundary validation |
| `dedup_discards_total` | Counter | count | Duplicate signals discarded |
| `llm_evaluation_latency` | Histogram | ms | LLM misinformation check latency |
| `llm_timeout_count` | Counter | count | LLM evaluations that timed out |
| `audit_buffer_depth` | Gauge | count | Current in-memory audit buffer entries |
| `audit_buffer_file_spills` | Counter | count | Times audit records spilled to file |
| `health_check_latency` | Histogram | ms | Health endpoint response time |
| `effective_confidence_distribution` | Histogram | ratio | Distribution of effectiveConfidence values |

## Dimensions (labels) on all metrics

| Dimension | Values | Description |
|-----------|--------|-------------|
| `category` | fire, weather, hydrology, earthquake, tsunami, etc. | Signal category |
| `source_type` | authoritative, iot, social | Data source type |
| `decision` | summarised, escalated, blocked, etc. | Decision type |
| `tenant_id` | live, simulation | Tenant scope |

---

## Distributed Traces

Each signal processing flow produces a trace with the following spans:

```
signal_processing (root span)
├── input_validation
├── dedup_check
├── freshness_assessment
├── misinformation_evaluation (conditional)
│   └── llm_call
├── signal_summarisation
│   └── llm_call (if available)
│   └── content_safety_validation
├── confidence_triage
│   └── handoff_creation (conditional)
│       └── handoff_delivery
│           └── retry_attempt_N
└── audit_record_write
    └── buffer_flush (conditional, on Cosmos failure)
```

**Trace context propagation**: Correlation ID from the incoming Service Bus message is used as the trace parent. The `signal_id` is set as a span attribute on the root span.

---

## Custom Events

| Event Name | When Emitted | Key Properties |
|------------|-------------|----------------|
| `MisinformationBlocked` | Signal blocked as misinformation | signal_id, category, source_kind |
| `SignalHeldForReview` | Signal held for human review | signal_id, reason (llm_unavailable, llm_timeout, unexpected_response) |
| `DataSourceDegraded` | Source freshness status changed to degraded/offline | data_source_id, source_type, previous_status, new_status |
| `DataSourceRecovered` | Source freshness status changed to healthy | data_source_id, source_type, downtime_minutes |
| `HandoffDeadLettered` | Handoff failed all retries | handoff_id, incident_id, failure_reason |
| `AuditBufferActivated` | Cosmos DB unavailable, buffering started | buffer_depth, trigger_error |
| `AuditBufferFlushed` | Buffered records flushed to Cosmos DB | records_flushed, flush_source |
| `RetrospectiveAssociation` | Signals linked to newly declared incident | incident_id, jurisdiction_id, signals_associated |

---

## Alerting Thresholds (recommended)

| Alert | Condition | Severity |
|-------|-----------|----------|
| High misinformation rate | misinformation_detection_rate > 10/min for 5 min | Warning |
| LLM unavailable | llm_timeout_count > 5 in 1 min | Critical |
| Audit buffer activated | audit_buffer_depth > 0 | Warning |
| Audit buffer near capacity | audit_buffer_depth > 8000 | Critical |
| Handoff dead letters | Any HandoffDeadLettered event | Critical |
| Processing latency spike | p95 signal_processing_latency > 4000ms | Warning |
| Queue depth critical | processing_queue_depth > 5000 | Critical |
