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
| `estimated_completion_minutes` | `int \| None` | Yes | Finite completion estimate, or `null` when any required movement is blocked |
| `zone_dispositions` | `list[ZoneDisposition]` | Yes | Exactly one reconciled movement/shelter outcome per zone |
| `confidence_score` | `float` | Yes | Numeric confidence (0.0–1.0) |
| `confidence_level` | `ConfidenceLevel` | Yes | `low` (<0.4) \| `medium` (0.4–0.69) \| `high` (≥0.7) |
| `status` | `PlanStatus` | Yes | `proposed` \| `approved` \| `rejected` \| `superseded` \| `expired` \| `cancelled` \| `paused` |
| `change_summary` | `str \| None` | No | For version > 1: what changed and why |
| `generation_method` | `str` | Yes | `ai_assisted` \| `template_fallback` \| `safety_fallback` |
| `summary_text` | `str` | Yes | Bounded deterministic fact summary, with optional pre-approved model acknowledgement |
| `summary_grounding_result` | `str` | Yes | `grounded`, deterministic fallback/update, or the rejected-output reason |
| `content_safety_result` | `str` | Yes | Validator outcome for the model contribution |
| `content_safety_validation_method` | `str` | No | Azure AI, keyword fallback, language check, or other validator method |
| `content_safety_reason` / `content_safety_reference` | `str` | No | Failure reason and restricted evidence reference |
| `model_deployment_id` | `str` | No | Deployment used for validated model assistance |
| `assumptions` | `list[str]` | Yes | Data quality notes, missing data flags |
| `traceability` | `Traceability` | Yes | handoff_id, assessment_id, recommendation_id, input_signal_ids |
| `configuration_version` | `str` | Yes | Hash of active config values |
| `data_snapshot` | `DataSnapshot` | Yes | Road network version, population data version, facility data version |
| `override_metadata` | `OverrideMetadata \| None` | No | Populated when commander applies override |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `simulation` | `bool` | Yes | Explicit review label; `true` for every non-live tenant |
| `created_at` | `datetime` | Yes | When plan was created |
| `updated_at` | `datetime` | Yes | When status last changed |
| `valid_until` | `datetime \| None` | No | Expiry based on hazard time horizon |

**Validation rules**:
- `confidence_score` must be in [0.0, 1.0]
- `version` must be ≥ 1
- `confidence_level` derived from `confidence_score`: `low` (<0.4), `medium` (0.4–0.69), `high` (≥0.7)
- Immutable once persisted — status transitions are the only permitted mutations
- `plan_id` format must match `ep-{incident_id}-v{N}`
- `plan_id`, `incident_id`, `version`, `tenant_id`, and `incident_scope_key` must agree exactly
- `population_estimate` and `total_population` must equal the sum of zone populations
- A plan must contain affected-area geometry, hazard sources and horizon, zones, phases, one disposition per zone, complete traceability, content-sensitive snapshots, summary, assumptions, generation method, and configuration version
- Hazard source assessment/signal IDs must agree across `HazardSummary`, `Traceability`, and `DataSnapshot`
- Versions after v1 must identify their source plan and include a non-empty change summary

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
| `boundary` | `dict` (GeoJSON Polygon) | Yes | Cumulative safety envelope used for road classification |
| `membership_boundary` | `dict` (GeoJSON Polygon/MultiPolygon) | Yes | Exclusive cohort/origin geometry: Zone 1, Zone 2 minus Zone 1, or Zone 3 minus Zone 2 |
| `population_estimate` | `int` | Yes | Authoritative source cohorts apportioned once into this membership |
| `vulnerable_population` | `int` | Yes | Authoritative vulnerable cohort apportioned independently and bounded by zone population |
| `evacuation_priority` | `str` | Yes | `mandatory` (Zone 1), `recommended` (Zone 2), `advisory` (Zone 3) |
| `status` | `str` | Yes | `evacuating` \| `shelter_in_place` \| `cleared` \| `pending` |
| `origin_node_ids` | `list[str]` | Yes | Road nodes assigned once to the highest-priority covering membership |
| `origin_coverage_status` | `str` | Yes | `unassigned` \| `covered` \| `no_network_origin` \| `not_required` |

