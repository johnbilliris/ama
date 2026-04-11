# Tasks: Resource Allocation Agent — Demand Prioritisation, Resource Matching, Deployment Planning, and Multi-Incident Coordination

**Input**: Design documents from `/specs/011-resource-allocation-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, checklists/requirements.md ✅

**Tests**: Included — plan.md explicitly specifies unit, contract, integration, and simulation tests per phase.

**Organization**: Tasks are grouped by user story (P1–P8) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Agent source**: `apps/agents/resource_allocation/`
- **Shared agent infra**: `apps/agents/common/`
- **Tests**: `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/simulation/`
- **Sample data**: `data/resource-inventories/`
- **Infrastructure**: `infra/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package initialization and sample data for the Resource Allocation Agent

- [X] T001 Create package init file at `apps/agents/resource_allocation/__init__.py` exporting `ResourceAllocationAgent`
- [X] T002 [P] Verify `azure-cosmos`, `azure-servicebus`, and `tenacity` dependencies already present in `apps/agents/pyproject.toml`; add if missing
- [X] T003 [P] Create sample resource inventory file at `data/resource-inventories/sample-inventory.json`with representative resources across all four categories (vehicles: ambulance, fire truck, bus, helicopter; personnel: paramedic, firefighter, SES volunteer, police; supplies: water, food, medical kit, generator, fuel; facilities: evacuation centre, hospital, staging area) including coordinates, capabilities, capacity, and status fields per data-model.md §ResourceInventoryItem

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, configuration, and domain entity definitions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `apps/agents/resource_allocation/config.py` with `ResourceAllocationConfig` frozen dataclass reading all environment variables from research.md and data-model.md §Configurable Parameters: priority weights (`PRIORITY_WEIGHT_CRITICAL=4.0`, `PRIORITY_WEIGHT_HIGH=3.0`, `PRIORITY_WEIGHT_MODERATE=2.0`, `PRIORITY_WEIGHT_LOW=1.0`), availability factors (`AVAILABILITY_AVAILABLE=1.0`, `AVAILABILITY_RETURNING=0.5`), distance floor (`DISTANCE_FLOOR_KM=0.1`), travel speeds (`TRAVEL_SPEED_PERSONNEL_KMH=40`, `TRAVEL_SPEED_VEHICLE_KMH=60`, `TRAVEL_SPEED_HELICOPTER_KMH=200`), mobilisation overheads (`MOBILISATION_PERSONNEL_MINUTES=15`, `MOBILISATION_VEHICLE_MINUTES=10`, `MOBILISATION_HELICOPTER_MINUTES=5`), plan expiry (`PLAN_EXPIRY_HOURS=4`), confidence base (`CONFIDENCE_BASE=0.9`), confidence penalties (`STALE_DATA_REDUCTION_FACTOR=0.8`, `PARTIAL_DATA_REDUCTION_FACTOR=0.7`, `FALLBACK_REDUCTION_FACTOR=0.8`), inventory staleness window (`INVENTORY_STALENESS_WINDOW_MINUTES=30`), dedup window (`HANDOFF_DEDUP_WINDOW_MINUTES=10`), rotation threshold (`ROTATION_THRESHOLD_HOURS=12`), replenishment threshold (`REPLENISHMENT_THRESHOLD_PERCENT=0.2`), audit buffer capacity (`AUDIT_BUFFER_CAPACITY=10000`), audit buffer file path, agent version, OCC max retries (`VERSION_CONFLICT_MAX_RETRIES=3`), Cosmos DB endpoint/database/container names, Service Bus connection
- [X] T005 [P] Create `apps/agents/resource_allocation/models.py` with all Pydantic v2 models and enums from data-model.md: enums — `DecisionType` (16 values: `handoff_received`, `handoff_rejected`, `duplicate_discarded`, `demand_identified`, `resource_matched`, `resource_excluded`, `partial_allocation`, `plan_generated`, `plan_superseded`, `plan_expired`, `override_applied`, `reallocation_recommended`, `transport_dispatched`, `resource_status_updated`, `degradation_detected`, `content_safety_failure`), `ConfidenceLevel` (`low`/`medium`/`high`), `PlanStatus` (`proposed`/`approved`/`rejected`/`superseded`/`cancelled`/`expired`), `ResourceStatus` (7 states: `available`/`reserved`/`assigned`/`en_route`/`deployed`/`returning`/`unavailable`), `ResourceType` (`vehicle`/`personnel`/`supply`/`facility`), `DemandFulfilmentStatus` (`pending`/`partially_met`/`fully_met`/`unmet`/`closed`), `PriorityTier` (`tier_1_life_safety`/`tier_2_property`/`tier_3_environment`), `UrgencyLevel` (`critical`/`high`/`moderate`/`low`); embedded models — `ScoringRationale` (9 fields), `DeploymentTimeline` (7 fields), `ShortfallDetail` (8 fields), `TradeOffAnalysis` (6 fields), `Traceability` (5 fields), `OverrideMetadata` (6 fields), `InputSnapshot` (5 fields), `ResourceDemand` (16 fields), `ResourceAssignment` (11 fields), `ResourceInventoryItem` (13 fields); primary models — `ResourceDeploymentPlan` (23 fields with validators: plan_id regex `rdp-.*-v\d+`, version ≥ 1, confidence clamped [0,1], confidence_level derived from confidence_score), `AllocationDecisionRecord` (26 canonical fields, append-only audit), `AuditBufferEntry` for degraded writes
- [X] T006 [P] Write unit tests for all models, enums, and config in `tests/unit/test_resource_allocation_models.py` covering: all 8 enum completeness checks, `ResourceDeploymentPlan` validation (plan_id regex, version ≥ 1, confidence range [0,1], confidence_level derivation: `low < 0.4`, `medium 0.4–0.69`, `high ≥ 0.7`, status transitions), `ResourceDemand` required field validation, `ResourceAssignment` required field validation, `AllocationDecisionRecord` required field validation and optional field handling, `ResourceInventoryItem` status default and capability list, `ScoringRationale` score range, `ShortfallDetail` quantity invariants (`quantity_unmet = quantity_requested - quantity_assigned`)
- [X] T007 [P] Write unit tests for config loading in `tests/unit/test_resource_allocation_config.py` covering: default values for all 25+ parameters, environment variable overrides, type coercion (str→float, str→int), missing optional variables use defaults, invalid types raise errors

