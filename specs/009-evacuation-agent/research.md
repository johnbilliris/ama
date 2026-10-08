# Research: Evacuation Agent — Route Optimisation, Transport Coordination, and Evacuation Planning

**Feature**: 009-evacuation-agent  
**Date**: 2026-04-16  
**Status**: Complete

---

## Research Task 1 — Audit Record Schema Consolidation (CHK055)

**Context**: CHK055 identifies a conflict between FR-028's field list (plan_version, routes, zones, populations, transport_requests, constraints_applied, replanning_triggers, processing_duration) and FR-029's field list (record ID, handoff ID, plan ID, decision type, confidence, processing duration, decision rationale, agent version, configuration version, timestamp). The evacuation agent needs a single canonical audit schema.

**Decision**: Merge FR-028 and FR-029 into one canonical `EvacuationDecisionRecord` schema matching the monitoring/risk assessment audit pattern. Core fields from FR-029 (record ID, handoff ID, plan ID, decision type, confidence, processing duration, rationale, agent version, configuration version, timestamp) form the base. FR-028's domain-specific fields (plan_version, routes_count, zones_affected, population_estimate, transport_requests_count, constraints_applied, replanning_triggers) are included as optional fields in the same record, populated when the decision type involves plan generation or updates.

**Canonical fields**:

The merged base contains **23 fields**: 10 FR-029/core identity fields, seven FR-028 domain fields, generation and tenant scope, and three storage timestamps/source fields. The earlier 22-field count omitted `incident_id`; the table below is authoritative. Implementations may add typed, queryable evidence fields without changing this canonical base.

| Field | Type | Source |
|-------|------|--------|
| `id` | str (UUID) | FR-029 |
| `handoff_id` | str | FR-029 |
| `plan_id` | str \| None | FR-029 |
| `incident_id` | str | Derived |
| `decision_type` | DecisionType enum | FR-029 |
| `confidence_raw` / `confidence_adjusted` | float | FR-029 confidence before/after explicit adjustments |
| `processing_duration_ms` | float | FR-028/FR-029 |
| `decision_rationale` | str | FR-029 |
| `agent_version` | str | FR-029 |
| `configuration_version` | str | FR-029 |
| `plan_version` | int \| None | FR-028 — populated for plan_generated/plan_updated |
| `routes_count` | int \| None | FR-028 — populated for plan_generated/plan_updated |
| `zones_affected` | list[int] \| None | FR-028 — populated for plan_generated/plan_updated |
| `population_estimate` | int \| None | FR-028 — populated for plan_generated/plan_updated |
| `transport_requests_count` | int \| None | FR-028 — populated for plan_generated/plan_updated |
| `constraints_applied` | list[str] \| None | FR-028 — populated for plan_generated/plan_updated |
| `replanning_triggers` | list[ReplanningTrigger] \| None | FR-028 — canonical names populated for plan_updated |
| `generation_method` | str | Aligned with monitoring/risk assessment pattern |
| `incident_scope_key` | str | Cosmos DB partition key |
| `tenant_id` | str | live \| simulation |
| `timestamp` | datetime (UTC) | FR-029 |
| `buffered_at` | datetime \| None | Three-tier degradation metadata |
| `flush_source` | str \| None | direct \| memory_buffer \| file_buffer |

**Rationale**: This follows the exact same pattern as risk assessment's `RiskAssessmentDecisionRecord` — shared structural fields (handoff_id, decision_type, confidence, processing_duration, agent_version, configuration_version, tenant_id, timestamp) with domain-specific optional fields. The merged schema eliminates the FR-028/FR-029 conflict while keeping domain-specific evacuation context available for post-incident review.

Typed extensions include `operation_id`, upstream assessment/recommendation/signal IDs, route IDs, principal identity, disposition and content-safety evidence, expected/observed steps, per-stage durations, and completeness warnings. Plan generation/update records require matching plan identity/version and exact route/transport counts. Every append returns an accepted storage-tier receipt; required-stage reconciliation counts only accepted receipts.

