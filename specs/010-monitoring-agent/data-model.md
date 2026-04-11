# Data Model: Monitoring Agent

**Feature**: 010-monitoring-agent  
**Date**: 2026-04-11  
**Status**: Complete

---

## Entity: SignalEnvelope (consumed, not owned)

**Source**: Ingestion pipeline (spec 006)  
**Location**: `apps/api/app/validators/signal_envelope.py`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `SignalSourceEnvelope` | Yes | Data source identity (dataSourceId, name, kind) |
| `incidentId` | `str \| None` | No | Associated incident ID, null if unassociated |
| `category` | `str` | Yes | Signal category (fire, weather, hydrology, earthquake, tsunami, infrastructure, etc.) |
| `occurredAt` | `str` (ISO 8601) | Yes | When the event occurred |
| `receivedAt` | `str` (ISO 8601) | Yes | When the signal was received by ingestion |
| `jurisdictionId` | `str \| None` | No | Jurisdiction for location matching |
| `location` | `dict` (GeoJSON) | Yes | Geographic location |
| `payload` | `dict` | No | Raw signal payload |
| `confidenceScore` | `float` (0–1) | Yes | Pipeline-computed confidence |
| `freshnessScore` | `float` (0–1) | Yes | Pipeline-computed freshness |
| `validationStatus` | `str` | Yes | pending \| validated \| contradicted \| rejected \| escalated |
| `provenance` | `dict` | No | Source provenance metadata |

**Validation rules** (at agent boundary):
- `category` must be non-empty string
- `confidenceScore` must be in range [0.0, 1.0]
- `freshnessScore` must be in range [0.0, 1.0]
- `source` must have non-empty `dataSourceId` and `kind`
- Rejection produces a `validation_failed` audit record

---

## Entity: MonitoringDecisionRecord (owned)