**Checkpoint**: Foundation ready — all models, enums, and configuration defined. User story implementation can now begin.

---

## Phase 3: User Story 1 — Receive Handoff and Generate Resource Deployment Plan (Priority: P1) 🎯 MVP

**Goal**: Receive `AgentHandoffEvent` from Risk Assessment Agent, retrieve referenced recommendation and assessment, identify resource demands, query inventory, score and assign resources via greedy algorithm, generate versioned `ResourceDeploymentPlan` with LLM or template rationale, and persist with traceability.

**Independent Test**: Send a synthetic `AgentHandoffEvent` with `source_agent=risk_assessment`, `target_agent=resource_allocation`, and a payload containing recommendation ID, summary, and assessment ID. Verify the agent produces a `ResourceDeploymentPlan` with resource assignments, deployment timelines, confidence, and traceability references back to the originating assessment.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Write unit tests for handoff deduplication in `tests/unit/test_resource_allocation_dedup.py` covering: first-seen handoff passes, duplicate within window discarded, duplicate after window passes, configurable window duration, concurrent dedup safety
- [X] T009 [P] [US1] Write unit tests for scoring algorithm in `tests/unit/test_resource_allocation_scoring.py` covering: Haversine formula at equator/poles/antipodes/known city pairs, distance floor enforcement at 0/0.05/0.1/1.0 km (`max(distance, 0.1)`), full scoring formula `score = capability_match × (1/max(distance, 0.1)) × availability_factor × priority_weight`, binary capability match (1.0 if all required present, 0.0 otherwise), type and sub-type compatibility (vehicle:ambulance ≠ vehicle:fire_truck), zero score when capability match is 0.0, availability factor integration (`available=1.0`, `returning=0.5`, others `0.0`), priority weight integration (critical=4.0, high=3.0, moderate=2.0, low=1.0)
- [X] T010 [P] [US1] Write unit tests for priority normalisation in `tests/unit/test_resource_allocation_priority.py` covering: AIDR 4-level mapping from Risk Assessment (`critical`/`high`/`medium`/`low` → `critical`/`high`/`moderate`/`low`), Evacuation priority mapping (`immediate` → `critical`, `critical` → `critical`, `high` → `high`), three-tier hierarchy ordering (Tier 1 life safety > Tier 2 property > Tier 3 environment), demand queue priority-ordered insertion (not append), four-level tiebreaking (life safety → severity → proximity → timestamp), proportional distribution for true ties (equal severity + population)
- [X] T011 [P] [US1] Write unit tests for resource inventory manager in `tests/unit/test_resource_allocation_inventory.py` covering: static inventory loading from JSON, state machine valid transitions (available→reserved, available→assigned, assigned→en_route, en_route→deployed, deployed→returning, returning→available), state machine invalid transitions rejected (e.g., available→deployed, deployed→assigned), `unavailable` reachable from any active state, operational flag: rotation after 12h continuous deployment, operational flag: replenishment below 20% stock, operational flag: mechanical issue, reserved resource excluded from general matching but available for reserved incident, bulk release on incident closure (assigned→available for all resources of incident), availability factor computation, missing/invalid location exclusion from distance scoring
- [X] T012 [P] [US1] Write unit tests for resource-demand matching in `tests/unit/test_resource_allocation_matcher.py` covering: greedy assignment (highest-scoring resource to highest-priority demand), partial allocation (assign what's available, mark remainder `unmet` with shortfall details), every demand appears in output as `fully_met`/`partially_met`/`unmet`, tie-breaking (highest capability count wins, then alphabetical resource ID), resource already assigned to active plan not reassigned without commander approval, empty inventory produces all demands as `unmet`
- [X] T013 [P] [US1] Write unit tests for version counter in `tests/unit/test_resource_allocation_versioning.py` covering: first version = 1, monotonic increment per incident, optimistic concurrency retry on 412 Precondition Failed, max 3 retries with jitter, fallback to UUID-suffixed version after exhausted retries, concurrent version assignment safety, separate version sequences per incident ID
- [X] T014 [P] [US1] Write unit tests for pipeline stages 1–9 in `tests/unit/test_resource_allocation_pipeline.py` covering: valid handoff acceptance, malformed handoff rejection, missing incident rejection, duplicate handoff discard, recommendation/assessment retrieval success/failure, demand extraction from coordination tasks, priority queue ordering, inventory query and filtering, scoring and greedy assignment, plan generation with version, plan persistence, audit record creation at each stage

### Implementation for User Story 1

- [X] T015 [P] [US1] Create `apps/agents/resource_allocation/dedup.py` with `HandoffDeduplicator` class: TTL-based in-memory cache keyed by `handoff_id`, configurable dedup window from `ResourceAllocationConfig.handoff_dedup_window_minutes` (default 10 min), `is_duplicate(handoff_id) -> bool` method, automatic eviction of expired entries
- [X] T016 [P] [US1] Create `apps/agents/resource_allocation/scoring.py` with scoring functions: `haversine_distance(lat1, lon1, lat2, lon2) -> float` returning km, `compute_score(resource, demand, config) -> float` implementing `score = capability_match × (1/max(distance, 0.1)) × availability_factor × priority_weight`, `check_capability_match(resource_capabilities, required_capabilities) -> float` returning 1.0 or 0.0 (binary), `check_type_compatibility(resource_type, resource_sub_type, demand_type, demand_sub_type) -> bool`, `get_availability_factor(status, config) -> float` returning factor from config, `estimate_travel_time(distance_km, resource_type, config) -> float` returning minutes including mobilisation overhead
- [X] T017 [P] [US1] Create `apps/agents/resource_allocation/priority.py` with priority normalisation and demand queue: `normalise_urgency(raw_priority, source_agent) -> UrgencyLevel` mapping Risk Assessment and Evacuation priorities to AIDR 4-level taxonomy per research.md §9, `classify_priority_tier(demand_context) -> PriorityTier` assigning Tier 1/2/3 based on demand type (evacuation/medical → Tier 1, structural defence → Tier 2, containment → Tier 3), `DemandQueue` class with priority-ordered insertion using four-level comparison (tier → urgency → proximity → timestamp), `distribute_proportionally(demands, resources, incidents) -> dict` for true-tie proportional allocation per FR-022
- [X] T018 [P] [US1] Create `apps/agents/resource_allocation/inventory.py` with `ResourceInventoryManager` class: `load_from_json(path) -> list[ResourceInventoryItem]` for static baseline inventory from `data/resource-inventories/sample-inventory.json`, `VALID_TRANSITIONS` dict defining the state machine (available→{reserved,assigned}, assigned→{en_route,unavailable}, en_route→{deployed,unavailable}, deployed→{returning,unavailable}, returning→{available,unavailable}, reserved→{assigned,available,unavailable}), `transition_status(resource_id, new_status) -> bool` validating and applying transitions with audit logging, `flag_operational_limits(resources) -> list` flagging rotation (>12h), replenishment (<20%), mechanical issues, `get_eligible_resources(demand) -> list[ResourceInventoryItem]` filtering by type/sub-type/capability/availability (only `available` and `returning` eligible), excluding reserved resources for other incidents per CHK021, `release_incident_resources(incident_id) -> int` for bulk release on closure per CHK032, `compute_utilisation() -> dict` returning totals, assigned/available counts, utilisation %, flagged resources
- [X] T019 [P] [US1] Create `apps/agents/resource_allocation/versioning.py` with `VersionCounter` class: Cosmos DB etag-based optimistic concurrency per research.md §7, counter document pattern `{incident_id}_plan_counter`, `assign_version(incident_id) -> int` with read-increment-replace, conflict retry with exponential jitter (max 3 from config), UUID-suffixed fallback version on exhausted retries, `409 Conflict` error when all retries fail
- [X] T020 [P] [US1] Create `apps/agents/resource_allocation/templates.py` with template-based fallback text generators: `generate_plan_summary(plan, assignments, shortfalls, trade_offs) -> str` producing structured rationale text with resource assignments, priorities, shortfalls, and trade-offs in plain AIIMS-consistent language, `generate_assignment_rationale(assignment, scoring_rationale) -> str` producing per-assignment explanation of why resource was selected, `generate_trade_off_summary(trade_off_analysis) -> str` for cross-incident trade-off text, `generate_transport_dispatch_summary(assignments, evacuation_plan_id) -> str` for evacuation transport rationale
- [X] T021 [P] [US1] Create `apps/agents/resource_allocation/audit.py` with `AuditWriter` class: primary Cosmos DB write path to `resource-allocation-decisions` container, `write_record(record: AllocationDecisionRecord) -> None` method, partition key `/incident_scope_key`, append-only (`create_item`, not upsert), error handling for Cosmos unavailability (to be extended with three-tier degradation in US8)
- [X] T022 [P] [US1] Create `apps/agents/resource_allocation/matcher.py` with `ResourceMatcher` class: `match_demands(demands, inventory, config) -> tuple[list[ResourceAssignment], list[ShortfallDetail]]` implementing greedy assignment (iterate demands in priority order, score all eligible resources, assign highest-scoring), `_score_candidates(demand, eligible_resources, config) -> list[tuple[ResourceInventoryItem, float, ScoringRationale]]` scoring all eligible resources for a demand, `_apply_tie_breaking(candidates) -> ResourceInventoryItem` resolving ties by highest capability count then alphabetical resource ID per research.md §8, `_build_shortfall(demand, assigned_count) -> ShortfallDetail` for unmet/partially-met demands, `_build_assignment(resource, demand, score, rationale) -> ResourceAssignment` constructing assignment with travel time estimation, `detect_cross_incident_contention(demands, inventory) -> list` identifying resources demanded by multiple incidents
- [X] T023 [US1] Create `apps/agents/resource_allocation/pipeline.py` with `AllocationProcessingPipeline` class orchestrating all 9 stages: Stage 1 (handoff intake — Pydantic validation, `target_agent=resource_allocation` check, incident existence check, idempotency via `HandoffDeduplicator`), Stage 2 (recommendation/assessment retrieval — Cosmos DB reads with missing-data rejection and `handoff_rejected` audit), Stage 3 (demand identification — extract demands from coordination tasks/transport requirements, normalise priorities via `priority.py`, insert into `DemandQueue`), Stage 4 (resource inventory query — load via `ResourceInventoryManager`, filter eligible, apply state machine), Stage 5 (resource-demand matching — invoke `ResourceMatcher.match_demands`, collect assignments and shortfalls), Stage 6 (cross-incident analysis — placeholder for US4, detect contention, generate trade-off analysis), Stage 7 (plan generation — assign version via `VersionCounter`, compute confidence, generate LLM or template summary via `_generate_with_fallback`, build `ResourceDeploymentPlan` with traceability, deployment timelines, and input snapshot), Stage 8 (plan persistence — Cosmos DB write with OCC to `resource-deployment-plans` container, supersede previous versions), Stage 9 (audit finalisation — comprehensive audit records per stage)
- [X] T024 [US1] Replace existing stub `apps/agents/resource_allocation/agent.py` with full `ResourceAllocationAgent` class: subclass `LLMCallMixin`, integrate `ResourceAllocationConfig`, `AllocationProcessingPipeline`, `ResourceInventoryManager`, `AuditWriter`, `VersionCounter`, `HandoffDeduplicator`; implement `process_handoff(event: AgentHandoffEvent) -> ResourceDeploymentPlan` as main entry point invoking pipeline; wire Service Bus consumer to deserialise messages to `AgentHandoffEvent`, invoke pipeline, acknowledge on completion, handle poison messages; create FastAPI app with `create_app()` factory, port 8083

**Checkpoint**: User Story 1 fully functional — the agent receives handoffs from Risk Assessment, retrieves recommendations, identifies demands, scores and assigns resources via greedy algorithm, generates versioned deployment plans with LLM or template rationale, and persists with full traceability.

---

## Phase 4: User Story 2 — Match Available Resources to Demands (Priority: P2)

**Goal**: Refine resource-demand matching with detailed scoring rationale, travel time estimation, partial allocation handling with shortfall explanations, and capability-based ranking visible to incident commanders.

**Independent Test**: Supply 3 demands (water tankers) against an inventory with known locations and capabilities. Verify the 3 closest capable tankers are assigned with estimated travel time, and that a hazmat demand with no capable resources is marked `unmet` without incompatible substitution.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T025 [P] [US2] Write contract tests for plan output schema in `tests/contract/test_resource_allocation_plan_schema.py` covering: `ResourceDeploymentPlan` output matches schema per data-model.md (all required fields present: plan_id, incident_id, version, demands, assignments, unmet_demands, deployment_timelines, confidence_score, confidence_level, status, generation_method, traceability), each `ResourceAssignment` includes `scoring_rationale` with all 9 fields, each `ShortfallDetail` includes quantity breakdown and recommendation, `DeploymentTimeline` includes mobilisation + travel time, traceability links back to handoff/recommendation/assessment IDs
- [X] T026 [P] [US2] Write contract tests for handoff intake structure in `tests/contract/test_resource_allocation_handoff.py` covering: inbound `AgentHandoffEvent` schema validation (`source_agent=risk_assessment`, `target_agent=resource_allocation`), payload contains `recommendationId`/`summary`/`assessmentId` per contracts/allocation-pipeline.md §Stage 1, evacuation source payload contains `transportRequirements`/`evacuationPlanId`, `tenant_id` propagation from handoff through plan

### Implementation for User Story 2

- [X] T027 [US2] Enhance `ResourceMatcher.match_demands` in `apps/agents/resource_allocation/matcher.py` with detailed scoring rationale: populate all 9 `ScoringRationale` fields per assignment (capability_match, distance_km, distance_factor, availability_factor, priority_weight, final_score, selection_reason, alternatives_considered count, tie_break_applied description), ensure travel time estimation uses configurable speeds per resource type (personnel=40km/h, vehicle=60km/h, helicopter=200km/h) plus mobilisation overhead per research.md §3
- [X] T028 [US2] Enhance `ResourceMatcher` in `apps/agents/resource_allocation/matcher.py` with equidistant resource preference: when two resources have equal distance, prefer the resource with higher capability match (more capabilities beyond required minimum) and document rationale per acceptance scenario 3, ensure resources already assigned to another active incident are treated as `unavailable` and not reassigned unless explicitly triggered per acceptance scenario 4 and FR-013
- [X] T029 [US2] Enhance pipeline Stage 5 shortfall handling in `apps/agents/resource_allocation/pipeline.py`: ensure every demand in input appears in output as `fully_met`, `partially_met`, or `unmet` per FR-012, populate `ShortfallDetail.recommendation` with actionable text (e.g., "Request mutual aid for 2 additional hazmat teams from neighbouring region"), never silently drop demands

**Checkpoint**: Resource matching now produces transparent, explainable assignments with full scoring rationale, travel time estimates, and detailed shortfall reports.

---

## Phase 5: User Story 3 — Process Transport Dispatch Requests from Evacuation Agent (Priority: P3)

**Goal**: Receive transport dispatch requests from the Evacuation Agent, classify as Tier 1 life-safety demands, match transport resources by type/capability/proximity, and generate dispatch assignments with traceability to the originating evacuation plan.

**Independent Test**: Send a synthetic `AgentHandoffEvent` with `source_agent=evacuation` containing transport requirements for wheelchair-accessible vehicles and ambulances. Verify critical ambulance requests are processed before high-priority bus requests, and each dispatch assignment includes the originating evacuation plan ID and transport requirement ID.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T030 [P] [US3] Write unit tests for transport dispatch processing in `tests/unit/test_resource_allocation_pipeline.py` (extend existing file) covering: evacuation handoff recognised and processed via transport path, transport requirements extracted into Tier 1 demands with correct vehicle types, wheelchair-accessible requirement matched to capable vehicles only, critical ambulance dispatched before high-priority bus, shortfall flagged when demand exceeds inventory with deficit in summary, each dispatch assignment includes `evacuation_plan_id` and `transport_requirement_id` in traceability, superseded evacuation plan triggers latest-version lookup

### Implementation for User Story 3

- [X] T031 [US3] Implement transport dispatch path in `apps/agents/resource_allocation/pipeline.py`: detect `source_agent=evacuation` handoffs in Stage 1, extract `transportRequirements` array from payload in Stage 3, create `ResourceDemand` per requirement with `source_type=evacuation`, `resource_type` from `vehicleType`, `priority_tier=tier_1_life_safety` per FR-008, populate `Traceability.evacuation_plan_id` and `transport_requirement_ids` from payload
- [X] T032 [US3] Implement evacuation priority mapping in `apps/agents/resource_allocation/priority.py`: add mapping for evacuation priority values (`immediate` → `critical`, `critical` → `critical`, `high` → `high`) per CHK020 and research.md §9, ensure transport demands with `immediate` priority are processed first in the demand queue
- [X] T033 [US3] Implement transport-specific matching in `apps/agents/resource_allocation/matcher.py`: add wheelchair-accessible capability filtering (vehicle must have `wheelchair_accessible` in capabilities), add `transport_dispatched` decision type to audit records for transport assignments, mark assigned transport resources as `assigned` status in inventory (not `dispatched`, which is only valid for `ResourceAssignment.assignment_status`)

**Checkpoint**: Transport dispatch requests from Evacuation Agent are processed as Tier 1 demands, matched by type/capability/proximity with correct priority ordering, and fully traceable to originating evacuation plans.

---

## Phase 6: User Story 4 — Handle Competing Demands Across Multiple Incidents (Priority: P4)

**Goal**: When resource demands from multiple active incidents compete for the same pool, allocate using four-level tiebreaking, generate trade-off analysis, recommend cross-incident reallocation with mandatory commander approval, and distribute proportionally for true ties.

**Independent Test**: Create two incidents — a critical bushfire (Tier 1) and a high flood (Tier 2) — both requiring medical teams that exceed inventory. Verify the critical incident gets first allocation, shortfall is documented with trade-off analysis, and reallocation recommendations require commander approval.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T034 [P] [US4] Write unit tests for cross-incident matching in `tests/unit/test_resource_allocation_matcher.py` (extend existing file) covering: higher-tier incident (Tier 1) allocated before lower-tier (Tier 2) for same resource pool, higher-severity incident allocated first within same tier, trade-off analysis generated showing what each incident loses, reallocation recommendation generated when critical demand cannot be met from unassigned resources, reallocation flagged as requiring commander approval per FR-013/FR-023, proportional distribution for equal severity and population with documented rationale per FR-022, three-way contention across three incidents

### Implementation for User Story 4

- [X] T035 [US4] Implement cross-incident analysis in pipeline Stage 6 in `apps/agents/resource_allocation/pipeline.py`: invoke `ResourceMatcher.detect_cross_incident_contention` to identify contested resources, build `TradeOffAnalysis` with competing incidents, contested resources, per-incident allocation results, and impact summary, set `requires_commander_approval=true` when reallocation from active plans is recommended per FR-023
- [X] T036 [US4] Implement four-level tiebreaking in `apps/agents/resource_allocation/matcher.py`: when multiple incidents compete for the same resource, evaluate in order: (1) priority tier (Tier 1 > Tier 2 > Tier 3), (2) severity (`critical` > `high` > `moderate` > `low`), (3) proximity (closer demand wins), (4) request timestamp (earlier wins), create `reallocation_recommended` audit record for each recommended cross-incident reallocation
- [X] T037 [US4] Implement proportional distribution in `apps/agents/resource_allocation/matcher.py`: when two incidents have identical tier, severity, and population-at-risk, distribute contested resources proportionally by ratio of unmet demands per FR-022, document tie-breaking rationale in `TradeOffAnalysis.impact_summary`, flag both allocations for incident commander review
- [X] T038 [US4] Implement re-allocation trigger in `apps/agents/resource_allocation/pipeline.py`: when a resource transitions to `available` (returning from deployment or newly added), check pending unmet demands across all active incidents, auto-trigger plan re-generation for affected incidents per CHK033, create `reallocation_recommended` audit record

**Checkpoint**: Cross-incident allocation operates with correct priority tiebreaking, transparent trade-off analysis, proportional distribution for true ties, and mandatory commander approval for reallocations.

---

## Phase 7: User Story 5 — Human Override of Allocation Decisions (Priority: P5)

**Goal**: Enable incident commanders to override allocation decisions — reassign, add, remove resources, change priority, approve/reject/cancel plans — with each override producing a new immutable plan version and complete audit trail.

**Independent Test**: Generate a proposed plan, then apply a commander override (reassign a resource). Verify a new plan version is created with override metadata, the original plan remains intact and queryable, and the audit trail records the override with user ID, role, and justification.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T039 [P] [US5] Write unit tests for override processing in `tests/unit/test_resource_allocation_endpoints.py` covering: reassign override creates new plan version with modified assignment, add-resource override includes new resource in plan, remove-resource override excludes resource and marks demand as potentially unmet, priority-change override re-orders demands and re-runs matching, approve transitions plan from `proposed` to `approved` with audit entry, reject transitions to `rejected` with mandatory justification, cancel transitions to `cancelled` and releases pending assignments, override metadata recorded (user_id, role, justification, action_type, timestamp), original plan version remains immutable and queryable, new information after approval produces new version but does not auto-supersede approved plan per acceptance scenario 4

### Implementation for User Story 5

- [X] T040 [US5] Implement `POST /override` endpoint in `apps/agents/resource_allocation/agent.py`: request schema per contracts/health-endpoint.md (plan_id, action: `reassign`/`add_resource`/`remove_resource`/`change_priority`/`approve`/`reject`/`cancel`, user_id, role, justification — mandatory, details object for action-specific parameters), response schema (success, new_plan_id, new_version, action_applied, override_record_id, message)
- [X] T041 [US5] Implement override processing logic in `apps/agents/resource_allocation/pipeline.py`: for modification overrides (reassign/add/remove/change_priority) — create new plan version linked to original via `OverrideMetadata`, re-run matching if needed, set `generation_method=commander_override`; for status overrides (approve/reject/cancel) — transition plan status, release resources on cancel, do not supersede approved plans on new information; populate `OverrideMetadata` with `override_by_user_id`, `override_by_role`, `override_justification`, `override_action_type`, `override_timestamp`, `original_plan_id`
- [X] T042 [US5] Create `override_applied` audit records in `apps/agents/resource_allocation/audit.py`: record original assignment, modified assignment, user ID, role, justification, timestamp, action type for every override action, ensure append-only immutability per FR-025

**Checkpoint**: Commanders can override any allocation decision with full traceability. Overrides produce new plan versions while originals remain immutable. Audit trail captures complete override provenance.

---

## Phase 8: User Story 6 — Track Resource Status and Utilisation (Priority: P6)

**Goal**: Process `resource_status` signals to update tracked resources, enforce state machine transitions, flag operational limits (rotation, replenishment, mechanical), and expose utilisation metrics.

**Independent Test**: Start with initial inventory, apply a sequence of status updates (assigned→en_route→deployed→returning→available), verify the status view reflects each transition, and verify utilisation metrics return correct totals, percentages, and rotation/replenishment flags.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T043 [P] [US6] Write unit tests for status update processing in `tests/unit/test_resource_allocation_inventory.py` (extend existing file) covering: `resource_status` signal updates resource to `deployed` with timestamp, partial supply consumption updates remaining quantity, supply flagged for replenishment below 20% threshold, personnel flagged for rotation after 12h continuous deployment, utilisation query returns correct totals/assigned/available/utilisation%/flags, invalid state transition rejected with error, `resource_status_updated` audit record created for each transition

### Implementation for User Story 6

- [X] T044 [US6] Implement `process_status_update(signal)` in `apps/agents/resource_allocation/agent.py`: parse `resource_status` signal (resource_id, new_status, location, remaining_capacity, timestamp), invoke `ResourceInventoryManager.transition_status` with state machine validation, update location if changed, update remaining capacity for consumables, trigger operational flag checks, create `resource_status_updated` audit record with previous state, new state, and trigger event per FR-018
- [X] T045 [US6] Enhance `ResourceInventoryManager` in `apps/agents/resource_allocation/inventory.py`: add `update_capacity(resource_id, remaining_capacity)` for consumable tracking, add `check_rotation_flags()` scanning all deployed resources for >12h continuous deployment per FR-019, add `check_replenishment_flags()` scanning consumables below 20% per FR-019, add `flag_mechanical_issue(resource_id)` for degraded vehicle marking, enhance `compute_utilisation()` to include flagged-for-rotation count, flagged-for-replenishment count, and per-incident resource breakdown per FR-020
- [X] T046 [US6] Wire status update processing into Service Bus consumer in `apps/agents/resource_allocation/agent.py`: listen for `resource_status` category signals on separate subscription or shared queue, route to `process_status_update`, trigger re-allocation check for affected incidents when resource becomes `available` per CHK033, 5-second SLA for status update processing per plan.md performance goals

**Checkpoint**: Resource status tracking operational with formal state machine, operational limit flagging, and real-time utilisation metrics. Status updates trigger re-allocation checks for newly available resources.

---

## Phase 9: User Story 7 — Rehearsal and Simulation Mode (Priority: P7)

**Goal**: Process simulation-tenant handoffs in isolation from live data, produce deterministic assignments for identical inputs, and ensure simulation plans never affect live resource inventories or appear in live queries.

**Independent Test**: Send a simulation-tenant handoff with simulated inventory. Verify simulation plans are labelled with simulation tenant ID, do not appear in live queries, and replaying identical inputs produces identical assignments.

### Tests for User Story 7

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T047 [P] [US7] Write reproducibility contract tests in `tests/contract/test_resource_allocation_reproducibility.py` covering: identical inputs (demands + inventory + config) produce identical assignments and rankings, configuration version tracked in each plan via `InputSnapshot.config_version`, input snapshot contains demands and inventory snapshot hash, simulation tenant plans isolated from live queries (different partition key), simulation handoffs do not trigger live resource inventory changes, simulation plans carry `tenant_id` in all records

### Implementation for User Story 7

- [X] T048 [US7] Implement simulation tenant isolation in `apps/agents/resource_allocation/pipeline.py`: propagate `tenant_id` from inbound handoff through all plan/demand/assignment/audit records, route simulation plans to simulation-scoped Cosmos partitions via `incident_scope_key` format `{tenant_id}:{incident_id}`, block simulation plans from triggering live resource state changes or appearing in live utilisation queries per FR-027, use separate in-memory inventory snapshot for simulation tenants (not live inventory)
- [X] T049 [US7] Implement deterministic output in `apps/agents/resource_allocation/pipeline.py`: enforce LLM `temperature=0` for all plan summary generation calls, store complete `InputSnapshot` per plan (demands snapshot, inventory snapshot hash, config version, scoring parameters) per FR-029, verify that identical inputs produce identical `ResourceAssignment` lists and rankings per FR-028
- [X] T050 [US7] Implement plan expiry logic in `apps/agents/resource_allocation/pipeline.py`: plans not approved within 4 hours auto-transition to `expired` status per research.md §6 and CHK008, expired plans release reserved resources back to `available`, create `plan_expired` audit record, expose active plan count and expired count in utilisation metrics

**Checkpoint**: Simulation mode fully isolated — simulation plans never leak to live data. Identical inputs produce identical outputs. Plans auto-expire after 4 hours, releasing reserved resources.

---

## Phase 10: User Story 8 — Audit Trail of All Allocation Decisions (Priority: P8)

**Goal**: Extend audit writer with three-tier degradation (Cosmos DB → memory buffer → file spill), ensure every processing step produces an `AllocationDecisionRecord`, and enable audit completeness verification.

**Independent Test**: Process a sequence of handoffs, overrides, and reallocations, then query the audit trail to verify every step produced a corresponding record with the required fields (handoff IDs, plan IDs, decision types, confidence, timestamps).

### Tests for User Story 8

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T051 [P] [US8] Write unit tests for three-tier audit degradation in `tests/unit/test_resource_allocation_audit.py` covering: tier 1 Cosmos write success, tier 2 in-memory ring buffer on Cosmos failure (bounded deque at 10K from config), tier 3 JSONL file spill when buffer full, recovery flush order (memory → file → Cosmos chronological), `buffered_at` and `flush_source` annotation on recovered records, audit completeness verification (handoff_ids processed vs records created), all 16 `DecisionType` values produce valid audit records

### Implementation for User Story 8

- [X] T052 [US8] Extend `AuditWriter` in `apps/agents/resource_allocation/audit.py` with tier 2 in-memory ring buffer: bounded `collections.deque` with `maxlen` from `ResourceAllocationConfig.audit_buffer_capacity` (default 10K), auto-fallback when Cosmos DB write raises exception, annotate buffered records with `buffered_at` timestamp
- [X] T053 [US8] Extend `AuditWriter` in `apps/agents/resource_allocation/audit.py` with tier 3 file spill: JSONL append to `ResourceAllocationConfig.audit_buffer_file_path`, triggered when memory buffer is full, file rotation/size management
- [X] T054 [US8] Implement recovery flush in `apps/agents/resource_allocation/audit.py`: `flush_buffered_records() -> int` method flushing memory buffer then file buffer to Cosmos in chronological order, annotating each record with `flush_source` (`memory_buffer` or `file_buffer`), invoked periodically and on Cosmos recovery detection
- [X] T055 [US8] Add comprehensive audit records for every pipeline stage in `apps/agents/resource_allocation/pipeline.py`: ensure stages 1–9 each produce one or more `AllocationDecisionRecord` entries with correct `decision_type` — `handoff_received` (stage 1), `handoff_rejected` (stage 1 failure), `duplicate_discarded` (stage 1 dedup), `demand_identified` (stage 3), `resource_matched`/`resource_excluded` (stage 5), `partial_allocation` (stage 5), `reallocation_recommended` (stage 6), `plan_generated` (stage 7), `plan_superseded` (stage 8), `transport_dispatched` (stage 5 transport path), `override_applied` (override endpoint), `resource_status_updated` (status processing), `degradation_detected`/`content_safety_failure` (fallback paths), `plan_expired` (expiry logic)
- [X] T056 [US8] Implement audit finalization (pipeline stage 9) in `apps/agents/resource_allocation/pipeline.py`: verify completeness by reconciling handoff_id processed against audit records created, log discrepancies, report current audit tier in health endpoint `audit_store` field, emit degradation transition as audit event per FR-031a

**Checkpoint**: Full audit trail operational with three-tier degradation. Every processing step is recorded and recoverable. Audit completeness is verifiable. All 16 decision types covered.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Health endpoint, observability instrumentation, graceful degradation, infrastructure, and end-to-end validation

### Health Endpoint

- [X] T057 Implement `GET /health` endpoint in `apps/agents/resource_allocation/agent.py` with FastAPI: response schema per contracts/health-endpoint.md (status: `healthy`/`degraded`/`unhealthy`, agent_version, timestamp, checks: `inventory_loaded`, `llm_connectivity`, `cosmos_connectivity`, `active_plan_count`, `pending_demands`, `processing_queue`, `audit_store` with current tier and buffer depth), ≤1s SLA, port 8083

### Graceful Degradation

- [X] T058 [P] Implement LLM fallback for plan summaries in `apps/agents/resource_allocation/pipeline.py`: when LLM is unavailable, use template-based summaries from `templates.py` with `generation_method=template_fallback`, apply multiplicative 0.8 confidence penalty per FR-033 and research.md §4, pre-approved templates skip runtime content safety check per FR-037
- [X] T059 [P] Implement stale inventory handling in `apps/agents/resource_allocation/pipeline.py`: when inventory data store is unavailable, use last-known-good snapshot if within staleness window (30 min default per FR-034), apply multiplicative 0.8 confidence penalty for stale data, flag in plan that inventory may be stale, when staleness window exceeded produce low-confidence plan with degradation flag per FR-036
- [X] T060 [P] Implement content safety validation in `apps/agents/resource_allocation/pipeline.py`: validate all LLM outputs through `ContentSafetyValidator` before inclusion in plan summaries per FR-037, on validation failure fall back to template and create `content_safety_failure` audit record

### Observability

- [X] T061 [P] Add OpenTelemetry distributed tracing in `apps/agents/resource_allocation/pipeline.py`: instrument span hierarchy per contracts/telemetry.md (root span `resource_allocation.process_handoff` with child spans: `validate_handoff`, `retrieve_recommendation`, `identify_demands`, `query_inventory`, `match_resources` with nested `score_resource` spans, `cross_incident_analysis`, `generate_plan` with nested `llm_call`/`template_fallback` and `content_safety_check`, `persist_plan` with nested `assign_version`, `write_audit`), root span `resource_allocation.process_status_update` with child spans, propagate correlation ID from `handoff_id`
- [X] T062 [P] Emit all metrics defined in contracts/telemetry.md in `apps/agents/resource_allocation/pipeline.py`: processing metrics (`allocation_latency` histogram, `plan_count`, `handoff_intake_count`, `handoff_rejected_count`, `duplicate_discard_count`, `sla_breach_count`, `status_update_latency`), matching metrics (`resource_matching_time`, `demand_fulfilment_rate`, `shortfall_count`, `resource_utilization_rate`, `unmet_demand_count`), cross-incident metrics (`cross_incident_conflicts`, `cross_incident_reallocation_count`, `cross_incident_analysis_latency`), override metrics (`override_count`, `override_rate`, `plan_approval_latency`), degradation metrics (`fallback_mode_activations`, `content_safety_failures`, `audit_buffer_depth`, `audit_tier`, `degradation_events`), lifecycle metrics (`plan_versions_per_incident`, `version_conflict_retries`, `active_plans_gauge`, `plan_expired_count`, `transport_dispatch_latency`, `handoff_success_rate`)
- [X] T063 [P] Emit custom events per contracts/telemetry.md in `apps/agents/resource_allocation/pipeline.py`: `HandoffReceived` (stage 1), `PlanGenerated` (stage 7), `ShortfallDetected` (stage 5), `CrossIncidentConflict` (stage 6), `ReallocationRecommended` (stage 6), `OverrideApplied` (override endpoint), `PlanExpired` (expiry logic), `DegradationEvent` (any fallback), `SLABreach` (processing > 15s), `VersionConflict` (OCC retry)

### Integration & Simulation Tests

- [X] T064 [P] Write integration tests for Cosmos DB persistence in `tests/integration/test_resource_allocation_cosmos.py` covering: `ResourceDeploymentPlan` write/read with partition key `/incident_scope_key`, `AllocationDecisionRecord` append-only write, version counter optimistic concurrency, plan status transitions (`proposed` → `approved`/`superseded`/`expired`), simulation tenant isolation (different partition scope)
- [X] T065 [P] Write integration tests for Service Bus handoff intake in `tests/integration/test_resource_allocation_service_bus.py` covering: message deserialization to `AgentHandoffEvent` (both risk_assessment and evacuation sources), message acknowledgement on success, poison message handling, queue consumer lifecycle
- [X] T066 [P] Write flood resource allocation simulation test in `tests/simulation/test_flood_allocation_scenario.py`: send flood-category handoff with coordination tasks, verify demand extraction and priority ordering, verify resource assignment by proximity and capability, verify shortfall reporting, verify audit trail completeness
- [X] T067 [P] Write bushfire resource allocation simulation test in `tests/simulation/test_bushfire_allocation_scenario.py`: send bushfire-category handoff, verify fire truck and water tanker prioritisation, verify personnel rotation flagging, verify LLM-generated summary content
- [X] T068 [P] Write multi-incident cross-allocation simulation test in `tests/simulation/test_multi_incident_scenario.py`: create two concurrent incidents (flood + bushfire) with competing demands, verify four-level tiebreaking, verify trade-off analysis generation, verify proportional distribution for equal-priority demands, verify reallocation recommendations with commander approval flag

### Infrastructure

- [X] T069 [P] Add/update Bicep modules in `infra/` for: Cosmos DB containers (`resource-deployment-plans` with partition key `/incident_scope_key`, `resource-allocation-decisions` with partition key `/incident_scope_key`), Service Bus queue for handoff intake (from both risk_assessment and evacuation agents), Container Apps configuration (port 8083, auto-scaling rules based on queue depth), managed identity for Cosmos DB and Service Bus access

### Quickstart Validation

- [ ] T070 Run quickstart.md validation: execute all steps from `specs/011-resource-allocation-agent/quickstart.md` (setup, environment variables, local run, health check, synthetic handoff, test suite) and verify end-to-end operation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — core pipeline, MVP
- **US2 (Phase 4)**: Depends on US1 — refines matching with detailed scoring rationale
- **US3 (Phase 5)**: Depends on US1 — adds evacuation transport dispatch path
- **US4 (Phase 6)**: Depends on US1 — adds cross-incident contention and tiebreaking
- **US5 (Phase 7)**: Depends on US1 — adds override endpoint and plan versioning on modification
- **US6 (Phase 8)**: Depends on US1 — adds status tracking and utilisation metrics
- **US7 (Phase 9)**: Depends on US1 — adds simulation isolation and plan expiry
- **US8 (Phase 10)**: Depends on US1 — extends audit to three-tier degradation
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2)**: Depends on US1 for matching infrastructure — enhances scoring rationale
- **US3 (P3)**: Depends on US1 for pipeline — adds transport dispatch path; independent of US2
- **US4 (P4)**: Depends on US1 for matching — adds cross-incident logic; independent of US2/US3
- **US5 (P5)**: Depends on US1 for plan generation — adds override endpoint; independent of US2-US4
- **US6 (P6)**: Depends on US1 for inventory — adds status tracking; independent of US2-US5
- **US7 (P7)**: Depends on US1 for pipeline — adds simulation isolation; independent of US2-US6
- **US8 (P8)**: Depends on US1 for audit writer — extends to three-tier; independent of US2-US7

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/enums before services
- Services before pipeline integration
- Core implementation before integration logic
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T005, T006, T007 can all run in parallel (different files)
- **Phase 3**: All test tasks (T008–T014) can run in parallel; implementation tasks T015–T022 can all run in parallel (different files); T023–T024 are sequential (pipeline depends on services, agent depends on pipeline)
- **Phase 4**: Test tasks (T025, T026) can run in parallel; T027–T029 are sequential (build on matcher)
- **Phase 5–Phase 10**: US3, US4, US5, US6, US7, US8 can all start in parallel after US1 completes (independent stories, different files)
- **Phase 11**: T058–T069 can all run in parallel (different files/concerns)