**Validation rules**:
- Membership geometries are disjoint for positive area; shared boundary points belong to the lowest-numbered zone.
- Population and vulnerable source counts use deterministic largest-remainder apportionment and reconcile exactly.
- `0 <= vulnerable_population <= population_estimate`.
- A road origin appears in at most one zone. Populated zones without an intersecting origin create no route and carry `no_network_origin` into their disposition.

---

## Entity: EvacuationRoute (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `route_id` | `str` | Yes | Unique route identifier within the plan |
| `path` | `list[str]` | Yes | Ordered edge IDs; canonical alias of legacy `waypoints` |
| `node_path` | `list[str]` | Yes | Connected nodes with exactly one more node than `path` edges |
| `origin_zone` | `int` | Yes | Source zone; canonical alias of legacy numeric `zone_id` |
| `origin_node_id` | `str` | Yes | First node in the connected path |
| `destination_assembly_area` | `str` | Yes | Canonical alias of legacy `assembly_area_id` |
| `total_distance_km` | `float` | Yes | Canonical alias of legacy `distance_km` |
| `estimated_travel_time_normal_min` | `float` | Yes | Travel time under normal conditions (minutes) |
| `estimated_travel_time_loaded_min` | `float` | Yes | Travel time under evacuation load (minutes) |
| `capacity_vehicles_per_hour` | `int` | Yes | Minimum capacity along the route (bottleneck) |
| `estimated_utilisation_pct` | `float` | Yes | Canonical uncapped utilization alias; may exceed 100 |
| `congestion_risk` | `bool` | Yes | True if precise utilisation strictly exceeds configured threshold |
| `vehicle_suitability` | `VehicleSuitability` | Yes | Typed `{standard, heavy, accessible}` booleans derived from every edge |
| `excluded_roads` | `list[ExcludedRoad]` | Yes | Roads excluded from this route with reasons |
| `selection_rationale` | `str` | Yes | Deterministic policy/mode/preferences/data-gap rationale; never LLM-selected |
| `routing_mode` | `str` | Yes | `hazard_aware` \| `hazard_constrained_degraded` |
| `hazard_data_gaps` | `list[str]` | Yes | Exact missing reference attributes for active hazards |
| `hazard_risk_score` | `float` | Yes | Non-negative relative soft-preference score for ordering routes |
| `hazard_preference_evidence` | `list[HazardPreferenceEvidence]` | Yes | Chosen-path edge, hazard, reason, and multiplier for every applied soft preference |
| `origin_node_id` / `node_path` | `str` / `list[str]` | Yes | Physical origin and connected node sequence used for shared-edge accounting |
| `allocated_population` | `int` | Yes | Unique people assigned to this route; all route allocations reconcile to zone demand |
| `evacuation_load_vehicles_per_hour` | `float` | Yes | `allocated_population / persons_per_vehicle / allocation_window_hours` |
| `uncapped_utilisation_pct` | `float` | Yes | Maximum total physical-edge utilization on the route; may exceed 100 |
| `congestion_risk` | `bool` | Yes | Precise utilization strictly exceeds configured threshold |
| `capacity_overloaded` | `bool` | Yes | Precise utilization exceeds 100% |
| `bottleneck_edge_ids` | `list[str]` | Yes | Edges tied for maximum utilization on the route |
| `zone_shared_capacity_vehicles_per_hour` | `int` | Yes | Unique-edge max-flow capacity for the zone's candidate route graph |

---

## Entity: ExcludedRoad (embedded in EvacuationRoute)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edge_id` | `str` | Yes | Road segment edge ID |
| `road_id` | `str` | Yes | Backward-compatible alias of `edge_id` |
| `road_name` | `str` | Yes | Human-readable road name |
| `closure_reason` | `str` | Yes | `emergency_services_closure` \| `flood_cut` \| `fire_proximity` \| `structural_damage` \| `zone_1_closure` \| `capacity_exhausted` \| `unspecified` |
| `exclusion_reason` | `str` | Yes | Exact deterministic hazard or operational exclusion explanation |
| `source_hazard_type` | `str \| None` | No | Active hazard that required the exclusion |

`EvacuationPlan` additionally persists `routing_mode`, `hazard_routing_data_gaps`, and every rejected destination (`assembly_area_id`, name, reason, source hazard). `HazardSourceSnapshot.routing_attributes` currently validates optional meteorological `wind_from_degrees` in `[0, 360)`.

