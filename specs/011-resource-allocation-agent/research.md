# Research: Resource Allocation Agent — Demand Prioritisation, Resource Matching, Deployment Planning, and Multi-Incident Coordination

**Feature**: 011-resource-allocation-agent  
**Date**: 2026-04-17  
**Status**: Complete

---

## Research Task 1 — Priority Weight Values and Scoring Formula (CHK001, CHK035)

**Context**: FR-011 specifies the scoring formula `score = capability_match × (1/distance) × availability_factor × priority_weight` but provides no values for `priority_weight`. CHK001 identifies this as undefined. CHK035 identifies that `1/distance` produces infinity when distance is zero (co-located resources). The formula needs concrete, configurable weight values and a safe distance calculation.

**Decision**:
- **Priority weights**: `critical=4.0, high=3.0, moderate=2.0, low=1.0` — configurable via environment variables `PRIORITY_WEIGHT_CRITICAL`, `PRIORITY_WEIGHT_HIGH`, `PRIORITY_WEIGHT_MODERATE`, `PRIORITY_WEIGHT_LOW`.
- **Distance floor**: `max(distance_km, 0.1)` — a 100-metre minimum prevents division-by-zero while preserving a strong proximity preference for genuinely co-located resources. Score at 0.1 km = 10.0, which is high but finite.

**Rationale**: The 4:3:2:1 ratio gives critical demands 4× the weight of low demands, creating clear separation in scoring without overwhelming other factors. The ratio is intentionally non-exponential to avoid extreme scoring gaps that could make distance and capability irrelevant for critical demands. The 0.1 km floor represents approximately 100 metres — well within "co-located" in any disaster scenario — and produces a finite, dominant proximity score that naturally prioritises nearby resources without breaking the formula.

**Alternatives considered**:
- **Exponential weights (8:4:2:1)**: Rejected because critical demands would dominate scoring to the point that a critical demand 500 km away would outscore a high demand 1 km away, which violates practical deployment efficiency.
- **Zero-distance special case (score = MAX)**: Rejected because it introduces a discontinuity that complicates ranking when multiple resources are co-located.
- **1/(distance + 1) normalisation**: Rejected because it compresses the proximity factor range (max score of 1.0 for co-located vs 0.001 for 1000 km), making distance nearly irrelevant compared to priority weight.

---

## Research Task 2 — Availability Factor and Inventory Dynamics (CHK002, CHK044)

**Context**: FR-011 states availability_factor is "reduced for `returning` based on estimated return time" but provides no reduction formula. CHK002 identifies this gap. CHK044 asks whether static inventory at startup is consistent with dynamic status updates.

**Decision**:
- **Availability factor**: Step function for MVP — `available=1.0, returning=0.5, all other statuses=0.0`. Resources with status `reserved`, `assigned`, `en_route`, `deployed`, or `unavailable` are ineligible (factor=0.0 excludes them from scoring). `Returning` resources receive a 50% reduction to reflect their partial availability.
- **Inventory delineation**: Static inventory structure (resource types, capabilities, locations, managing org) loaded at startup from a JSON configuration file. Dynamic status updates (availability transitions, location changes, capacity updates) arrive via Service Bus `resource_status` signals. The `inventory.py` module maintains the runtime state by applying dynamic updates to the static baseline.

**Rationale**: A step function is simpler than a continuous decay curve based on estimated return time and is sufficient for MVP where return time estimates may be unreliable. The 0.5 factor acknowledges that returning resources are partially available but should be deprioritised relative to immediately available ones. The clear delineation between static structure and dynamic status addresses CHK044 by making the boundary explicit in the code architecture.

**Alternatives considered**:
- **Linear decay based on return ETA**: `availability_factor = max(0.1, 1.0 - (minutes_until_return / max_return_minutes))`. More precise but depends on accurate return time estimates that may not be available in MVP. Deferred to v2.
- **Binary available/unavailable**: Simpler but wastes returning resources that could be useful for lower-priority demands.
- **Three-step (1.0/0.7/0.3)** with separate factors for `returning-nearby` vs `returning-distant`: Overcomplicates MVP without clear operational benefit.

