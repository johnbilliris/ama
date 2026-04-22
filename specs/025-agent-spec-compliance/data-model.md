# Data Model: Agent Specification Compliance Audit

**Feature**: 025-agent-spec-compliance  
**Date**: 2026-04-21

## Existing Entities (Modified)

### AgentHandoffEvent

**File**: `apps/agents/common/handoffs.py` (L8-27)  
**Changes**: No schema changes. Delivery function `deliver_handoff_with_retry()` changes from sync to async. Model unchanged.

| Field | Type | Change |
|-------|------|--------|
| *All existing fields* | — | No change |

### ContentSafetyResult

**File**: `apps/agents/common/content_safety.py` (L1-5)  
**Changes**: Add `confidence` (normalized 0.0–1.0) and `validation_method` fields.

| Field | Type | Change |
|-------|------|--------|
| passed | bool | No change |
| result | str | No change |
| reason | str \| None | No change |
| confidence | float | **NEW** — Normalized 0.0–1.0 (see mapping below) |
| validation_method | str | **NEW** — `"azure_ai"`, `"factual"`, `"tone"`, or `"keyword_fallback"` |
| review_flag | bool | **NEW** — `True` when validated via keyword fallback (FR-009); default `False` |

**Confidence mapping** (R13):
- Azure AI Content Safety: `severity / 6.0` (0→0.0, 6→1.0)
- Factual consistency: match=0.0, mismatch=1.0
- Tone check: pass=0.0, fail=1.0
- Keyword fallback: severity-based heuristic 0.0–1.0

### HazardAssessment

**File**: `packages/domain/src/domain/models/hazard_assessment.py` (L19-65)  
**Changes**: No schema changes. The existing `hazard_map: HazardMap | None` field is populated by the new `HazardMapGenerator` stage.

### HazardMap

**File**: `packages/domain/src/domain/models/hazard_assessment.py` (L5-16)  
**Changes**: No schema changes. `affected_area` field receives properly generated GeoJSON Polygon/MultiPolygon.

**Validation rules** (enforced in generator, not model):
- `affected_area` must be a valid GeoJSON Polygon or MultiPolygon
- `affected_area.coordinates` must use EPSG:4326 (WGS84) CRS
- `confidence_score` must be ≥ 0.0 and ≤ 1.0
- `severity_level` must match the highest severity of merged input signals

---

## New Entities

### HazardRadiusLookup (F03 / FR-006)

**File**: `apps/agents/risk_assessment/hazard_radius.py` (NEW)  
**Storage**: Cosmos DB collection `radius_lookup`  
**Purpose**: Admin-editable severity-indexed radius lookup table per hazard type for GeoJSON polygon generation. Changes take effect on next generation without restart.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Cosmos DB document ID = hazard_type |
| hazard_type | str | Key: hazard classification (bushfire, flood, cyclone, etc.) |
| radii | dict[str, float] | Map of severity ("1"–"5") → radius in metres |
| last_updated | datetime | Timestamp of last modification |
| updated_by | str | Identity that last modified the entry |

**Cosmos DB document** (R12):
```json
{
  "id": "bushfire",
  "hazard_type": "bushfire",
  "radii": { "1": 1000, "2": 2500, "3": 5000, "4": 7500, "5": 10000 },
  "last_updated": "2026-04-21T00:00:00Z",
  "updated_by": "system-seed"
}
```

**Seed data** (5 hazard types, severity 1–5):
- bushfire: 1000 / 2500 / 5000 / 7500 / 10000 m
- flood: 500 / 1500 / 3000 / 4500 / 5000 m
- earthquake: 2000 / 5000 / 10000 / 15000 / 20000 m
- cyclone: 5000 / 15000 / 30000 / 40000 / 50000 m
- chemical_spill: 200 / 500 / 1000 / 1500 / 2000 m

**Management API**: CRUD under `/api/v1/admin/radius-lookup` (R12, FR-021 RBAC)

