# API Contract Changes: Agent Specification Compliance Audit

**Feature**: 025-agent-spec-compliance  
**Date**: 2026-04-21

## Overview

This feature primarily affects inter-agent handoff contracts (internal) and adds two new infrastructure integration points. The public-facing FastAPI REST API has minimal changes — one new endpoint for dead-letter inspection.

---

## 1. Inter-Agent Handoff Contracts (Internal)

### 1a. Evacuation → Resource Allocation (F05)

**Transport**: Direct async `deliver_handoff_with_retry()` call  
**Direction**: Evacuation agent → Resource Allocation agent

```json
{
  "handoff_id": "string (UUID)",
  "incident_id": "string",
  "source_agent": "evacuation",
  "target_agent": "resource_allocation",
  "scope_key": "string (incident_scope_key)",
  "confidence": 0.85,
  "payload": {
    "transportRequirements": [
      {
        "vulnerability_category": "string",
        "estimated_vehicles": 3,
        "vehicle_type": "bus",
        "capacity_needed": 120,
        "pickup_location": { "type": "Point", "coordinates": [144.96, -37.81] },
        "dropoff_location": { "type": "Point", "coordinates": [144.98, -37.78] },
        "priority": 4
      }
    ],
    "evacuation_plan_id": "string",
    "zones_affected": ["zone-1", "zone-2"]
  },
  "tenant_id": "live",
  "status": "pending"
}
```

**Receiver**: `apps/agents/resource_allocation/pipeline.py` at L267-270 (existing handler for `source_agent == "evacuation"`).

### 1b. Resource Allocation → Communication (F06)

**Transport**: Direct async `deliver_handoff_with_retry()` call  
**Direction**: Resource Allocation agent → Communication agent

```json
{
  "handoff_id": "string (UUID)",
  "incident_id": "string",
  "source_agent": "resource_allocation",
  "target_agent": "communication",
  "scope_key": "string (incident_scope_key)",
  "confidence": 0.90,
  "payload": {
    "dispatch_type": "operational_dispatch",
    "assignments": [
      {
        "assignment_type": "personnel",
        "quantity": 15,
        "destination": { "type": "Point", "coordinates": [144.97, -37.80] },
        "destination_name": "Melbourne Convention Centre Staging",
        "assigned_agency": "CFA",
        "priority": "high",
        "resource_details": "15 firefighters with turnout gear"
      }
    ],
    "plan_id": "string",
    "incident_id": "string"
  },
  "tenant_id": "live",
  "status": "pending"
}
```

**Receiver**: `apps/agents/communication/pipeline.py` — existing handoff handler. Communication agent generates multilingual dispatch notifications for the assigned agencies.

### 1c. Monitoring → Evacuation (F04)

**Transport**: Direct async `deliver_handoff_with_retry()` call  
**Direction**: Monitoring agent → Evacuation agent

```json
{
  "handoff_id": "string (UUID)",
  "incident_id": "string",
  "source_agent": "monitoring",
  "target_agent": "evacuation",
  "scope_key": "string (incident_scope_key)",
  "confidence": 0.80,
  "payload": {
    "closure_type": "road_closure",
    "road_segment_id": "edge-042",
    "location": { "type": "Point", "coordinates": [144.95, -37.82] },
    "road_name": "Princes Freeway",
    "reason": "Flood water over roadway - depth exceeding 300mm",
    "source_signal_id": "sig-20240421-0034"
  },
  "tenant_id": "live",
  "status": "pending"
}
```

**Receiver**: `apps/agents/evacuation/pipeline.py` — new handler at pipeline entry for road closure handoffs (distinct from evacuation planning handoffs).

---

## 2. Infrastructure Integration Points

### 2a. Azure IoT Hub → Monitoring Agent (F01)

**Transport**: Azure Event Grid subscription → HTTPS webhook to Container App  
**Direction**: IoT Hub → Event Grid → Monitoring agent HTTP endpoint

**Event Grid event envelope**:
```json
{
  "specversion": "1.0",
  "type": "Microsoft.Devices.DeviceTelemetry",
  "source": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Devices/IotHubs/{hub}",
  "subject": "devices/{deviceId}",
  "data": {
    "body": {
      "sensor_type": "water_level",
      "value": 4.2,
      "unit": "metres",
      "location": { "type": "Point", "coordinates": [144.96, -37.81] }
    },
    "properties": {
      "message_id": "msg-uuid-123",
      "device_id": "sensor-flood-01"
    },
    "systemProperties": {
      "iothub-enqueuedtime": "2026-04-21T03:14:00Z"
    }
  }
}
```

**Normalisation output**: Existing `SignalEnvelope` format (in `packages/schemas/`).

### 2b. Azure AI Content Safety (F08)

**Transport**: HTTPS REST API (Azure SDK)  
**Direction**: Communication agent → Azure AI Content Safety service

**Request** (via SDK):
```python
client = ContentSafetyClient(endpoint, credential)
request = AnalyzeTextOptions(text="alert message text")
response = client.analyze_text(request)
```

**Response categories**: `Hate`, `SelfHarm`, `Sexual`, `Violence` — each with severity 0-6.  
**Pass threshold**: All categories severity ≤ 2.

---

## 3. REST API Changes (FastAPI)

### 3a. Dead-Letter Inspection Endpoint (F10/FR-003a)

**Method**: `GET`  
**Path**: `/api/v1/dead-letters`  
**Query params**:
- `incident_id` (optional): Filter by incident
- `target_agent` (optional): Filter by target agent
- `status` (optional): `dead_lettered` | `redelivered` | `permanently_failed`
- `limit` (optional, default 20): Page size
- `offset` (optional, default 0): Pagination offset

