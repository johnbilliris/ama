# Contract: Telemetry

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16  
**Type**: Observability contract

---

## Metrics (Azure Monitor / Application Insights)

### Processing Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.plan_generation_latency` | Histogram | ms | End-to-end time from handoff receipt to plan persisted (p50, p95, p99) |
| `evacuation.route_computation_time` | Histogram | ms | Duration of Dijkstra's pathfinding per plan (p50, p95, p99) |
| `evacuation.replan_count` | Counter | count | Number of replans per incident (tagged by incident_id) |
| `evacuation.replan_latency` | Histogram | ms | Dynamic replanning time (15-second SLA, p50/p95/p99) |
| `evacuation.handoff_intake_count` | Counter | count | Total handoffs received |
| `evacuation.handoff_rejected_count` | Counter | count | Handoffs rejected (invalid, missing assessment) |
| `evacuation.duplicate_discard_count` | Counter | count | Duplicate handoffs discarded |
| `evacuation.sla_breach_count` | Counter | count | Plans exceeding 30-second SLA |
| `evacuation.replan_sla_breach_count` | Counter | count | Replans exceeding 15-second SLA |

### Safety Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.shelter_in_place_count` | Counter | count | Shelter-in-place recommendations issued |
| `evacuation.shelter_to_evacuation_recovery_count` | Counter | count | Transitions from shelter-in-place back to evacuation |
| `evacuation.emergency_escalation_count` | Counter | count | Emergency escalations (no route + immediate threat) |
| `evacuation.time_deficit_flag_count` | Counter | count | Plans where clearance time exceeds hazard arrival window |

### Transport Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.transport_requests_generated` | Counter | count | TransportRequirement records created |
| `evacuation.transport_by_category` | Counter | count | Transport requests by vulnerability category (tagged) |
| `evacuation.transport_vehicles_estimated` | Gauge | count | Total estimated vehicles needed across active plans |

### Zone & Population Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.zone_population_covered` | Gauge | count | Population estimate per zone in active plans (tagged by zone) |
| `evacuation.active_plans_gauge` | Gauge | count | Current number of active non-superseded plans |
| `evacuation.routes_per_plan` | Histogram | count | Number of evacuation routes per plan |
| `evacuation.congestion_risk_routes` | Counter | count | Routes flagged as congestion-risk (>80% utilisation) |

### Override & Dynamic Update Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.dynamic_update_rate` | Gauge | count | Plan versions per incident (tagged by incident_id) |
| `evacuation.override_rate` | Gauge | ratio | Percentage of plans modified by commanders |
| `evacuation.override_by_type` | Counter | count | Overrides by action type (tagged: route, zone, phase, cancel, pause) |

### Degradation Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.fallback_mode_activations` | Counter | count | Template fallback activations (LLM unavailable) |
| `evacuation.content_safety_failures` | Counter | count | LLM outputs failing content safety |
| `evacuation.audit_buffer_depth` | Gauge | count | Current in-memory audit buffer depth |
| `evacuation.audit_tier` | Gauge | enum | Current audit write tier (1=cosmos, 2=memory, 3=file) |
| `evacuation.road_data_stale` | Gauge | bool | Whether road network data exceeds staleness window |
| `evacuation.degradation_events` | Counter | count | Total degradation events per time window |

