# Data Model: Simulation-as-Tenant

**Feature**: 007-simulation-tenant-isolation | **Date**: 2026-04-09

## Entity Relationship Overview

```
ScenarioTemplate 1──* SimulationTenant 1──1 ScenarioRun
                                        1──* SimulationSignal
                                        1──* ExerciseReport
                                        1──* TenantContext (request-scoped)
```

### Storage Note

"Immutable storage" referenced throughout this specification means Azure Blob Storage with a **time-based retention policy** (WORM — Write Once, Read Many) applied at the container level. The `simulation/{tenant_id}/archive/` blob prefix uses append blobs for audit trail writes during active simulation and block blobs with immutability policies during archival. Retention period aligns with `simulation_archive_retention_days` (default: 90 days).

## Entities

### SimulationTenant (NEW)

**Container**: `simulation` | **Partition Key**: `/scenario_id`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Document ID = `tenant_id` |
| `tenant_id` | string | Yes | `sim-{scenarioRunId}` |
| `scenario_id` | string | Yes | Partition key, equals `scenario_run_id` |
| `scenario_run_id` | string | Yes | FK to ScenarioRun |
| `scenario_type` | enum | Yes | `bushfire` \| `flood` \| `cyclone` \| `cross-jurisdiction` |
| `scenario_template_id` | string | No | FK to ScenarioTemplate (if created from template) |
| `status` | enum | Yes | `provisioning` \| `active` \| `paused` \| `archiving` \| `archived` \| `deleted` |
| `created_by` | string | Yes | Entra ID object ID of exercise coordinator |
| `created_at` | datetime | Yes | ISO 8601 UTC |
| `ttl_hours` | int | Yes | Default: 72 |
| `expires_at` | datetime | Yes | `created_at + ttl_hours` |
| `participants` | list[string] | Yes | Entra ID object IDs of users granted access |
| `jurisdictions` | list[string] | Yes | Jurisdiction IDs scoped to this simulation |
| `resource_limits` | object | Yes | `{max_signals, max_recommendations, max_duration_hours}` |
| `resource_consumption` | object | Yes | `{signal_count, recommendation_count, storage_bytes, cache_keys}` |
| `throttle_mode` | enum | Yes | `normal` \| `throttled` \| `incident-throttled` |
| `throttle_quota_pct` | int | Yes | Default: 100; set to 20 during live incidents |
| `exercise_report_uri` | string | No | Blob URI of generated report |
| `archive_uri` | string | No | Blob prefix for archived data |
| `document_type` | string | Yes | `"simulation_tenant"` (discriminator) |

**Validation Rules**:
- `tenant_id` must match pattern `^sim-[a-z0-9-]{36}$`
- `participants` must contain at least `created_by`
- `status` transitions: `provisioning → active → paused ↔ active → archiving → archived → deleted`
- `resource_limits.max_signals` default: 10,000

### ScenarioTemplate (NEW)

