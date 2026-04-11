# Data Model: Resource Allocation Agent

**Feature**: 011-resource-allocation-agent  
**Date**: 2026-04-17  
**Status**: Complete

---

## Entity: AgentHandoffEvent (consumed from risk_assessment and evacuation)

**Source**: `apps/agents/common/handoffs.py` (existing shared model)  
**Direction**: Inbound from Risk Assessment Agent and Evacuation Agent

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Unique handoff identifier |
| `incident_id` | `str` | Yes | Associated incident ID |
| `source_agent` | `str` | Yes | Originating agent (`risk_assessment` or `evacuation`) |
| `target_agent` | `str` | Yes | Always `resource_allocation` |
| `scope_key` | `str` | Yes | Incident scope key for routing |
| `confidence` | `float` | Yes | Source agent's confidence in the escalation |
| `payload` | `dict` | Yes | Handoff-specific data (see payload schemas below) |
| `tenant_id` | `str` | Yes | `live` or simulation tenant ID |
| `status` | `str` | Yes | `pending` → `delivered` / `retrying` / `dead_lettered` |
| `retry_count` | `int` | Yes | Current retry attempt |
| `max_retries` | `int` | Yes | Maximum retry attempts (default: 3) |
| `created_at` | `datetime` | Yes | When the handoff was created |
| `delivered_at` | `datetime | None` | No | When successfully delivered |
| `failed_at` | `datetime | None` | No | When permanently failed |

**Inbound payload schema — From Risk Assessment Agent** (FR-001):
```json
{
  "recommendationId": "rec-inc001-ra-001",
  "summary": "Flood impacts requiring water tankers and medical teams",
  "explanation": "Based on signals [sig-001, sig-002], the flood extent...",
  "assessmentId": "ha-inc001-impact-v2"
}
```

**Inbound payload schema — From Evacuation Agent** (FR-005):
```json
{
  "transportRequirements": [
    {
      "requirementId": "tr-001",
      "vehicleType": "wheelchair_accessible",
      "quantity": 4,
      "pickupLocation": { "lat": -27.4698, "lon": 153.0251 },
      "priority": "critical",
      "evacuationPlanId": "ep-inc001-v3"
    }
  ],
  "evacuationPlanId": "ep-inc001-v3"
}
```

---

## Entity: ResourceDeploymentPlan (owned — primary output)

**Storage**: Azure Cosmos DB — container `resource-deployment-plans`  
**Partition key**: `/incident_scope_key` (format: `{tenant_id}:{incident_id}`)  
**TTL**: None (immutable, versioned)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | `str` | Yes | Unique identifier (format: `rdp-{incident_id}-v{N}`) |
| `incident_id` | `str` | Yes | Associated incident |
| `version` | `int` | Yes | Monotonically increasing per incident (≥1) |
| `demands` | `list[ResourceDemand]` | Yes | Identified resource demands |
| `assignments` | `list[ResourceAssignment]` | Yes | Resource-to-demand assignments |
| `unmet_demands` | `list[ShortfallDetail]` | Yes | Demands not fully met with reasoning |
| `deployment_timelines` | `list[DeploymentTimeline]` | Yes | Estimated timeline per assignment |
| `confidence_score` | `float` | Yes | Overall plan confidence (0.0–1.0) |
| `confidence_level` | `ConfidenceLevel` | Yes | `low` (<0.4) \| `medium` (0.4–0.69) \| `high` (≥0.7) |
| `status` | `PlanStatus` | Yes | `proposed` \| `approved` \| `rejected` \| `superseded` \| `cancelled` \| `expired` |
| `generation_method` | `str` | Yes | `ai_assisted` \| `template_fallback` \| `safety_fallback` |
| `configuration_version` | `str` | Yes | Hash of active config values |
| `input_snapshot` | `InputSnapshot` | Yes | Complete input data for reproducibility |
| `traceability` | `Traceability` | Yes | Handoff, recommendation, assessment, evacuation plan refs |
| `summary` | `str` | Yes | Human-readable plan summary (AIIMS terminology) |
| `trade_off_analysis` | `TradeOffAnalysis | None` | No | Cross-incident trade-off details (when applicable) |
| `override_metadata` | `OverrideMetadata | None` | No | Override details (when applicable) |
| `related_incident_ids` | `list[str]` | No | For cross-incident context (v2 expansion) |
| `expires_at` | `datetime` | Yes | Plan expiry time (default: created_at + 4 hours) |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `created_at` | `datetime` | Yes | When plan was generated |
| `updated_at` | `datetime` | Yes | When status last changed |

