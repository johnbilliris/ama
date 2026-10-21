# Contract: Health Endpoint

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16  
**Type**: HTTP API contract

---

## GET /health

**SLA**: Response within 1 second under normal operation (FR-034).

This endpoint is a pure snapshot read. It does not call the LLM, Cosmos DB, or Service Bus. Dependency outcomes are
maintained by background/runtime producers, and audit health uses a non-blocking cached snapshot when an audit append
or recovery flush is in progress. The endpoint always returns HTTP `200`; callers determine capability from the body.

### Response Schema

```json
{
  "status": "healthy | degraded | unhealthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-16T10:30:00Z",
  "checks": {
    "road_network_loaded": {
      "status": "healthy | degraded | offline",
      "node_count": 500,
      "edge_count": 2100,
      "stale": false,
      "last_loaded_at": "2026-04-16T08:00:00Z",
      "source_updated_at": "2026-04-16T07:55:00Z"
    },
    "llm_connectivity": {
      "status": "unknown | healthy | degraded | offline",
      "last_checked_at": "2026-04-16T10:30:00Z",
      "last_successful_at": "2026-04-16T10:30:00Z",
      "latency_ms": 350
    },
    "cosmos_connectivity": {
      "status": "unknown | healthy | degraded | not_configured",
      "last_checked_at": "2026-04-16T10:30:00Z",
      "last_successful_at": "2026-04-16T10:30:00Z",
      "latency_ms": null
    },
    "active_plan_count": {
      "count": 3,
      "status": "healthy | warning"
    },
    "processing_queue_depth": {
      "depth": 5,
      "status": "healthy | backpressure | reconnecting | offline | not_configured",
      "connected": true,
      "last_checked_at": "2026-04-16T10:30:00Z",
      "last_successful_at": "2026-04-16T10:30:00Z"
    },
    "audit_store": {
      "status": "healthy | buffering | degraded",
      "buffer_depth": 0
    }
  }
}
```

### Status Determination

| Condition | Overall Status |
| --- | --- |
| All checks healthy | `healthy` |
| Road network not loaded (cannot compute routes) | `unhealthy` |
| Processing queue offline (cannot receive handoffs) | `unhealthy` |
| Any other check not healthy: stale roads, LLM offline/unknown, Cosmos degraded/unknown, queue reconnecting/backpressure, active-plan warning, or audit buffering/degradation | `degraded` |

> **Rationale**: The road graph and connected intake queue are critical capabilities. LLM and audit degradation retain
> deterministic template fallback and the durable audit WAL, so those states remain `degraded`. Platform probes use
> `/ready`, where an `unhealthy` snapshot produces HTTP `503`.

### State Producers

| State | Producer |
| --- | --- |
| Road network | Atomic loader state and source-time freshness from `metadata.last_updated` |
| LLM | Background monitor every 30 seconds; each probe is bounded to 500 ms and overlapping probes are not started |
| Cosmos DB | Actual plan persistence, lifecycle, override, and replan outcomes; object construction is not success |
| Active plans | Successful persisted-plan counts plus committed lifecycle and terminal override transitions |
| Processing queue | Service Bus connect/reconnect/offline transitions and in-flight message increments/decrements |
| Audit store | Cosmos delivery, bounded memory cache, durable JSONL WAL backlog, corruption, and rejected writes |

### Check Details

| Check | Healthy | Degraded | Offline/Warning |
| --- | --- | --- | --- |
| `road_network_loaded` | Graph loaded, node/edge counts valid, source fresh | Graph loaded but source data is stale | Graph not loaded or invalid |
| `llm_connectivity` | Background probe completed within its bound | Explicit degraded cached outcome | Probe failed/timed out; `unknown` before first probe |
| `cosmos_connectivity` | Last tracked plan-store operation succeeded | Last tracked operation failed | `unknown` before the first operation; `not_configured` locally |
| `active_plan_count` | Count 0-39 | — | Count 40 or greater (`warning`, approaching NFR-001 limit of 50) |
| `processing_queue_depth` | Connected with depth 0-19 | Reconnecting or not configured | Connected at depth 20 or greater (`backpressure`), or disconnected (`offline`) |
| `audit_store` | Tier 1 (Cosmos) active | Tier 2 (memory buffer) active | Tier 3 (file spill) active |

### Response Codes