**Storage**: Azure Cosmos DB — container `monitoring-decisions`  
**Partition key**: `/incident_scope_key`  
**TTL**: None (infinite retention, append-only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` (UUID) | Yes | Unique record identifier |
| `signal_id` | `str` | Yes | Originating signal ID |
| `decision` | `DecisionType` (enum) | Yes | Type of decision made |
| `confidence` | `float` | Yes | Confidence at decision time |
| `effective_confidence` | `float \| None` | No | confidenceScore × freshnessScore (when applicable) |
| `freshness_score` | `float \| None` | No | Original freshness score from signal |
| `inputs` | `dict` | Yes | Data used to make decision |
| `output` | `dict` | Yes | Result of the decision |
| `agent_version` | `str` | Yes | Semantic version of agent code |
| `reasoning_summary` | `str` | Yes | Brief explanation of decision logic (max 500 chars) |
| `llm_classification` | `str \| None` | No | credible \| suspicious \| misinformation \| llm_unavailable \| llm_timeout |
| `content_safety_result` | `str \| None` | No | passed \| failed_with_fallback \| not_checked |
| `incident_scope_key` | `str` | Yes | Partition key: `{tenant_id}:{incident_id}` or `{tenant_id}:unassociated:{hash}` |
| `tenant_id` | `str` | Yes | Tenant scope (live \| simulation) |
| `timestamp` | `datetime` (UTC) | Yes | When the decision was recorded |
| `buffered_at` | `datetime \| None` | No | Set if record was buffered during Cosmos DB outage |
| `flush_source` | `str \| None` | No | `direct` \| `memory_buffer` \| `file_buffer` |

**DecisionType enum values** (9 types):
- `summarised` — Signal was summarised
- `escalated` — Signal met escalation criteria, handoff created
- `blocked` — Signal blocked (misinformation or content safety)
- `handed_off` — Handoff successfully delivered
- `held_for_review` — Signal held for human review (LLM unavailable/unexpected)
- `associated` — Signal retrospectively linked to an incident
- `degradation_detected` — Data source freshness degradation logged
- `discarded` — Duplicate signal discarded (idempotency)
- `validation_failed` — Signal rejected at boundary validation

**State transitions**: None — records are immutable (append-only). Multiple records may exist for the same `signal_id` representing different decision points in the pipeline.

---

## Entity: DataFreshnessIndicator (owned, in-memory with telemetry)

**Storage**: In-memory per instance, emitted as metrics to Application Insights  
**Not persisted to Cosmos DB** (ephemeral operational state)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data_source_id` | `str` | Yes | Unique source identifier |
| `source_type` | `SourceType` (enum) | Yes | authoritative \| iot \| social |
| `last_signal_received_at` | `datetime` (UTC) | Yes | Timestamp of most recent signal from this source |
| `current_freshness_score` | `float` (0–1) | Yes | Computed freshness (decays over time) |
| `staleness_threshold_minutes` | `int` | Yes | Per-type threshold (authoritative: 15, iot: 5, social: 30) |
| `status` | `FreshnessStatus` (enum) | Yes | healthy \| degraded \| offline |
| `last_status_change_at` | `datetime` (UTC) | Yes | When status last changed |

**Status transition rules**:
- `healthy` → `degraded`: No signal received for `staleness_threshold_minutes`
- `degraded` → `offline`: No signal received for `2 × staleness_threshold_minutes`
- `degraded` → `healthy`: Signal received with `freshnessScore >= 0.5`
- `offline` → `healthy`: Signal received with `freshnessScore >= 0.5`

---

## Entity: AgentHandoffEvent (shared, from common module)

**Source**: `apps/agents/common/handoffs.py`  
**Owned by**: Common agent infrastructure  
**Used by**: Monitoring Agent (creates), Risk Assessment Agent (consumes)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Unique handoff identifier |
| `incident_id` | `str` | Yes | Associated incident |
| `source_agent` | `str` | Yes | Always `monitoring` for this agent |
| `target_agent` | `str` | Yes | Always `risk_assessment` for v1 |
| `scope_key` | `str` | Yes | Incident scope key for routing |
| `confidence` | `float` | Yes | `effectiveConfidence` at escalation time |
| `payload` | `dict` | Yes | Signal summary (category, sourceKind, incidentId) |
| `tenant_id` | `str` | Yes | `live` or simulation scope |
| `status` | `str` | Yes | pending → delivered \| failed \| dead_lettered |
| `retry_count` | `int` | Yes | Number of delivery attempts |
| `max_retries` | `int` | Yes | Default: 3 |
| `created_at` | `datetime` | Yes | Handoff creation time |
| `delivered_at` | `datetime \| None` | No | Successful delivery time |
| `failed_at` | `datetime \| None` | No | Final failure time |
| `failure_reason` | `str \| None` | No | Error description |

---

## Entity: AuditBufferEntry (internal, degradation support)

**Storage**: In-memory ring buffer (10,000 capacity) with file spill  
**Purpose**: Temporary buffer for audit records when Cosmos DB is unavailable

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `record` | `MonitoringDecisionRecord` | Yes | The audit record to be persisted |
| `buffered_at` | `datetime` (UTC) | Yes | When the record was buffered |
| `retry_count` | `int` | Yes | Number of flush attempts |
| `last_retry_at` | `datetime \| None` | No | Last flush attempt time |

---

## Relationships

```
SignalEnvelope (input)
    │
    ├──► MonitoringDecisionRecord (1:many — one signal can produce multiple decisions)
    │       │
    │       └──► incident_scope_key → Cosmos DB partition
    │
    ├──► AgentHandoffEvent (0:1 — created only if escalation criteria met)
    │       │
    │       └──► Risk Assessment Agent (consumer)
    │
    └──► DataFreshnessIndicator (many:1 — many signals update one indicator per source)
```

## Configurable Parameters (consolidated per CHK073)

| Parameter | Environment Variable | Default | Type | Description |
|-----------|---------------------|---------|------|-------------|
| Escalation confidence threshold | `ESCALATION_CONFIDENCE_THRESHOLD` | `0.8` | float | Minimum `effectiveConfidence` for escalation |
| Signal dedup window | `SIGNAL_DEDUP_WINDOW_MINUTES` | `10` | int | Minutes to check for duplicate signal_id |
| Retrospective lookback | `RETROSPECTIVE_LOOKBACK_HOURS` | `24` | int | Hours to scan for unassociated signals |
| Authoritative staleness | `STALENESS_THRESHOLD_AUTHORITATIVE_MINUTES` | `15` | int | Minutes before authoritative source is stale |
| IoT staleness | `STALENESS_THRESHOLD_IOT_MINUTES` | `5` | int | Minutes before IoT source is stale |
| Social staleness | `STALENESS_THRESHOLD_SOCIAL_MINUTES` | `30` | int | Minutes before social source is stale |
| LLM evaluation timeout | `LLM_EVAL_TIMEOUT_SECONDS` | `3` | float | Max seconds for misinformation LLM call |
| Suspicious confidence penalty | `SUSPICIOUS_CONFIDENCE_PENALTY` | `0.15` | float | Confidence reduction for "suspicious" LLM result |
| Audit buffer capacity | `AUDIT_BUFFER_CAPACITY` | `10000` | int | Max in-memory audit buffer entries |
| Audit buffer file path | `AUDIT_BUFFER_FILE_PATH` | `/var/log/monitoring-agent/audit-buffer.jsonl` | str | Local spill file for audit buffer |
| Max reasoning summary length | `MAX_REASONING_SUMMARY_LENGTH` | `500` | int | Max chars for reasoning_summary field |
| Agent version | `AGENT_VERSION` | `0.1.0` | str | Semantic version for audit records |