**Validation rules**:
- `plan_id` must match regex `^rdp-.+-v\d+$`
- `version` must be ≥ 1
- `confidence_score` must be in [0.0, 1.0]
- `confidence_level` derived from `confidence_score` using thresholds: `low` (<0.4), `medium` (0.4–0.69), `high` (≥0.7)
- `expires_at` must be after `created_at`
- Immutable once persisted — status transitions are the only permitted mutation

**Status transitions**:
```
proposed → approved     (commander approves)
proposed → rejected     (commander rejects)
proposed → superseded   (new version created for same incident)
proposed → cancelled    (commander cancels)
proposed → expired      (4-hour timeout, no action taken)
approved → superseded   (new version presented; approved plan remains until commander reviews)
```

**PlanStatus enum**: `proposed`, `approved`, `rejected`, `superseded`, `cancelled`, `expired`

---

## Entity: ResourceDemand (embedded in ResourceDeploymentPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `demand_id` | `str` | Yes | Unique demand identifier |
| `incident_id` | `str` | Yes | Associated incident |
| `source_id` | `str` | Yes | Originating coordination task ID or transport requirement ID |
| `source_type` | `str` | Yes | `coordination_task` \| `transport_requirement` |
| `resource_type` | `ResourceType` | Yes | `vehicle` \| `personnel` \| `supply` \| `facility` |
| `resource_sub_type` | `str` | Yes | Sub-type (e.g., `ambulance`, `paramedic`, `medical_kit`) |
| `required_capabilities` | `list[str]` | Yes | Required capability tags |
| `quantity` | `int` | Yes | Number of resources needed |
| `location` | `dict` | Yes | `{"lat": float, "lon": float}` or `{"locality": str}` |
| `priority_tier` | `PriorityTier` | Yes | `tier_1_life_safety` \| `tier_2_property` \| `tier_3_environment` |
| `urgency` | `UrgencyLevel` | Yes | `critical` \| `high` \| `moderate` \| `low` (normalised from AIDR) |
| `urgency_raw` | `str` | No | Original urgency before normalisation (for audit) |
| `fulfilment_status` | `DemandFulfilmentStatus` | Yes | `pending` \| `partially_met` \| `fully_met` \| `unmet` \| `closed` |
| `handoff_id` | `str` | Yes | Originating handoff ID |
| `created_at` | `datetime` | Yes | When demand was identified |

**ResourceType enum**: `vehicle`, `personnel`, `supply`, `facility`

**PriorityTier enum**: `tier_1_life_safety`, `tier_2_property`, `tier_3_environment`

**UrgencyLevel enum**: `critical`, `high`, `moderate`, `low`

**DemandFulfilmentStatus enum**: `pending`, `partially_met`, `fully_met`, `unmet`, `closed`

---

## Entity: ResourceAssignment (embedded in ResourceDeploymentPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assignment_id` | `str` | Yes | Unique assignment identifier |
| `demand_id` | `str` | Yes | Matched demand ID |
| `resource_id` | `str` | Yes | Assigned resource ID |
| `assignment_status` | `str` | Yes | `proposed` \| `approved` \| `dispatched` \| `en_route` \| `deployed` \| `completed` \| `cancelled` |
| `score` | `float` | Yes | Computed matching score |
| `scoring_rationale` | `ScoringRationale` | Yes | Why this resource was chosen |
| `estimated_travel_minutes` | `float` | Yes | Estimated travel time |
| `estimated_arrival_time` | `datetime` | Yes | Estimated arrival at demand location |
| `mobilisation_minutes` | `float` | Yes | Mobilisation overhead applied |
| `distance_km` | `float` | Yes | Haversine distance from resource to demand |
| `created_at` | `datetime` | Yes | When assignment was created |

---

## Entity: ScoringRationale (embedded in ResourceAssignment)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capability_match` | `float` | Yes | 1.0 (full match) or 0.0 (excluded) |
| `distance_km` | `float` | Yes | Haversine distance (km) |
| `distance_factor` | `float` | Yes | `1 / max(distance_km, 0.1)` |
| `availability_factor` | `float` | Yes | 1.0 (available), 0.5 (returning), 0.0 (excluded) |
| `priority_weight` | `float` | Yes | From weight table (critical=4.0, high=3.0, moderate=2.0, low=1.0) |
| `final_score` | `float` | Yes | Product of all factors |
| `selection_reason` | `str` | Yes | Human-readable explanation |
| `alternatives_considered` | `int` | Yes | Number of eligible resources evaluated |
| `tie_break_applied` | `str | None` | No | `capability_count` or `alphabetical_id` if tie-breaking used |

