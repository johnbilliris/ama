# Contract: Simulation API

**Feature**: 007-simulation-tenant-isolation | **Contract version**: 2 | **Date**: 2026-09-16

Lifecycle values use canonical Title-Case strings: `Provisioning`, `Active`, `Paused`, `Archiving`, `Archived`, and `Deleted`. Version 1 lowercase examples are superseded; clients must compare case-sensitively.

## Base URL

`/api/simulations`

All endpoints require Entra ID authentication with the `SimulationUser` app role.

## Endpoints

### POST /api/simulations

Create a new simulation tenant.

**Request**:

```json
{
  "scenario_type": "Cyclone",
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
  "status": "Active",
  "created_at": "2026-04-09T10:00:00Z"
}
```

**Errors**:

- `409 Conflict` — Maximum concurrent simulations reached (FR-010); body includes `activeSimulationIds`
- `403 Forbidden` — User does not have `SimulationUser` role
- `400 Bad Request` — Invalid scenario type or empty participants list

### GET /api/simulations

List all simulation tenants accessible to the authenticated user.

**Query Parameters**:

- `status` (optional): Filter by status (`Active`, `Paused`, `Archiving`, `Archived`)
- `limit` (optional): Default 20, max 100
- `offset` (optional): Pagination offset

**Response** (200 OK):

```json
{
  "simulations": [
    {
      "tenant_id": "sim-a1b2c3d4-...",
      "scenario_type": "Cyclone",
      "status": "Active",
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

**Response** (200 OK): `{"tenant_id": "...", "status": "Paused"}`

**Errors**:

- `409 Conflict` — Tenant not in `Active` status

### POST /api/simulations/{tenantId}/resume

Resume a paused simulation tenant.

**Response** (200 OK): `{"tenant_id": "...", "status": "Active"}`

### POST /api/simulations/{tenantId}/archive

Archive a simulation tenant (FR-009). Triggers report generation, audit trail persistence, and resource cleanup.

**Response** (202 Accepted): `{"tenant_id": "...", "status": "Archiving"}`. The resumable archive job writes the report and manifest before resource cleanup. Poll tenant detail until `Archived`.

The archive manifest enumerates the tenant's audit records (`auditEventCount`, a per-record
`eventId`/`sha256` list, and `auditSnapshotSha256`) alongside the seed snapshot. Cleanup records
removed counts and re-reads each store afterwards; a non-zero residual fails the job and the tenant
stays `Archiving` rather than reporting `Archived`. A conditional archive lease on the tenant
document means the route, the startup resume pass and the expiry worker cannot produce a second
report or manifest.

### DELETE /api/simulations/{tenantId}

Delete an archived simulation tenant after `delete_after`. Requires `simulation.admin` or `system-administrator`.
Participant membership is **not** required: retention-governed deletion is an administrator action.

Deletion removes operational tenant resources and metadata only. The exercise report and archive
manifest are immutable evidence and are retained; an authorized lookup record
(`simulation_archive_evidence`) keeps them reachable by `tenantId` after the tenant document is gone.

**Response** (204 No Content)

**Errors**:

- `409 Conflict` — Tenant is not fully `Archived` or its retention deadline has not elapsed
- `403 Forbidden` — Requires admin role

### POST /api/simulations/{tenantId}/seed

Seed a simulation tenant with scenario template data (FR-012).

**Request**:

```json
{
  "template_id": "qld-cyclone-multi-agency"
}
```

**Response** (202 Accepted):

```json
{
  "status": "accepted",
  "template_id": "qld-cyclone-multi-agency",
  "signals_injected": 0,
  "signals_scheduled": 25,
  "organisations_seeded": 5
}
```

### POST /api/simulations/{tenantId}/seed/replay

Replay a historical live incident into a simulation tenant (FR-013).

**Request**:

```json
{
  "incident_id": "inc-xyz-...",
  "start": "2026-03-15T06:00:00Z",
  "end": "2026-03-16T18:00:00Z",
  "time_compression": 10
}
```

**Response** (202 Accepted): Replay metadata.

### POST /api/simulations/{tenantId}/participants

Add participants to a simulation tenant.

**Request**:

```json
{
  "participants": [
    {
      "oid": "<entra-oid-3>",
      "persona": "incident-commander",
      "organisation_id": "qps",
      "jurisdiction_id": "qld",
      "role": "participant"
    }
  ]
}
```

### GET /api/simulations/{tenantId}/report

Get the exercise report for a completed simulation (FR-026).

**Response** (200 OK): Full `ExerciseReport` document.

**Errors**:

- `404 Not Found` — Report not yet generated
- `409 Conflict` — Simulation still active

### GET /api/simulations/reports/{reportId}

Resolve a stable report ID to its owning tenant, authorize participant membership, and return the persisted report. Missing reports return `404`; reads never generate a report.

## Tenant-Scoped Data Access

All existing API endpoints (`/api/signals`, `/api/recommendations`, `/api/alerts`, `/api/dashboard`, etc.) operate within the tenant context derived from the authenticated user's Entra ID token. An explicit `/api/simulations/{tenantId}/...` path is membership-checked. For ordinary operational routes, exactly one active membership may be inferred; multiple active memberships return `409` and require an explicit simulation path.

No changes to existing endpoint signatures are needed — tenant isolation is transparent.

## Idle Expiry Policy

Expiry is idle-based: `expires_at = last_activity_at + ttl_hours`. An accepted tenant-scoped write
refreshes `last_activity_at` and clears any pending notice.

- **Paused exercises follow the same idle policy as active ones.** Pausing the simulation clock does
  not pause the idle clock, so a paused exercise still receives its notice and is still archived
  automatically. Pausing is never an exemption from expiry.
- A notice is delivered to explicit recipients (coordinator, participants, administrators) at least
  24 hours before automatic archive and is recorded as a tenant-visible `simulation_notice` document.
- **A notice always precedes automatic archive.** When the remaining TTL is shorter than the notice
  window — including an already-expired exercise — the notice is delivered first in the same tick
  with `advance_notice_met: false`, rather than being skipped.
- Notice delivery is fail-closed: a delivery failure leaves `expiry_notice_sent_at` unset, blocks the
  archive for that tenant, and is retried on the next tick.
- A conditional expiry lease on the tenant document ensures competing workers archive an eligible
  exercise exactly once.

## Resolved Decisions

The authoritative machine-readable decision table is [contract-resolution.v2.json](contract-resolution.v2.json). It supersedes conflicting version 1 examples without weakening authentication, tenant ownership, retention, or fail-closed report behavior.
