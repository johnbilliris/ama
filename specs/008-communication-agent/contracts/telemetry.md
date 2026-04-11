# Contract: Telemetry — Metrics, Traces, and Events

**Date**: 2026-04-18 | **Spec**: [../spec.md](../spec.md) | **Service name**: `communication-agent`

## Trace Hierarchy

All spans are rooted under the pipeline processing span. Each stage of the 11-stage pipeline creates a child span.

```
communication.pipeline.process
├── communication.stage.handoff_intake
├── communication.stage.data_retrieval
├── communication.stage.audience_segmentation
├── communication.stage.template_loading
├── communication.stage.alert_drafting
│   ├── communication.llm.generate.en-AU
│   ├── communication.llm.generate.zh-Hans
│   ├── communication.llm.generate.ar
│   ├── communication.llm.generate.vi
│   ├── communication.llm.generate.el
│   └── communication.llm.generate.it
├── communication.stage.back_translation
│   ├── communication.backtranslate.zh-Hans
│   ├── communication.backtranslate.ar
│   ├── communication.backtranslate.vi
│   ├── communication.backtranslate.el
│   └── communication.backtranslate.it
├── communication.stage.content_safety
├── communication.stage.versioning
├── communication.stage.approval_notification
├── communication.stage.delivery
│   ├── communication.delivery.sms.{segment_id}
│   ├── communication.delivery.push.{segment_id}
│   └── communication.delivery.broadcast.{segment_id}
└── communication.stage.audit_finalisation
```

---

## Metrics

All metrics are emitted via OpenTelemetry and exported to Azure Monitor / Application Insights.

### Processing Metrics

| Metric Name | Type | Unit | Description | Alerting Threshold |
|-------------|------|------|-------------|-------------------|
| `communication.alert_draft_latency` | Histogram | ms | Time from handoff receipt to draft completion | p95 > 20,000ms |
| `communication.translation_latency` | Histogram | ms | Time per language translation (LLM + back-translation) | p95 > 5,000ms |
| `communication.content_safety_check_latency` | Histogram | ms | Content safety validation per language | p95 > 1,000ms |
| `communication.pipeline_total_latency` | Histogram | ms | Total pipeline time (stages 1–9) | p95 > 35,000ms |
| `communication.end_to_end_latency` | Histogram | ms | Handoff receipt to first delivery (excl. approval wait) | p95 > 60,000ms |

### Approval Metrics

| Metric Name | Type | Unit | Description | Alerting Threshold |
|-------------|------|------|-------------|-------------------|
| `communication.approval_wait_time` | Histogram | ms | Time from alert creation to commander action | p95 > 900,000ms (15 min) |
| `communication.approval_notification_latency` | Histogram | ms | Time to publish approval notification to Service Bus | p95 > 5,000ms |
| `communication.escalation_count` | Counter | count | Number of escalation events | > 5 per hour |

### Delivery Metrics

| Metric Name | Type | Unit | Description | Alerting Threshold |
|-------------|------|------|-------------|-------------------|
| `communication.delivery_latency_per_channel` | Histogram | ms | Time from approval to delivery completion, by channel label | p95 > 10,000ms |
| `communication.delivery_success_rate_per_channel` | Gauge | ratio | Success rate (0.0–1.0), by channel label | < 0.90 |
| `communication.sms_segment_count` | Histogram | count | Number of SMS segments per delivery | p95 > 4 |

### Quality Metrics

| Metric Name | Type | Unit | Description | Alerting Threshold |
|-------------|------|------|-------------|-------------------|
| `communication.back_translation_quality_score` | Histogram | ratio | Cosine similarity score per language | p50 < 0.85 |
| `communication.template_fallback_rate` | Gauge | ratio | Percentage of alerts using template fallback | > 0.20 (20%) |
| `communication.content_safety_failure_rate` | Gauge | ratio | Percentage of content blocks failing safety | > 0.10 (10%) |

### Operational Metrics