The plan also persists `excluded_roads` as the authoritative complete inventory, `unavailable_roads_by_reason` as bounded summary counts, and `zero_route_zones`. Route-level `excluded_roads` is retained for client compatibility. Same-count replans identify each changed route ID and its old/new edge path.

## Entity: CorridorLoad (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edge_id` | `str` | Yes | Physical road edge, represented once in the plan ledger |
| `capacity_vehicles_per_hour` | `int` | Yes | Edge design/effective capacity used for the plan |
| `current_traffic_load_vehicles_per_hour` | `float` | Yes | Existing measured/reference load |
| `evacuation_load_vehicles_per_hour` | `float` | Yes | Sum of unique route assignments traversing this edge |
| `total_load_vehicles_per_hour` | `float` | Yes | Current plus evacuation load |
| `uncapped_utilisation_pct` | `float` | Yes | `100 * total_load / capacity` |
| `capacity_overloaded` | `bool` | Yes | Utilization exceeds 100% |
| `route_ids` | `list[str]` | Yes | Deterministically sorted routes using the edge |

---

## Entity: TransportRequirement (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requirement_id` | `str` | Yes | Stable SHA-256-derived logical request ID within incident scope |
| `facility_id` / `facility_name` | `str` / `str` | Yes | Pickup facility identity and display name |
| `category` | `VulnerabilityCategory` | Yes | `mobility_impaired` \| `medical_dependent` \| `elderly_aged_care` \| `children_schools_childcare` |
| `estimated_individuals` | `int` | Yes | Positive facility cohort count requiring transport |
| `vehicle_type` | `str` | Yes | `bus` \| `wheelchair_accessible_vehicle` \| `ambulance` \| `medical_transport` \| `accessible_bus` |
| `quantity_required` | `int` | Yes | Ceiling of individuals divided by vehicle capacity |
| `estimated_trips` | `int` | Yes | Planned trips per requested vehicle (currently 1) |
| `pickup_location` | `dict` | Yes | Typed WGS84 `{lat, lng}` coordinates |
| `destination_assembly_area_id` / `destination_assembly_area_name` | `str` / `str` | Yes | Structured destination identity |
| `destination_route_id` | `str` | Yes when resolved | Compatible route that makes the destination reachable |
| `destination_resolved` | `bool` | Yes | False when no compatible verified-capacity area/route exists |
| `unresolved_destination_reason` | `str \| None` | No | Required operational gap when unresolved |
| `priority_level` | `TransportPriority` | Yes | `critical` (medical) \| `immediate` (mobility/aged care) \| `high` (schools/childcare) |
| `origin_zone` / `phase_number` | `int` / `int` | Yes | Zone 1/Phase 1 or Zone 2/Phase 3 |
| `special_considerations` | `list[str]` | Yes | Medical, mobility, supervision, and facility-specific requirements |
| `count_basis` | `str` | Yes | `facility_capacity` until current-occupancy data is authoritative |
| `dispatch_authorized` | `bool` | Yes | Always false in evacuation output |
| `notes` | `str` | Yes | Backward-compatible human-readable rendering; never the machine contract |

**Vehicle capacity assumptions** (for computing `estimated_vehicles`):
| Vehicle Type | Capacity |
|-------------|----------|
| Bus | 50 persons |
| Wheelchair-accessible vehicle | 4 wheelchair users |
| Ambulance | 2 patients |
| Medical transport vehicle | 6 patients |

`EvacuationPlan` persists `transport_coordination_status` (`complete`, `partial`, `unavailable`), typed `transport_exclusions`, `identified_transport_population_by_zone`, and `uncovered_vulnerable_population_by_zone`. Exclusion reasons are `advisory_only`, `outside_affected_area`, `invalid_location`, `unknown_category`, `invalid_population`, or `no_destination`.

`EvacuationPlan.to_resource_allocation_payload()` is a pure adapter and does not publish or dispatch. Resource Allocation preserves the request ID, individuals, destination, origin zone, phase, considerations, count basis, and source plan in `ResourceDemand`; demand IDs are deterministic per scoped requirement.

