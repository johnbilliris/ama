# Contract: Health Endpoint

**Feature**: 012-risk-assessment-agent  
**Date**: 2026-04-15  
**Type**: HTTP API contract

---

## GET /health

**SLA**: Response within 1 second under normal operation.

### Response Schema

```json
{
  "status": "healthy | degraded | unhealthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-15T10:30:00Z",
  "checks": {
    "llm_connectivity": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-15T10:30:00Z",
      "latency_ms": 250
    },
    "signal_store": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-15T10:30:00Z"
    },
    "processing_queue": {
      "depth": 12,
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
| Processing queue offline (cannot receive handoffs) | `unhealthy` |
| Any other check not healthy: LLM offline (template fallback active), signal store degraded/offline, audit store buffering/degraded, queue backpressure | `degraded` |

> **Rationale**: LLM offline and audit store degradation MUST map to `degraded`, not `unhealthy`, because the agent continues operating via template fallback (FR-031) and three-tier audit buffering (CHK047). Marking these as `unhealthy` would risk platform-initiated restarts that violate Constitution Principle I (safe degradation) and FR-034 (never halt for single dependency failure). Only loss of the processing queue — which prevents all handoff intake — constitutes a genuinely unhealthy state.

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Health check completed (status may be unhealthy) |
| 503 | Health check itself failed to execute |

---

## POST /override

**Purpose**: Incident commander override of recommendation status.

### Request Schema

```json
{
  "recommendation_id": "rec-inc001-pa-001",
  "action": "approve | reject | modify",
  "user_id": "cmd-jane-doe",
  "role": "incident_commander",
  "justification": "Confirmed by ground team observation",
  "modifications": {}
}
```

### Response Schema

```json
{
  "recommendation_id": "rec-inc001-pa-001",
  "previous_status": "proposed",
  "new_status": "approved",
  "override_timestamp": "2026-04-15T10:35:00Z",
  "audit_record_id": "abc123"
}
```

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Override applied |
| 404 | Recommendation not found |
| 409 | Concurrent override conflict |
| 422 | Invalid action or missing required fields |
