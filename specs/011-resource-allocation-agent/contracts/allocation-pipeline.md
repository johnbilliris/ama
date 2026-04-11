# Contract: Allocation Processing Pipeline

**Feature**: 011-resource-allocation-agent  
**Date**: 2026-04-17  
**Type**: Processing pipeline contract

---

## Overview

The Resource Allocation Agent processes inbound `AgentHandoffEvent` messages from the Risk Assessment Agent (coordination tasks) and the Evacuation Agent (transport dispatch requests) through a 9-stage pipeline, producing versioned `ResourceDeploymentPlan` records with resource assignments, shortfall details, and cross-incident trade-off analysis.

---

## Pipeline Stages

### Stage 1: Handoff Intake and Validation

**Input**: Raw `AgentHandoffEvent` from Azure Service Bus  
**Output**: Validated handoff or rejection audit record  
**SLA**: Acknowledge within 5 seconds of delivery

| Check | Action on Failure |
|-------|-------------------|
| Pydantic schema validation | Reject with `handoff_rejected` audit record |
| `target_agent == "resource_allocation"` | Reject with `handoff_rejected` audit record |
| `source_agent` is `risk_assessment` or `evacuation` | Reject with `handoff_rejected` audit record |
| `incident_id` exists in incident store | Reject with `handoff_rejected` audit record |
| Incident status is not `closed` (CHK032) | Reject — release resources if incident was recently closed |
| Idempotency check (handoff_id dedup, 10-min window) | Discard with `duplicate_discarded` audit record |
| Tenant validation (simulation vs live) | Route to appropriate processing context |

### Stage 2: Recommendation/Assessment Retrieval

**Input**: Validated handoff with payload references  
**Output**: Retrieved recommendation + hazard assessment data, OR transport requirements  
**Degradation**: If data store is partially unavailable, proceed with available data; reduce confidence.

| Source Agent | Retrieval Action |
|-------------|-----------------|
| `risk_assessment` | Retrieve `Recommendation` by `recommendationId` and `HazardAssessment` by `assessmentId` from Cosmos DB |
| `evacuation` | Extract `TransportRequirement[]` directly from handoff payload; retrieve `EvacuationPlan` by `evacuationPlanId` for context |

| Outcome | Action |
|---------|--------|
| All referenced data retrieved | Continue with full data set |
| Recommendation/assessment not found | Reject handoff with `handoff_rejected` audit record (FR-002, US1-AS4) |
| Evacuation plan superseded | Retrieve latest active plan for incident; log supersession (Edge Case) |
| Partial data available | Proceed with available data; reduce confidence by `PARTIAL_DATA_REDUCTION_FACTOR` |

### Stage 3: Demand Identification and Prioritisation

**Input**: Retrieved recommendation/assessment data or transport requirements  
**Output**: Prioritised `ResourceDemand[]` inserted into consolidated demand queue

| Source | Demand Extraction |
|--------|------------------|
| Risk Assessment coordination tasks | Extract resource type, sub-type, capabilities, quantity, location from task data. Derive priority tier from task category (life safety/property/environment). Derive urgency from task priority (normalise to AIDR 4-level). |
| Evacuation transport requirements | Classify as Tier 1 (life safety). Map transport priority to AIDR 4-level: `critical` → `critical`, `immediate` → `critical`, `high` → `high`. Extract vehicle type, quantity, pickup location. |

**Priority normalisation** (CHK020):

| Incoming (Risk Assessment) | Normalised |
|---------------------------|------------|
| `critical` | `critical` |
| `high` | `high` |
| `medium` | `moderate` |
| `low` | `low` |

| Incoming (Evacuation) | Normalised |
|----------------------|------------|
| `critical` | `critical` |
| `immediate` | `critical` |
| `high` | `high` |

**Queue insertion**: Demands are inserted at the correct position in the consolidated demand queue using the four-level tiebreaking hierarchy:
1. Life safety tier (Tier 1 > Tier 2 > Tier 3)
2. Severity/urgency (critical > high > moderate > low)
3. Proximity to available resources (closer preferred)
4. Request timestamp (earlier wins)

### Stage 4: Resource Inventory Query

**Input**: Prioritised demand list  
**Output**: Eligible resource pool per demand

| Step | Detail |
|------|--------|
| Load inventory | Static baseline + dynamic status updates |
| Filter by type/sub-type | Only resources matching demand's resource type and sub-type |
| Filter by capability | Binary match: resource must possess ALL `required_capabilities` |
| Filter by status | `available` (factor=1.0) or `returning` (factor=0.5); exclude all others |
| Handle reserved (CHK021) | Include `reserved` resources only if `assigned_incident_id` matches demand's `incident_id`; exclude otherwise |
| Handle missing location | Exclude resources with no valid coordinates from distance-based scoring; log warning |
| Check staleness | If inventory data older than `INVENTORY_STALENESS_WINDOW_MINUTES`, flag stale; reduce confidence by `STALE_DATA_REDUCTION_FACTOR` |