## Entity: DestinationAllocation (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assembly_area_id` / `assembly_area_name` | `str` / `str` | Yes | Reachable, hazard-screened destination |
| `zone_number` | `int` | Yes | Source zone consuming shared capacity |
| `assigned_population` | `int` | Yes | Total people assigned from this zone |
| `assigned_vulnerable_population` | `int` | Yes | Vulnerable subset reserved on accessible area/route capacity |
| `residual_capacity_before` / `residual_capacity_after` | `int` / `int` | Yes | Verified residual capacity ledger; difference equals assignment |
| `route_ids` | `list[str]` | Yes | Reachable route candidates supporting the allocation |
| `accessibility_features` | `list[str]` | Yes | Explicit destination accessibility evidence |

`UnresolvedDestinationDemand` persists zone, total/vulnerable people, reason, and commander-facing detail. Assigned plus unresolved destination population equals the plan total. Route allocations equal destination allocations by zone/area, and every resolved transport request matches its exact compatible route.

---

## Entity: EvacuationPhase (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phase_number` | `int` | Yes | 1–5 per FR-015 |
| `description` | `str` | Yes | e.g., "Zone 1 vulnerable populations" |
| `zone_number` / `zone_ids` | `int` / `list[str]` | Yes | Target evacuation zone |
| `population_type` | `PhasePopulationType` | Yes | `vulnerable` \| `general` \| `advisory` |
| `estimated_population` / `routable_population` | `int` / `int` | Yes | Total cohort and destination-backed subset |
| `start_offset_minutes` / `starts_at` | `float` / `datetime \| None` | Yes | Modeled start from plan anchor |
| `duration_minutes` | `float \| None` | Yes | Effective movement duration, or `null` when blocked |
| `completion_offset_minutes` / `completes_at` | `float \| None` / `datetime \| None` | Yes | Completion; absent for populated blocked phases |
| `mobilisation_minutes` / `travel_minutes` / `clearance_minutes` | `float` / `float` / `float \| None` | Yes | Explicit timing components in minutes |
| `effective_capacity_vehicles_per_hour` | `int` | Yes | Unique-edge zone max-flow capacity |
| `estimated_departure_rate_people_per_minute` | `float` | Yes | Routable population divided by buffered clearance minutes |
| `population_transition_threshold` | `int` | Yes | Whole-person configured departure threshold |
| `population_transition_offset_minutes` | `float \| None` | No | Modeled threshold time when reachable |
| `time_transition_offset_minutes` | `float \| None` | No | Configured time-factor candidate |
| `selected_transition_offset_minutes` / `transition_at` | `float \| None` / `datetime \| None` | No | Winning modeled transition |
| `selected_transition_trigger` | `PhaseTransitionTrigger` | Yes | `population_threshold` \| `time_threshold` \| `phase_completion` \| `zero_population` \| `blocked` |
| `transition_delay_minutes` | `float` | Yes | Additional shared-corridor capacity delay |
| `population_moved` | `int` | Yes | Population that can clear in this phase before impact |
| `population_remaining` | `int` | Yes | Population still requiring shelter or emergency intervention |
| `clearance_blocked` | `bool` | Yes | True only when no viable positive-capacity route exists |
| `is_empty` | `bool` | Yes | Derived true only for zero-population phases |
| `buffer_multiplier` / `buffered_transport_population` | `float` / `int` | Yes | Effective resolved-transport-only buffer evidence |
| `route_edge_ids` | `list[str]` | Yes | Physical edges reserved by the phase |
| `route_allocation_snapshot` | `dict[str, int]` | Yes | Route ID to plan-wide assigned population snapshot |
| `zone_shared_capacity_vehicles_per_hour` | `int` | Yes | Capacity input used by this phase |
| `transport_requirements` | `list[TransportRequirement]` | Yes | Phase 1/3 linked typed requests; empty elsewhere |

**Validation rules**: moved plus remaining equals estimated population; routable and buffered transport populations are bounded subsets; completion equals start plus duration; transition cannot precede start; timestamps are timezone-aware. Configuration requires buffer `>=1`, positive time factor, and population threshold in `1..100`.

**Phase sequence** (per FR-015):
| Phase | Zone | Population Type | Priority |
|-------|------|----------------|----------|
| 1 | Zone 1 | Vulnerable | Highest |
| 2 | Zone 1 | General | High |
| 3 | Zone 2 | Vulnerable | Medium |
| 4 | Zone 2 | General | Medium-Low |
| 5 | Zone 3 | Advisory (all) | Lowest |