---

## Parallel Example: User Story 1

```text
# After Foundational phase completes, launch all US1 tests in parallel:
T008: "Unit tests for dedup in tests/unit/test_resource_allocation_dedup.py"
T009: "Unit tests for scoring in tests/unit/test_resource_allocation_scoring.py"
T010: "Unit tests for priority in tests/unit/test_resource_allocation_priority.py"
T011: "Unit tests for inventory in tests/unit/test_resource_allocation_inventory.py"
T012: "Unit tests for matching in tests/unit/test_resource_allocation_matcher.py"
T013: "Unit tests for versioning in tests/unit/test_resource_allocation_versioning.py"
T014: "Unit tests for pipeline in tests/unit/test_resource_allocation_pipeline.py"

# Then launch all US1 service modules in parallel:
T015: "HandoffDeduplicator in apps/agents/resource_allocation/dedup.py"
T016: "Scoring functions in apps/agents/resource_allocation/scoring.py"
T017: "Priority normalisation in apps/agents/resource_allocation/priority.py"
T018: "ResourceInventoryManager in apps/agents/resource_allocation/inventory.py"
T019: "VersionCounter in apps/agents/resource_allocation/versioning.py"
T020: "Template generators in apps/agents/resource_allocation/templates.py"
T021: "AuditWriter in apps/agents/resource_allocation/audit.py"
T022: "ResourceMatcher in apps/agents/resource_allocation/matcher.py"

# Then sequential pipeline + agent integration:
T023: "AllocationProcessingPipeline in apps/agents/resource_allocation/pipeline.py"
T024: "ResourceAllocationAgent + FastAPI in apps/agents/resource_allocation/agent.py"
```

