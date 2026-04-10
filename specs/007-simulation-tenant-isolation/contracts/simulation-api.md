# Contract: Simulation API

**Feature**: 007-simulation-tenant-isolation | **Date**: 2026-04-09

## Base URL

`/api/simulations`

All endpoints require Entra ID authentication with the `SimulationUser` app role.

## Endpoints

### POST /api/simulations

Create a new simulation tenant.

**Request**:
```json
{
  "scenario_type": "cyclone",
  "jurisdictions": ["qld-fnq", "qld-nq"],
  "scenario_template_id": "qld-cyclone-multi-agency",
  "participants": ["<entra-oid-1>", "<entra-oid-2>"],
  "resource_limits": {
    "max_signals": 10000,
    "max_recommendations": 500,
    "max_duration_hours": 48
  }
}
```

**Response** (201 Created):
```json
{
  "tenant_id": "sim-a1b2c3d4-...",
  "scenario_run_id": "a1b2c3d4-...",
  "status": "provisioning",
  "created_at": "2026-04-09T10:00:00Z"
}
```

**Errors**:
- `409 Conflict` — Maximum concurrent simulations reached (FR-010)
- `403 Forbidden` — User does not have `SimulationUser` role
- `400 Bad Request` — Invalid scenario type or empty participants list

### GET /api/simulations

List all simulation tenants accessible to the authenticated user.

**Query Parameters**:
- `status` (optional): Filter by status (`active`, `paused`, `archived`)
- `limit` (optional): Default 20, max 100
- `offset` (optional): Pagination offset

**Response** (200 OK):
```json
{
  "simulations": [
    {
      "tenant_id": "sim-a1b2c3d4-...",
      "scenario_type": "cyclone",
      "status": "active",
      "created_at": "2026-04-09T10:00:00Z",
      "participant_count": 5,
      "signal_count": 342,
      "storage_bytes": 1048576
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

### GET /api/simulations/{tenantId}

Get simulation tenant details.

**Response** (200 OK): Full `SimulationTenant` document.

**Errors**:
- `403 Forbidden` — User not in participant list
- `404 Not Found` — Tenant does not exist

### POST /api/simulations/{tenantId}/pause

Pause a simulation tenant (FR-008).

**Response** (200 OK): `{"tenant_id": "...", "status": "paused"}`

**Errors**:
- `409 Conflict` — Tenant not in `active` status

### POST /api/simulations/{tenantId}/resume

Resume a paused simulation tenant.

**Response** (200 OK): `{"tenant_id": "...", "status": "active"}`

### POST /api/simulations/{tenantId}/archive

Archive a simulation tenant (FR-009). Triggers report generation, audit trail persistence, and resource cleanup.

**Response** (202 Accepted): `{"tenant_id": "...", "status": "archiving"}`

### DELETE /api/simulations/{tenantId}

Delete an archived simulation tenant. Requires admin role.

**Response** (204 No Content)

**Errors**:
- `409 Conflict` — Tenant not in `archived` status
- `403 Forbidden` — Requires admin role

### POST /api/simulations/{tenantId}/seed

Seed a simulation tenant with scenario template data (FR-012).

**Request**:
```json
{
  "template_id": "qld-cyclone-multi-agency",
  "replay_mode": "real-time"
}
```

**Response** (202 Accepted):
```json
{
  "tenant_id": "sim-a1b2c3d4-...",
  "seed_status": "seeding",
  "signal_count": 25,
  "organisation_count": 5
}
```

### POST /api/simulations/{tenantId}/seed/replay

Replay a historical live incident into a simulation tenant (FR-013).

**Request**:
```json
{
  "incident_id": "inc-xyz-...",
  "start_from": "2026-03-15T06:00:00Z",
  "end_at": "2026-03-16T18:00:00Z",
  "replay_mode": "real-time"
}
```

**Response** (202 Accepted): Replay metadata.

### POST /api/simulations/{tenantId}/participants

Add participants to a simulation tenant.

**Request**:
```json
{
  "participants": ["<entra-oid-3>"],
  "persona_assignments": [
    {"participant_oid": "<entra-oid-3>", "persona_id": "incident-commander", "org_id": "qps"}
  ]
}
```

### GET /api/simulations/{tenantId}/report

Get the exercise report for a completed simulation (FR-026).

**Response** (200 OK): Full `ExerciseReport` document.

**Errors**:
- `404 Not Found` — Report not yet generated
- `409 Conflict` — Simulation still active

## Tenant-Scoped Data Access

All existing API endpoints (`/api/signals`, `/api/recommendations`, `/api/alerts`, `/api/dashboard`, etc.) operate within the tenant context derived from the authenticated user's Entra ID token. When a user is an active participant in a simulation, the middleware resolves their `tenant_id` to the simulation's identifier, and all queries/writes are scoped to that partition.

No changes to existing endpoint signatures are needed — tenant isolation is transparent.