### TransportHandoffPayload (F05)

**Purpose**: Payload schema for Evacuation → Resource Allocation handoff.  
**Carried inside**: `AgentHandoffEvent.payload`

| Field | Type | Constraints |
|-------|------|-------------|
| transportRequirements | list[TransportRequirement] | Non-empty |
| evacuation_plan_id | str | References EvacuationPlan.plan_id |
| zones_affected | list[str] | Zone identifiers |

**TransportRequirement** (nested):

| Field | Type | Constraints |
|-------|------|-------------|
| vulnerability_category | str | e.g., "mobility_impaired", "elderly", "general" |
| estimated_vehicles | int | ≥ 1 |
| vehicle_type | str | e.g., "bus", "ambulance", "wheelchair_transport" |
| capacity_needed | int | ≥ 1 |
| pickup_location | dict | GeoJSON Point |
| dropoff_location | dict | GeoJSON Point |
| priority | int | 1–5 (aligned with hazard severity, 5=critical) |

### NamedLocation (FR-004a)

**File**: `apps/agents/risk_assessment/named_locations.py` (NEW)  
**Storage**: Cosmos DB collection `named_locations`  
**Purpose**: Device name / location identifier → coordinate lookup for signals missing lat/lon.

| Field | Type | Description |
|-------|------|-------------|
| location_id | str | Device name or location identifier (partition key) |
| display_name | str | Human-readable name |
| latitude | float | WGS84 latitude |
| longitude | float | WGS84 longitude |
| last_updated | datetime | Timestamp of last modification |

**Behaviour**: Risk Assessment agent queries by `location_id` when signal has no coordinates. On match → use resolved (lat, lon) and log resolution. On miss → reject signal with validation error.

### ContentSafetyCircuitBreaker (FR-009)

**File**: `apps/agents/common/circuit_breaker.py` (NEW)  
**Purpose**: Wraps Azure AI Content Safety calls with circuit breaker pattern.

| Field | Type | Description |
|-------|------|-------------|
| state | str | `"closed"` \| `"open"` \| `"half_open"` |
| failure_count | int | Consecutive Azure AI failures (resets on success) |
| trip_threshold | int | Failures to trip (default 3) |
| cooldown_seconds | float | Seconds to wait before probe (default 60) |
| last_failure_at | datetime \| None | Timestamp of last failure |
| fallback_message_count | int | Messages validated via keyword fallback since circuit opened |

**State machine**: CLOSED → (3 failures) → OPEN → (60s) → HALF_OPEN → (probe success) → CLOSED / (probe fail) → OPEN

### DeadLetterEntry (FR-003a update)

**File**: `apps/agents/common/dead_letters.py` (UPDATED)  
**Changes**: Add `permanently_failed` status, audit trail fields.

| Field | Type | Change |
|-------|------|--------|
| status | str | **UPDATED** — add `"permanently_failed"` value |
| auto_redeliver_attempts | int | **NEW** — count of auto redelivery attempts (max 3) |
| manual_redeliver_attempts | int | **NEW** — count of manual redelivery attempts |
| failure_reasons | list[str] | **NEW** — reason for each failed attempt |
| permanently_failed_at | datetime \| None | **NEW** — timestamp when marked permanently failed |

### DispatchHandoffPayload (F06)

**Purpose**: Payload schema for Resource Allocation → Communication handoff.  
**Carried inside**: `AgentHandoffEvent.payload`

| Field | Type | Constraints |
|-------|------|-------------|
| dispatch_type | str | Always `"operational_dispatch"` |
| assignments | list[DispatchAssignment] | Non-empty |
| plan_id | str | References ResourceDeploymentPlan.plan_id |
| incident_id | str | Matches parent incident |

**DispatchAssignment** (nested):

| Field | Type | Constraints |
|-------|------|-------------|
| assignment_type | str | "personnel" \| "supply" |
| quantity | int | ≥ 1 |
| destination | dict | GeoJSON Point |
| destination_name | str | Human-readable location |
| assigned_agency | str | Agency identifier |
| priority | str | "critical" \| "high" \| "moderate" \| "low" |
| resource_details | str | Description of assigned resources |

