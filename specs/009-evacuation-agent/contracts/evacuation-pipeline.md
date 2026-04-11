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

**Input**: Validated handoff with assessment ID  
**Output**: Retrieved `HazardAssessment` with hazard map  
**Degradation**: If assessment cannot be retrieved, reject handoff with `handoff_rejected` audit record (FR-002, Edge Case 1).

| Outcome | Action |
|---------|--------|
| Assessment retrieved with hazard map | Continue to zone computation |
| Assessment retrieved without hazard map | Reject — insufficient data for route computation |
| Assessment not found | Reject with `handoff_rejected` audit record, log missing assessment |

### Stage 3: Zone Computation

**Input**: HazardAssessment with affected_area GeoJSON  
**Output**: Three concentric evacuation zones with population estimates

**Algorithm**:
1. Parse `affected_area` GeoJSON polygon as the Zone 1 boundary (immediate danger).
2. Compute Zone 2 by buffering Zone 1 polygon outward (buffer distance derived from hazard type characteristics).
3. Compute Zone 3 by buffering Zone 2 polygon outward.
4. For multi-hazard scenarios (FR-009d): compute `shapely.ops.unary_union()` of all hazard polygons before zone derivation. Highest severity (lowest zone number) applies to overlapping areas.
5. Estimate population per zone using pre-loaded population density data for the region.

**Geospatial operations** (using Shapely):
- Zone boundary: `hazard_polygon.buffer(distance)` for concentric zones
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

**Road data staleness check**: If road network data is older than `ROAD_DATA_STALENESS_HOURS` (default 6h), flag plan as degraded and reduce confidence.

### Stage 5: Route Computation

**Input**: Prepared road network graph, zones, assembly areas  
**Output**: List of `EvacuationRoute` records

**Algorithm** (Dijkstra's variant):
1. For each zone, identify origin nodes within the zone.
2. For each origin, compute shortest path to each reachable assembly area using Dijkstra's with edge weights = `distance / (capacity × utilisation_factor)`.
3. Hazard-type-aware routing: apply routing strategy modifiers per hazard type (see data-model.md mapping).
4. Multi-path distribution (FR-007): When population exceeds single-corridor capacity, compute additional paths by penalising edges on the first path and re-running Dijkstra.
5. Flag corridors with utilisation > 80% as congestion-risk.
6. For each route, compute vehicle suitability based on `surface_type` and `accessibility_features` of edges in the path.

**Tie-breaking** (CHK007): When two routes have equal cost, prefer the route with lower congestion risk, then shorter distance.

**No viable routes**: If no routes exist for a zone, trigger shelter-in-place decision (Stage 7).

### Stage 6: Transport Coordination

**Input**: Zone data, facility/population registry  
**Output**: List of `TransportRequirement` records

**Process**:
1. Query facility registry for facilities within each zone: aged care, disability care, hospitals, schools/childcare.
2. For each facility, create a `TransportRequirement` with appropriate vulnerability category, vehicle type, and priority level.
3. Compute `estimated_vehicles` using vehicle capacity assumptions (see data-model.md).
4. If population data is unavailable (FR-032), skip transport coordination, note data gap in plan assumptions.

**Priority mapping**:
| Vulnerability Category | Priority Level |
|----------------------|---------------|
| `medical_dependent` | `critical` |
| `mobility_impaired` | `immediate` |
| `elderly_aged_care` | `immediate` |
| `children_schools_childcare` | `high` |

### Stage 7: Timeline Estimation and Shelter-in-Place

**Input**: Routes, transport requirements, hazard time horizon  
**Output**: Five-phase timeline, shelter-in-place recommendations (if needed)

**Timeline formula** (per FR-013):
```
clearance_time = (population / road_capacity) × distance_km × 60  [minutes]
vulnerable_time = clearance_time × 1.5  [buffer multiplier]
phase_duration = mobilisation_time + travel_time
```

**Phase transitions** (per FR-015 + Research Task 2):
- **Primary trigger**: Elapsed time ≥ `phase_duration × PHASE_TRANSITION_TIME_FACTOR` (default 1.2)
- **Secondary trigger**: Estimated population departed ≥ `PHASE_TRANSITION_POPULATION_PCT`% (default 50%)
- Whichever trigger fires first initiates the next phase

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
| Normal | LLM via `_generate_with_fallback()` — plain language summary with AIIMS terminology |
| LLM unavailable | Template fallback — structured summary from route/timeline/transport data |
| Content safety failure | Safety fallback — template text with `generation_method=safety_fallback` |

**Confidence adjustment in fallback**:
- Template fallback: `confidence × 0.8` (multiplicative, per Research Task 4)
- Content safety failure: `confidence × 0.8` + `generation_method=safety_fallback` in audit

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
- Tier 2: In-memory `deque` (10K capacity)
- Tier 3: Local JSONL file
- Recovery flush: memory → file → Cosmos, annotating `buffered_at` and `flush_source`

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