### Version Metrics

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.version_count_per_incident` | Gauge | count | Plan versions per incident (tagged by incident_id) |
| `evacuation.version_conflict_retries` | Counter | count | Optimistic concurrency retries |

### Handoff Success

| Metric | Type | Unit | Description |
|--------|------|------|-------------|
| `evacuation.handoff_success_rate` | Gauge | ratio | Successfully processed vs total handoffs received |

---

## Alerting Thresholds

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Plan SLA breach | `plan_generation_latency` p95 > 30,000ms for 5 min | Warning | Investigate LLM latency or route computation |
| Sustained plan SLA breach | `plan_generation_latency` p95 > 30,000ms for 15 min | Critical | Scale out ACA instances |
| Replan SLA breach | `replan_latency` p95 > 15,000ms for 5 min | Warning | Check incremental update path |
| Road data stale | `road_data_stale` = true for 15 min | Critical | Check road network data source |
| LLM unavailable | `fallback_mode_activations` > 5 in 5 min | Warning | Check Azure OpenAI status |
| Audit degradation | `audit_tier` = 2 or 3 for 5 min | Critical | Check Cosmos DB connectivity |
| Audit buffer near capacity | `audit_buffer_depth` > 8,000 | Critical | Cosmos DB likely down; file spill imminent |
| High shelter-in-place rate | `shelter_in_place_count` > 5 in 30 min | Warning | Review road network — may indicate widespread closures |
| Emergency escalations | `emergency_escalation_count` > 0 | Critical | Immediate attention — people may be trapped |
| No plans generated | `active_plans_gauge` = 0 for 10 min during active incident | Critical | Agent may be stuck or queue empty |
| High congestion risk | `congestion_risk_routes` > 50% of routes in 5 min | Warning | Corridor bottleneck — consider additional routes |
| Approaching capacity limit | `active_plans_gauge` > 40 | Warning | Nearing NFR-001 limit of 50 concurrent plans |

---

## Distributed Tracing

### Trace Context

| Field | Value |
|-------|-------|
| Service name | `evacuation-agent` |
| Correlation ID | Propagated from inbound `AgentHandoffEvent.handoff_id` |
| Parent span | Risk Assessment Agent's handoff delivery span |

### Span Hierarchy

```
evacuation.process_handoff (root)
├── evacuation.validate_handoff
├── evacuation.retrieve_assessment
├── evacuation.compute_zones
│   └── evacuation.shapely_intersection (per zone)
├── evacuation.prepare_road_network
│   └── evacuation.apply_zone_capacity_reduction
├── evacuation.compute_routes
│   ├── evacuation.dijkstra_run (per origin-destination pair)
│   └── evacuation.multi_path_distribution
├── evacuation.coordinate_transport
│   └── evacuation.query_facilities (per zone)
├── evacuation.estimate_timeline
│   └── evacuation.compute_phase (per phase)
├── evacuation.generate_summary
│   ├── evacuation.llm_call (or .template_fallback)
│   └── evacuation.content_safety_check
├── evacuation.assign_version
├── evacuation.persist_plan
└── evacuation.write_audit
```

### Replanning Span Hierarchy

```
evacuation.replan (root)
├── evacuation.evaluate_replan_trigger
├── evacuation.incremental_road_update
├── evacuation.recompute_affected_routes
├── evacuation.update_transport (if needed)
├── evacuation.reestimate_timeline
├── evacuation.generate_change_summary
├── evacuation.assign_version
├── evacuation.persist_plan
└── evacuation.write_audit
```

---

## Custom Events

| Event | When Emitted | Properties |
|-------|-------------|------------|
| `HandoffReceived` | Stage 1 complete | handoff_id, incident_id, tenant_id |
| `PlanGenerated` | Stage 9 complete | plan_id, version, confidence, routes_count, generation_method |
| `PlanUpdated` | Replan complete | plan_id, version, triggers, change_summary |
| `ShelterInPlaceRecommended` | Stage 7, no viable routes | incident_id, zone, population, hazard_type |
| `ShelterToEvacuationRecovery` | Replan recovers route | plan_id, zone, new_route_id |
| `EmergencyEscalation` | Stage 7, immediate threat + no routes | incident_id, zone, population |
| `OverrideApplied` | POST /override processed | plan_id, action, user_id, role |
| `DegradationEvent` | Any fallback activation | component (llm/cosmos/road_network), tier |
| `SLABreach` | Processing > SLA | handoff_id, actual_duration_ms, sla_type (initial/replan) |
| `VersionConflict` | Optimistic concurrency retry | incident_id, retry_count |
| `RouteConflict` | Congestion risk detected | plan_id, route_id, utilisation_pct |
| `TimeDeficitDetected` | Clearance > hazard window | plan_id, zone, deficit_minutes |
