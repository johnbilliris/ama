# Data Model: Evacuation Agent

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16  
**Status**: Complete

---

## Entity: AgentHandoffEvent (consumed from Risk Assessment)

**Source**: `apps/agents/common/handoffs.py` (existing shared model)  
**Direction**: Inbound from Risk Assessment Agent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Unique handoff identifier |
| `incident_id` | `str` | Yes | Associated incident ID |
| `source_agent` | `str` | Yes | Always `risk_assessment` for inbound |
| `target_agent` | `str` | Yes | Always `evacuation` for inbound |
| `scope_key` | `str` | Yes | Incident scope key for routing |
| `confidence` | `float` | Yes | Risk Assessment Agent's confidence in the escalation |
| `payload` | `dict` | Yes | `{recommendationId, summary, explanation, assessmentId}` |
| `tenant_id` | `str` | Yes | `live` or simulation tenant ID |
| `status` | `str` | Yes | `pending` → `delivered` / `retrying` / `dead_lettered` |
| `retry_count` | `int` | Yes | Current retry attempt |
| `max_retries` | `int` | Yes | Maximum retry attempts (default: 3) |
| `created_at` | `datetime` | Yes | When the handoff was created |
| `delivered_at` | `datetime \| None` | No | When successfully delivered |
| `failed_at` | `datetime \| None` | No | When permanently failed |

**Inbound payload schema** (from Risk Assessment Agent):
```json
{
  "recommendationId": "rec-inc001-ev-001",
  "summary": "Cyclone Category 4 approaching Far North Queensland coast. Evacuation recommended for coastal communities.",
  "explanation": "Based on BoM signals [sig-001, sig-002] indicating Category 4 cyclone with 18-hour landfall window...",
  "assessmentId": "ha-inc001-impact-v3"
}
```

---

## Entity: EvacuationPlan (owned — primary output)

**Storage**: Azure Cosmos DB — container `evacuation-plans`  
**Partition key**: `/incident_scope_key` (format: `{tenant_id}:{incident_id}`)  
**TTL**: None (immutable, versioned)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | `str` | Yes | Unique ID (format: `ep-{incident_id}-v{N}`) |
| `incident_id` | `str` | Yes | Associated incident |
| `version` | `int` | Yes | Monotonically increasing per incident (≥ 1) |
| `affected_area` | `dict` (GeoJSON Polygon) | Yes | Geographic boundary — may be merged union of multiple hazard polygons |
| `population_estimate` | `int` | Yes | Estimated population in affected area |
| `hazard_summary` | `HazardSummary` | Yes | Type, severity, time horizon from triggering assessment |
| `evacuation_zones` | `list[EvacuationZone]` | Yes | Zone 1, 2, 3 with boundaries and populations |
| `routes` | `list[EvacuationRoute]` | Yes | Computed evacuation routes |
| `assembly_areas` | `list[AssemblyArea]` | Yes | Designated assembly/staging areas |
| `transport_coordination` | `list[TransportRequirement]` | No | Transport needs for vulnerable populations (empty if no data) |
| `phases` | `list[EvacuationPhase]` | Yes | Five-phase timeline |
| `confidence_score` | `float` | Yes | Numeric confidence (0.0–1.0) |
| `confidence_level` | `ConfidenceLevel` | Yes | `low` (<0.4) \| `medium` (0.4–0.69) \| `high` (≥0.7) |
| `status` | `PlanStatus` | Yes | `proposed` \| `approved` \| `rejected` \| `superseded` \| `expired` \| `cancelled` \| `paused` |
| `change_summary` | `str \| None` | No | For version > 1: what changed and why |
| `generation_method` | `str` | Yes | `ai_assisted` \| `template_fallback` |
| `summary_text` | `str` | Yes | Human-readable plan summary (LLM-generated or template) |
| `assumptions` | `list[str]` | Yes | Data quality notes, missing data flags |
| `traceability` | `Traceability` | Yes | handoff_id, assessment_id, recommendation_id, input_signal_ids |
| `configuration_version` | `str` | Yes | Hash of active config values |
| `data_snapshot` | `DataSnapshot` | Yes | Road network version, population data version, facility data version |
| `override_metadata` | `OverrideMetadata \| None` | No | Populated when commander applies override |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `created_at` | `datetime` | Yes | When plan was created |
| `updated_at` | `datetime` | Yes | When status last changed |
| `valid_until` | `datetime \| None` | No | Expiry based on hazard time horizon |