**Alternatives considered**:
- **Two separate record types**: One for general audit, one for plan-specific details. Rejected — adds complexity, the monitoring/risk assessment agents use a single record type, and joins during post-incident review are unnecessary friction.
- **FR-028 fields as nested JSON**: Storing plan-specific fields as an untyped dict. Rejected because Pydantic v2 validation would be lost and querying in Cosmos DB becomes harder.

---

## Research Task 2 — Phase Progress Measurement Without GPS (CHK025)

**Context**: CHK025 asks how "50% completion" is measured for phase transitions (FR-015) without real-time GPS tracking, which is explicitly out of scope. The spec defines phase transition as "estimated population departed from pickup/origin points" reaching 50%.

**Decision**: Use estimated departure rates derived from pre-loaded population data, not real-time GPS. Phase transitions use time-based thresholds as the primary mechanism and estimated population moved as the secondary mechanism.

**Implementation**:
1. **Primary trigger**: Time-based — each phase has a calculated duration estimate based on `population × distance / capacity`. When elapsed time reaches `phase_duration_estimate × 1.2` (the configurable threshold from FR-015), the phase transitions.
2. **Secondary trigger**: Estimated population moved — calculated as `departure_rate × elapsed_time` where `departure_rate = road_capacity × utilisation_factor`. When this estimate reaches 50% of phase population, the phase transitions. Whichever trigger fires first wins (per FR-015 "whichever occurs first").
3. **No real-time tracking**: All estimates are computed at plan generation time from pre-loaded population data and road network capacity. Phase transitions are modelled as expected timelines in the plan, not as runtime state machines monitoring live data.

**Rationale**: The spec explicitly excludes real-time GPS tracking (Out of Scope). The estimated departure rate model provides a reasonable approximation using the same population density and road capacity data already available for timeline estimation. The time-based threshold as primary ensures phases always progress even if the estimated model is inaccurate.

**Alternatives considered**:
- **Real-time check-in system**: Would require field infrastructure and is explicitly out of scope.
- **Time-based only**: Simpler but loses the 50% population metric required by FR-015. The estimated model satisfies the requirement while being computationally feasible.

---

## Research Task 3 — Shelter-in-Place to Evacuation Recovery (CHK042)

**Context**: CHK042 identifies a gap in the spec — no requirements exist for transitioning from shelter-in-place back to evacuation when conditions change (e.g., new route becomes available).

**Decision**: Allow transition from shelter-in-place back to evacuation when a new route becomes available. This is treated as a replanning event and follows the existing dynamic replanning mechanism (FR-016).

**Implementation**:
1. When a new road network update arrives and an active plan has shelter-in-place zones, the agent re-evaluates whether evacuation routes now exist for those zones.
2. If a viable route is found, a new plan version is generated that replaces the shelter-in-place recommendation with an evacuation route for the affected zone.
3. The change summary explicitly notes the transition from shelter-in-place to evacuation with the triggering event (new route availability).
4. The audit trail logs this as `decision_type=plan_updated` with `replanning_triggers=["shelter_to_evacuation_recovery"]`.

**Rationale**: The Constitution (Principle I) mandates prioritising life safety. If an evacuation route becomes available for a zone previously designated as shelter-in-place, failing to offer it could endanger lives. Treating this as a standard replanning event keeps the implementation simple — no new mechanisms are needed beyond the existing dynamic replanning pipeline.

**Alternatives considered**:
- **Manual-only recovery**: Only allow commanders to switch from shelter-in-place to evacuation. Rejected because it adds latency to a life-safety decision and contradicts the agent's role in dynamic replanning.
- **Automatic transition without logging**: Rejected — all plan changes must be audited per FR-028.

---

## Research Task 4 — Confidence Reduction Method (CHK063)

