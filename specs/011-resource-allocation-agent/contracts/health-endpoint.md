# Contract: Health Endpoint

**Feature**: 011-resource-allocation-agent  
**Date**: 2026-04-17  
**Type**: HTTP API contract

---

## GET /health

**SLA**: Response within 1 second under normal operation.

### Response Schema

```json
{
  "status": "healthy | degraded | unhealthy",
  "agent_version": "0.1.0",
  "timestamp": "2026-04-17T10:30:00Z",
  "checks": {
    "inventory_loaded": {
      "status": "healthy | degraded | offline",
      "resource_count": 150,
      "last_updated_at": "2026-04-17T10:29:00Z",
      "staleness_minutes": 1.0
    },
    "llm_connectivity": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-17T10:30:00Z",
      "latency_ms": 250
    },
    "cosmos_connectivity": {
      "status": "healthy | degraded | offline",
      "last_checked_at": "2026-04-17T10:30:00Z"
    },
    "active_plan_count": 5,
    "pending_demands": 12,
    "processing_queue": {
      "depth": 3,
      "status": "healthy | backpressure"
    },
    "audit_store": {
      "status": "healthy | buffering | degraded",
      "buffer_depth": 0,
      "current_tier": 1
    }
  }
}
```

### Status Determination

| Condition | Overall Status |
|-----------|---------------|
| All checks healthy | `healthy` |
| Processing queue offline (cannot receive handoffs) | `unhealthy` |
| Inventory not loaded AND Cosmos offline (cannot process at all) | `unhealthy` |
| Any other check not healthy: LLM offline (template fallback active), Cosmos degraded, audit store buffering/degraded, queue backpressure, inventory stale | `degraded` |

> **Rationale**: LLM offline and audit store degradation MUST map to `degraded`, not `unhealthy`, because the agent continues operating via template fallback (FR-033) and three-tier audit buffering (FR-031a). Marking these as `unhealthy` would risk platform-initiated restarts that violate Constitution Principle I (safe degradation) and FR-036 (never halt for single dependency failure). Only loss of the processing queue or complete loss of inventory AND data store — which prevents all allocation — constitutes a genuinely unhealthy state.

### Response Codes

| Code | Meaning |
|------|---------|
| 200 | Health check completed (status may be unhealthy) |
| 503 | Health check itself failed to execute |

---

## POST /override

**Purpose**: Incident commander actions on deployment plans (FR-024, FR-025, FR-026).  
**Authentication**: Requires `commander` role claim in JWT (CHK040). Returns `403 Forbidden` if role check fails.

### Request Schema

```json
{
  "plan_id": "rdp-inc001-v3",
  "action": "reassign | add | remove | change_priority | approve | reject | cancel",
  "justification": "Reassigning rescue team to support active evacuation",
  "user_id": "cmd-jane-smith",
  "role": "incident_commander",
  "details": {
    "assignment_id": "asgn-001",
    "new_resource_id": "res-helo-003",
    "new_demand_id": "dem-evac-002",
    "new_priority": "critical"
  }
}
```

### Action Details

| Action | Required Fields in `details` | Effect |
|--------|------|--------|
| `reassign` | `assignment_id`, `new_demand_id` or `new_resource_id` | Redirect resource to different demand or swap resource |
| `add` | `resource_id`, `demand_id` | Manually add a resource assignment not selected by agent |
| `remove` | `assignment_id` | Remove a resource assignment from plan |
| `change_priority` | `demand_id`, `new_priority` | Adjust demand urgency |
| `approve` | — | Transition plan status from `proposed` → `approved` |
| `reject` | — | Transition plan status to `rejected`; release resources |
| `cancel` | — | Transition plan status to `cancelled`; release resources |

### Response Schema

```json
{
  "success": true,
  "new_plan_id": "rdp-inc001-v4",
  "new_version": 4,
  "action_applied": "reassign",
  "override_record_id": "uuid-hex",
  "message": "Override applied. New plan version rdp-inc001-v4 created."
}
```

### Override Rules

- **Modify actions** (`reassign`, `add`, `remove`, `change_priority`): Create a new plan version linked to the original via `Traceability`. Original plan remains immutable and queryable. Override metadata recorded in new plan AND in audit trail.
- **Status actions** (`approve`, `reject`, `cancel`): Mutate plan status in-place (the only permitted mutation). Record override in audit trail.
- **Justification**: Mandatory for all actions (FR-024). Requests without `justification` return `400 Bad Request`.

### Error Responses

| Code | Meaning |
|------|---------|
| 200 | Override applied successfully |
| 400 | Invalid request (missing justification, invalid action, invalid plan_id format) |
| 403 | Forbidden — missing or invalid role claim |
| 404 | Plan not found |
| 409 | Conflict — plan status does not allow this action (e.g., overriding an already-approved plan with `reject`) |
| 500 | Internal error |