### Stage 5: Resource-Demand Matching (Scoring)

**Input**: Prioritised demands + eligible resource pools  
**Output**: Scored assignments and partial allocation details

**Scoring formula** (FR-011):
```
score = capability_match × (1 / max(distance_km, 0.1)) × availability_factor × priority_weight
```

| Factor | Value |
|--------|-------|
| `capability_match` | 1.0 (all required capabilities present) or 0.0 (excluded pre-scoring) |
| `distance_km` | Haversine formula; floor at `DISTANCE_FLOOR_KM` (default 0.1) |
| `availability_factor` | `available`=1.0, `returning`=0.5 |
| `priority_weight` | `critical`=4.0, `high`=3.0, `moderate`=2.0, `low`=1.0 |

**Greedy assignment**:
1. Sort demands by priority order (Tier → urgency → proximity → timestamp)
2. For highest-priority demand, compute scores for all eligible resources
3. Assign highest-scoring resource; remove from available pool
4. Tie-breaking (CHK014): highest capability count → alphabetical resource ID
5. Repeat for next demand
6. Mark demands as `fully_met`, `partially_met`, or `unmet` with shortfall details

**Partial allocation** (FR-012):
- Assign whatever resources are available that match type/capability
- Mark unfulfilled quantity with `ShortfallDetail` (quantity_unmet, reason, recommendation)
- Never silently drop demands — every demand appears in output as `fully_met`, `partially_met`, or `unmet`

### Stage 6: Cross-Incident Analysis

**Input**: Matched assignments across all active incidents  
**Output**: Trade-off analysis and reallocation recommendations (if applicable)

| Condition | Action |
|-----------|--------|
| Single-incident handoff, no contention | Skip cross-incident analysis |
| Multiple active incidents competing for same resource type | Generate `TradeOffAnalysis` with allocations per incident |
| Higher-priority incident has unmet life-safety demands | Recommend reallocation from lower-tier incidents; flag for commander approval |
| Equal-priority incidents with tied severity (CHK022) | Distribute proportionally by ratio of unmet demand counts |

**Reallocation guard** (FR-013):
- MUST NOT reassign from active approved plans without commander approval
- When critical life-safety demand cannot be met from unassigned resources AND a resource is assigned to Tier 2/3 demand → recommend (not execute) reallocation
- All cross-incident reallocations require `requires_commander_approval = true`

**Cross-incident SLA**: 30 seconds (longer than 15-second single-incident SLA to account for multi-incident scoring)

### Stage 7: Plan Generation and Summary

**Input**: Assignments, shortfalls, trade-off analysis, demands  
**Output**: Versioned `ResourceDeploymentPlan` with summary

| Step | Detail |
|------|--------|
| Assign version | Optimistic concurrency via version counter (Cosmos DB etag) — max 3 retries (CHK037) |
| Generate plan_id | Format: `rdp-{incident_id}-v{N}` |
| Compute deployment timelines | Per assignment: mobilisation overhead + travel time (Haversine distance / speed) |
| Compute confidence | Base 0.9 with multiplicative penalties (stale ×0.8, partial ×0.7, template ×0.8) |
| Set expiry | `created_at + PLAN_EXPIRY_HOURS` (default 4 hours) |
| Generate summary | LLM with template fallback; content safety validation |
| Store input snapshot | Demands, inventory hash, config version, scoring parameters for reproducibility |
| Mark previous versions | Transition existing `proposed` plans for same incident to `superseded` |

**LLM summary generation** (FR-016):
- System prompt scopes LLM to resource allocation rationale generation
- Include: what resources are deployed, where, why (linked to hazard assessment), gaps remaining
- AIIMS-consistent terminology
- Content safety validation before persistence (FR-037)

**LLM fallback mode** (Azure OpenAI unavailable):
- `generation_method = "template_fallback"`
- Confidence reduced by `FALLBACK_REDUCTION_FACTOR` (default ×0.8)
- Template includes structured assignment list, shortfall table, priority rationale

**Content safety fallback**:
- `generation_method = "safety_fallback"`
- Same confidence reduction as template fallback
- Failure logged as `content_safety_failure` audit record

### Stage 8: Plan Persistence

**Input**: Complete `ResourceDeploymentPlan`  
**Output**: Persisted plan in Cosmos DB

| Step | Detail |
|------|--------|
| Write plan | `create_item()` to `resource-deployment-plans` container |
| Update resource statuses | Transition assigned resources from `available` → `assigned` (or `reserved` → `assigned` for reserved resources) |
| Log assignments | Audit record per assignment with full scoring rationale |
| Emit plan event | `PlanGenerated` custom event for telemetry |

**Error handling**:
- Cosmos write failure: Three-tier degradation (audit continues; plan queued for retry)
- Version conflict during write: Retry from Stage 7 (re-read counter, re-increment)