| Metric Name | Type | Unit | Description | Alerting Threshold |
|-------------|------|------|-------------|-------------------|
| `communication.active_alerts_count` | Gauge | count | Current number of active (non-terminal) alerts | > 50 |
| `communication.audience_segment_count` | Histogram | count | Number of segments generated per alert | — |
| `communication.pending_approvals` | Gauge | count | Alerts in `pending_review` status | > 10 |
| `communication.processing_queue_depth` | Gauge | count | Service Bus queue depth | > 10 (scale-out trigger) |

### Degradation Metrics

| Metric Name | Type | Unit | Description | Alerting Threshold |
|-------------|------|------|-------------|-------------------|
| `communication.llm_fallback_active` | Gauge | boolean | 1 if LLM unavailable, 0 if healthy | = 1 |
| `communication.channel_degraded` | Gauge | boolean | 1 if any delivery channel degraded, by channel label | = 1 |
| `communication.audit_tier` | Gauge | enum | Current audit tier (1=cosmos, 2=memory, 3=file) | > 1 |
| `communication.embedding_service_available` | Gauge | boolean | 1 if embedding service healthy | = 0 |

---

## Custom Events

Emitted via `trace.get_tracer().start_span()` with event semantics.

| Event Name | Trigger | Key Attributes |
|------------|---------|---------------|
| `HandoffReceived` | Stage 1 — valid handoff processed | `handoff_id`, `incident_id`, `recommendation_id` |
| `HandoffRejected` | Stage 1 — handoff validation failed | `handoff_id`, `reason` |
| `DuplicateDiscarded` | Stage 1 — dedup cache hit | `handoff_id`, `duplicate_type` |
| `AlertDrafted` | Stage 5 — alert content generated | `alert_id`, `language_count`, `generation_method`, `confidence` |
| `BackTranslationFlagged` | Stage 6 — score below threshold | `alert_id`, `language`, `score`, `threshold` |
| `ContentSafetyFailed` | Stage 7 — content safety rejection | `alert_id`, `language`, `failure_reason` |
| `AlertVersionCreated` | Stage 8 — new version persisted | `alert_id`, `version`, `change_type`, `incident_id` |
| `ApprovalRequested` | Stage 9 — approval notification sent | `alert_id`, `commander_id` |
| `EscalationTriggered` | Escalation timer — commander timeout | `alert_id`, `from_commander`, `to_commander`, `level` |
| `EscalationExhausted` | Escalation — max levels reached | `alert_id`, `held_for_next_available` |
| `DeliveryStarted` | Stage 10 — delivery initiated | `alert_id`, `channel`, `segment_id` |
| `DeliveryCompleted` | Stage 10 — delivery succeeded | `delivery_id`, `channel`, `duration_ms` |
| `DeliveryFailed` | Stage 10 — all retries exhausted | `delivery_id`, `channel`, `failure_reason`, `attempt_count` |
| `DeliveryDeduplicated` | Stage 10 — recipient dedup | `segment_id`, `deduplicated_by_segment_id` |
| `DegradationDetected` | Any stage — service unavailable | `service`, `fallback_used`, `impact` |
| `DegradationRecovered` | Any stage — service restored | `service`, `downtime_ms` |
| `TemplateFileMissing` | Stage 4 — language template not found | `language_code`, `fallback_to` |

---

## Alerting Rules

| Rule | Condition | Severity | Action |
|------|-----------|----------|--------|
| Alert drafting SLA breach | `alert_draft_latency` p95 > 20s | Warning | Page on-call; check LLM latency |
| End-to-end SLA breach | `end_to_end_latency` p95 > 60s | Critical | Page on-call; check all pipeline stages |
| Delivery channel down | `delivery_success_rate_per_channel` < 0.5 for 5 min | Critical | Page on-call; check channel health |
| LLM unavailable | `llm_fallback_active` = 1 for 5 min | Warning | Alert ops; templates in use |
| Audit degradation | `audit_tier` > 1 for 10 min | Warning | Alert ops; check Cosmos DB |
| Escalation spike | `escalation_count` > 5 in 1 hour | Warning | Alert ops; check commander availability |
| Queue backup | `processing_queue_depth` > 10 | Info | Auto-scaling should trigger |
| Translation quality drop | `back_translation_quality_score` p50 < 0.80 | Warning | Review LLM model version |