**Validation rules**:
- `confidence_score` must be in [0.0, 1.0]
- `version` must be ≥ 1
- `confidence_level` derived from `confidence_score`: `low` (<0.4), `medium` (0.4–0.69), `high` (≥0.7)
- Immutable once persisted — status transitions are the only permitted mutations
- `plan_id` format must match `ep-{incident_id}-v{N}`

**Status transitions**:
```
proposed → approved       (incident commander approval)
proposed → rejected       (incident commander rejection)
proposed → superseded     (new version created)
proposed → cancelled      (incident commander cancellation)
proposed → paused         (incident commander pause)
approved → superseded     (new version approved by commander)
approved → cancelled      (incident commander cancellation)
approved → paused         (incident commander pause)
paused   → approved       (incident commander resumes)
paused   → cancelled      (incident commander cancellation)
paused   → superseded     (new version created)
superseded → (terminal)   (no further transitions)
rejected   → (terminal)   (no further transitions)
cancelled  → (terminal)   (no further transitions)
expired    → (terminal)   (no further transitions — set when valid_until elapses)
```

---

## Entity: EvacuationZone (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `zone_number` | `int` | Yes | 1 (immediate danger), 2 (likely impact), 3 (possible impact) |
| `boundary` | `dict` (GeoJSON Polygon) | Yes | Zone boundary polygon |
| `population_estimate` | `int` | Yes | Estimated population in zone |
| `vulnerable_population` | `int` | Yes | Estimated vulnerable individuals in zone |
| `evacuation_priority` | `str` | Yes | `mandatory` (Zone 1), `recommended` (Zone 2), `advisory` (Zone 3) |
| `status` | `str` | Yes | `evacuating` \| `shelter_in_place` \| `cleared` \| `pending` |

---

## Entity: EvacuationRoute (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `route_id` | `str` | Yes | Unique route identifier within the plan |
| `path` | `list[str]` | Yes | Ordered sequence of road segment edge IDs |
| `origin_zone` | `int` | Yes | Source evacuation zone number |
| `destination_assembly_area` | `str` | Yes | Assembly area ID |
| `total_distance_km` | `float` | Yes | Total route distance |
| `estimated_travel_time_normal_min` | `float` | Yes | Travel time under normal conditions (minutes) |
| `estimated_travel_time_loaded_min` | `float` | Yes | Travel time under evacuation load (minutes) |
| `capacity_vehicles_per_hour` | `int` | Yes | Minimum capacity along the route (bottleneck) |
| `estimated_utilisation_pct` | `float` | Yes | Expected capacity utilisation percentage |
| `congestion_risk` | `bool` | Yes | True if utilisation > 80% |
| `vehicle_suitability` | `dict` | Yes | `{standard: bool, heavy: bool, accessible: bool}` |
| `excluded_roads` | `list[ExcludedRoad]` | Yes | Roads excluded from this route with reasons |
| `selection_rationale` | `str` | Yes | Why this route was chosen (LLM-generated or template) |

---

## Entity: ExcludedRoad (embedded in EvacuationRoute)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edge_id` | `str` | Yes | Road segment edge ID |
| `road_name` | `str` | Yes | Human-readable road name |
| `reason` | `str` | Yes | `emergency_services_closure` \| `flood_cut` \| `fire_proximity` \| `structural_damage` \| `zone_1_closure` \| `capacity_exhausted` |

---

## Entity: TransportRequirement (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requirement_id` | `str` | Yes | Unique requirement identifier |
| `group_type` | `VulnerabilityCategory` | Yes | `mobility_impaired` \| `medical_dependent` \| `elderly_aged_care` \| `children_schools_childcare` |
| `estimated_individuals` | `int` | Yes | Number of individuals requiring transport |
| `required_vehicle_type` | `str` | Yes | `bus` \| `wheelchair_accessible_vehicle` \| `ambulance` \| `medical_transport` |
| `estimated_vehicles` | `int` | Yes | Estimated number of vehicles needed |
| `pickup_location` | `str` | Yes | Facility name/address |
| `pickup_coordinates` | `dict` | Yes | `{lat: float, lng: float}` |
| `destination_assembly_area` | `str` | Yes | Assembly area ID |
| `priority_level` | `str` | Yes | `critical` (medical) \| `immediate` (mobility/aged care) \| `high` (schools/childcare) |
| `special_considerations` | `list[str]` | No | e.g., "medical equipment", "child supervision", "oxygen supply" |
| `origin_zone` | `int` | Yes | Evacuation zone number |