---

## Entity: ZoneDisposition (embedded in EvacuationPlan and audit records)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `zone_id` / `zone_number` | `str` / `int` | Yes | Zone receiving the outcome |
| `disposition` | `str` | Yes | `evacuation` \| `shelter_in_place` \| `partial_evacuation` \| `emergency_escalation` |
| `urgency` | `str` | Yes | `planned` \| `urgent` \| `critical` \| `maximum` |
| `affected_population` | `int` | Yes | Total zone population covered by this outcome |
| `evacuating_population` | `int` | Yes | Population expected to clear before impact |
| `remaining_population` | `int` | Yes | Population requiring shelter or emergency intervention |
| `origin_coverage_status` | `str` | Yes | Origin coverage inherited from the zone; distinguishes geographic non-coverage from a blocked path |
| `clearance_deficit_minutes` | `int` | Yes | Estimated movement shortfall for partial evacuation |
| `prerequisites` | `list[str]` | Yes | Conditions and human actions required for the disposition |
| `shelter_requirements` | `ShelterRequirements` | Yes | Building, supplies, and verified-communication requirements |
| `rationale` | `str` | Yes | Human-readable basis for the outcome |
| `emergency_notification_id` | `str \| None` | No | Deterministic internal operator-notification request ID |
| `emergency_notification_receipt` | `str \| None` | No | Receipt from the authorized emergency-services integration |

**Validation rules**:
- `evacuating_population + remaining_population == affected_population`.
- `evacuation` has no remaining population.
- `shelter_in_place` and `emergency_escalation` move no population.
- Unknown no-route horizons fail closed to `emergency_escalation`.
- Emergency notification records always set `public_order_authorized=false`; they request authorized operator action and never issue public orders.

---

## Entity: HazardSummary (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hazard_type` | `str` | Yes | `bushfire` \| `cyclone` \| `flood` \| `earthquake` \| `tsunami` |
| `hazard_types` | `list[str]` | Yes | Sorted distinct active hazard types; `hazard_type` remains the primary recommendation type |
| `severity_level` | `str` | Yes | Highest active severity: `low` \| `moderate` \| `high` \| `critical` |
| `time_horizon` | `str` | Yes | Time to impact (e.g., `18h`, `4h`) |
| `assessment_id` | `str` | Yes | Source assessment ID |
| `affected_area` | `dict` (GeoJSON) | Yes | Union of every active source HazardMap area |
| `sources` | `list[HazardSourceSnapshot]` | Yes | Deterministically ordered active sources used to derive the plan |
| `population_estimate` | `int \| None` | No | From the HazardMap |

---

## Entity: HazardSourceSnapshot (embedded in HazardSummary)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assessment_id` / `version` | `str` / `int` | Yes | Immutable source assessment identity |
| `hazard_type` / `severity_level` | `str` / `str` | Yes | Inputs to the configured radius policy |
| `affected_area` | `dict` (GeoJSON) | Yes | Original validated source geometry |
| `input_signal_ids` | `list[str]` | Yes | Upstream evidence references |
| `generated_at` / `valid_until` | `datetime` / `datetime \| None` | Yes / No | Source freshness window |
| `buffer_radius_metres` | `float` | Yes | Resolved metric radius used for both outward zone steps |
| `geometry_sha256` | `str` | Yes | SHA-256 of canonical sorted source geometry JSON |

Sources are loaded with a partition-scoped `status=active` query. Expired secondary sources are excluded; an expired primary source or malformed/foreign active source rejects planning.

---