**Priority mapping** (TransportRequirement `int` → DispatchAssignment `str`):
- 5 → `"critical"`
- 4 → `"high"`
- 3 → `"moderate"`
- 1–2 → `"low"`

### RoadClosureSignalPayload (F04)

**Purpose**: Payload schema for Monitoring → Evacuation road closure handoff.  
**Carried inside**: `AgentHandoffEvent.payload`

| Field | Type | Constraints |
|-------|------|-------------|
| closure_type | str | "road_closure" \| "road_reopening" |
| road_segment_id | str \| None | If known edge ID |
| location | dict \| None | GeoJSON Point for nearest-edge lookup |
| road_name | str \| None | Human-readable name |
| reason | str | Why the road is closed/reopened |
| source_signal_id | str | References originating SignalEnvelope |

### IoTSignalMessage (F01 / FR-018)

**Purpose**: Raw IoT device message before normalisation to SignalEnvelope.  
**Received from**: Azure IoT Hub via Event Grid.

| Field | Type | Constraints |
|-------|------|-------------|
| device_id | str | IoT Hub device identity |
| sequence_number | int | Device-assigned sequence for dedup (composite key with device_id) |
| message_id | str | IoT Hub message ID (backup dedup) |
| timestamp | datetime | Device-reported time |
| sensor_type | str | e.g., "temperature", "water_level", "wind_speed", "seismic" |
| value | float | Sensor reading |
| unit | str | Measurement unit |
| location | dict | GeoJSON Point |
| metadata | dict | Device-specific extra fields |

**Normalisation target**: Existing `SignalEnvelope` in `packages/schemas/`

---

## State Transitions

### AgentHandoffEvent Status (existing, extended per FR-003a)

```
pending → delivered           (successful delivery)
pending → failed              (temporary failure, retrying)
failed  → pending             (retry attempt)
failed  → dead_lettered       (max retries exhausted)
dead_lettered → pending       (auto/manual redelivery attempt)
dead_lettered → permanently_failed  (3 auto + 1 manual redelivery failed)
```

`permanently_failed` is a terminal state — read-only with full audit trail, no further retries.

### ContentSafetyResult.result (extended)

```
"passed"               → content safe (Azure AI or keyword check)
"failed_with_fallback" → content unsafe, needs human review
"azure_ai_unavailable" → fallback to keyword check (flagged)
```

### RoadEdge.closure_status (existing, unchanged)

```
"open"   → "closed"   (via apply_closure)
"closed" → "open"     (via remove_closure)
```

---

## Relationships

```
SignalEnvelope (monitoring)
    ├──→ HazardAssessment (risk_assessment)
    │       └── HazardMap (affected_area GeoJSON)
    │
    ├──→ RoadClosureSignalPayload (F04: monitoring → evacuation)
    │
    └──→ IoTSignalMessage (F01: IoT Hub → monitoring adapter)

HazardAssessment
    └──→ EvacuationPlan (evacuation)
            ├── TransportHandoffPayload (F05: evacuation → resource_allocation)
            └── RoadNetwork.apply_closure() (F04: dynamic updates)

ResourceDeploymentPlan
    └──→ DispatchHandoffPayload (F06: resource_allocation → communication)

Communication Agent
    └── ContentSafetyValidator (F08: Azure AI Content Safety)
    │       └── ContentSafetyCircuitBreaker (FR-009)
    └── _compute_similarity() (F09: embedding-based)

HazardRadiusLookup (Cosmos DB)
    └──→ HazardMapGenerator (reads radius per hazard_type + severity)

NamedLocation (Cosmos DB)
    └──→ HazardMapGenerator (coordinate resolution for signals without lat/lon)

DeadLetterEntry
    └── pending → dead_lettered → permanently_failed (terminal)
```