## Parallel Example: After US1 Completes

```text
# US3-US8 can all start in parallel (independent of each other):
Developer A: US2 (Matching Refinement) — T025-T029
Developer B: US3 (Transport Dispatch) — T030-T033
Developer C: US4 (Cross-Incident) — T034-T038
Developer D: US5 (Human Override) — T039-T042
Developer E: US6 (Status Tracking) — T043-T046
Developer F: US7 (Simulation) — T047-T050
Developer G: US8 (Audit Trail) — T051-T056

# All Polish tasks can run in parallel:
All developers: Polish phase (T057-T070, parallelizable tasks)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T007) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T008–T024)
4. **STOP and VALIDATE**: Send synthetic handoff, verify `ResourceDeploymentPlan` is produced with resource assignments, scoring rationale, deployment timelines, and traceability to originating assessment
5. Deploy/demo if ready — the agent can receive handoffs and generate deployment plans

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test: synthetic handoff → versioned deployment plan (**MVP!**)
3. Add US2 → Test: detailed scoring rationale, travel time, shortfall reports
4. Add US3 → Test: evacuation transport dispatch → Tier 1 matching
5. Add US4 → Test: competing incidents → tiebreaking + trade-off analysis
6. Add US5 → Test: commander override → new plan version + audit
7. Add US6 → Test: status updates → state machine + utilisation metrics
8. Add US7 → Test: simulation handoff → isolated plan + deterministic output
9. Add US8 → Test: Cosmos outage → memory buffer → file spill → recovery
10. Polish → Health endpoint, observability, degradation, infrastructure, quickstart validation

### Parallel Team Strategy

With multiple developers after US1 completes:

1. Team completes Setup + Foundational + US1 together
2. Once US1 is done:
   - Developer A: US2 (Matching Refinement — detailed rationale)
   - Developer B: US3 (Transport Dispatch — evacuation integration)
   - Developer C: US4 (Cross-Incident — tiebreaking + trade-offs)
   - Developer D: US5 (Human Override — commander control)
   - Developer E: US6 (Status Tracking — state machine)
   - Developer F: US7 + US8 (Simulation + Audit — related concerns)
3. All developers: Polish phase (parallelizable tasks)

---

## Notes

- [P] tasks = different files, no dependencies on concurrent tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after US1 (MVP)
- US3-US8 are all independent of each other — maximum parallel opportunity
- US2 enhances US1's matching but is not blocking for other stories
- Scoring formula: `score = capability_match × (1/max(distance, 0.1)) × availability_factor × priority_weight`
- Distance floor: `max(distance_km, 0.1)` prevents division-by-zero (CHK035)
- Priority normalisation: all incoming priorities mapped to AIDR 4-level (CHK020)
- Penalty stacking: stale data (×0.8) → partial inventory (×0.7) → template fallback (×0.8) per research.md §4
- Plan versioning: `rdp-{incident_id}-v{N}` with optimistic concurrency, max 3 retries
- Plan expiry: 4 hours if not approved, auto-transition to `expired`, release resources
- All Cosmos containers use partition key `/incident_scope_key` with format `{tenant_id}:{incident_id}`
- Port 8083 avoids conflict with monitoring (8080), risk assessment (8081), evacuation (8082)
- Plan.md identifies 2 issues in existing `agent.py` — stub replacement in T024
- Commit after each task or logical group; stop at any checkpoint to validate independently