**Response** (200):
```json
{
  "items": [
    {
      "handoff_id": "string",
      "incident_id": "string",
      "source_agent": "evacuation",
      "target_agent": "resource_allocation",
      "status": "dead_lettered",
      "failure_reason": "Connection timeout after 3 retries",
      "created_at": "2026-04-21T03:14:00Z",
      "failed_at": "2026-04-21T03:19:00Z",
      "retry_count": 3,
      "payload": {}
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### 3b. Dead-Letter Redelivery Endpoint (F10/FR-003a)

**Method**: `POST`  
**Path**: `/api/v1/dead-letters/{handoff_id}/redeliver`  
**Request body**: None  
**Response** (202):
```json
{
  "handoff_id": "string",
  "status": "pending",
  "message": "Redelivery initiated"
}
```

**Error** (404): Handoff not found or not in `dead_lettered` status.

---

## 4. Management API — Radius Lookup Table (FR-006 / FR-021)

### 4a. List All Radius Entries

**Method**: `GET`  
**Path**: `/api/v1/admin/radius-lookup`  
**Auth**: Azure RBAC (`operator` or `admin` role) in production; API key in local dev  

**Response** (200):
```json
{
  "items": [
    {
      "hazard_type": "bushfire",
      "radii": { "1": 1000, "2": 2500, "3": 5000, "4": 7500, "5": 10000 },
      "last_updated": "2026-04-21T00:00:00Z",
      "updated_by": "system-seed"
    }
  ]
}
```

### 4b. Get Radius Entry

**Method**: `GET`  
**Path**: `/api/v1/admin/radius-lookup/{hazard_type}`  
**Auth**: Azure RBAC (`operator` or `admin` role) in production; API key in local dev  

**Response** (200): Single radius entry object.  
**Error** (404): Hazard type not found.

### 4c. Update Radius Entry

**Method**: `PUT`  
**Path**: `/api/v1/admin/radius-lookup/{hazard_type}`  
**Auth**: Azure RBAC (`admin` role only) in production; API key in local dev  

**Request body**:
```json
{
  "radii": { "1": 1200, "2": 3000, "3": 6000, "4": 9000, "5": 12000 }
}
```

**Response** (200): Updated entry with `last_updated` and `updated_by` set.  
**Error** (404): Hazard type not found.

### 4d. Create Radius Entry

**Method**: `POST`  
**Path**: `/api/v1/admin/radius-lookup`  
**Auth**: Azure RBAC (`admin` role only) in production; API key in local dev  

**Request body**:
```json
{
  "hazard_type": "tsunami",
  "radii": { "1": 3000, "2": 8000, "3": 15000, "4": 25000, "5": 40000 }
}
```

**Response** (201): Created entry.  
**Error** (409): Hazard type already exists.

---

## 5. Management API — Dead-Letter Permanently Failed (FR-003a update)

### 5a. Updated Dead-Letter Entry Response

The dead-letter inspection endpoint (3a) response now includes `permanently_failed` status and audit trail:

```json
{
  "items": [
    {
      "handoff_id": "string",
      "incident_id": "string",
      "source_agent": "evacuation",
      "target_agent": "resource_allocation",
      "status": "permanently_failed",
      "failure_reason": "Connection timeout after 3 auto + 1 manual retries",
      "created_at": "2026-04-21T03:14:00Z",
      "failed_at": "2026-04-21T03:19:00Z",
      "permanently_failed_at": "2026-04-21T05:22:00Z",
      "retry_count": 3,
      "auto_redeliver_attempts": 3,
      "manual_redeliver_attempts": 1,
      "failure_reasons": [
        "Auto: Connection refused (attempt 1)",
        "Auto: Connection refused (attempt 2)",
        "Auto: Timeout (attempt 3)",
        "Manual: Connection refused"
      ],
      "payload": {}
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### 5b. Permanently Failed Entries Are Read-Only

`POST /api/v1/dead-letters/{handoff_id}/redeliver` returns **409 Conflict** for entries with status `permanently_failed`:
```json
{
  "error": "permanently_failed",
  "message": "This handoff has been permanently failed and cannot be redelivered",
  "handoff_id": "string"
}
```

---

## 6. Management API — Authorization Middleware (FR-021)

All endpoints under `/api/v1/admin/*` and `/api/v1/dead-letters/*/redeliver` require authorization:

| Environment | Auth Method | Details |
|-------------|-------------|---------|
| Production  | Azure RBAC  | JWT Bearer token, Azure AD issuer, `operator` or `admin` role claim |
| Local dev   | API key     | `X-API-Key` header matching `MANAGEMENT_API_KEY` env var |

**Error responses**:
- `401 Unauthorized`: Missing or invalid credentials
- `403 Forbidden`: Valid identity but insufficient role

All auth failures are logged as structured security audit events:
```python
logger.warning("management_api_auth_failure", extra={
    "endpoint": "/api/v1/admin/radius-lookup",
    "method": "PUT",
    "reason": "insufficient_role",
    "caller_identity": "user@example.com",
    "required_role": "admin"
})
```

---

## 7. No Changes

The following existing contracts are **not modified**:
- Signal ingestion API (`/api/v1/signals`)
- Assessment retrieval API (`/api/v1/assessments`)
- Evacuation plan API (`/api/v1/evacuation-plans`)
- Resource deployment plan API (`/api/v1/deployment-plans`)
- WebSocket event stream (`/ws/events`)
- OpenAPI spec structure (additive changes only)