---

## Research Task 3 — Travel Speed Assumptions for Deployment Timelines (CHK003)

**Context**: FR-017 specifies deployment timelines with mobilisation overhead but doesn't define how Haversine distance is converted to travel time. CHK003 identifies this gap.

**Decision**: Configurable average travel speeds per resource type:
- **Personnel** (on foot/mixed transport): 40 km/h (default via `TRAVEL_SPEED_PERSONNEL_KMH`)
- **Vehicles** (road): 60 km/h (default via `TRAVEL_SPEED_VEHICLE_KMH`)
- **Helicopters**: 200 km/h (default via `TRAVEL_SPEED_HELICOPTER_KMH`)

Deployment timeline formula:
```
estimated_travel_minutes = haversine_distance_km / speed_kmh × 60
total_deployment_minutes = mobilisation_overhead_minutes + estimated_travel_minutes
```

Mobilisation overhead defaults: 15 minutes for personnel (`MOBILISATION_PERSONNEL_MINUTES`), 10 minutes for vehicles (`MOBILISATION_VEHICLE_MINUTES`), 5 minutes for helicopters (`MOBILISATION_HELICOPTER_MINUTES`).

**Rationale**: Haversine (straight-line) distance is an underestimate of road distance (typically 1.2–1.4× for Australian regional roads). The configured speeds implicitly account for this by being lower than theoretical maximum road speeds. These are initial defaults — operational teams can tune via environment variables for their region. Road-distance optimisation is deferred to v2, consistent with the spec.

**Alternatives considered**:
- **Fixed 1.3× road correction factor**: Applying a blanket correction to Haversine distance. Rejected because the factor varies significantly between urban (1.2×) and remote (1.5×+) areas, and configuring per-area factors adds unwarranted complexity for MVP.
- **Road-distance API call**: Using a mapping service for actual road distance. Explicitly deferred to v2 per spec assumptions.

---

## Research Task 4 — Confidence Level Calculation (CHK004)

**Context**: The spec references confidence as "0.0–1.0 numeric and categorical" and a 0.8 multiplier in fallback, but no base confidence calculation method is defined. CHK004 identifies this gap.

**Decision**: Base confidence starts at 0.9 with multiplicative penalty stacking:

| Condition | Penalty | Resulting Factor |
|-----------|---------|-----------------|
| Full inventory available + LLM available | None | 0.9 (base) |
| Stale inventory data (beyond staleness window) | ×0.8 | 0.72 |
| Partial inventory data (some resource types missing) | ×0.7 | 0.63 |
| LLM unavailable (template fallback) | ×0.8 | 0.72 |
| Content safety fallback | ×0.8 | 0.72 |
| Combined: stale + template fallback | ×0.8 × ×0.8 | 0.576 |

Confidence level derived from adjusted value: `low` (<0.4), `medium` (0.4–0.69), `high` (≥0.7).