### Stage 9: Audit Finalisation

**Input**: All processing artifacts  
**Output**: Comprehensive `AllocationDecisionRecord` entries for each processing step

Every stage produces one or more `AllocationDecisionRecord` entries. The finalisation stage verifies completeness: handoff_id processed vs audit records created.

**Three-tier audit degradation** (FR-031a):
1. **Tier 1**: Cosmos DB `create_item()` (primary — `resource-allocation-decisions` container)
2. **Tier 2**: In-memory ring buffer (capacity: `AUDIT_BUFFER_CAPACITY`, default 10,000)
3. **Tier 3**: File spill (JSONL to `AUDIT_BUFFER_FILE_PATH`)

Recovery flush: Tier 3 → Tier 2 → Tier 1 in chronological order when Cosmos DB recovers.

---

## Latency Budget (15-second SLA — single-incident allocation)

| Stage | Target | Notes |
|-------|--------|-------|
| 1. Handoff intake | ≤ 500ms | Pydantic validation + dedup lookup |
| 2. Data retrieval | ≤ 1,500ms | Cosmos DB reads (recommendation + assessment) |
| 3. Demand identification | ≤ 300ms | In-memory extraction and priority normalisation |
| 4. Inventory query | ≤ 1,000ms | In-memory filtering (static + dynamic state) |
| 5. Resource matching | ≤ 2,000ms | Scoring + greedy assignment (scales with inventory × demands) |
| 6. Cross-incident analysis | ≤ 0ms | Skipped for single-incident (30s budget when triggered) |
| 7. Plan generation | ≤ 7,000ms | LLM call (primary bottleneck); template fallback ≤ 100ms |
| 8. Plan persistence | ≤ 1,500ms | Cosmos DB write + resource status updates |
| 9. Audit finalisation | ≤ 1,200ms | Cosmos DB writes (async batch where possible) |
| **Total** | **≤ 15,000ms** | SLA breach logged if exceeded; processing still completes |

## Latency Budget (30-second SLA — cross-incident analysis)

| Stage | Target | Notes |
|-------|--------|-------|
| Stages 1–5 | ≤ 5,300ms | Same as above |
| 6. Cross-incident analysis | ≤ 10,000ms | Multi-incident scoring, trade-off analysis, proportional distribution |
| Stages 7–9 | ≤ 9,700ms | Same as above (may include multiple plan updates) |
| **Total** | **≤ 30,000ms** | SLA breach logged if exceeded; processing still completes |

---

## Error Handling

| Error | Behaviour |
|-------|-----------|
| Malformed handoff | Reject, audit, do not process |
| Missing incident | Reject, audit, do not process |
| Closed incident (CHK032) | Reject new allocation; release any assigned resources |
| Missing recommendation/assessment | Reject, audit (US1-AS4) |
| Superseded evacuation plan | Retrieve latest active plan; log supersession |
| No eligible resources (empty inventory) | Generate plan with all demands `unmet`; flag for commander |
| LLM timeout/error | Template fallback, confidence × 0.8 |
| Content safety failure | Replace with template text, audit |
| Cosmos DB write failure | Three-tier audit degradation (memory → file) |
| Version counter conflict (CHK037) | Retry 3× with jitter, fail with 409 on exhaustion |
| Resource becomes unavailable mid-planning (CHK009) | OCC ensures plan references consistent state; stale assignment caught at persistence |
| Invalid state transition (CHK039) | Reject signal, log anomaly, keep current state |
| Division by zero in scoring (CHK035) | Prevented by `max(distance_km, 0.1)` floor |

---

## Transport Dispatch Flow (FR-005, FR-008)

Transport dispatch requests from the Evacuation Agent follow the same pipeline but with specific handling:

1. **Stage 1**: Validate `source_agent == "evacuation"`, extract `transportRequirements` from payload
2. **Stage 3**: Classify all transport demands as **Tier 1 (life safety)**; normalise priority (`immediate` → `critical`)
3. **Stage 5**: Match against transport-capable resources (vehicles with required capability tags)
4. **Stage 7**: Include `evacuation_plan_id` and `transport_requirement_ids` in `Traceability`
5. **Stage 9**: Audit with `transport_dispatched` decision type

---

## Resource Status Update Flow (FR-018, FR-019)

Resource status signals are processed outside the main pipeline via a separate handler:

1. **Validate** signal structure (resource_id, new_status, timestamp)
2. **Validate** state transition against state machine (reject invalid transitions)
3. **Apply** status change to inventory manager
4. **Check** operational flags:
   - Personnel > 12h continuous deployment → flag `rotation_needed`
   - Consumable < 20% initial stock → flag `replenishment_needed`
   - Vehicle with mechanical issues → flag `degraded`
5. **Trigger** re-allocation check if resource transitions to `available` (CHK033)
6. **Audit** with `resource_status_updated` decision type

**SLA**: 5 seconds per status update