**Context**: CHK063 asks whether the 20% confidence reduction in FR-033 (LLM unavailable fallback) is absolute (0.8 → 0.6) or relative/multiplicative (0.8 → 0.64).

**Decision**: Multiplicative — `adjusted_confidence = confidence × 0.8`. This matches the risk assessment agent's pattern where `FALLBACK_REDUCTION_FACTOR=0.8` is applied multiplicatively.

**Rationale**: Consistency with the risk assessment agent's established pattern. Multiplicative reduction keeps values bounded in [0.0, 1.0] regardless of the base confidence. An absolute reduction of 0.2 could produce negative values for low-confidence assessments (e.g., 0.15 − 0.2 = −0.05).

**Alternatives considered**:
- **Absolute reduction (−0.2)**: Could produce negative values. Rejected for the same reasons as the risk assessment agent's decision.

---

## Research Task 5 — Duplicate Handoff for Existing Approved Plan (CHK080)

**Context**: CHK080 asks what happens when the Evacuation Agent receives a handoff for an incident that already has an `approved` plan.

**Decision**: Create a new plan version incorporating the new assessment data. Do not reject the handoff.

**Implementation**:
1. The agent queries for the latest plan for the incident.
2. If a plan exists (in any status including `approved`), the agent creates a new version (`v{N+1}`) incorporating the new assessment data.
3. The previous version is NOT automatically superseded — an `approved` plan can only be superseded by a new plan that is also approved (by the incident commander).
4. The new version is created in `proposed` status, allowing the commander to compare it with the current approved plan and decide whether to approve the update.
5. Audit records capture the existing plan version, the new plan version, and the triggering handoff.

**Rationale**: During dynamic disaster events, new assessment data often arrives while plans are already in execution. Rejecting the handoff would lose critical updated information. Creating a new version preserves the approved plan's authority while giving commanders updated options based on new data.

**Alternatives considered**:
- **Reject with audit log**: Simpler but loses updated hazard information during active incidents. Rejected.
- **Auto-supersede the approved plan**: Would bypass human authority. Rejected — Constitution mandates commander approval.
- **Merge into existing plan**: Complex and violates plan immutability. Rejected.

---

## Research Task 6 — Road Network Data Source for MVP (CHK002, user resolution)

**Context**: The spec states the road network comes from a static JSON file for MVP (FR-005). The exact schema, format, and sample data need to be defined.

**Decision**: Use a static JSON file with a graph representation containing nodes (intersections) and edges (road segments). Include a sample road network for testing covering a simplified Far North Queensland coastal region.

**Schema**:
```json
{
  "metadata": {
    "version": "1.0",
    "region": "Far North Queensland",
    "coordinate_system": "EPSG:4326",
    "generated_at": "2026-04-16T00:00:00Z"
  },
  "nodes": [
    {
      "id": "node-001",
      "name": "Cairns CBD",
      "coordinates": { "lat": -16.9186, "lng": 145.7781 },
      "type": "intersection",
      "zone_membership": null,
      "is_assembly_area": false
    }
  ],
  "edges": [
    {
      "id": "edge-001",
      "from_node": "node-001",
      "to_node": "node-002",
      "name": "Captain Cook Highway",
      "distance_km": 25.0,
      "capacity_vehicles_per_hour": 1200,
      "surface_type": "sealed",
      "accessibility_features": ["wheelchair_accessible_footpath"],
      "closure_status": "open",
      "closure_reason": null,
      "geometry": {
        "type": "LineString",
        "coordinates": [[-16.9186, 145.7781], [-16.75, 145.70]]
      }
    }
  ],
  "assembly_areas": [
    {
      "id": "aa-001",
      "name": "Cairns Convention Centre",
      "node_id": "node-001",
      "capacity_persons": 5000,
      "accessibility_features": ["wheelchair_accessible", "medical_facilities"],
      "coordinates": { "lat": -16.9186, "lng": 145.7781 }
    }
  ]
}
```