---

## Entity: ResourceInventoryItem (runtime state, loaded from config + dynamic updates)

**Storage**: In-memory (loaded from static JSON at startup, updated dynamically via Service Bus)  
**Persistence**: Static structure in JSON config file; runtime status in Cosmos DB for recovery

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resource_id` | `str` | Yes | Unique resource identifier |
| `resource_type` | `ResourceType` | Yes | `vehicle` \| `personnel` \| `supply` \| `facility` |
| `resource_sub_type` | `str` | Yes | Sub-type (e.g., `ambulance`, `fire_truck`, `paramedic`) |
| `capabilities` | `list[str]` | Yes | Capability tags (e.g., `[medical_transport, patient_stabilization]`) |
| `location` | `dict` | Yes | `{"lat": float, "lon": float}` |
| `status` | `ResourceStatus` | Yes | Current availability status |
| `assigned_incident_id` | `str | None` | No | Incident ID if assigned/reserved |
| `capacity` | `int | None` | No | Remaining quantity (for consumables) |
| `initial_capacity` | `int | None` | No | Original quantity (for consumables) |
| `last_status_update` | `datetime` | Yes | When status was last updated |
| `managing_org_id` | `str | None` | No | Managing organisation identifier |
| `flags` | `list[str]` | No | Operational flags: `rotation_needed`, `replenishment_needed`, `degraded` |
| `continuous_deployment_hours` | `float` | No | Hours since last rest (for personnel rotation flagging) |

**ResourceStatus enum**: `available`, `reserved`, `assigned`, `en_route`, `deployed`, `returning`, `unavailable`

**State machine transitions**:
```
available → reserved       (held for specific incident)
available → assigned       (plan generated)
reserved  → assigned       (plan generated for reserved incident)
reserved  → available      (reservation released by commander or plan expired)
assigned  → en_route       (dispatch confirmed by commander)
en_route  → deployed       (arrived on-site)
deployed  → returning      (leaving site)
returning → available      (back at base / ready for reassignment)
[any active state] → unavailable  (broken, destroyed, non-operational)
unavailable → available    (repaired, restored — commander override only)
```

**Invalid transitions** (rejected with error): `available → deployed`, `available → returning`, `assigned → available` (must go through cancellation workflow).

---

## Entity: ShortfallDetail (embedded in ResourceDeploymentPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `demand_id` | `str` | Yes | Unmet/partially met demand ID |
| `resource_type` | `ResourceType` | Yes | Type needed |
| `resource_sub_type` | `str` | Yes | Sub-type needed |
| `quantity_requested` | `int` | Yes | Total quantity demanded |
| `quantity_assigned` | `int` | Yes | Quantity actually assigned |
| `quantity_unmet` | `int` | Yes | Shortfall quantity |
| `reason` | `str` | Yes | Why demand couldn't be met (e.g., "No available ambulances in inventory") |
| `recommendation` | `str` | Yes | Suggested action (e.g., "Request mutual aid from adjacent region") |

---

## Entity: TradeOffAnalysis (embedded in ResourceDeploymentPlan, optional)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `competing_incidents` | `list[str]` | Yes | Incident IDs competing for same resources |
| `contested_resources` | `list[str]` | Yes | Resource IDs demanded by multiple incidents |
| `allocations` | `list[dict]` | Yes | `{"incident_id": str, "allocated_count": int, "demand_count": int, "priority_tier": str, "urgency": str}` |
| `reallocation_recommendations` | `list[dict]` | No | `{"from_incident": str, "to_incident": str, "resource_ids": list, "justification": str}` |
| `impact_summary` | `str` | Yes | What each affected incident loses/gains |
| `requires_commander_approval` | `bool` | Yes | Always `true` for cross-incident reallocation |

---

## Entity: AllocationDecisionRecord (owned — audit trail)

**Storage**: Azure Cosmos DB — container `resource-allocation-decisions`  
**Partition key**: `/incident_scope_key`  
**TTL**: None (infinite retention, append-only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` (UUID) | Yes | Unique record identifier |
| `handoff_id` | `str` | Yes | Originating handoff ID |
| `plan_id` | `str | None` | No | Resulting plan ID |
| `plan_version` | `int | None` | No | Plan version number |
| `demand_id` | `str | None` | No | Specific demand ID |
| `resource_id` | `str | None` | No | Specific resource ID |
| `decision_type` | `DecisionType` | Yes | Processing step type (enum) |
| `confidence_score` | `float` | Yes | Plan confidence at this step |
| `priority_tier` | `str | None` | No | Priority tier applied |
| `urgency` | `str | None` | No | Urgency level applied |
| `scoring_rationale` | `str | None` | No | Scoring explanation |
| `resources_considered` | `int | None` | No | Number of eligible resources evaluated |
| `resources_excluded_reason` | `str | None` | No | Why resources were excluded |
| `processing_duration_ms` | `float` | Yes | Processing time for this step |
| `decision_rationale` | `str` | Yes | Human-readable decision explanation |
| `generation_method` | `str` | Yes | `ai_assisted` \| `template_fallback` \| `safety_fallback` |
| `override_by_user_id` | `str | None` | No | User who performed override |
| `override_by_role` | `str | None` | No | Role of overriding user |
| `override_justification` | `str | None` | No | Reason for override |
| `agent_version` | `str` | Yes | Semantic version of agent code |
| `configuration_version` | `str` | Yes | Hash of active config |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `timestamp` | `datetime` (UTC) | Yes | When recorded |
| `buffered_at` | `datetime | None` | No | When buffered (degradation) |
| `flush_source` | `str | None` | No | `direct` \| `memory_buffer` \| `file_buffer` |