**Vehicle capacity assumptions** (for computing `estimated_vehicles`):
| Vehicle Type | Capacity |
|-------------|----------|
| Bus | 50 persons |
| Wheelchair-accessible vehicle | 4 wheelchair users |
| Ambulance | 2 patients |
| Medical transport vehicle | 6 patients |

---

## Entity: EvacuationPhase (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phase_number` | `int` | Yes | 1–5 per FR-015 |
| `description` | `str` | Yes | e.g., "Zone 1 vulnerable populations" |
| `zone` | `int` | Yes | Target evacuation zone |
| `population_type` | `str` | Yes | `vulnerable` \| `general` \| `advisory` |
| `estimated_population` | `int` | Yes | Population in this phase |
| `estimated_start_time` | `datetime` | Yes | When this phase is expected to begin |
| `estimated_completion_time` | `datetime` | Yes | When this phase is expected to complete |
| `estimated_duration_min` | `float` | Yes | Duration in minutes |
| `transition_criteria` | `str` | Yes | "Previous phase 50% complete OR time threshold met" |
| `mobilisation_time_min` | `float` | Yes | Preparation time before departure |
| `travel_time_min` | `float` | Yes | Travel time along assigned routes |
| `buffer_multiplier` | `float` | Yes | 1.0 for general, 1.5 for vulnerable populations |

**Phase sequence** (per FR-015):
| Phase | Zone | Population Type | Priority |
|-------|------|----------------|----------|
| 1 | Zone 1 | Vulnerable | Highest |
| 2 | Zone 1 | General | High |
| 3 | Zone 2 | Vulnerable | Medium |
| 4 | Zone 2 | General | Medium-Low |
| 5 | Zone 3 | Advisory (all) | Lowest |

---

## Entity: HazardSummary (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hazard_type` | `str` | Yes | `bushfire` \| `cyclone` \| `flood` \| `earthquake` \| `tsunami` |
| `severity_level` | `str` | Yes | `low` \| `moderate` \| `high` \| `critical` |
| `time_horizon` | `str` | Yes | Time to impact (e.g., `18h`, `4h`) |
| `assessment_id` | `str` | Yes | Source assessment ID |
| `affected_area` | `dict` (GeoJSON) | Yes | From the HazardMap |
| `population_estimate` | `int \| None` | No | From the HazardMap |

---

## Entity: Traceability (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Triggering handoff |
| `assessment_id` | `str` | Yes | Source hazard assessment |
| `recommendation_id` | `str` | Yes | Source recommendation |
| `input_signal_ids` | `list[str]` | No | Signal IDs from the assessment (if available) |

---

## Entity: OverrideMetadata (embedded in EvacuationPlan, when applicable)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `override_by_user_id` | `str` | Yes | Commander user ID |
| `override_by_role` | `str` | Yes | e.g., `incident_commander` |
| `override_justification` | `str` | Yes | Mandatory justification text |
| `override_action_type` | `str` | Yes | `route_override` \| `zone_boundary_change` \| `phase_reprioritization` \| `cancel` \| `pause` |
| `override_timestamp` | `datetime` | Yes | When override was applied |

---

## Entity: DataSnapshot (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `road_network_version` | `str` | Yes | Version/hash of road network data used |
| `population_data_version` | `str \| None` | No | Version of population data |
| `facility_data_version` | `str \| None` | No | Version of facility registry |
| `assembly_area_version` | `str \| None` | No | Version of assembly area config |
| `snapshot_timestamp` | `datetime` | Yes | When snapshot was taken |

---

## Entity: AssemblyArea (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assembly_area_id` | `str` | Yes | Reference data ID |
| `name` | `str` | Yes | Human-readable name |
| `coordinates` | `dict` | Yes | `{lat: float, lng: float}` |
| `capacity_persons` | `int` | Yes | Maximum capacity |
| `accessibility_features` | `list[str]` | Yes | e.g., `["wheelchair_accessible", "medical_facilities"]` |
| `assigned_zones` | `list[int]` | Yes | Which zones route to this area |

---

## Entity: EvacuationDecisionRecord (owned — audit trail)

