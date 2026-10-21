# Contract: Evacuation Processing Pipeline

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16  
**Type**: Processing pipeline contract

---

## Overview

The Evacuation Agent processes inbound `AgentHandoffEvent` messages from the Risk Assessment Agent through a 10-stage pipeline, producing versioned `EvacuationPlan` records with routes, transport coordination, and phased timelines. Plans require incident commander approval before becoming operational.

---

## Pipeline Stages

### Stage 1: Handoff Intake and Validation

**Input**: Raw `AgentHandoffEvent` from Azure Service Bus  
**Output**: Validated handoff or rejection audit record  
**SLA**: Acknowledge within 5 seconds of delivery (FR-001)

| Check | Action on Failure |
|-------|-------------------|
| Pydantic v2 schema validation | Reject with `handoff_rejected` audit record |
| `target_agent == "evacuation"` | Reject with `handoff_rejected` audit record |
| Payload contains `recommendationId`, `assessmentId` | Reject with `handoff_rejected` audit record |
| Idempotency check (handoff_id dedup, 10-min window) | Discard with `duplicate_discarded` audit record |
| Tenant validation (simulation vs live) | Route to appropriate processing context |

### Stage 2: Assessment Retrieval

**Input**: Validated handoff with primary assessment ID
**Output**: Primary assessment plus every unexpired `active` hazard assessment in the same incident partition
**Degradation**: If assessment cannot be retrieved, reject handoff with `handoff_rejected` audit record (FR-002, Edge Case 1).

| Outcome | Action |
|---------|--------|
| Assessment retrieved with hazard map | Continue to zone computation |
| Assessment retrieved without hazard map | Reject — insufficient data for route computation |
| Assessment not found | Reject with `handoff_rejected` audit record, log missing assessment |
| Active-hazard query unavailable | Retain handoff for retry; do not plan from an incomplete hazard set |
| Any active hazard has invalid/empty geometry or foreign scope | Reject the handoff atomically; do not omit that hazard |

### Stage 3: Zone Computation

**Input**: All active incident-scoped hazards with type, severity, and affected-area GeoJSON
**Output**: Three cumulative evacuation zones, exclusive population memberships, and the merged raw affected area

**Algorithm**:
1. Validate every source as a non-empty WGS84 Polygon/MultiPolygon; no geometry repair or omission occurs in planning.
2. Resolve each source's metric radius from the shared hazard-type/severity radius policy (`low=1`, `moderate=2`, `high=3`, `critical=4`).
3. Project each source to a local azimuthal-equidistant CRS centered on that geometry, derive Zone 2 and Zone 3 in metres, then transform each level back to WGS84.
4. Union Zone 1 from all sources, union Zone 2 from all sources, and union Zone 3 from all sources. Checking levels from 1 to 3 makes the lowest zone number authoritative in overlaps and preserves disjoint MultiPolygon hazards.
5. Derive exclusive cohort/origin memberships as Zone 1, Zone 2 minus Zone 1, and Zone 3 minus Zone 2. Apportion authoritative population and vulnerability counts once across those memberships.
6. Persist the raw-hazard union as `affected_area`, all contributing source snapshots/hashes/resolved radii, and `per-hazard-aeqd-level-union-v1` as the geometry algorithm.

**Geospatial operations** (using Shapely + pyproj):
- Zone boundary: local-AEQD `hazard_polygon.buffer(distance_metres)` followed by WGS84 transform
- Multi-hazard boundary: level-by-level `shapely.ops.unary_union()`
- Road segment intersection: `zone_polygon.contains(road_linestring)` for full containment, `zone_polygon.intersects(road_linestring)` for partial overlap
- Partial overlap (CHK013): Highest-severity zone applies (conservative, Life Safety First)

### Stage 4: Road Network Preparation

**Input**: Computed zones, current road network state  
**Output**: Modified road network graph with zone-based capacity adjustments