**Rationale**: The 0.9 base (not 1.0) acknowledges that even with full data, the greedy algorithm may not produce a globally optimal allocation. Multiplicative stacking follows the same pattern as risk assessment (CHK039 in spec 012's research) and evacuation agents, keeping adjustments composable and bounded in [0.0, 1.0]. Each penalty is independently auditable.

**Alternatives considered**:
- **Base confidence = 1.0**: Rejected because it implies perfect certainty which is misleading for a greedy (non-optimal) algorithm.
- **Additive penalties**: Rejected because they can produce negative values and don't compose cleanly.
- **Data-driven confidence from scoring quality**: Computing confidence from the distribution of scores (how close alternatives are). Interesting but adds significant complexity for MVP. Deferred to v2.

---

## Research Task 5 — Demand Lifecycle and Resource Release (CHK005, CHK032, CHK033)

**Context**: CHK005 asks about demand lifecycle management (removal, fulfilment, cancellation). CHK032 asks about incident closure handling. CHK033 asks about automatic re-allocation when new resources become available.

**Decision**:
- **Demand lifecycle**: `pending` → `partially_met`/`fully_met`/`unmet` → `closed`. Demands transition based on assignment results. Cancellation is performed via commander override, transitioning to `closed` with a cancellation record.
- **Incident closure** (CHK032): On incident closure handoff, the agent transitions all assigned resources for that incident back to `available` status. Each transition is individually logged in the audit trail. Active deployment plans are transitioned to `cancelled`.
- **Re-allocation trigger** (CHK033): When a resource status update transitions a resource to `available`, the agent queries the pending unmet demands queue. If any unmet demands match the newly available resource's type and capabilities, a re-allocation cycle is triggered automatically (producing a new plan version or a new plan). This is fire-and-forget with audit logging — it does not require a new handoff from upstream.

**Rationale**: The demand lifecycle mirrors the plan lifecycle (both are immutable records with status transitions). Automatic re-allocation on resource availability aligns with the Constitution's target of 30% efficiency improvement — waiting for manual re-planning would waste newly available resources during time-critical disasters. The bulk resource release on incident closure prevents resource leaks.

**Alternatives considered**:
- **Manual re-allocation only**: Requires a new handoff from risk assessment. Rejected because it adds unnecessary delay when the agent already knows about unmet demands.
- **Continuous background optimisation**: Periodically re-score all assignments to find improvements. Rejected for MVP due to complexity and potential plan version churn.

---

## Research Task 6 — Plan Expiry for Unapproved Plans (CHK008)

**Context**: CHK008 identifies that no plan expiration, timeout, or escalation requirements exist for pending commander approvals. A proposed plan could sit indefinitely, blocking resources.

**Decision**: Plans expire after **4 hours** if not approved, rejected, or cancelled by a commander. Configurable via `PLAN_EXPIRY_HOURS` (default: 4).

- On expiry: status transitions from `proposed` to `expired`
- All resource assignments in the expired plan are released (resources return to `available`)
- An audit record captures the expiry event with timestamp
- Expired plans remain queryable for audit purposes
- A warning metric (`resource_allocation.plan_expired_count`) is emitted

**Rationale**: Four hours balances operational reality (commanders may be engaged with immediate response) with resource efficiency (plans shouldn't block resources for half a day during a dynamic disaster). This is consistent with the risk assessment agent's `valid_until` pattern (configurable per hazard type, default 4h).

**Alternatives considered**:
- **No expiry**: Rejected because proposed plans could indefinitely block resources from re-allocation, degrading response capacity.
- **1-hour expiry**: Too aggressive — commanders in active response may need more time to review complex multi-incident plans.
- **24-hour expiry**: Too long — disaster conditions change rapidly and a day-old plan is likely operationally irrelevant.

---

## Research Task 7 — Optimistic Concurrency for Plan Versioning (CHK009, CHK037)

**Context**: FR-015 requires monotonically increasing version numbers per incident. CHK009 asks about race conditions during concurrent plan generation. CHK037 asks about retry limits for optimistic concurrency.

**Decision**: Same pattern as risk assessment and evacuation agents:

1. **Counter document**: `{id: "{incident_id}_plan_counter", current_version: N, _etag: "..."}` in the resource-deployment-plans Cosmos container.
2. **Version assignment**: Read counter → increment → conditional `replace_item` with `If-Match: {_etag}`.
3. **Conflict handling**: On `412 Precondition Failed`, re-read, re-increment, retry. Maximum **3 retries** with exponential backoff + jitter (base 100ms, factor 2, jitter ±50ms).
4. **Exhausted retries**: Log error, return `409 Conflict` to the pipeline. The handoff remains in the queue for re-processing. Do NOT generate a plan with a UUID-based fallback version — plan IDs must follow the `rdp-{incident_id}-v{N}` format.

**Rationale**: Three retries with jitter handle typical contention (most incidents have serial plan generation). Unlike risk assessment's UUID fallback, we reject on exhausted retries because plan versioning is critical for commander decision-making — a non-sequential version would confuse the approval workflow. The handoff stays in the queue for automatic retry.

**Alternatives considered**:
- **UUID-based fallback version**: Used by risk assessment, but rejected here because plan version numbers are user-facing (commanders reference "Plan v3") and non-sequential IDs would cause confusion.
- **Locking (pessimistic concurrency)**: Rejected because Cosmos DB serverless doesn't support distributed locks, and lock contention during multi-incident peaks would degrade throughput.
- **Infinite retries**: Rejected because pathological contention could cause unbounded latency, violating the 15-second SLA.

---

## Research Task 8 — Tie-Breaking for Equal-Scoring Resources (CHK014)

**Context**: FR-022 mentions "proportional distribution" for equal-priority tie-breaking but CHK014 identifies the metric (demand count, quantity, population-at-risk) as ambiguous. Additionally, when two resources score identically for the same demand, a deterministic tiebreaker is needed.

**Decision**: Two levels of tie-breaking:

1. **Same demand, multiple resources with equal scores**: Prefer the resource with the **highest capability count** (more versatile resource gets assigned). If capability counts also tie, use **alphabetical resource ID** for deterministic ordering.
2. **Cross-incident proportional distribution** (FR-022): When two incidents have identical priority, severity, and population-at-risk, distribute contested resources proportionally based on the **ratio of unmet demand count** (not quantity or population). Example: Incident A has 5 unmet demands, Incident B has 3 — distribute 62.5% to A, 37.5% to B (rounded to nearest whole resource).

**Rationale**: Capability count as the primary tiebreaker sends the most versatile resource — this is operationally sound because a resource with more capabilities can handle unexpected follow-up demands at the deployment site. Alphabetical ID as the final tiebreaker ensures deterministic, reproducible ordering (SC-007). Unmet demand count for cross-incident distribution is the simplest metric that directly reflects operational load.

**Alternatives considered**:
- **Random tiebreaker**: Would violate reproducibility requirement SC-007.
- **Population-at-risk ratio for cross-incident**: More meaningful but requires population estimates that may not be available for all incidents. Deferred to v2 enhancement.
- **First-come-first-served for cross-incident**: Rejected because the spec explicitly requires proportional distribution, not temporal priority.

---

## Research Task 9 — Priority Taxonomy Normalisation (CHK020)

**Context**: Risk Assessment Agent (spec 012) uses urgency levels `critical > high > medium > low`. Evacuation Agent (spec 009) uses transport priority `critical > immediate > high`. The Resource Allocation Agent must consume both. CHK020 identifies this as a conflict.

**Decision**: Normalise all incoming priorities to the AIDR 4-level taxonomy: `low`, `moderate`, `high`, `critical`. Mapping tables:

**From Risk Assessment (FR-007)**:
| Incoming | Normalised |
|----------|------------|
| `critical` | `critical` |
| `high` | `high` |
| `medium` | `moderate` |
| `low` | `low` |

**From Evacuation (FR-008)**:
| Incoming | Normalised |
|----------|------------|
| `critical` | `critical` |
| `immediate` | `critical` |
| `high` | `high` |

**Unknown priorities**: Map to `low` and log a warning. This ensures the system never fails on unexpected input while preventing unknown priorities from being incorrectly elevated.

**Rationale**: AIDR (Australian Institute for Disaster Resilience) is the authoritative Australian framework referenced by the Constitution's AIIMS alignment requirement. Using the 4-level taxonomy (`low/moderate/high/critical`) provides a consistent scale across all agents. Mapping `immediate` → `critical` is the safest interpretation — evacuation transport marked `immediate` implies life-safety urgency equivalent to `critical`. Mapping `medium` → `moderate` aligns with AIDR terminology.

**Alternatives considered**:
- **5-level taxonomy adding `immediate` between `high` and `critical`**: Rejected because it introduces a level unique to evacuation, complicating cross-agent comparison and scoring weights.
- **Passthrough (no normalisation)**: Rejected because the scoring formula requires a single weight table, and different taxonomy strings would produce `KeyError` or incorrect weights.

---

## Research Task 10 — Reserved Resource Eligibility (CHK021)

**Context**: FR-010 defines a `reserved` state ("held for specific incident") but FR-011 only lists `available` and `returning` as eligible for matching. CHK021 asks whether `reserved` resources are intentionally excluded.

**Decision**: Reserved resources are **excluded from general matching** but are **available for their reserved incident**. Implementation:

- When matching resources for incident X, include resources with status `reserved` IF `resource.assigned_incident_id == X`.
- When matching for any other incident, exclude `reserved` resources (availability_factor = 0.0).
- A reservation can be released by the incident commander (override action), transitioning the resource back to `available`.
- Reservations are time-bounded: they expire when the associated plan expires (4-hour default) unless the plan is approved.

**Rationale**: Reservations exist to ensure critical resources are available when a specific plan is approved. Allowing general allocation of reserved resources would undermine the purpose of the reservation mechanism. However, the reserving incident must be able to use its own reserved resources in subsequent plan versions.

**Alternatives considered**:
- **Fully exclude reserved from all matching**: Would prevent the reserving incident from using its own reserved resources in new plan versions, creating a paradox.
- **Make reserved resources available to higher-priority incidents**: Sounds logical but would undermine the trust relationship between commanders and the system — if I reserve a helicopter, I expect it to remain reserved.

---

## Research Task 11 — 30% Improvement Baseline Measurement (CHK025)

**Context**: SC-006 requires "30% improvement in resource deployment efficiency compared to manual allocation baselines" but CHK025 identifies that no baseline methodology is defined.

**Decision**: Document "30% improvement" as an **aspirational target** with the following measurement framework:

- **Baseline establishment**: Manual allocation times from structured tabletop exercises using the same scenarios (bushfire, cyclone, flood). Time measurements: demand identification → resource selection → plan approval → dispatch instruction.
- **Metrics**: (a) **Time-to-allocation**: average time from demand identification to resource assignment in the plan (automated vs manual). (b) **Demand fulfilment rate**: percentage of demands fully met from available resources (automated vs manual).
- **Measurement method**: Paired comparison — same scenario, same resource inventory, one manual (human team using paper/whiteboard), one automated (agent). Minimum 3 scenarios per disaster type.
- **Statistical validity**: Given small sample sizes in tabletop exercises, report as directional improvement with confidence intervals. Full statistical significance not required for MVP validation.

**Rationale**: Training exercises are the only ethical and practical way to establish a manual baseline — real disasters cannot be repeated with controlled variables. The measurement framework is realistic for the MVP evaluation stage while acknowledging the limitations of small-sample comparison. SC-010's survey requirement (90% commander satisfaction) provides a qualitative complement.

**Alternatives considered**:
- **Historical incident data**: Real incident data from past disasters. Attractive but impractical — allocation decision timing is rarely recorded in post-incident reports, and conditions vary too widely for controlled comparison.
- **Defer measurement entirely**: Rejected because the Constitution explicitly lists this as a success target.

---

## Research Task 12 — Override Security and RBAC (CHK040)

**Context**: FR-024 records `override_by_user_id` and `override_by_role` but CHK040 identifies that no authentication, authorisation, or RBAC requirements are defined for who may perform overrides.

**Decision**: Full RBAC implementation is **deferred to v2**. For MVP:

- All override endpoints require a `commander` role claim in the incoming JWT token.
- The JWT validation extracts `user_id` and `role` from claims and records them in the override audit record.
- If the JWT is missing or the role is not `commander`, the endpoint returns `403 Forbidden`.
- The JWT issuer and validation are handled by the API gateway / Container Apps ingress (not by the agent itself).
- Environment variable `REQUIRE_AUTH` (default: `true`) allows disabling JWT validation in development/simulation environments.

**Rationale**: Full RBAC with role hierarchies, fine-grained permissions, and multi-agency access control is a cross-cutting concern that should be implemented consistently across all agents (not just resource allocation). For MVP, a simple role check provides a security boundary while the full RBAC design is developed as a platform capability.

**Alternatives considered**:
- **No auth check (rely on network isolation)**: Rejected because it provides no audit trail of WHO performed the override, violating the intent of FR-024.
- **Full RBAC in this agent**: Rejected as premature — role hierarchies and cross-agency permissions need platform-level design, not per-agent implementation.