**Storage**: Azure Cosmos DB — container `evacuation-decisions`  
**Partition key**: `/incident_scope_key`  
**TTL**: None (infinite retention, append-only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` (UUID) | Yes | Unique record identifier |
| `handoff_id` | `str` | Yes | Originating handoff ID |
| `incident_id` | `str` | Yes | Associated incident |
| `plan_id` | `str \| None` | No | Resulting plan ID (when applicable) |
| `decision_type` | `DecisionType` | Yes | Processing step type (enum) |
| `confidence_level` | `float` | Yes | Confidence at time of decision |
| `processing_duration_ms` | `float` | Yes | Processing time for this step |
| `decision_rationale` | `str` | Yes | Human-readable decision explanation |
| `generation_method` | `str` | Yes | `ai_assisted` \| `template_fallback` \| `safety_fallback` |
| `agent_version` | `str` | Yes | Semantic version of agent code |
| `configuration_version` | `str` | Yes | Hash of active config |
| `plan_version` | `int \| None` | No | Plan version number (when applicable) |
| `routes_count` | `int \| None` | No | Number of routes in plan (plan_generated/plan_updated) |
| `zones_affected` | `list[int] \| None` | No | Zone numbers affected (plan_generated/plan_updated) |
| `population_estimate` | `int \| None` | No | Population covered (plan_generated/plan_updated) |
| `transport_requests_count` | `int \| None` | No | Transport requirements generated (plan_generated/plan_updated) |
| `constraints_applied` | `list[str] \| None` | No | e.g., `["road_closure:edge-005", "zone_1_capacity_reduction"]` |
| `replanning_triggers` | `list[str] \| None` | No | e.g., `["new_road_closure", "hazard_expansion"]` |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `timestamp` | `datetime` (UTC) | Yes | When recorded |
| `buffered_at` | `datetime \| None` | No | When buffered (degradation) |
| `flush_source` | `str \| None` | No | `direct` \| `memory_buffer` \| `file_buffer` |

**DecisionType enum values** (15 types):

| Value | Description |
|-------|-------------|
| `handoff_received` | Handoff acknowledged and validated |
| `handoff_rejected` | Handoff rejected (invalid structure, missing assessment) |
| `duplicate_discarded` | Duplicate handoff discarded by idempotency check |
| `assessment_retrieved` | Hazard assessment data retrieved from store |
| `road_network_loaded` | Road network data loaded/verified |
| `zones_computed` | Evacuation zones computed from hazard GeoJSON |
| `routes_computed` | Evacuation routes computed via Dijkstra's |
| `transport_coordinated` | Transport requirements generated for vulnerable populations |
| `timeline_estimated` | Phase-by-phase timeline computed |
| `plan_generated` | Complete evacuation plan produced |
| `plan_updated` | Existing plan updated via dynamic replanning |
| `override_applied` | Incident commander override recorded |
| `shelter_in_place_recommended` | Shelter-in-place recommendation issued |
| `degradation_detected` | Service degradation event (LLM, Cosmos, road data) |
| `content_safety_failure` | LLM output failed content safety validation |

---

## Entity: VersionCounter (internal — concurrency control)

**Storage**: Azure Cosmos DB — container `evacuation-plans`  
**Partition key**: `/incident_scope_key`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | `{incident_id}_plan_counter` |
| `current_version` | `int` | Yes | Current version number |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `_etag` | `str` | Auto | Cosmos DB-managed ETag for OCC |

**Concurrency pattern** (same as risk assessment):
1. Read counter + `_etag`
2. Increment `current_version`
3. `replace_item` with `If-Match: {_etag}`
4. On 412 Precondition Failed: re-read, re-increment, retry (max 3 with jitter)

---

## Entity: RoadNetwork (loaded from static JSON — not persisted to Cosmos)

**Source**: Static JSON file (path from `ROAD_NETWORK_FILE_PATH` env var)  
**Lifecycle**: Loaded at agent startup, held in memory

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | `RoadNetworkMetadata` | Version, region, coordinate system |
| `nodes` | `list[RoadNode]` | Intersections with coordinates |
| `edges` | `list[RoadEdge]` | Road segments with capacity and geometry |
| `assembly_areas` | `list[AssemblyAreaConfig]` | Pre-configured assembly areas |

**RoadNode** fields: `id`, `name`, `coordinates` (lat/lng), `type` (intersection/endpoint), `zone_membership` (computed at runtime), `is_assembly_area`

**RoadEdge** fields: `id`, `from_node`, `to_node`, `name`, `distance_km`, `capacity_vehicles_per_hour`, `surface_type` (sealed/unsealed), `accessibility_features` (list), `closure_status` (open/closed), `closure_reason` (nullable), `geometry` (GeoJSON LineString)

**Size constraints (MVP)**: Max 1,000 nodes, max 5,000 edges. Validated on load.

---

## Relationships

```
AgentHandoffEvent (from Risk Assessment)
    └── triggers → EvacuationPlan (1:1 per plan version)
        ├── contains → EvacuationZone (1:3 — zones 1, 2, 3)
        ├── contains → EvacuationRoute (1:N — multiple corridors)
        │   └── references → ExcludedRoad (0:N)
        ├── contains → TransportRequirement (0:N — one per vulnerable group)
        ├── contains → EvacuationPhase (1:5 — five-phase sequence)
        ├── contains → AssemblyArea (1:N — destination points)
        ├── contains → HazardSummary (1:1 — from assessment)
        ├── contains → Traceability (1:1 — upstream references)
        ├── contains → DataSnapshot (1:1 — reproducibility)
        └── contains → OverrideMetadata (0:1 — when overridden)

VersionCounter ──guards──→ EvacuationPlan.version (per incident)

RoadNetwork (in-memory) ──feeds──→ Route computation

All processing steps → EvacuationDecisionRecord (audit trail)
```

---

## Hazard Type → Routing Strategy Mapping

| Hazard Type | Routing Priority | Road Exclusion Strategy |
|-------------|-----------------|------------------------|
| `bushfire` | Away from fire front and downwind direction | Close roads within 2km of fire perimeter |
| `cyclone` | Inland shelters, away from coast | Close coastal roads in storm surge zone |
| `flood` | Higher ground, away from waterways | Close flood-prone roads and low-lying crossings |
| `earthquake` | Away from damaged infrastructure | Close roads near collapsed/damaged structures |
| `tsunami` | Elevated ground inland | Close all coastal and low-elevation roads |

---

## Configurable Parameters

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| Road network file path | `ROAD_NETWORK_FILE_PATH` | `data/road-network.json` | Path to static road network JSON |
| Road data staleness window | `ROAD_DATA_STALENESS_HOURS` | `6` | Hours before road data considered stale |
| Handoff dedup window | `HANDOFF_DEDUP_WINDOW_MINUTES` | `10` | Minutes for duplicate detection |
| Congestion risk threshold | `CONGESTION_RISK_THRESHOLD_PCT` | `80` | Capacity utilisation % flagged as congestion risk |
| Vulnerable population buffer | `VULNERABLE_POPULATION_BUFFER` | `1.5` | Timeline multiplier for vulnerable populations |
| Phase transition time factor | `PHASE_TRANSITION_TIME_FACTOR` | `1.2` | Time threshold = estimate × this factor |
| Phase transition population pct | `PHASE_TRANSITION_POPULATION_PCT` | `50` | Population % trigger for phase transition |
| Hazard expansion replan threshold | `HAZARD_EXPANSION_REPLAN_PCT` | `10` | Hazard area expansion % triggering replan |
| Progress delay replan threshold | `PROGRESS_DELAY_REPLAN_PCT` | `30` | Delay % triggering replan |
| Fallback confidence reduction | `FALLBACK_CONFIDENCE_REDUCTION` | `0.8` | Multiplicative reduction when LLM unavailable |
| Mobilisation time — tsunami | `MOBILISATION_TIME_TSUNAMI_MIN` | `30` | Minutes for sudden-onset events |
| Mobilisation time — flood | `MOBILISATION_TIME_FLOOD_MIN` | `120` | Minutes for slower-onset events |
| Mobilisation time — bushfire | `MOBILISATION_TIME_BUSHFIRE_MIN` | `60` | Minutes for bushfire events |
| Mobilisation time — cyclone | `MOBILISATION_TIME_CYCLONE_MIN` | `120` | Minutes for cyclone events |
| Mobilisation time — earthquake | `MOBILISATION_TIME_EARTHQUAKE_MIN` | `30` | Minutes for earthquake events |
| Audit buffer capacity | `AUDIT_BUFFER_CAPACITY` | `10000` | In-memory ring buffer size |
| Audit buffer file path | `AUDIT_BUFFER_FILE_PATH` | `/var/log/evacuation-agent/audit-buffer.jsonl` | Tier 3 spill location |
| Max summary length | `MAX_SUMMARY_LENGTH` | `1000` | Truncation limit for plan summary text |
| Replan rate limit | `REPLAN_RATE_LIMIT_SECONDS` | `30` | Minimum seconds between replans for same incident |
| Agent version | `AGENT_VERSION` | `0.1.0` | Semantic version |
