# Contract: Telemetry

**Feature**: 012-risk-assessment-agent  
**Date**: 2026-04-15  
**Type**: Observability contract

---

## Metrics (Azure Monitor / Application Insights)

### Processing Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `risk_assessment.assessment_latency` | Histogram | ms | End-to-end processing time per handoff (p50, p95, p99) |
| `risk_assessment.assessment_count` | Counter | count | Total assessments generated |
| `risk_assessment.handoff_intake_count` | Counter | count | Total handoffs received |
| `risk_assessment.handoff_rejected_count` | Counter | count | Handoffs rejected (invalid, missing incident, etc.) |
| `risk_assessment.duplicate_discard_count` | Counter | count | Duplicate handoffs discarded |
| `risk_assessment.sla_breach_count` | Counter | count | Assessments exceeding 10-second SLA |

### Escalation Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `risk_assessment.escalation_rate_by_type` | Counter | count | Downstream handoffs created, tagged by `target_agent` |
| `risk_assessment.handoff_success_rate` | Gauge | ratio | Delivered vs dead-lettered handoff ratio |
| `risk_assessment.dead_letter_count` | Counter | count | Handoffs permanently failed |

### Quality Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `risk_assessment.contradiction_detection_rate` | Gauge | ratio | Percentage of assessments with contradictions detected |
| `risk_assessment.confidence_distribution` | Histogram | score | Distribution of final adjusted confidence scores |
| `risk_assessment.severity_distribution` | Counter | count | Assessments by severity level (tagged) |
| `risk_assessment.stale_signal_rate` | Gauge | ratio | Percentage of signals below freshness threshold |

### Degradation Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `risk_assessment.fallback_mode_activations` | Counter | count | Template fallback activations (LLM unavailable) |
| `risk_assessment.content_safety_failures` | Counter | count | LLM outputs failing content safety |
| `risk_assessment.audit_buffer_depth` | Gauge | count | Current in-memory audit buffer depth |
| `risk_assessment.audit_tier` | Gauge | enum | Current audit write tier (1=cosmos, 2=memory, 3=file) |

### Version Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `risk_assessment.version_count_per_incident` | Gauge | count | Assessment versions per incident (tagged by incident_id) |
| `risk_assessment.version_conflict_retries` | Counter | count | Optimistic concurrency retries |

---

## Alerting Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| SLA breach | `assessment_latency` p95 > 10,000ms for 5 min | Warning | Investigate LLM latency or signal store |
| Sustained SLA breach | `assessment_latency` p95 > 10,000ms for 15 min | Critical | Scale out ACA instances |
| High dead-letter rate | `handoff_success_rate` < 0.9 for 5 min | Critical | Check downstream agent availability |
| LLM unavailable | `fallback_mode_activations` > 10 in 5 min | Warning | Check Azure OpenAI status |
| Audit degradation | `audit_tier` = 2 or 3 for 5 min | Critical | Check Cosmos DB connectivity |
| Audit buffer near capacity | `audit_buffer_depth` > 8,000 | Critical | Cosmos DB likely down; file spill imminent |
| High contradiction rate | `contradiction_detection_rate` > 0.5 for 15 min | Warning | Possible data quality issue or sensor malfunction |
| No assessments | `assessment_count` = 0 for 10 min during active incident | Critical | Agent may be stuck or queue empty |

---

## Distributed Tracing

### Trace Context

| Field | Value |
|-------|-------|
| Service name | `risk-assessment-agent` |
| Correlation ID | Propagated from inbound `AgentHandoffEvent.handoff_id` |
| Parent span | Monitoring Agent's handoff delivery span |

### Span Hierarchy

```
risk_assessment.process_handoff (root)
├── risk_assessment.validate_handoff
├── risk_assessment.retrieve_signals
├── risk_assessment.correlate_signals
├── risk_assessment.detect_contradictions
├── risk_assessment.generate_assessment
│   ├── risk_assessment.llm_call (or .template_fallback)
│   └── risk_assessment.content_safety_check
├── risk_assessment.assign_version
├── risk_assessment.generate_recommendations
├── risk_assessment.evaluate_escalation
│   └── risk_assessment.deliver_handoff (per target agent)
└── risk_assessment.write_audit
```

---

## Custom Events

| Event | When Emitted | Properties |
|-------|-------------|------------|
| `HandoffReceived` | Stage 1 complete | handoff_id, incident_id, tenant_id |
| `AssessmentGenerated` | Stage 5 complete | assessment_id, confidence, severity, generation_method |
| `ContradictionDetected` | Stage 4, when contradictions found | signal_ids, source_names, confidence_reduction |
| `EscalationTriggered` | Stage 7, per downstream handoff | target_agent, recommendation_id, confidence |
| `DegradationEvent` | Any fallback activation | component (llm/cosmos/signal_store), tier |
| `SLABreach` | Processing > 10s | handoff_id, actual_duration_ms |
| `VersionConflict` | Optimistic concurrency retry | incident_id, assessment_type, retry_count |