| Zone | Road Segment Action |
|------|-------------------|
| Zone 1 (fully within) | Mark closed, capacity = 0 |
| Zone 2 (fully or partially within) | Reduce capacity by 50% |
| Zone 3 (fully or partially within) | Reduce capacity by 25% |
| Outside all zones | Full capacity retained |
| Explicitly closed (closure_status = closed) | Mark closed, capacity = 0 |

**Road data freshness** uses the validated, timezone-aware source `metadata.last_updated`, never process load time. Refresh is atomic: a failed refresh preserves the last-known-good graph. A fresh cached graph after refresh failure may support provisional routes with an immediate-review flag and confidence reduction. Once source age exceeds `ROAD_DATA_STALENESS_HOURS` (default 6h), or no usable graph exists, route/destination computation is disabled and the plan carries hazard-specific generic guidance stating that passability and capacity are unverified.

Population and facility data use their shared source timestamp and `POPULATION_DATA_STALENESS_HOURS` (default 24h). Stale records remain best-available inputs, but the plan persists source age, structured gaps, confidence adjustments, and an immediate local-verification flag. Unavailable registries remain distinct from verified-empty registries.

### Stage 5: Route Computation

**Input**: Prepared road network graph, zones, assembly areas, and all persisted active-hazard source snapshots
**Output**: List of `EvacuationRoute` records

