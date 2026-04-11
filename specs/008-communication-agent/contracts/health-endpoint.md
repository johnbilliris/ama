# Contract: Health Endpoint & Approval API

**Date**: 2026-04-18 | **Spec**: [../spec.md](../spec.md) | **Port**: 8084

## GET /health

Reports agent readiness for container orchestration health checks. Must respond within 1 second under normal operation (SC-007).

### Response Schema

```json
{
  "status": "healthy | degraded | unhealthy",
  "agent": "communication",
  "version": "0.1.0",
  "timestamp": "2026-04-18T10:30:00Z",
  "checks": {
    "llm_connectivity": {
      "status": "healthy | degraded | unhealthy",
      "latency_ms": 150,
      "last_checked": "2026-04-18T10:29:55Z"
    },
    "cosmos_connectivity": {
      "status": "healthy | degraded | unhealthy",
      "latency_ms": 25,
      "last_checked": "2026-04-18T10:29:55Z"
    },
    "sms_service_status": {
      "status": "healthy | degraded | unhealthy",
      "last_checked": "2026-04-18T10:29:55Z"
    },
    "push_service_status": {
      "status": "healthy | degraded | unhealthy",
      "last_checked": "2026-04-18T10:29:55Z"
    },
    "broadcast_endpoint_status": {
      "status": "healthy | degraded | unhealthy",
      "last_checked": "2026-04-18T10:29:55Z"
    }
  },
  "operational": {
    "pending_approvals_count": 2,
    "active_deliveries_count": 5,
    "processing_queue_depth": 3,
    "audit_store": "cosmos | memory | file",
    "dedup_cache_size": 42
  },
  "config_hash": "a1b2c3d4..."
}
```

### Status Determination

| Overall Status | Condition |
|---------------|-----------|
| `healthy` | All checks healthy |
| `degraded` | Any non-critical check degraded (LLM, single delivery channel) |
| `unhealthy` | Cosmos DB unhealthy OR all delivery channels unhealthy |

### Response Codes

| Code | Condition |
|------|-----------|
| 200 | Agent operational (healthy or degraded) |
| 503 | Agent unhealthy (critical dependency failure) |

---

## POST /alerts/{alert_id}/approve

Commander approves an alert for public delivery. Triggers Stage 10 (multi-channel delivery).

### Authentication

- **Method**: Bearer JWT token
- **Required claim**: `role=commander` (CHK059)
- **Issuer**: Azure Entra ID (platform identity provider)

### Request

```http
POST /alerts/{alert_id}/approve
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "cmd-001",
  "role": "incident_controller"
}
```

### Response 200 — Approved

```json
{
  "alert_id": "ca-inc-001-v1",
  "status": "approved",
  "approved_by_user_id": "cmd-001",
  "approved_by_role": "incident_controller",
  "approved_at": "2026-04-18T10:35:00Z",
  "delivery_initiated": true,
  "message": "Alert approved and delivery initiated"
}
```

### Response 409 — Conflict

Returned when the alert has already been actioned by another commander (R-014).

```json
{
  "error": "conflict",
  "alert_id": "ca-inc-001-v1",
  "current_status": "approved",
  "actioned_by": "cmd-002",
  "actioned_at": "2026-04-18T10:34:55Z",
  "message": "Alert has already been approved by cmd-002"
}
```

### Response 404 — Not Found

```json
{
  "error": "not_found",
  "alert_id": "ca-inc-999-v1",
  "message": "Alert not found"
}
```

### Response 403 — Forbidden

```json
{
  "error": "forbidden",
  "message": "Insufficient role: required role=commander"
}
```

---

## POST /alerts/{alert_id}/reject

Commander rejects an alert with mandatory justification.

### Request

```http
POST /alerts/{alert_id}/reject
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "cmd-001",
  "role": "incident_controller",
  "justification": "Zone mapping incorrect — Zone 2 should extend to cover coastal suburbs"
}
```

### Response 200 — Rejected

```json
{
  "alert_id": "ca-inc-001-v1",
  "status": "rejected",
  "rejected_by_user_id": "cmd-001",
  "rejected_by_role": "incident_controller",
  "justification": "Zone mapping incorrect — Zone 2 should extend to cover coastal suburbs",
  "rejected_at": "2026-04-18T10:36:00Z",
  "message": "Alert rejected"
}
```

### Validation

- `justification` field is **required** and must be non-empty (FR-020)
- Returns 422 if `justification` is missing or empty

---

## POST /alerts/{alert_id}/modify

Commander requests modifications — creates a new alert version.

### Request

```http
POST /alerts/{alert_id}/modify
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "cmd-001",
  "role": "incident_controller",
  "modifications": {
    "audience_segments": ["zone-1-immediate", "zone-2-watch"],
    "content_overrides": {
      "en-AU": {
        "body": "Updated body text with corrected zone boundaries..."
      }
    },
    "modification_reason": "Expanding Zone 2 to include coastal suburbs based on updated wind model"
  }
}
```

### Response 200 — New Version Created

```json
{
  "original_alert_id": "ca-inc-001-v1",
  "new_alert_id": "ca-inc-001-v2",
  "new_version": 2,
  "status": "pending_review",
  "change_type": "update",
  "change_summary": "Commander modification: Expanding Zone 2 to include coastal suburbs based on updated wind model",
  "message": "New alert version created for review"
}
```

---

## POST /alerts/{alert_id}/cancel

Cancel an alert before delivery completes.

### Request

```http
POST /alerts/{alert_id}/cancel
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "cmd-001",
  "role": "incident_controller",
  "reason": "False alarm — weather conditions changed"
}
```

### Response 200 — Cancelled

```json
{
  "alert_id": "ca-inc-001-v1",
  "status": "cancelled",
  "cancelled_by_user_id": "cmd-001",
  "cancelled_at": "2026-04-18T10:37:00Z",
  "message": "Alert cancelled"
}
```

### Validation

- Only cancellable from `drafting`, `pending_review`, or `approved` (pre-delivery) states
- Returns 409 if alert is already `delivering`, `delivered`, or in a terminal state

---

## GET /alerts/{alert_id}

Retrieve a specific alert with all language variants and metadata.

### Response 200

Returns the full `PublicAlert` object as defined in [data-model.md](../data-model.md).

---

## GET /alerts/{alert_id}/delivery-status

Retrieve delivery status for an alert across all channels and segments.

### Response 200

```json
{
  "alert_id": "ca-inc-001-v1",
  "overall_status": "delivering",
  "delivery_summary": {
    "total_segments": 5,
    "total_deliveries": 15,
    "delivered": 10,
    "in_progress": 3,
    "failed": 1,
    "pending": 1,
    "completion_percentage": 66.7
  },
  "by_channel": {
    "sms": { "total": 5, "delivered": 4, "failed": 1 },
    "push": { "total": 5, "delivered": 4, "in_progress": 1 },
    "emergency_broadcast": { "total": 5, "delivered": 2, "in_progress": 2, "pending": 1 }
  },
  "records": [ ... ]
}
```

---

## Error Response Format

All error responses follow a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": { ... }
}
```

| Code | HTTP Status | Condition |
|------|-------------|-----------|
| `not_found` | 404 | Alert does not exist |
| `forbidden` | 403 | JWT invalid or insufficient role |
| `conflict` | 409 | Alert already actioned or in incompatible state |
| `validation_error` | 422 | Request body validation failed |
| `too_many_requests` | 429 | Queue at 50-alert capacity (NFR-001) |
| `service_unavailable` | 503 | Agent unhealthy |
