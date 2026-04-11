# Contract: Telemetry

**Feature**: 011-resource-allocation-agent  
**Date**: 2026-04-17  
**Type**: Observability contract

---

## Metrics (Azure Monitor / Application Insights)

### Processing Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `resource_allocation.allocation_latency` | Histogram | ms | End-to-end processing time per handoff (p50, p95, p99) |
| `resource_allocation.plan_count` | Counter | count | Total deployment plans generated |
| `resource_allocation.handoff_intake_count` | Counter | count | Total handoffs received (tagged by `source_agent`) |
| `resource_allocation.handoff_rejected_count` | Counter | count | Handoffs rejected (invalid, missing incident, etc.) |
| `resource_allocation.duplicate_discard_count` | Counter | count | Duplicate handoffs discarded |
| `resource_allocation.sla_breach_count` | Counter | count | Plans exceeding 15-second SLA (or 30s for cross-incident) |
| `resource_allocation.status_update_latency` | Histogram | ms | Time from resource status signal to inventory update |

### Matching Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `resource_allocation.resource_matching_time` | Histogram | ms | Duration of demand-to-resource matching per plan |
| `resource_allocation.demand_fulfilment_rate` | Gauge | ratio | Percentage of demands fully met per plan |
| `resource_allocation.shortfall_count` | Counter | count | Number of unmet demands per time window |
| `resource_allocation.resource_utilization_rate` | Gauge | ratio | Percentage of each resource type currently assigned (tagged by `resource_type`) |
| `resource_allocation.unmet_demand_count` | Gauge | count | Current number of demands not fully met |

### Cross-Incident Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `resource_allocation.cross_incident_conflicts` | Counter | count | Cross-incident resource contention events per time window |
| `resource_allocation.cross_incident_reallocation_count` | Counter | count | Reallocations recommended per time window |
| `resource_allocation.cross_incident_analysis_latency` | Histogram | ms | Time for cross-incident analysis (30s SLA) |

### Override Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `resource_allocation.override_count` | Counter | count | Commander overrides per time window (tagged by `action`) |
| `resource_allocation.override_rate` | Gauge | ratio | Percentage of plans modified by commanders |
| `resource_allocation.plan_approval_latency` | Histogram | ms | Time from plan creation to commander approval |

### Degradation Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `resource_allocation.fallback_mode_activations` | Counter | count | Template fallback activations (LLM unavailable) |
| `resource_allocation.content_safety_failures` | Counter | count | LLM outputs failing content safety |
| `resource_allocation.audit_buffer_depth` | Gauge | count | Current in-memory audit buffer depth |
| `resource_allocation.audit_tier` | Gauge | enum | Current audit write tier (1=cosmos, 2=memory, 3=file) |
| `resource_allocation.degradation_events` | Counter | count | Degradation events per time window |

### Version and Plan Lifecycle Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `resource_allocation.plan_versions_per_incident` | Gauge | count | Average and max plan versions per incident |
| `resource_allocation.version_conflict_retries` | Counter | count | Optimistic concurrency retries |
| `resource_allocation.active_plans_gauge` | Gauge | count | Current number of active non-superseded plans |
| `resource_allocation.plan_expired_count` | Counter | count | Plans expired without commander action |
| `resource_allocation.transport_dispatch_latency` | Histogram | ms | Time from evacuation transport request to dispatch plan |
| `resource_allocation.handoff_success_rate` | Gauge | ratio | Processed vs rejected handoff ratio |

---

## Alerting Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| SLA breach | `allocation_latency` p95 > 15,000ms for 5 min | Warning | Investigate LLM latency or inventory size |
| Sustained SLA breach | `allocation_latency` p95 > 15,000ms for 15 min | Critical | Scale out ACA instances |
| Cross-incident SLA breach | `cross_incident_analysis_latency` p95 > 30,000ms for 5 min | Warning | Check concurrent incident count |
| High shortfall rate | `demand_fulfilment_rate` < 0.5 for 15 min | Warning | Possible resource exhaustion; check mutual aid |
| LLM unavailable | `fallback_mode_activations` > 10 in 5 min | Warning | Check Azure OpenAI status |
| Audit degradation | `audit_tier` = 2 or 3 for 5 min | Critical | Check Cosmos DB connectivity |
| Audit buffer near capacity | `audit_buffer_depth` > 8,000 | Critical | Cosmos DB likely down; file spill imminent |
| High override rate | `override_rate` > 0.5 for 30 min | Warning | Agent recommendations may not match field conditions |
| No plans generated | `plan_count` = 0 for 10 min during active incident | Critical | Agent may be stuck or queue empty |
| Plan version churn | `plan_versions_per_incident` > 10 for any incident | Warning | Possible re-planning loop |

---

## Distributed Tracing

### Trace Context

| Field | Value |
|-------|-------|
| Service name | `resource-allocation-agent` |
| Correlation ID | Propagated from inbound `AgentHandoffEvent.handoff_id` |
| Parent span | Risk Assessment or Evacuation Agent's handoff delivery span |

### Span Hierarchy

```
resource_allocation.process_handoff (root)
├── resource_allocation.validate_handoff
├── resource_allocation.retrieve_data
│   └── resource_allocation.cosmos_read (per document)
├── resource_allocation.identify_demands
│   └── resource_allocation.normalise_priority
├── resource_allocation.query_inventory
│   └── resource_allocation.filter_eligible
├── resource_allocation.match_resources
│   ├── resource_allocation.compute_score (per resource-demand pair)
│   └── resource_allocation.greedy_assign
├── resource_allocation.cross_incident_analysis (conditional)
│   └── resource_allocation.trade_off_analysis
├── resource_allocation.generate_plan
│   ├── resource_allocation.assign_version
│   ├── resource_allocation.compute_timelines
│   ├── resource_allocation.llm_call (or .template_fallback)
│   └── resource_allocation.content_safety_check
├── resource_allocation.persist_plan
│   └── resource_allocation.cosmos_write
└── resource_allocation.write_audit

resource_allocation.process_status_update (separate root)
├── resource_allocation.validate_transition
├── resource_allocation.apply_status
├── resource_allocation.check_operational_flags
├── resource_allocation.trigger_reallocation (conditional)
└── resource_allocation.write_audit
```

---

## Custom Events

| Event | When Emitted | Properties |
|-------|-------------|------------|
| `HandoffReceived` | Stage 1 complete | handoff_id, incident_id, source_agent, tenant_id |
| `PlanGenerated` | Stage 7 complete | plan_id, version, confidence, generation_method, demand_count, assignment_count |
| `ShortfallDetected` | Stage 5, when demand unmet | demand_id, resource_type, quantity_unmet |
| `CrossIncidentConflict` | Stage 6, when contention found | incident_ids, contested_resource_types, resolution |
| `ReallocationRecommended` | Stage 6, when reallocation flagged | from_incident, to_incident, resource_count |
| `OverrideApplied` | POST /override | plan_id, action, user_id, role |
| `PlanExpired` | Expiry check | plan_id, incident_id, age_hours |
| `DegradationEvent` | Any fallback activation | component (llm/cosmos/inventory), tier |
| `SLABreach` | Processing > 15s (or 30s) | handoff_id, actual_duration_ms, pipeline_type |
| `VersionConflict` | Optimistic concurrency retry | incident_id, retry_count |