**Algorithm** (Dijkstra's variant):
1. For each zone, identify origin nodes within the zone.
2. Compile every active hazard into one most-restrictive deterministic policy. Hard exclusions are applied when any hazard marks an edge/destination unsafe.
3. Screen assembly areas before pathfinding. Explicitly exposed/unsafe destinations are persisted with hazard-specific rejection reasons.
4. For each origin, compute paths to eligible destinations with edge weight `distance / capacity × congestion_penalty × hazard_preference_penalty`.
5. Bushfire applies the documented metric 2 km perimeter exclusion and a continuous downwind penalty when validated `wind_from_degrees` exists. Cyclone excludes explicit coastal/storm-surge exposure and requires explicit non-conflicting shelter certification. Flood excludes explicit flood exposure and prefers relative higher ground. Earthquake excludes confirmed damage and penalises suspected damage. Tsunami excludes dedicated coastal/inundation exposure and prefers relative higher ground.
6. Multi-path discovery (FR-007): When population exceeds single-corridor capacity, compute additional candidates by penalising edges on the first path and re-running Dijkstra.
7. After candidates for every zone are known, perform one plan-wide deterministic allocation. Apportion each zone population exactly once by available path capacity with largest-remainder rounding; odd persons are retained and no origin/destination pair receives a duplicate copy of zone demand.
8. Convert assigned people to evacuation vehicles/hour using `AVERAGE_PERSONS_PER_VEHICLE` (default 2) and `ROUTE_ALLOCATION_WINDOW_MINUTES` (default 120). Add each route's load once to every physical edge it traverses, together with `current_traffic_load_vehicles_per_hour`.
9. Compute uncapped edge/route utilisation from total physical-edge load. `congestion_risk` is true only when precise utilisation is strictly greater than `CONGESTION_RISK_THRESHOLD_PCT`; `capacity_overloaded` is independently true above 100%. The legacy integer display remains capped at 100.
10. Compute each zone's usable corridor capacity with deterministic max flow over unique candidate edges. Disjoint corridors add capacity; shared choke edges contribute once. Timeline estimation consumes this value rather than summing route bottlenecks.
11. Derive canonical route evidence from the connected path: edge and node sequences, normal and loaded float-minute estimates from named speed assumptions, bottleneck capacity/edges, typed vehicle suitability, exact allocation/utilisation, and compatibility aliases for existing clients.
12. Generate each selection rationale only after plan-wide allocation so it states the actual origin/destination, path length, both travel estimates, assigned people, uncapped utilisation, congestion/overload, applied per-edge preferences, exclusions, mode, and data gaps.
13. Persist every hard/zero-capacity/explicit exclusion without truncation. Unknown causes remain `unspecified`, not an invented emergency closure. The authoritative plan-level inventory and reason counts remain available even when no route exists.
14. Allocate assembly destinations once after route discovery. Candidate arcs must already be hazard-screened and reachable, match the area's `assigned_zones`, and have known residual capacity (`capacity_persons - current_occupancy_persons`). Unknown occupancy is unresolved, never treated as zero.
15. Reserve verified wheelchair-accessible area and route capacity for the zone's vulnerable cohort first, then allocate remaining population. Zone 1 consumes shared destination capacity before Zone 2, then Zone 3. Deterministic largest-remainder allocation preserves whole-person totals.
16. Persist each zone/area assignment, vulnerable subset, route IDs, residual capacity before/after, and any unresolved demand (`no_reachable_destination`, `capacity_unverified`, `no_accessible_capacity`, or `capacity_exhausted`). Route/corridor load is calculated only from destination-backed assigned population.

**Routing completeness**:
- `hazard_aware`: all attributes required by every active hazard are present.
- `hazard_constrained_degraded`: available geometry, closure, and explicit exposure constraints are still enforced, but missing wind/elevation/coast/exposure/damage/shelter facts are listed in the plan and route. Confidence is reduced and the summary requires commander review; it never claims complete hazard-safe passage.
- Missing values are unknown, not safe. They do not silently become zero elevation or no exposure. Explicit unsafe values still exclude the edge/destination in degraded mode.

**Tie-breaking** (CHK007): When two routes have equal cost, prefer the route with lower congestion risk, then shorter distance.

**No viable routes/capacity**: If no route-backed verified destination capacity exists for a zone, retain its full unresolved demand and trigger shelter/emergency handling in Stage 7. Partial destination capacity caps phase movement and produces a `partial_evacuation` disposition with the remainder explicit.

**Summary visibility**: Every template/fallback summary includes a bounded reason-grouped unavailable-road count, rejected destinations, overloaded routes, and zones without routes. Full edge-level evidence remains structured in the plan and is not dependent on summary length.

**Conservation invariant**: For each plan, `sum(route.allocated_population) + sum(zone.unallocated_route_population) == total_population`. Excess demand is assigned and exposed as uncapped overload; absent routes remain explicitly unallocated and feed the shelter/emergency disposition.

### Stage 6: Transport Coordination

**Input**: Zone data, facility/population registry  
**Output**: List of `TransportRequirement` records

**Process**:
1. Validate every facility's stable identity (or deterministic identity fallback), positive integer capacity, WGS84 location, vulnerability category, and exclusive zone membership.
2. For each valid Zone 1/2 facility, create one typed `TransportRequirement` carrying exact individuals, vehicle quantity, pickup, destination, compatible selected route ID, priority, phase, considerations, and count basis. IDs are deterministic from incident scope, facility, category, and vehicle type.
3. Compute vehicles with ceiling division by the documented per-vehicle capacity. `estimated_trips=1` means each requested vehicle makes one planned trip; vehicle quantity and trip count are not conflated.
4. Keep Zone 3 facilities in the identified inventory as `advisory_only`; never create a mandatory transport request for Phase 5.
5. Retain outside-area, invalid-location/category/population, and no-destination facilities as typed exclusions rather than silently dropping them.
6. Reconcile facility-identified people against each Zone 1/2 authoritative vulnerable estimate. Persist identified and uncovered counts plus contradictions where facility capacity exceeds the estimate.
7. Preserve unavailable registry (`status=unavailable`) separately from an authoritative empty registry (`status=complete` with zero facilities). Both states remain explicit in assumptions and plan fields.
8. Link Zone 1 requests to Phase 1 and Zone 2 requests to Phase 3 through the full typed request/requirement ID.
9. Expose a pure camelCase Resource Allocation payload adapter with `dispatchAuthorized=false`. Plan generation does not publish a handoff or dispatch vehicles; the downstream Resource Allocation boundary preserves every typed field and derives its demand ID deterministically.
10. A resolved request may select only an assembly area already allocated to its zone with sufficient vulnerable capacity and a selected route compatible with its vehicle type. If none exists, keep the request with `destination_resolved=false` and an explicit reason; do not duplicate it as an excluded group or drop it.

**Priority mapping**:
| Vulnerability Category | Priority Level |
|----------------------|---------------|
| `medical_dependent` | `critical` |
| `mobility_impaired` | `immediate` |
| `elderly_aged_care` | `immediate` |
| `children_schools_childcare` | `high` |

**Downstream payload fields**: `requirementId`, `vehicleType`, `quantity`, `pickupLocation`, `priority`, `estimatedIndividuals`, `facilityId`, `facilityName`, destination ID/name, `originZone`, `phaseNumber`, `specialConsiderations`, `countBasis`, and `dispatchAuthorized=false`.

### Stage 7: Timeline Estimation and Shelter-in-Place

**Input**: Routes, transport requirements, hazard time horizon  
**Output**: Five typed, overlapping capacity-aware phases plus reconciled movement/shelter dispositions

**Timeline formula** (per FR-013):
```
clearance_time = (population / road_capacity) × distance_km × 60  [minutes]
effective_buffer = 1 + (VULNERABLE_POPULATION_BUFFER - 1)
				   × resolved_transport_population / routable_phase_population
buffered_clearance_time = clearance_time × effective_buffer
```

`road_capacity` is the zone's unique-edge max-flow capacity in vehicles/hour. Route distance is weighted by assigned population. The legacy FR-013 dimensional formula remains unchanged pending AUD-009-036; this remediation removes duplicated people/capacity without silently redefining that formula.

Mobilisation is an explicit pre-phase offset. Loaded travel time is persisted separately and is not silently added again to the legacy clearance formula. The 1.5 default applies only to the linked, resolved transport cohort in vulnerable phases; general, Zone 3, and unresolved transport populations receive no unsupported buffer.

**Phase transitions** (per FR-015 + Research Task 2):
- **Population candidate**: `start + ceil(phase_population × PHASE_TRANSITION_POPULATION_PCT / 100) / modeled_departure_rate`. It is eligible only when the modeled movement before hazard arrival can reach the threshold.
- **Time candidate**: `start + buffered_clearance_time × PHASE_TRANSITION_TIME_FACTOR`.
- **Completion fallback**: The modeled phase completion is also safe to advance when it precedes both configured candidates.
- The earliest eligible candidate permits the next phase, but a shared-edge capacity check may delay its actual start until active higher-priority phases release sufficient physical corridor capacity.
- Disjoint-corridor phases may overlap. Shared current plus phase loads may not exceed edge capacity because of overlap; unavoidable single-phase overload remains explicit in route/corridor evidence.
- Phase order remains 1 through 5. No lower-priority phase starts before its predecessor's modeled transition.

Every phase persists population type and conservation, routable population, mobilisation/travel/clearance minutes, effective capacity, departure rate, both trigger candidates and winner, transition delay, start/completion/transition offsets and timezone-aware timestamps anchored to handoff creation, linked requests, effective buffer, route edges/allocation snapshot, and empty/blocked state. Zero-population phases transition immediately with zero duration. Populated blocked phases have no completion; plan completion is `max(phase.completion_offset_minutes)` when all required phase completions are finite, otherwise `null`. Initial, replan, and commander-modified versions use the same calculation.

**Shelter-in-place decision** (FR-014):
| Condition | Action |
|-----------|--------|
| No viable route AND hazard timeline > `MOBILISATION_TIME` × 2 | Shelter-in-place with building requirements |
| No viable route AND immediate threat | Escalate to emergency services, flag for human intervention |
| Clearance time > hazard arrival window | Phased evacuation + shelter-in-place for unclearable zones |

**Shelter-to-evacuation recovery** (Research Task 3, CHK042):
- On road network update, re-evaluate shelter-in-place zones for new routes
- If viable route found, generate new plan version with evacuation route
- Log as `replanning_triggers=["shelter_to_evacuation_recovery"]`

### Stage 8: Plan Summary Generation

**Input**: All computed plan components  
**Output**: Human-readable plan summary

| Mode | Method |
|------|--------|
| Normal | Deterministic fact summary plus an optional pre-approved model acknowledgement; persisted as `ai_assisted` only after content-safety validation |
| LLM unavailable | Template fallback — structured summary from route/timeline/transport data |
| Content safety failure | Safety fallback — template text with `generation_method=safety_fallback` |

The authoritative narrative is rendered from validated routes and destinations, exclusions and capacity state, zone dispositions, phase deadlines/triggers, transport requests, data gaps, and final confidence. The model cannot add routes, numbers, directives, or safety claims; non-empty output outside the pre-approved acknowledgement set is treated as ungrounded and falls back to the deterministic template. Replans and commander-modified versions regenerate the same factual summary from their changed structured decisions.

Mandatory review, shelter/escalation/partial-movement, unavailable-road, zero-route, unresolved-demand, selected-route, and urgent assumption facts are budgeted separately from explanatory body text. Full assumptions remain structured on the plan and are never appended then truncated. The final displayed confidence is rendered only after all unique adjustment reasons have been applied.

**Confidence adjustment in fallback**:
- Template fallback: `confidence × 0.8` (multiplicative, per Research Task 4)
- Content safety failure: `confidence × 0.8` + `generation_method=safety_fallback` in audit

The shared LLM mixin retains its native labels for other agents. Evacuation adapts successful `llm` responses to `ai_assisted` locally and persists validator result/method/reason/evidence reference, grounding outcome, model deployment ID, and review requirement on both the plan and final audit. Keyword-validator fallback marks otherwise safe output for human review.

### Stage 9: Plan Versioning and Persistence

**Input**: Complete plan data  
**Output**: Persisted `EvacuationPlan` in Cosmos DB

**Process**:
1. Assign version via optimistic concurrency counter (same pattern as risk assessment).
2. Format `plan_id` as `ep-{incident_id}-v{N}`.
3. If previous versions exist, mark them as `superseded` (only if new version is approved — otherwise previous approved version remains active).
4. Store with `status=proposed` — no plan auto-executes (FR-024).
5. Capture data snapshot (road network version, population data version, facility data version, assembly area version) for reproducibility (FR-027).

**Duplicate handoff for existing plan** (Research Task 5, CHK080):
- If an approved plan exists for this incident, create a new version in `proposed` status.
- The approved plan is NOT auto-superseded. Commander decides whether to approve the new version.

### Stage 10: Audit Finalisation

**Input**: All processing artifacts  
**Output**: Comprehensive audit records for each processing step

Every stage produces one or more `EvacuationDecisionRecord` entries. The finalisation stage verifies completeness: handoff_id processed vs audit records created.

**Three-tier degradation** (same as monitoring/risk assessment):
- Tier 1: Cosmos DB `create_item()`
- Tier 2: Bounded in-memory cache backed by a local JSONL write-ahead log
- Tier 3: WAL-only overflow after the memory cache reaches `AUDIT_BUFFER_CAPACITY`
- A buffered receipt is accepted only after metadata serialization, file flush, and `fsync`; disk, permission, or `fsync` failure returns an explicit rejected receipt
- One process lock serializes append, flush, atomic suffix rewrite, and status reads. Recovery drains the WAL strictly oldest-first and stops at the first Cosmos failure or malformed line, retaining that exact suffix
- A 409 retry is idempotent success only when a partition-scoped point read matches the original record identity/content; conflicting content remains pending
- Existing WAL backlog is detected on restart and blocks newer direct writes. Status is derived from actual pending, corrupt, or rejected state and returns healthy only after complete recovery

---

## Latency Budget (30-second SLA — initial plan)

| Stage | Target | Notes |
|-------|--------|-------|
| 1. Handoff intake | ≤ 500ms | Pydantic validation + dedup lookup |
| 2. Assessment retrieval | ≤ 2,000ms | Cosmos DB read |
| 3. Zone computation | ≤ 1,000ms | Shapely polygon operations |
| 4. Road network prep | ≤ 1,000ms | In-memory graph modification |
| 5. Route computation | ≤ 5,000ms | Dijkstra's × multiple paths × multiple zones |
| 6. Transport coordination | ≤ 1,000ms | Facility lookup + requirement generation |
| 7. Timeline estimation | ≤ 1,000ms | In-memory computation |
| 8. Plan summary generation | ≤ 15,000ms | LLM call (primary bottleneck); template fallback ≤ 100ms |
| 9. Plan versioning + persistence | ≤ 2,000ms | Cosmos DB write with OCC |
| 10. Audit finalisation | ≤ 1,500ms | Cosmos DB writes (async batch) |
| **Total** | **≤ 30,000ms** | SLA breach logged if exceeded; processing still completes |

### Replanning Latency Budget (15-second SLA)

| Stage | Target | Notes |
|-------|--------|-------|
| 1. Trigger evaluation | ≤ 500ms | Evaluate replanning conditions |
| 4. Road network prep | ≤ 500ms | Incremental update (changed edges only) |
| 5. Route computation | ≤ 3,000ms | Recompute affected routes only |
| 6. Transport coordination | ≤ 500ms | Incremental update |
| 7. Timeline re-estimation | ≤ 500ms | Recalculate affected phases |
| 8. Plan summary generation | ≤ 8,000ms | LLM call or template fallback |
| 9. Versioning + persistence | ≤ 1,000ms | Cosmos DB write |
| 10. Audit finalisation | ≤ 500ms | Cosmos DB write |
| **Total** | **≤ 15,000ms** | SLA breach logged if exceeded; processing still completes |

---

## Dynamic Replanning Triggers (FR-016)

| Trigger | Detection | Action |
|---------|-----------|--------|
| New road closure on active route | Road network update event | Re-run stages 4–10 |
| Hazard area expands > 10% | New handoff with larger affected_area | Re-run stages 3–10 |
| Progress delay > 30% | Estimated vs actual phase timing | Re-run stages 5–10 |
| Higher-severity assessment received | New handoff with higher severity | Re-run stages 2–10 |
| Manual commander trigger | POST /replan endpoint | Re-run stages 3–10 |
| Shelter-to-evacuation recovery | Road update enables new route | Re-run stages 4–10 |

**Rate limiting**: Minimum `REPLAN_RATE_LIMIT_SECONDS` (default 30s) between replans for the same incident. Prevents version churn during rapidly changing conditions (CHK037).

**No-change detection** (FR-016 last sentence): If the replanning evaluation determines no material change (no affected routes, no zone changes), log that the existing plan remains valid and do NOT create a new version.

---

## Error Handling

| Error | Behaviour |
|-------|-----------|
| Malformed handoff | Reject, audit, do not process |
| Missing assessment | Reject, audit, do not process |
| Road network unavailable (fresh) | Use last-known-good if within staleness window; else degraded generic guidance |
| Road network unavailable (stale) | Degraded plan with generic evacuation guidance per hazard type, flag for human review |
| Population data unavailable | Produce plan without transport coordination, note data gap in assumptions |
| LLM timeout/error | Template fallback, 20% confidence reduction (multiplicative) |
| Content safety failure | Replace with template text, audit |
| Cosmos DB write failure | Three-tier degradation (memory → file) |
| Version counter conflict | Retry 3× with jitter, fallback to UUID-suffixed version |
| No viable routes for zone | Shelter-in-place or emergency escalation per FR-014 |
| All routes exceed capacity | Flag all corridors as congestion-risk, distribute as evenly as possible |
| Assembly area at capacity | Flag in plan assumptions, recommend commander verify alternatives (CHK081) |