**Rationale**: A JSON graph representation aligns with standard network/graph algorithms (Dijkstra's). Including `geometry` as GeoJSON `LineString` on edges enables Shapely-based zone intersection without a separate geospatial layer. The sample network for Far North Queensland supports the spec's User Story 1 (cyclone approaching coastal region).

**Alternatives considered**:
- **GeoJSON FeatureCollection**: Standard geospatial format but doesn't naturally represent graph topology (adjacency). Would require additional processing to build the graph.
- **GraphML/GML**: Standard graph formats but add XML parsing complexity and are less familiar in Python/JSON ecosystems.
- **SQLite/GeoPackage**: Better for large datasets but overkill for MVP static data and adds a database dependency.

---

## Research Task 7 — Geospatial Library for Zone Intersection (user resolution)

**Context**: FR-009c requires determining which road segments fall within hazard zones by intersecting road segment geometries with zone boundary polygons. The user specified Shapely for this purpose.

**Decision**: Use Shapely for all geospatial operations: zone boundary computation, road segment intersection, capacity reduction based on zone membership, and multi-hazard zone merging (geometric union per FR-009d).

**Key operations**:
1. **Zone boundary computation**: Buffer the hazard center point or use the provided GeoJSON polygon to define zone boundaries.
2. **Road segment intersection**: For each edge in the road network, create a Shapely `LineString` from its geometry and test intersection with zone polygons using `polygon.contains(line)` for full containment and `polygon.intersects(line)` for partial overlap.
3. **Partial overlap handling** (CHK013): Road segments that partially overlap a zone boundary use the highest-severity zone they touch. If a segment starts in Zone 2 and ends in Zone 3, it gets Zone 2's capacity reduction (50%). This is conservative and aligns with Life Safety First.
4. **Multi-hazard merging**: `shapely.ops.unary_union()` to compute the geometric union of all hazard polygons.
5. **Geospatial precision** (CHK012): Use EPSG:4326 (WGS84) coordinates with default Shapely floating-point precision (~1mm at equator). No explicit tolerance is needed for zone intersection at road-segment scale.

**Rationale**: Shapely is the standard Python geospatial library, well-maintained, and has no native code dependencies beyond GEOS (bundled). It handles all required operations (intersection, contains, union, buffer) without needing a full GIS stack. The conservative partial-overlap rule aligns with Constitution Principle I (Life Safety First).

**Alternatives considered**:
- **GeoPandas**: Built on Shapely but adds Pandas dependency. Overkill for per-segment operations — we're not doing bulk spatial joins on large datasets.
- **Turf.js (via subprocess)**: Python-native solution preferred. Rejected.
- **Custom coordinate math**: Error-prone for polygon operations. Rejected.

---

## Research Task 8 — Three-Tier Audit Degradation (user resolution, CHK054)

**Context**: CHK054 asks for specific transition criteria for the three-tier audit degradation pattern. The user specified matching the monitoring/risk assessment pattern.

**Decision**: Replicate the exact three-tier audit degradation pattern from `apps/agents/risk_assessment/audit.py` and `apps/agents/monitoring/audit.py`:

1. **Tier 1 — Cosmos DB**: Primary append-only write via `create_item()`. Attempted first for every audit record.
2. **Tier 2 — WAL-backed memory cache**: A bounded in-memory `deque` (default 10K records via `AUDIT_BUFFER_CAPACITY`) accelerates inspection, but acceptance occurs only after the record and its buffer metadata are fsynced to the local JSONL WAL.
3. **Tier 3 — WAL-only overflow**: After the memory cache is full, additional records append to the same synchronized WAL at `AUDIT_BUFFER_FILE_PATH` (default `/app/var/evacuation-agent/audit-buffer.jsonl`). Disk, permission, or fsync failure is an explicit rejected receipt.
4. **Recovery flush**: Drain the single WAL strictly oldest-first under the append/drain lock. Stop on the first failure or corrupt line and atomically retain the exact suffix. A 409 is success only after scoped identity/content reconciliation. Restart detects backlog before accepting newer direct writes, and healthy status returns only when no pending/corrupt/rejected state remains.
5. **Status reporting**: `get_status()` returns `healthy` (Tier 1 active), `buffering` (Tier 2 active), or `degraded` (Tier 3 active).

**Transition criteria**:
- Tier 1 → Tier 2: Any Cosmos DB write exception (timeout, 429 throttle, connection error, 503)
- Tier 2 → Tier 3: `len(buffer) >= AUDIT_BUFFER_CAPACITY`
- Tier 3 → Tier 2: File write succeeds (buffer remains active for new writes)
- Tier 2 → Tier 1: Cosmos DB write succeeds on flush attempt
- Direct Tier 1: Every write always attempts Cosmos first before falling back

**Rationale**: Proven pattern already validated in two agents. Consistency across agents simplifies operations and troubleshooting. The Constitution mandates unbroken audit trail (NFR) while also mandating no halt for single dependency failure (FR-035). This pattern satisfies both.

**Alternatives considered**: None — the existing pattern is validated and mandated by consistency with other agents.

---

## Research Task 9 — Dijkstra's Variant Selection (CHK001)

**Context**: CHK001 asks why Dijkstra's algorithm was selected over A*, Bellman-Ford, or other pathfinding algorithms.

**Decision**: Use standard Dijkstra's algorithm with a priority queue (min-heap) for route computation. For MVP with static road network data, no heuristic-based algorithms (A*) are needed.

**Rationale**:
- **Dijkstra's vs A***: A* requires an admissible heuristic (typically Euclidean distance). For evacuation routing, the edge weights incorporate capacity, distance, and hazard zone penalties — making a simple geographic heuristic potentially inadmissible. Dijkstra's guarantees optimal paths without heuristic design. For MVP network sizes (hundreds of nodes, not millions), the performance difference is negligible.
- **Dijkstra's vs Bellman-Ford**: Bellman-Ford handles negative edge weights (irrelevant here — all weights are positive) and is O(VE) vs Dijkstra's O((V+E) log V). Dijkstra's is faster for our use case.
- **Multi-path**: The agent needs multiple routes for load distribution (FR-007). After finding the shortest path, subsequent paths are found by increasing the weight of edges on the first path (penalising reuse) and running Dijkstra again. This simple iterative approach avoids the complexity of k-shortest-paths algorithms.

**Alternatives considered**:
- **A* with Euclidean heuristic**: Would be faster for geographic routing but heuristic admissibility is not guaranteed when weights include capacity and hazard penalties. Rejected for MVP.
- **Bellman-Ford**: Slower, handles negative weights we don't have. Rejected.
- **Yen's k-shortest paths**: More rigorous multi-path algorithm but adds significant complexity. Deferred to v2 if performance requires it.

---

## Research Task 10 — Road Network Size Constraints for MVP (CHK059)

**Context**: CHK059 asks for size constraints on the "simplified road network graph" for MVP performance expectations.

**Decision**: MVP road network is constrained to:
- **Max nodes**: 1,000 (intersections)
- **Max edges**: 5,000 (road segments)
- **Rationale for limits**: Dijkstra's on a 1,000-node graph with 5,000 edges completes in <10ms on a single CPU core. This supports the 30-second initial plan generation SLA (SC-001) with ample headroom even with multiple Dijkstra runs for multi-path computation.
- **Validation**: Road network loader validates these limits on startup and logs a warning if exceeded.

**Rationale**: These limits support the entire Far North Queensland coastal region (Cairns to Cooktown) at a simplified level appropriate for MVP. Future versions with live GIS integration can handle larger networks with spatial indexing (R-tree).