| Code | Meaning |
| --- | --- |
| 200 | Cached health snapshot returned; body status may be `unhealthy` |

---

## GET /live

Process liveness probe. Returns HTTP `200` with `{"status":"live"}` while the HTTP process can serve requests. It
does not evaluate dependencies.

---

## GET /ready

Platform readiness probe. Returns the same six-check response as `/health` without dependency I/O.

| Code | Meaning |
| --- | --- |
| 200 | Overall body status is `healthy` or `degraded`; processing can continue with documented fallbacks |
| 503 | Overall body status is `unhealthy`; the road graph or intake queue is unavailable |

---

## POST /override

**Purpose**: Incident commander override of evacuation plan.

### Request Schema

```json
{
  "plan_id": "ep-inc001-v2",
  "action": "approve | reject | cancel | pause | resume | modify",
  "user_id": "cmd-jane-doe",
  "role": "incident_commander",
  "justification": "Ground team confirmed route A is passable. Overriding agent route recommendation.",
  "modifications": {
    "override_type": "route_override | zone_boundary_change | phase_reprioritization",
    "details": {}
  }
}
```

**Action semantics**:

| Action | Description | Status Transition |
|--------|-------------|-------------------|
| `approve` | Approve proposed plan for execution | `proposed` → `approved` |
| `reject` | Reject proposed plan | `proposed` → `rejected` |
| `cancel` | Cancel an active plan | `proposed`/`approved`/`paused` → `cancelled` |
| `pause` | Pause an active plan | `proposed`/`approved` → `paused` |
| `resume` | Resume a paused plan | `paused` → `approved` |
| `modify` | Apply modifications, create new version | Creates `v{N+1}` with modifications |

### Response Schema

```json
{
  "plan_id": "ep-inc001-v2",
  "previous_status": "proposed",
  "new_status": "approved",
  "override_timestamp": "2026-04-16T10:35:00Z",
  "audit_record_id": "abc123",
  "new_version_plan_id": null
}
```

For `modify` actions, `new_version_plan_id` contains the ID of the newly created plan version.

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Override applied |
| 404 | Plan not found |
| 409 | Concurrent override conflict (another override in progress) |
| 422 | Invalid action, invalid status transition, or missing required fields |

---

## POST /replan

**Purpose**: Manual replanning trigger by incident commander (FR-016e).

### Request Schema

```json
{
  "plan_id": "ep-inc-001-v2",
  "incident_id": "inc-001",
  "update_id": "ground-report-20260416T1035Z",
  "base_plan_version": 2,
  "observed_at": "2026-04-16T10:35:00Z",
  "user_id": "cmd-jane-doe",
  "role": "incident_commander",
  "justification": "New road conditions reported by ground team",
  "new_road_closures": ["edge-015"],
  "updated_zones": null,
  "progress_completed_pct": 40,
  "expected_progress_pct": 80,
  "new_severity": "critical",
  "manual_trigger": false,
  "shelter_zones_with_new_routes": []
}
```

`user_id` and `role` are optional assertions only; verified bearer claims remain authoritative. Geometry expansion is derived from `updated_zones`, progress delay is derived from completed versus expected progress, severity is compared with the persisted source plan, and closures trigger only when they intersect a persisted active route. `update_id`, source version, and timezone-aware observation time are mandatory.

### Response Schema

```json
{
  "status": "plan_version_created",
  "incident_id": "inc-001",
  "previous_plan_id": "ep-inc001-v2",
  "new_plan_id": "ep-inc001-v3",
  "audit_record_id": "def456",
  "triggered": true,
  "triggers": ["road_closure: 1 active-route closure(s) — edge-015"],
  "material_change": true,
  "change_summary": "Triggers: road_closure... Closed roads excluded: ['edge-015']."
}
```

When evidence contains no trigger or produces no structured change, the endpoint returns `200` with `status=unchanged`, `new_plan_id=null`, and an audit ID. A committed linked version returns `202`.

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Update evaluated and audited; no material plan version created |
| 202 | Material replan committed as a linked proposed version |
| 404 | No active plan found for incident |
| 429 | Rate limited — replan attempted too soon (within `REPLAN_RATE_LIMIT_SECONDS`) |
| 409 | Source ETag or atomic version reservation conflict |
| 422 | Invalid, stale, out-of-order, or unsupported update evidence |