## Entity: Traceability (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Triggering handoff |
| `assessment_id` | `str` | Yes | Source hazard assessment |
| `assessment_ids` | `list[str]` | Yes | All active source assessments in deterministic order |
| `recommendation_id` | `str` | Yes | Source recommendation |
| `input_signal_ids` | `list[str]` | No | Signal IDs from the assessment (if available) |
| `input_data_versions` | `dict[str, str]` | Yes | Effective road, population, facility, assembly, and configuration hashes |
| `generation_method` | `str` | Yes | Must agree with the plan generation method |

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
| `population_data_available` | `bool` | Yes | Distinguishes unavailable data from a verified empty dataset |
| `facility_data_available` | `bool` | Yes | Distinguishes unavailable data from a verified empty registry |
| `assembly_area_data_available` | `bool` | Yes | Whether assembly-area configuration was available |
| `population_record_ids` | `list[str]` | Yes | Stable IDs, or canonical content IDs, for records used |
| `facility_record_ids` | `list[str]` | Yes | Stable IDs, or canonical content IDs, for records used |
| `assembly_area_record_ids` | `list[str]` | Yes | Stable IDs for assembly-area records used |
| `*_record_count` | `int` | Yes | Count matching each corresponding record-ID list |
| `snapshot_timestamp` | `datetime` | Yes | When snapshot was taken |
| `hazard_assessment_ids` | `list[str]` | Yes | Source IDs used for this exact derivation |
| `hazard_geometry_algorithm` | `str` | Yes | `per-hazard-aeqd-level-union-v1` |
| `road_data_status` | `str` | Yes | `fresh`, `fresh_cache_refresh_failed`, `stale`, or `unavailable` |
| `road_source_updated_at` / `road_source_age_hours` | `datetime \| None` / `float \| None` | Yes | Source-time freshness evidence, independent of process load time |
| `population_data_status` / `facility_data_status` | `str` | Yes | `fresh`, `stale`, `unavailable`, or explicit freshness-invalid/unknown state |
| `population_source_updated_at` / `facility_source_updated_at` | `datetime \| None` | No | Shared reference source timestamp when validated |
| `population_source_age_hours` / `facility_source_age_hours` | `float \| None` | No | Source ages at planning time |
| `road_refresh_failure_reason` | `str` | No | Failed refresh evidence when a last-known-good graph is retained |

`road_network_version` hashes the effective per-plan graph after closures and zone capacity reductions. Collection versions hash canonical record content, so record reordering is stable while same-count material changes produce a new version. Credentials and connection secrets are excluded from configuration hashes.

Plans also persist `data_quality_gaps`, ordered multiplicative `confidence_adjustments`, `immediate_human_review_required`, and `generic_guidance`. Stale/unavailable road state cannot coexist with computed routes, assembly outputs, or destination allocations. Generic guidance is hazard-specific and never claims a verified safe route or known absence of vulnerable people.

---

## Entity: AssemblyArea (embedded in EvacuationPlan)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assembly_area_id` | `str` | Yes | Reference data ID |
| `name` | `str` | Yes | Human-readable name |
| `coordinates` | `dict` | Yes | `{lat: float, lng: float}` |
| `capacity_persons` | `int` | Yes | Maximum capacity |
| `current_occupancy` | `int \| None` | Yes | Explicit occupancy snapshot; `None` means capacity is unverified |
| `residual_capacity` | `int \| None` | Yes | Capacity minus occupancy and this plan's assignment |
| `assigned_population` / `assigned_vulnerable_population` | `int` / `int` | Yes | Plan-specific shared allocation totals |
| `assigned_zones` | `list[int]` | Yes | Zones actually allocated to this area |
| `accessibility_features` | `list[str]` | Yes | e.g., `["wheelchair_accessible", "medical_facilities"]` |
| `shelter_types` | `list[str]` | Yes | Declared shelter certifications; empty means no shelter claim |

`accessible` is true only for explicit `wheelchair_accessible`; `shelter_available` is true only when `shelter_types` is non-empty. The planner never mutates reference occupancy with proposed allocations. Each version snapshots reference occupancy and keeps its proposed assignment separate.

---

## Entity: EvacuationDecisionRecord (owned — audit trail)