**DecisionType enum values** (16 types):

| Value | Description |
|-------|-------------|
| `handoff_received` | Handoff acknowledged and validated |
| `handoff_rejected` | Handoff rejected (invalid structure, missing incident) |
| `duplicate_discarded` | Duplicate handoff discarded by idempotency check |
| `demand_identified` | Resource demand extracted from handoff data |
| `resource_matched` | Resource matched to demand via scoring algorithm |
| `resource_excluded` | Resource evaluated but excluded (capability/type mismatch, unavailable) |
| `partial_allocation` | Demand partially met — shortfall flagged |
| `plan_generated` | Deployment plan created |
| `plan_superseded` | Previous plan version superseded |
| `plan_expired` | Plan expired without commander action |
| `override_applied` | Commander override recorded |
| `reallocation_recommended` | Cross-incident reallocation flagged |
| `transport_dispatched` | Transport dispatch request processed |
| `resource_status_updated` | Resource status transition processed |
| `degradation_detected` | Service degradation event (LLM, Cosmos, inventory) |
| `content_safety_failure` | LLM output failed content safety validation |

---

## Embedded Support Types

### Traceability

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Originating handoff |
| `recommendation_id` | `str | None` | No | From risk assessment (if applicable) |
| `assessment_id` | `str | None` | No | From risk assessment (if applicable) |
| `evacuation_plan_id` | `str | None` | No | From evacuation (if transport-related) |
| `transport_requirement_ids` | `list[str]` | No | Transport requirement IDs (if applicable) |

### OverrideMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `override_by_user_id` | `str` | Yes | User who performed override |
| `override_by_role` | `str` | Yes | Role of overriding user |
| `override_justification` | `str` | Yes | Mandatory justification text |
| `override_action_type` | `str` | Yes | `reassign` \| `add` \| `remove` \| `change_priority` \| `approve` \| `reject` \| `cancel` |
| `override_timestamp` | `datetime` | Yes | When override was performed |
| `original_plan_id` | `str` | Yes | Plan that was overridden |

### InputSnapshot

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `demands_snapshot` | `list[dict]` | Yes | All demands at generation time |
| `inventory_snapshot_hash` | `str` | Yes | Hash of resource inventory state |
| `inventory_staleness_minutes` | `float` | Yes | Age of inventory data |
| `config_version` | `str` | Yes | Configuration hash |
| `scoring_parameters` | `dict` | Yes | Priority weights, distance floor, availability factors |