**Container**: `seed` | **Partition Key**: `/kind` (value: `"scenario_template"`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Template identifier |
| `template_id` | string | Yes | Human-friendly ID (e.g., `qld-cyclone-multi-agency`) |
| `kind` | string | Yes | `"scenario_template"` (partition key) |
| `scenario_type` | enum | Yes | `bushfire` \| `flood` \| `cyclone` \| `cross-jurisdiction` |
| `name` | string | Yes | Display name |
| `description` | string | Yes | Exercise description |
| `seed_organisations` | list[object] | Yes | `[{org_id, name, type, jurisdiction_ids}]` |
| `seed_jurisdictions` | list[string] | Yes | Jurisdiction IDs |
| `seed_framework_ids` | list[string] | Yes | AIIMS framework config references |
| `signal_timeline` | list[object] | Yes | `[{offset_seconds, signal_envelope}]` |
| `benchmark_targets` | object | Yes | `{time_to_first_recommendation_s, time_to_alert_s, coordination_coverage_pct}` |
| `document_type` | string | Yes | `"scenario_template"` (discriminator) |

**Validation Rules**:
- `signal_timeline` entries must have non-negative `offset_seconds`, sorted ascending
- `signal_timeline[].signal_envelope` must conform to the signal-envelope schema
- `benchmark_targets` values must be positive numbers

### ScenarioRun (EXTENDED)

**Container**: `simulation` | **Partition Key**: `/scenario_id`

Existing fields preserved. New fields added:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | string | Yes | `sim-{scenario_run_id}` (FK to SimulationTenant) |
| `exercise_report_uri` | string | No | Blob URI when report generated |
| `archive_status` | enum | No | `pending` \| `archived` \| `failed` |
| `resource_consumption` | object | No | `{signal_count, recommendation_count, elapsed_hours}` |
| `document_type` | string | Yes | `"scenario_run"` (discriminator) |

### SimulationSignal (CLARIFICATION)

Not a separate entity. A `Signal` stored in the `signals` container with `scope = sim-{scenarioRunId}` in its multi-hash partition key. The `provenance.source_context` field is set to `"simulation"`. No schema changes to the Signal model are needed — the partition key discriminates tenant ownership.

### ExerciseReport (NEW)

**Storage**: Azure Blob Storage (`simulation/{tenant_id}/reports/{report_id}.json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_id` | string | Yes | UUID |
| `tenant_id` | string | Yes | `sim-{scenarioRunId}` |
| `scenario_run_id` | string | Yes | FK to ScenarioRun |
| `scenario_type` | enum | Yes | `bushfire` \| `flood` \| `cyclone` \| `cross-jurisdiction` |
| `generated_at` | datetime | Yes | ISO 8601 UTC |
| `exercise_timeline` | list[object] | Yes | Chronological event list |
| `participating_organisations` | list[object] | Yes | `[{org_id, name, persona_count}]` |
| `participating_personas` | list[object] | Yes | `[{persona_id, role, org_id}]` |
| `signal_summary` | object | Yes | `{total, by_category: {weather: N, fire: N, ...}}` |
| `recommendation_summary` | object | Yes | `{total, approved, rejected, escalated, avg_approval_time_s}` |
| `alert_summary` | object | Yes | `{total, published_simulation, blocked_channels}` |
| `coordination_gaps` | list[string] | Yes | Identified gaps |
| `performance_metrics` | object | Yes | `{time_to_first_recommendation_s, time_to_alert_publication_s, coordination_coverage_pct}` |
| `benchmark_comparison` | object | No | `{target: {...}, actual: {...}, delta: {...}}` |

### TenantContext (EXTENDED)

**Scope**: Request-level value object (not persisted)

| Field | Type | Description |
|-------|------|-------------|
| `tenant_id` | string | `live` or `sim-{scenarioRunId}` |
| `agency_id` | string | From Entra ID claims |
| `jurisdiction_ids` | tuple[str] | From Entra ID claims |
| `persona_id` | string \| None | From Entra ID claims |

**Derived Properties**:
- `is_simulation` → `tenant_id != "live"`
- `scope_key` → `{tenant_id}:{agency_id}:{sorted_jurisdictions}`

## State Transitions

### SimulationTenant Lifecycle

```
provisioning ──→ active ──→ paused
                   ↑          │
                   └──────────┘
                   │
                   ↓
               archiving ──→ archived ──→ deleted
```

| Transition | Trigger | Side Effects |
|------------|---------|--------------|
| provisioning → active | Storage partition + cache namespace created | Tenant available for signal injection |
| active → paused | Coordinator action or admin action | Signal injection suspended; state preserved |
| paused → active | Coordinator action | Signal injection resumed |
| active → archiving | Coordinator action, admin action, or TTL expiry | Report generated; audit trail to blob storage |
| archiving → archived | Archive complete | Cosmos partition cleaned; cache keys deleted |
| archived → deleted | Admin action (after retention period) | Blob archive deleted |

## Indexes

### signals container (existing — no changes)

Existing composite indexes on `jurisdictionId + category + occurredAt` continue to work. The `scope` field in the multi-hash partition key provides tenant isolation without additional indexes.

### simulation container

| Index | Fields | Purpose |
|-------|--------|---------|
| Composite 1 | `document_type + status` | List active simulation tenants |
| Composite 2 | `document_type + created_at` | Sort simulations by creation date |
| Composite 3 | `document_type + expires_at` | TTL expiry queries |