**Storage**: Azure Cosmos DB — container `evacuation-decisions`  
**Partition key**: `/incident_scope_key`  
**TTL**: None (infinite retention, append-only)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` (UUID) | Yes | Unique record identifier |
| `handoff_id` | `str` | Yes | Originating handoff ID |
| `operation_id` | `str` | Yes | Stable handoff, update, override, lifecycle, or health-operation identity |
| `incident_id` | `str` | Yes | Associated incident |
| `plan_id` | `str \| None` | No | Resulting plan ID (when applicable) |
| `assessment_id` / `recommendation_id` | `str \| None` | No | Upstream provenance when applicable |
| `input_signal_ids` | `list[str]` | Yes | Upstream signal provenance when available |
| `decision_type` | `DecisionType` | Yes | Processing step type (enum) |
| `confidence_raw` / `confidence_adjusted` | `float` | Yes | Confidence before and after recorded adjustments |
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
| `replanning_triggers` | `list[ReplanningTrigger]` | No | Closed canonical vocabulary, including `new_road_closure` and `shelter_to_evacuation_recovery` |
| `principal_id` | `str \| None` | No | Authenticated actor for commander-initiated decisions |
| `expected_steps` / `observed_steps` | `list[str]` | No | Exact required-stage reconciliation on final plan records |
| `stage_durations_ms` | `dict[str, float]` | No | Accepted audit duration totals by decision type |
| `completeness_warnings` | `list[str]` | No | Missing/duplicate required observations |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `tenant_id` | `str` | Yes | `live` or simulation |
| `timestamp` | `datetime` (UTC) | Yes | When recorded |
| `buffered_at` | `datetime \| None` | No | When buffered (degradation) |
| `flush_source` | `str \| None` | No | `direct` \| `memory_buffer` \| `file_buffer` |

Core identity is strict: tenant, incident, partition key, plan ID, and version must agree; timestamps are normalized to UTC; plan events require identity/version and exact route/transport counts. Stage 10 compares branch-aware expected cardinalities with accepted write receipts and emits a structured degradation warning before failing when a required record is missing.

`AuditWriteReceipt` exposes `accepted`, `storage_tier`, and `durable`. Direct Cosmos acceptance is durable. Every buffered record, including the bounded memory-cached tier, is serialized with `buffered_at`/`flush_source` and fsynced to one JSONL WAL before a durable receipt is returned. Append and drain share one lock. Flush stops on the oldest failure or corrupt line, atomically retains the exact suffix, and treats 409 as recovered only after scoped content reconciliation. Restarted writers detect backlog before direct writes; health derives from current backlog/corruption/rejection rather than cumulative spill history.

Authorized `GET /audits/{incident_id}` retrieval remains inside the caller's incident partition and supports combined plan, decision-type, inclusive UTC time-range, and page-size filters. Results sort by `(timestamp, id)` ascending. Opaque cursors are bound to tenant, incident, and the complete filter set, preventing cross-scope replay.

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
| `last_reserved_version` | `int` | Yes | Most recent integer successfully reserved by ETag update |
| `orphaned_versions` | `list[dict]` | Yes | Bounded record of reservations whose plan absence was confirmed |
| `uncertain_versions` | `list[dict]` | Yes | Bounded record of reservations whose write/read-back outcome was unavailable |
| `incident_scope_key` | `str` | Yes | Cosmos DB partition key |
| `_etag` | `str` | Auto | Cosmos DB-managed ETag for OCC |

**Concurrency pattern** (same as risk assessment):
1. Read counter + `_etag`
2. Increment `current_version`
3. `replace_item(..., etag=_etag, match_condition=MatchConditions.IfNotModified)` using the installed Cosmos SDK contract
4. On 412 Precondition Failed: re-read, re-increment, and retry with capped exponential jitter (maximum 5 attempts)
5. On an initial 404/409 create race, re-read and reserve the next integer
6. On timeout, malformed/missing ETag, or exhausted conflicts, raise `VersionReservationError`; never return an unreserved fallback

Without a persistence container, development/test instances use a lock-protected in-process counter scoped by `incident_scope_key`. Such versions are not represented as durable reservations and production startup requires the scoped Cosmos containers.

Plan creation is not considered committed from the `create_item` response alone. The pipeline immediately reads the plan from the same partition, validates the complete `EvacuationPlan`, and requires exact equality with the intended body. A lost create response is accepted only when this read-back succeeds. Confirmed 404 and unavailable/mismatched read-back outcomes are recorded respectively in `orphaned_versions` or `uncertain_versions`, the handoff claim remains retryable, and no active count or `plan_generated` completion audit is emitted.

---

## Entity: HandoffProcessingClaim (internal — idempotency control)

**Storage**: `evacuation-plans`, co-located with the resulting plan
**Partition key**: `/incident_scope_key`
**ID**: `handoff-claim-{sha256(tenant_id, incident_id, handoff_id)}`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `handoff_id` | `str` | Yes | Trusted handoff identity |
| `incident_id` / `tenant_id` | `str` | Yes | Scope components used to prevent cross-tenant suppression |
| `incident_scope_key` | `str` | Yes | Same partition as the owned plan |
| `owner_id` | `str` | Yes | Per-process replica identity permitted to mutate the active claim |
| `status` | `str` | Yes | `processing` \| `completed` \| `rejected` \| `abandoned` |
| `claimed_at` / `lease_expires_at` | `datetime` | Yes | Processing lease and stale-takeover boundary |
| `completed_at` | `datetime \| None` | No | Durable outcome timestamp |
| `plan_id` | `str \| None` | No | Reserved/resulting plan used for lost-response recovery |
| `failure_reason` | `str \| None` | No | Rejection or retry release reason |
| `ttl` | `int` | Yes | Per-item retention metadata matching the configured deduplication window |

Claims are created atomically. A live claim owned by another replica is retryable and cannot be released by the loser. Abandoned or expired leases may be conditionally taken over with the current ETag. Plan IDs are attached before plan creation; if the plan exists after a crash or lost response, redelivery completes the claim without creating another version. Completed and rejected claims are idempotent duplicate outcomes.

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

**RoadNode** fields: `id`, `name`, `coordinates` (lat/lng), `type` (intersection/endpoint), `zone_membership` (computed at runtime), `is_assembly_area`, optional `elevation_m`, optional `coastal_exposure`.

**RoadEdge** fields: the base identity/capacity/surface/closure/GeoJSON fields, non-negative `current_traffic_load_vehicles_per_hour`, plus optional `elevation_m`, `coastal_exposure`, `flood_exposure`, `tsunami_inundation_exposure`, and `earthquake_damage_status` (`none`, `suspected`, `confirmed`).

**AssemblyAreaConfig** hazard fields: optional `elevation_m`, `coastal_exposure`, `flood_exposure`, `tsunami_inundation_exposure`, `shelter_types`, and `structural_status` (`safe`, `uninspected`, `unsafe`). Missing fields force degraded routing; they are never interpreted as safe values.

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
| `bushfire` | Prefer travel not aligned with downwind bearing | Exclude roads intersecting the metric 2 km fire-perimeter buffer |
| `cyclone` | Prefer relative higher elevation; screen shelter certification | Exclude explicit coastal/storm-surge exposure |
| `flood` | Prefer relative higher ground | Exclude explicit flood exposure and flood/low-lying closures |
| `earthquake` | Prefer inspected infrastructure; penalise suspected damage | Exclude confirmed structural damage |
| `tsunami` | Prefer relative higher ground and screen destinations | Exclude dedicated coastal/tsunami-inundation exposure |

---

## Configurable Parameters

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| Road network file path | `ROAD_NETWORK_FILE_PATH` | `data/road-network.json` | Path to static road network JSON |
| Road data staleness window | `ROAD_DATA_STALENESS_HOURS` | `6` | Hours before road data considered stale |
| Population/facility staleness window | `POPULATION_DATA_STALENESS_HOURS` | `24` | Hours before reference estimates require stale-data degradation |
| Handoff dedup window | `HANDOFF_DEDUP_WINDOW_MINUTES` | `10` | Minutes for duplicate detection |
| Congestion risk threshold | `CONGESTION_RISK_THRESHOLD_PCT` | `80` | Capacity utilisation % flagged as congestion risk |
| Average persons per vehicle | `AVERAGE_PERSONS_PER_VEHICLE` | `2` | Occupancy conversion used only for route load allocation |
| Route allocation window | `ROUTE_ALLOCATION_WINDOW_MINUTES` | `120` | Named time window used to convert assigned people to vehicles/hour |
| Normal route speed | `NORMAL_ROUTE_SPEED_KMH` | `60` | Explicit free-flow assumption used only for normal travel estimate |
| Loaded route speed | `LOADED_ROUTE_SPEED_KMH` | `30` | Existing evacuation-load speed assumption, now explicit and validated not to exceed normal speed |
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
| Audit buffer file path | `AUDIT_BUFFER_FILE_PATH` | `/app/var/evacuation-agent/audit-buffer.jsonl` | Nonroot-writable audit WAL path |
| Max summary length | `MAX_SUMMARY_LENGTH` | `1000` | Truncation limit for plan summary text |
| Replan rate limit | `REPLAN_RATE_LIMIT_SECONDS` | `30` | Minimum seconds between replans for same incident |
| Agent version | `AGENT_VERSION` | `0.1.0` | Semantic version |