### DeploymentTimeline

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assignment_id` | `str` | Yes | Related assignment |
| `resource_id` | `str` | Yes | Assigned resource |
| `mobilisation_minutes` | `float` | Yes | Mobilisation overhead (personnel=15, vehicle=10, helicopter=5) |
| `travel_minutes` | `float` | Yes | Estimated travel time |
| `total_deployment_minutes` | `float` | Yes | Mobilisation + travel |
| `estimated_departure` | `datetime` | Yes | When resource departs |
| `estimated_arrival` | `datetime` | Yes | When resource arrives at demand location |

---

## Configurable Parameters

All parameters are configurable via environment variables with sensible defaults.

### Scoring Parameters

| Parameter | Env Var | Default | Description |
|-----------|---------|---------|-------------|
| Priority weight: critical | `PRIORITY_WEIGHT_CRITICAL` | `4.0` | Scoring weight for critical urgency |
| Priority weight: high | `PRIORITY_WEIGHT_HIGH` | `3.0` | Scoring weight for high urgency |
| Priority weight: moderate | `PRIORITY_WEIGHT_MODERATE` | `2.0` | Scoring weight for moderate urgency |
| Priority weight: low | `PRIORITY_WEIGHT_LOW` | `1.0` | Scoring weight for low urgency |
| Distance floor | `DISTANCE_FLOOR_KM` | `0.1` | Minimum distance (km) to prevent division-by-zero |
| Availability: available | — | `1.0` | Fixed — not configurable |
| Availability: returning | `AVAILABILITY_RETURNING` | `0.5` | Factor for returning resources |

### Travel and Timeline Parameters

| Parameter | Env Var | Default | Description |
|-----------|---------|---------|-------------|
| Personnel speed | `TRAVEL_SPEED_PERSONNEL_KMH` | `40` | Average speed for personnel (km/h) |
| Vehicle speed | `TRAVEL_SPEED_VEHICLE_KMH` | `60` | Average speed for vehicles (km/h) |
| Helicopter speed | `TRAVEL_SPEED_HELICOPTER_KMH` | `200` | Average speed for helicopters (km/h) |
| Personnel mobilisation | `MOBILISATION_PERSONNEL_MINUTES` | `15` | Mobilisation overhead for personnel |
| Vehicle mobilisation | `MOBILISATION_VEHICLE_MINUTES` | `10` | Mobilisation overhead for vehicles |
| Helicopter mobilisation | `MOBILISATION_HELICOPTER_MINUTES` | `5` | Mobilisation overhead for helicopters |

### Operational Parameters

| Parameter | Env Var | Default | Description |
|-----------|---------|---------|-------------|
| Plan expiry | `PLAN_EXPIRY_HOURS` | `4` | Hours before unapproved plans expire |
| Dedup window | `HANDOFF_DEDUP_WINDOW_MINUTES` | `10` | Idempotency deduplication window |
| Inventory staleness | `INVENTORY_STALENESS_WINDOW_MINUTES` | `30` | Max age for last-known-good inventory |
| Rotation threshold | `ROTATION_THRESHOLD_HOURS` | `12` | Continuous deployment hours before rotation flag |
| Replenishment threshold | `REPLENISHMENT_THRESHOLD_PERCENT` | `20` | Stock percentage below which replenishment is flagged |
| Confidence base | `CONFIDENCE_BASE` | `0.9` | Base confidence for full-data plans |
| Fallback reduction | `FALLBACK_REDUCTION_FACTOR` | `0.8` | Multiplicative confidence penalty for LLM fallback |
| Stale data reduction | `STALE_DATA_REDUCTION_FACTOR` | `0.8` | Multiplicative confidence penalty for stale inventory |
| Partial data reduction | `PARTIAL_DATA_REDUCTION_FACTOR` | `0.7` | Multiplicative confidence penalty for partial inventory |
| OCC max retries | `VERSION_CONFLICT_MAX_RETRIES` | `3` | Max retries for optimistic concurrency |
| Agent version | `AGENT_VERSION` | `0.1.0` | Semantic version |
| Port | `PORT` | `8083` | HTTP server port |
| Audit buffer capacity | `AUDIT_BUFFER_CAPACITY` | `10000` | In-memory audit buffer size |
| Audit buffer file | `AUDIT_BUFFER_FILE_PATH` | `resource_allocation_audit.jsonl` | File spill path |
| Require auth | `REQUIRE_AUTH` | `true` | Enable/disable JWT validation |

---

## Relationships

```
AgentHandoffEvent (from risk_assessment/evacuation)
  └── triggers → ResourceDeploymentPlan
                    ├── contains → ResourceDemand[]
                    │                └── has → DemandFulfilmentStatus
                    ├── contains → ResourceAssignment[]
                    │                ├── has → ScoringRationale
                    │                └── has → DeploymentTimeline
                    ├── contains → ShortfallDetail[]
                    ├── contains → TradeOffAnalysis (optional)
                    ├── contains → Traceability
                    ├── contains → OverrideMetadata (optional)
                    ├── contains → InputSnapshot
                    └── produces → AllocationDecisionRecord[] (audit)

ResourceInventoryItem (runtime state)
  ├── matched to → ResourceDemand (via scoring algorithm)
  ├── assigned in → ResourceAssignment
  └── tracked by → AllocationDecisionRecord (status changes)
```
