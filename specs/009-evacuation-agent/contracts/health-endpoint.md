# Contract: Health Endpoint

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16  
**Type**: HTTP API contract

---

## GET /health

**SLA**: Response within 1 second under normal operation (FR-034).

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
      "last_loaded_at": "2026-04-16T08:00:00Z"
    },
    "llm_connectivity": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-16T10:30:00Z",
      "latency_ms": 350
    },
    "cosmos_connectivity": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-16T10:30:00Z"
    },
    "active_plan_count": {
      "count": 3,
      "status": "healthy | warning"
    },
    "processing_queue_depth": {
      "depth": 5,
      "status": "healthy | backpressure"
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
|-----------|---------------|
| All checks healthy | `healthy` |
| Road network not loaded (cannot compute routes) | `unhealthy` |
| Processing queue offline (cannot receive handoffs) | `unhealthy` |
| Any other check not healthy: LLM offline (template fallback active), Cosmos degraded (audit buffering), queue backpressure, active_plan_count warning | `degraded` |

> **Rationale**: Road network is critical for the Evacuation Agent — unlike LLM or Cosmos which have fallback mechanisms, route computation is impossible without the road network graph. Road network failure maps to `unhealthy` to trigger platform restart and re-loading. LLM offline and audit degradation map to `degraded` (not `unhealthy`) because the agent continues operating via template fallback (FR-033) and three-tier audit buffering (FR-028). This follows the same pattern as monitoring/risk assessment health endpoints.

### Check Details

| Check | Healthy | Degraded | Offline/Warning |
|-------|---------|----------|-----------------|
| `road_network_loaded` | Graph loaded, node/edge counts valid | Graph loaded but data is stale (> staleness window) | Graph not loaded or load failed |
| `llm_connectivity` | Last LLM call succeeded within 60s | LLM latency > 5s but responding | LLM unreachable |
| `cosmos_connectivity` | Last Cosmos write succeeded | Cosmos write retrying or throttled | Cosmos unreachable |
| `active_plan_count` | Count < 40 | — | Count ≥ 40 (approaching NFR-001 limit of 50) |
| `processing_queue_depth` | Depth < 20 | — | Depth ≥ 20 (backpressure) |
| `audit_store` | Tier 1 (Cosmos) active | Tier 2 (memory buffer) active | Tier 3 (file spill) active |

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Health check completed (status may be unhealthy) |
| 503 | Health check itself failed to execute |

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
  "incident_id": "inc-001",
  "user_id": "cmd-jane-doe",
  "role": "incident_commander",
  "justification": "New road conditions reported by ground team",
  "road_closures": [
    {
      "edge_id": "edge-015",
      "closure_reason": "fire_proximity"
    }
  ]
}
```

### Response Schema

```json
{
  "status": "replanning_initiated",
  "incident_id": "inc-001",
  "previous_plan_id": "ep-inc001-v2",
  "audit_record_id": "def456"
}
```

### Response Codes

| Code | Meaning |
|------|---------|
| 202 | Replanning initiated (async processing) |
| 404 | No active plan found for incident |
| 429 | Rate limited — replan attempted too soon (within `REPLAN_RATE_LIMIT_SECONDS`) |
| 422 | Invalid request |
