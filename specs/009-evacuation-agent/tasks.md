# Tasks: Evacuation Agent — Route Optimisation, Transport Coordination, and Evacuation Planning

**Input**: Design documents from `/specs/009-evacuation-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅, quickstart.md ✅, checklists/requirements.md ✅

**Tests**: Included — the implementation plan explicitly specifies 19 test files across unit, contract, integration, and simulation tiers.

**Organization**: Tasks are grouped by user story (8 stories: US1–US8) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US8)
- Exact file paths included in all descriptions

## Path Conventions

- **Agent source**: `apps/agents/evacuation/` (new modules within existing agent workspace)
- **Shared modules**: `apps/agents/common/` (existing — ContentSafetyValidator, LLMCallMixin, handoffs, etc.)
- **Test files**: `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/simulation/`
- **Sample data**: `data/road-networks/`, `data/population/`
- **Agent workspace config**: `apps/agents/pyproject.toml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package initialization, dependency installation, and sample data for local development.

- [x] T001 Create package initialization file at `apps/agents/evacuation/__init__.py` with version string `__version__ = "0.1.0"` and public API imports
- [x] T002 Add `shapely` to the `[project.dependencies]` section of `apps/agents/pyproject.toml` (required for geospatial zone computation and road segment intersection)
- [x] T003 [P] Create sample road network JSON at `data/road-networks/far-north-qld-sample.json` with ~50 nodes (intersections), ~120 edges (road segments), and 5 assembly areas covering simplified Far North Queensland coastal region (Cairns to Cooktown) per research.md §6 schema
- [x] T004 [P] Create sample population and facility data at `data/population/sample-population.json` with aged care facilities, disability care facilities, hospitals, schools, and population density estimates for the Far North Queensland sample region

**Checkpoint**: Project initialised — dependencies available, sample data in place for local development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, configuration, and infrastructure modules that MUST be complete before ANY user story can be implemented. Every user story depends on these modules.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create `apps/agents/evacuation/config.py` with `EvacuationConfig` Pydantic settings class reading 21 environment variables from data-model.md §Configurable Parameters: `ROAD_NETWORK_FILE_PATH`, `ROAD_DATA_STALENESS_HOURS` (default 6), `HANDOFF_DEDUP_WINDOW_MINUTES` (default 10), `CONGESTION_RISK_THRESHOLD_PCT` (default 80), `VULNERABLE_POPULATION_BUFFER` (default 1.5), `PHASE_TRANSITION_TIME_FACTOR` (default 1.2), `PHASE_TRANSITION_POPULATION_PCT` (default 50), `HAZARD_EXPANSION_REPLAN_PCT` (default 10), `PROGRESS_DELAY_REPLAN_PCT` (default 30), `FALLBACK_CONFIDENCE_REDUCTION` (default 0.8), 5 mobilisation times per hazard type, `AUDIT_BUFFER_CAPACITY` (default 10000), `AUDIT_BUFFER_FILE_PATH`, `MAX_SUMMARY_LENGTH` (default 1000), `REPLAN_RATE_LIMIT_SECONDS` (default 30), `AGENT_VERSION` (default "0.1.0"), plus Azure service connection strings
- [x] T006 Create `apps/agents/evacuation/models.py` with all Pydantic v2 models per data-model.md: 5 enums (`DecisionType` with 15 values, `ConfidenceLevel`, `PlanStatus` with 7 states and transition rules, `VulnerabilityCategory`, `ClosureReason`), 10 embedded models (`EvacuationZone`, `EvacuationRoute`, `ExcludedRoad`, `TransportRequirement`, `EvacuationPhase`, `HazardSummary`, `Traceability`, `OverrideMetadata`, `DataSnapshot`, `AssemblyArea`), primary output model `EvacuationPlan` with validation rules (confidence_score in [0.0, 1.0], version ≥ 1, plan_id format `ep-{incident_id}-v{N}`, confidence_level derived from score), audit model `EvacuationDecisionRecord` with canonical 22-field schema per research.md §1, and `AuditBufferEntry` for degraded writes
- [x] T007 [P] Create `apps/agents/evacuation/road_network.py` with `RoadNetworkLoader` class: JSON parsing with Pydantic validation for nodes/edges/assembly areas, adjacency list graph construction from edges, MVP size validation (max 1,000 nodes / 5,000 edges per research.md §10), edge geometry as Shapely `LineString` objects from GeoJSON coordinates for zone intersection, road closure status management (apply/remove closures by edge_id), data staleness check against `ROAD_DATA_STALENESS_HOURS`, and `get_version()` returning hash of loaded data for reproducibility (FR-027)
- [x] T008 [P] Create `apps/agents/evacuation/zones.py` with `ZoneComputer` class: zone boundary computation from hazard GeoJSON using `shapely.buffer()` (Zone 1 = affected_area polygon, Zone 2 = buffered Zone 1, Zone 3 = buffered Zone 2), road segment zone membership via `polygon.contains(line)` for full containment and `polygon.intersects(line)` for partial overlap, conservative partial-overlap rule per research.md §7 (highest-severity zone applies), zone-based capacity reduction (Zone 1: closed/0%, Zone 2: −50%, Zone 3: −25%), multi-hazard merging via `shapely.ops.unary_union()` per FR-009d, and population estimation per zone from pre-loaded density data
- [x] T009 [P] Create `apps/agents/evacuation/dedup.py` with `HandoffDeduplicator` class using TTL-based in-memory cache (default 10-minute window from `HANDOFF_DEDUP_WINDOW_MINUTES`), `is_duplicate(handoff_id) → bool` method, and automatic TTL expiry — same pattern as risk assessment agent
- [x] T010 [P] Create `apps/agents/evacuation/versioning.py` with `VersionCounter` class implementing Cosmos DB ETag-based optimistic concurrency control per data-model.md §VersionCounter: read counter document `{incident_id}_plan_counter` + `_etag`, increment `current_version`, `replace_item` with `If-Match`, retry up to 3× with jitter on 412 Precondition Failed, format `plan_id` as `ep-{incident_id}-v{N}`
- [x] T011 [P] Create `apps/agents/evacuation/audit.py` with `AuditWriter` class implementing three-tier degradation per research.md §8: Tier 1 Cosmos DB `create_item()` to `evacuation-decisions` container, Tier 2 in-memory `deque` (capacity from `AUDIT_BUFFER_CAPACITY`), Tier 3 file spill to JSONL at `AUDIT_BUFFER_FILE_PATH`, recovery flush (memory → file → Cosmos in chronological order annotating `buffered_at` and `flush_source`), `get_status()` returning `healthy`/`buffering`/`degraded`, and `write_record(EvacuationDecisionRecord)` method
- [x] T012 [P] Write unit tests for all models, enums, and validation rules in `tests/unit/test_evacuation_models.py`: test EvacuationPlan validation (confidence bounds, version ≥ 1, plan_id format), PlanStatus transition enforcement, ConfidenceLevel derivation from score (<0.4 → low, 0.4–0.69 → medium, ≥0.7 → high), DecisionType enum completeness, all embedded model serialization/deserialization
- [x] T013 [P] Write unit tests for config loading in `tests/unit/test_evacuation_config.py`: test all 21 environment variable defaults, type validation, missing required vars, and config hash generation for `configuration_version`
- [x] T014 [P] Write unit tests for road network loading in `tests/unit/test_evacuation_road_network.py`: test JSON parsing, graph construction, size limit validation (reject >1,000 nodes), Shapely LineString creation from edge geometry, road closure application/removal, staleness detection
- [x] T015 [P] Write unit tests for zone computation in `tests/unit/test_evacuation_zones.py`: test zone boundary buffering, road segment containment/intersection, partial-overlap rule (highest severity wins), Zone 1/2/3 capacity reductions, multi-hazard merging via unary_union, population estimation per zone
- [x] T016 [P] Write unit tests for dedup in `tests/unit/test_evacuation_dedup.py`: test duplicate detection within window, TTL expiry, concurrent access, edge cases (empty cache, expired entries)
- [x] T017 [P] Write unit tests for versioning in `tests/unit/test_evacuation_versioning.py`: test version increment, OCC retry on conflict, max retry exhaustion, plan_id formatting

**Checkpoint**: Foundation ready — all data models validated, infrastructure modules tested. User story implementation can now begin.

---

## Phase 3: User Story 1 — Receive Handoff and Generate Evacuation Plan (Priority: P1) 🎯 MVP

**Goal**: End-to-end pipeline: receive `AgentHandoffEvent` from Risk Assessment, validate, retrieve assessment, compute zones, prepare road network, compute basic routes (Dijkstra's with closed road exclusion), generate template-based plan summary, version, persist to Cosmos DB, and write audit records. Produces a complete `EvacuationPlan` that an incident commander can review.

**Independent Test**: Send a synthetic `AgentHandoffEvent` with `source_agent=risk_assessment`, `target_agent=evacuation`, and payload containing `recommendationId`, `summary`, and `assessmentId`. Verify the agent produces an `EvacuationPlan` with routes, assembly areas, confidence level, and summary text linked to the originating assessment.

- [x] T018 [P] [US1] Create `apps/agents/evacuation/router.py` with `RouteComputer` class implementing Dijkstra's algorithm using a priority queue (min-heap) on capacity-weighted edges (weight = `distance / (capacity × utilisation_factor)`), computing shortest paths from zone origin nodes to reachable assembly areas, excluding road segments with `closure_status=closed` or Zone 1 membership (capacity=0), returning `EvacuationRoute` records with `total_distance_km`, `estimated_travel_time_normal_min`, `estimated_travel_time_loaded_min`, `capacity_vehicles_per_hour`, `estimated_utilisation_pct`, `vehicle_suitability` dict, and `excluded_roads` list per data-model.md §EvacuationRoute
- [x] T019 [P] [US1] Create `apps/agents/evacuation/templates.py` with template-based fallback plan summary generators: `generate_plan_summary_template(plan_data) → str` producing a structured plain-language summary from route/timeline/zone data, `generate_route_rationale_template(route) → str` for per-route selection rationale, and `generate_change_summary_template(old_plan, new_plan) → str` for replan diffs — all using AIIMS terminology per FR-020
- [x] T020 [US1] Create `apps/agents/evacuation/pipeline.py` with `EvacuationProcessingPipeline` class orchestrating the 10-stage processing pipeline per contracts/evacuation-pipeline.md: Stage 1 (handoff intake with Pydantic v2 validation, `target_agent=evacuation` check, dedup via `HandoffDeduplicator`), Stage 2 (assessment retrieval from Cosmos DB with missing-assessment rejection), Stage 3 (zone computation via `ZoneComputer`), Stage 4 (road network preparation with zone-based capacity reduction via `RoadNetworkLoader`), Stage 5 (route computation via `RouteComputer`), Stage 8 (plan summary via `templates.py` for MVP), Stage 9 (versioning via `VersionCounter` and persistence to `evacuation-plans` container with `status=proposed`), Stage 10 (audit finalisation via `AuditWriter`). Stages 6 (transport) and 7 (timeline) are stub pass-throughs for MVP, integrated in US3/US4.
- [x] T021 [US1] Replace existing stub in `apps/agents/evacuation/agent.py` with full `EvacuationAgent` class: subclass `LLMCallMixin`, implement `process_handoff(handoff: AgentHandoffEvent)` as main pipeline entry point delegating to `EvacuationProcessingPipeline`, implement Service Bus consumer loop for `evacuation-handoffs` queue, create FastAPI app factory `create_app()` with health endpoint placeholder, configure port 8082, and implement `__main__.py` entry point per quickstart.md (`uv run python -m evacuation.agent`)
- [x] T022 [P] [US1] Write contract tests for handoff structure in `tests/contract/test_evacuation_handoff.py`: validate inbound `AgentHandoffEvent` schema (required fields: handoff_id, incident_id, source_agent=risk_assessment, target_agent=evacuation, payload with recommendationId/assessmentId), validate rejection of malformed handoffs, validate duplicate discard with audit record
- [x] T023 [P] [US1] Write contract tests for plan output schema in `tests/contract/test_evacuation_plan_schema.py`: validate `EvacuationPlan` output contains all required sections per FR-019 (affected_area, population_estimate, hazard_summary, routes, assembly_areas, confidence_score/level, status=proposed, traceability, assumptions, generation_method, data_snapshot), validate plan_id format `ep-{incident_id}-v{N}`, validate traceability references back to handoff/assessment/recommendation
- [x] T024 [US1] Write unit tests for pipeline stages in `tests/unit/test_evacuation_pipeline.py`: test end-to-end handoff processing with mock dependencies, test handoff rejection (invalid structure, missing assessment), test duplicate discard, test zone computation integration, test route computation integration, test plan versioning (v1, v2 for same incident per research.md §5), test audit record creation per processing step

**Checkpoint**: US1 complete — end-to-end evacuation plan generation from handoff. Plans include routes, assembly areas, confidence, and template-based summaries. Fully testable with synthetic handoffs.

---

## Phase 4: User Story 2 — Compute Routes with Road Closure and Capacity Constraints (Priority: P2)

**Goal**: Enhance route computation with multi-path distribution across corridors, hazard-type-aware routing strategies for 5 Australian disaster types, congestion risk flagging, and deterministic tie-breaking.

**Independent Test**: Provide a road network graph with specific closures and capacity limits, an affected population exceeding single-corridor capacity, and verify generated routes avoid closed segments, distribute load, include capacity utilisation estimates, and flag corridors exceeding 80% utilisation.

- [x] T025 [US2] Add multi-path distribution to `apps/agents/evacuation/router.py`: when population exceeds single-corridor capacity, compute additional paths by penalising edges on the first path (increase weight) and re-running Dijkstra per FR-007, distribute population across corridors with estimated load percentages, and return multiple `EvacuationRoute` records per zone
- [x] T026 [US2] Add hazard-type-aware routing strategies to `apps/agents/evacuation/router.py` per data-model.md §Hazard Type → Routing Strategy Mapping: bushfire (away from fire front/downwind, close roads within 2km of fire perimeter), cyclone (inland shelters, close coastal roads in storm surge zone), flood (higher ground, close flood-prone/low-lying crossings), earthquake (away from damaged infrastructure), tsunami (elevated ground inland, close all coastal/low-elevation roads)
- [x] T027 [US2] Add congestion risk flagging and tie-breaking to `apps/agents/evacuation/router.py`: flag any corridor with `estimated_utilisation_pct > CONGESTION_RISK_THRESHOLD_PCT` (default 80%) as `congestion_risk=true` per FR-007, implement deterministic tie-breaking per contracts/evacuation-pipeline.md §Stage 5 (prefer lower congestion risk, then shorter distance), and compute `vehicle_suitability` dict (standard/heavy/accessible) based on edge `surface_type` and `accessibility_features`
- [x] T028 [US2] Write unit tests for routing in `tests/unit/test_evacuation_router.py`: test Dijkstra's shortest path, test closed road exclusion, test multi-path distribution (population > single corridor), test all 5 hazard-type routing strategies, test congestion risk flagging at 80% threshold, test tie-breaking (equal cost → lower congestion → shorter distance), test no-viable-route returns empty for shelter-in-place, test vehicle suitability assessment

**Checkpoint**: US2 complete — route computation handles real-world constraints. Plans now include multi-path corridors, capacity utilisation, congestion warnings, and hazard-specific routing.

---

## Phase 5: User Story 3 — Transport Coordination for Vulnerable Populations (Priority: P3)

**Goal**: Identify vulnerable population groups (mobility-impaired, medical-dependent, elderly/aged care, children/schools) in affected zones and generate transport requirements with vehicle types, quantities, pickup locations, and priority levels.

**Independent Test**: Provide an affected area containing a disability care facility (40 residents), a primary school (200 students), and aged care facility (80 residents). Verify the plan includes transport requirements with correct vehicle types, estimated vehicles, pickup locations, and priority levels (critical/immediate/high).

- [x] T029 [US3] Create `apps/agents/evacuation/transport.py` with `TransportCoordinator` class: query facility registry for facilities within each zone (aged care, disability care, hospital, school/childcare), create `TransportRequirement` per facility with vulnerability category, vehicle type mapping per FR-010 (mobility_impaired → wheelchair_accessible_vehicle, medical_dependent → ambulance/medical_transport, elderly_aged_care → accessible_bus, children_schools_childcare → bus), priority mapping (critical/immediate/immediate/high), vehicle estimation using capacity assumptions (bus: 50, wheelchair vehicle: 4, ambulance: 2, medical transport: 6), and missing population data handling per FR-032 (skip transport coordination, note data gap in assumptions)
- [x] T030 [US3] Integrate transport coordination into `apps/agents/evacuation/pipeline.py` Stage 6: wire `TransportCoordinator` into the pipeline between route computation (Stage 5) and timeline estimation (Stage 7), populate `EvacuationPlan.transport_coordination` list, include transport section separately from general evacuation per FR-012
- [x] T031 [US3] Write unit tests for transport coordination in `tests/unit/test_evacuation_transport.py`: test all 4 vulnerability categories generate correct vehicle types and priority levels, test vehicle count estimation (40 wheelchair users → 10 vehicles), test missing facility data handling (empty transport list + assumption note), test multi-zone facility aggregation, test special_considerations population (medical equipment, child supervision)

**Checkpoint**: US3 complete — plans now include transport coordination for vulnerable populations with vehicle requirements, pickup locations, and priority ordering.

---

## Phase 6: User Story 4 — Evacuation Timeline Estimation (Priority: P4)

**Goal**: Compute phased evacuation timelines (5-phase sequence per FR-015), estimate zone-by-zone clearance times, apply vulnerable population buffer multiplier, implement shelter-in-place decision logic, and detect time deficits against hazard arrival window.

**Independent Test**: Provide an affected area with 5,000 residents across 3 zones, route distances, capacity constraints, and a hazard time horizon. Verify the plan includes per-zone clearance times with mobilisation/travel components, 5-phase timeline, and time deficit flag when clearance exceeds hazard window.

- [x] T032 [US4] Create `apps/agents/evacuation/timeline.py` with `TimelineEstimator` class: compute per-zone clearance time using formula `(population / road_capacity) × distance_km × 60` minutes per FR-013, apply `VULNERABLE_POPULATION_BUFFER` (default 1.5×) multiplier to vulnerable population transport times, compute 5-phase timeline sequence (Phase 1: Zone 1 vulnerable, Phase 2: Zone 1 general, Phase 3: Zone 2 vulnerable, Phase 4: Zone 2 general, Phase 5: Zone 3 advisory), set phase transition criteria per research.md §2 (primary: elapsed time ≥ `phase_duration × PHASE_TRANSITION_TIME_FACTOR`, secondary: estimated population departed ≥ `PHASE_TRANSITION_POPULATION_PCT`%, whichever fires first), use configurable mobilisation times per hazard type (tsunami 30min, flood 120min, bushfire 60min, cyclone 120min, earthquake 30min), implement shelter-in-place decision per FR-014 (no viable route + hazard timeline allows → shelter-in-place with building requirements; no viable route + immediate threat → emergency escalation), detect time deficit (clearance time > hazard arrival window → flag deficit, recommend shelter-in-place for unclearable zones), and implement shelter-to-evacuation recovery per research.md §3 (re-evaluate shelter zones on road network update, generate new plan version if viable route found)
- [x] T033 [US4] Integrate timeline estimation into `apps/agents/evacuation/pipeline.py` Stage 7: wire `TimelineEstimator` between transport coordination (Stage 6) and plan summary generation (Stage 8), populate `EvacuationPlan.phases` list with `EvacuationPhase` records, add shelter-in-place zones to plan when no viable routes exist, flag time deficits in plan assumptions
- [x] T034 [US4] Write unit tests for timeline estimation in `tests/unit/test_evacuation_timeline.py`: test clearance time formula, test 1.5× buffer multiplier for vulnerable populations, test 5-phase sequence ordering and transition criteria (time-based and population-based triggers), test mobilisation time defaults per hazard type, test shelter-in-place decision (no route + safe timeline → shelter, no route + immediate threat → escalation), test time deficit detection and zone flagging, test shelter-to-evacuation recovery on new route availability

**Checkpoint**: US4 complete — plans now include phased timelines, clearance estimates, shelter-in-place recommendations, and time deficit warnings.

---

## Phase 7: User Story 5 — Dynamic Route Updates as Conditions Change (Priority: P5)

**Goal**: Evaluate replanning triggers, generate updated plan versions with change summaries, enforce rate limiting to prevent version churn, detect no-material-change situations, and support shelter-to-evacuation recovery as a replanning event.

**Independent Test**: Generate an initial plan, then provide updated road network status (close a previously open road on an active route). Verify a new plan version is generated with a change summary, revised routes, superseded status on the previous version, and the change completed within 15-second SLA.

- [x] T035 [US5] Create `apps/agents/evacuation/replanner.py` with `DynamicReplanner` class: evaluate all 6 replanning triggers per contracts/evacuation-pipeline.md §Dynamic Replanning Triggers — (a) new road closure on active route, (b) hazard area expands > `HAZARD_EXPANSION_REPLAN_PCT`%, (c) progress delay > `PROGRESS_DELAY_REPLAN_PCT`%, (d) higher-severity assessment received, (e) manual commander trigger via POST /replan, (f) shelter-to-evacuation recovery when new route enables evacuation of shelter-in-place zone — with incremental update path (changed edges only → recompute affected routes), change summary generation listing routes changed, assembly areas changed, transport changes, timeline changes, and triggering event per FR-018
- [x] T036 [US5] Add rate limiting, no-change detection, and multi-trigger merging to `apps/agents/evacuation/replanner.py`: enforce minimum `REPLAN_RATE_LIMIT_SECONDS` (default 30s) between replans for same incident per CHK037, detect no-material-change (no affected routes, no zone changes → log existing plan valid, skip version creation per FR-016), merge multiple simultaneous triggers into a single replan operation
- [x] T037 [US5] Wire replanning into `apps/agents/evacuation/agent.py`: add `process_replan(incident_id, trigger)` method that invokes `DynamicReplanner`, re-runs pipeline stages 4–10 (or 3–10 for hazard expansion), creates new plan version via `VersionCounter`, marks previous version as `superseded` (only if new version gets approved — approved plans not auto-superseded per research.md §5), and produce `EvacuationDecisionRecord` with `decision_type=plan_updated` and `replanning_triggers` list
- [x] T038 [US5] Write unit tests for replanning in `tests/unit/test_evacuation_replanner.py`: test each of 6 trigger conditions independently, test rate limiting (reject replan within 30s window → return 429), test no-change detection (no version created), test simultaneous trigger merging, test change summary content, test incremental update (only affected routes recomputed), test shelter-to-evacuation recovery flow with `replanning_triggers=["shelter_to_evacuation_recovery"]`

**Checkpoint**: US5 complete — agent dynamically replans when conditions change, producing versioned plan updates with change summaries within 15-second SLA.

---

## Phase 8: User Story 6 — Human-Reviewable Evacuation Plans for Incident Commanders (Priority: P6)

**Goal**: Generate LLM-powered plan summaries with AIIMS terminology, validate all LLM outputs through content safety, apply confidence reduction for template fallback, and expose HTTP endpoints for commander overrides and manual replanning.

**Independent Test**: Generate an evacuation plan and verify it contains all required sections (area, routes with rationale, assembly areas, transport, timelines, confidence, assumptions, traceability). Submit an override (approve/reject/modify) and verify the override is recorded in audit trail with user ID, role, justification, and the plan status transitions correctly.

- [x] T039 [US6] Enhance `apps/agents/evacuation/templates.py` with AIIMS-terminology plan summaries per hazard type: structured summary sections (Situation, Objectives, Strategy, Tactics, Administration/Logistics), route rationale templates explaining selection criteria (distance, capacity, hazard avoidance), change summary templates for replans highlighting key differences, and `MAX_SUMMARY_LENGTH` truncation
- [x] T040 [US6] Integrate `_generate_with_fallback()` from `LLMCallMixin` into `apps/agents/evacuation/pipeline.py` Stage 8: use Azure OpenAI (reasoning deployment for plan analysis, drafting deployment for summary text) to generate human-readable plan summaries, fall back to template-based summaries when LLM unavailable, apply multiplicative confidence reduction (`confidence × FALLBACK_CONFIDENCE_REDUCTION` where default 0.8) per research.md §4 on template fallback, set `generation_method` to `ai_assisted` or `template_fallback`, validate all LLM outputs through `ContentSafetyValidator` from `apps/agents/common/content_safety.py` per FR-036, replace with template text and record `content_safety_failure` audit record on validation failure
- [x] T041 [US6] Implement POST /override endpoint in `apps/agents/evacuation/agent.py` per contracts/health-endpoint.md §POST /override: accept override request with `plan_id`, `action` (approve/reject/cancel/pause/resume/modify), `user_id`, `role`, `justification`, and optional `modifications`, enforce valid status transitions per data-model.md §EvacuationPlan status transitions, create new plan version for `modify` actions, record `OverrideMetadata` in plan and `EvacuationDecisionRecord` with `decision_type=override_applied` in audit trail, return 404/409/422 for plan-not-found/concurrent-conflict/invalid-transition
- [x] T042 [US6] Implement POST /replan endpoint in `apps/agents/evacuation/agent.py` per contracts/health-endpoint.md §POST /replan: accept replan request with `incident_id`, `user_id`, `role`, `justification`, and optional `road_closures`, validate active plan exists for incident (404 if not), enforce rate limiting (429 if within `REPLAN_RATE_LIMIT_SECONDS`), trigger `process_replan()` asynchronously, return 202 with `replanning_initiated` status and `previous_plan_id`
- [x] T043 [US6] Write unit tests for endpoints in `tests/unit/test_evacuation_endpoints.py`: test POST /override with all 6 action types (approve/reject/cancel/pause/resume/modify), test invalid status transitions return 422, test concurrent override returns 409, test POST /replan triggers replanning, test rate limiting returns 429, test missing plan returns 404, test override audit record contains user_id/role/justification/timestamp

**Checkpoint**: US6 complete — plans include LLM-powered summaries with AIIMS terminology, content safety validation, and commanders can override/replan via HTTP API.

---

## Phase 9: User Story 7 — Rehearsal and Simulation Mode (Priority: P7)

**Goal**: Process handoffs in simulation tenant contexts with full isolation from live data, support reproducibility verification for scenario-based testing.

**Independent Test**: Send handoffs with a simulation tenant identifier. Verify generated plans are stored within the simulation tenant boundary, do not appear in live incident queries, carry the simulation tenant identifier, and produce identical outputs when replayed with identical inputs.

- [x] T044 [US7] Add tenant isolation handling to `apps/agents/evacuation/pipeline.py`: route simulation vs live handoffs through appropriate processing context based on `tenant_id` field, scope all Cosmos DB queries (plan reads, assessment retrieval, audit writes) to `incident_scope_key` containing `tenant_id` per data-model.md partition key format `{tenant_id}:{incident_id}`, ensure simulation plans carry `tenant_id` in all records and never appear in live-scoped queries per FR-025
- [x] T045 [US7] Add deterministic tie-breaking for reproducibility verification to `apps/agents/evacuation/router.py`: ensure that given identical inputs (same road network, same zones, same population data) and identical `configuration_version`, the `RouteComputer` produces identical route selections per FR-026 and SC-006 — use stable sort keys (edge_id as secondary sort) to eliminate non-determinism from equal-weight paths
- [x] T046 [US7] Write contract tests for reproducibility in `tests/contract/test_evacuation_reproducibility.py`: test that identical inputs produce identical route selections, timeline estimates, and transport coordination across multiple runs, test that configuration_version and data_snapshot are captured for each plan, test simulation tenant isolation (simulation plans invisible to live queries)

**Checkpoint**: US7 complete — simulation mode fully isolated from live operations, plans are reproducible for scenario-based testing and tabletop exercises.

---

## Phase 10: User Story 8 — Audit Trail of All Evacuation Decisions (Priority: P8)

**Goal**: Ensure every processing step produces a corresponding `EvacuationDecisionRecord`, verify audit completeness via reconciliation, and support queryable audit retrieval by incident ID, plan ID, decision type, and time range.

**Independent Test**: Process a sequence of handoffs resulting in plans, route updates, and overrides. Query the audit trail and verify every processing step has a corresponding record with all required fields (handoff_id, plan_id, decision_type, confidence, processing_duration, rationale, agent_version, configuration_version, timestamp).

- [x] T047 [US8] Ensure all 15 `DecisionType` values produce audit records across pipeline stages in `apps/agents/evacuation/pipeline.py`: `handoff_received` (Stage 1), `handoff_rejected` (Stage 1), `duplicate_discarded` (Stage 1), `assessment_retrieved` (Stage 2), `road_network_loaded` (Stage 4), `zones_computed` (Stage 3), `routes_computed` (Stage 5), `transport_coordinated` (Stage 6), `timeline_estimated` (Stage 7), `plan_generated` (Stage 9), `plan_updated` (replan), `override_applied` (POST /override), `shelter_in_place_recommended` (Stage 7), `degradation_detected` (any fallback), `content_safety_failure` (Stage 8) — each with all 22 canonical fields per data-model.md §EvacuationDecisionRecord including domain-specific optional fields populated when applicable
- [x] T048 [US8] Add audit completeness verification to `apps/agents/evacuation/pipeline.py` Stage 10: reconcile handoff_id processed against audit records created per SC-007, log warning if any processing step lacks a corresponding audit record, ensure `processing_duration_ms` is measured precisely for each stage, and support queryable audit retrieval by `incident_id`, `plan_id`, `decision_type`, and time range per FR-030
- [x] T049 [US8] Write unit tests for audit writer and completeness in `tests/unit/test_evacuation_audit.py`: test three-tier degradation transitions (Cosmos → memory buffer on write exception, memory → file when buffer full, recovery flush memory → file → Cosmos), test `buffered_at` and `flush_source` annotation on flushed records, test `get_status()` returns correct tier status, test audit completeness reconciliation (all 15 decision types have records), test audit record querying by incident_id and decision_type

**Checkpoint**: US8 complete — every processing step audited with complete records, three-tier degradation ensures no audit data loss, records are queryable for post-incident review.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Health endpoint, observability instrumentation, integration tests, simulation tests, and quickstart validation.

- [x] T050 Implement GET /health endpoint in `apps/agents/evacuation/agent.py` per contracts/health-endpoint.md: report 6 health checks — `road_network_loaded` (graph loaded + node/edge counts + staleness), `llm_connectivity` (last call latency), `cosmos_connectivity` (last write status), `active_plan_count` (count < 40 healthy, ≥ 40 warning), `processing_queue_depth` (depth < 20 healthy, ≥ 20 backpressure), `audit_store` (tier 1/2/3 status from `AuditWriter.get_status()`) — determine overall status: `healthy` (all checks pass), `unhealthy` (road network not loaded OR queue offline), `degraded` (any other check degraded) — respond within 1 second per FR-034
- [x] T051 [P] Add OpenTelemetry distributed tracing spans to `apps/agents/evacuation/pipeline.py` per contracts/telemetry.md §Span Hierarchy: root span `evacuation.process_handoff` with child spans for each pipeline stage (`validate_handoff`, `retrieve_assessment`, `compute_zones`, `prepare_road_network`, `compute_routes` with nested `dijkstra_run`/`multi_path_distribution`, `coordinate_transport`, `estimate_timeline`, `generate_summary` with nested `llm_call`/`template_fallback`/`content_safety_check`, `assign_version`, `persist_plan`, `write_audit`), and replanning span hierarchy `evacuation.replan` — propagate correlation ID from `handoff_id`
- [x] T052 [P] Emit all metrics defined in contracts/telemetry.md across `apps/agents/evacuation/pipeline.py` and `apps/agents/evacuation/agent.py`: processing metrics (plan_generation_latency histogram, route_computation_time histogram, replan_count/latency, handoff_intake/rejected/duplicate counters, SLA breach counters), safety metrics (shelter_in_place_count, shelter_to_evacuation_recovery_count, emergency_escalation_count, time_deficit_flag_count), transport metrics (transport_requests_generated, transport_by_category, transport_vehicles_estimated), zone/population metrics (zone_population_covered, active_plans_gauge, routes_per_plan, congestion_risk_routes), override metrics (dynamic_update_rate, override_rate, override_by_type), degradation metrics (fallback_mode_activations, content_safety_failures, audit_buffer_depth, audit_tier, road_data_stale, degradation_events), version metrics (version_count_per_incident, version_conflict_retries), handoff success rate
- [x] T053 [P] Emit 12 custom events in `apps/agents/evacuation/pipeline.py` and `apps/agents/evacuation/agent.py` per contracts/telemetry.md §Custom Events: `HandoffReceived`, `PlanGenerated`, `PlanUpdated`, `ShelterInPlaceRecommended`, `ShelterToEvacuationRecovery`, `EmergencyEscalation`, `OverrideApplied`, `DegradationEvent`, `SLABreach`, `VersionConflict`, `RouteConflict`, `TimeDeficitDetected` — each with specified properties
- [x] T054 Write integration test for Cosmos DB persistence in `tests/integration/test_evacuation_cosmos.py`: test plan write/read round-trip to `evacuation-plans` container, test audit record write/read to `evacuation-decisions` container, test version counter OCC under concurrent writes, test partition key scoping (`incident_scope_key`), test query by incident_id and time range
- [x] T055 [P] Write integration test for Service Bus handoff intake in `tests/integration/test_evacuation_service_bus.py`: test message receive/acknowledge from `evacuation-handoffs` queue, test message deserialization to `AgentHandoffEvent`, test at-least-once delivery with deduplication
- [x] T056 Write simulation scenario test in `tests/simulation/test_cyclone_evacuation_scenario.py`: simulate Category 4 cyclone approaching Far North Queensland coast per User Story 1 scenario — send handoff with cyclone hazard assessment, verify plan includes inland evacuation routes avoiding coastal roads, assembly areas at inland shelters, transport coordination for vulnerable populations, phased timeline, and confidence level
- [x] T058 Write simulation scenario test in `tests/simulation/test_bushfire_evacuation_scenario.py`: simulate bushfire approaching a rural NSW/VIC community — send handoff with bushfire hazard assessment, verify plan prioritises routes away from fire front and wind direction per FR-008, excludes roads within fire proximity (closure_reason=fire_proximity), includes phased timeline with mobilisation time 60 min, transport coordination for aged care facility, and confidence level — required by constitution §Quality Gates for bushfire scenario coverage
- [x] T059 Write simulation scenario test in `tests/simulation/test_flood_evacuation_scenario.py`: simulate major riverine flood in QLD/NSW — send handoff with flood hazard assessment, verify plan prioritises routes to higher ground per FR-008, excludes flood-prone roads (closure_reason=flood_cut), applies Zone 2 capacity reduction on partially inundated corridors, includes phased timeline with mobilisation time 120 min, and shelter-in-place recommendation for zones that cannot be cleared before floodwater arrival — required by constitution §Quality Gates for flood scenario coverage
- [x] T057 Run `specs/009-evacuation-agent/quickstart.md` validation end-to-end: verify health check returns healthy JSON with all 6 checks, run synthetic handoff contract test, verify plan output structure matches contract

**Checkpoint**: All cross-cutting concerns addressed — health endpoint operational, full observability instrumentation, integration tests passing, simulation scenario validated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **User Stories (Phases 3–10)**: All depend on Foundational phase completion
  - **US1 (Phase 3)**: Can start after Foundational — no story dependencies
  - **US2 (Phase 4)**: Depends on US1 (enhances router.py created in US1)
  - **US3 (Phase 5)**: Depends on US1 (integrates into pipeline.py from US1)
  - **US4 (Phase 6)**: Depends on US1 (integrates into pipeline.py from US1)
  - **US5 (Phase 7)**: Depends on US1 + US2 (replans routes computed by enhanced router)
  - **US6 (Phase 8)**: Depends on US1 (enhances pipeline.py from US1)
  - **US7 (Phase 9)**: Depends on US1 (adds tenant handling to pipeline.py from US1)
  - **US8 (Phase 10)**: Depends on US1 (verifies audit across pipeline stages from US1)
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Independence

After US1 is complete, the following stories can proceed **in parallel** (if staffed):
- **US2, US3, US4**: Independent of each other — US2 enhances routing, US3 adds transport, US4 adds timeline. All integrate into different pipeline stages.
- **US6, US7, US8**: Independent of each other — US6 adds LLM/API, US7 adds simulation, US8 adds audit verification.

**US5** depends on US2 (enhanced routing) for full replanning capability but can start with basic routing from US1.

### Within Each User Story

1. Create/enhance modules (implementation files) FIRST
2. Integrate into pipeline.py or agent.py
3. Write tests LAST (verify completed implementation)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T007–T017 after T005–T006 complete)
- Once Foundational completes, US1 starts; after US1, US2/US3/US4 can start in parallel
- Within US1: T018 (router.py) and T019 (templates.py) can run in parallel
- Within Foundational: All test tasks (T012–T017) can run in parallel
- Within Polish: T051, T052, T053, T055 can run in parallel

---

## Parallel Example: Foundational Phase

```text
# After T005 (config) and T006 (models) complete sequentially:

# Launch all infrastructure modules in parallel:
Task: T007 "Create road_network.py with RoadNetworkLoader"
Task: T008 "Create zones.py with ZoneComputer"
Task: T009 "Create dedup.py with HandoffDeduplicator"
Task: T010 "Create versioning.py with VersionCounter"
Task: T011 "Create audit.py with AuditWriter"

# After all modules complete, launch all tests in parallel:
Task: T012 "Write models unit tests"
Task: T013 "Write config unit tests"
Task: T014 "Write road_network unit tests"
Task: T015 "Write zones unit tests"
Task: T016 "Write dedup unit tests"
Task: T017 "Write versioning unit tests"
```

## Parallel Example: After US1 Complete

```text
# Three developers can work independently:

Developer A (US2): T025 → T026 → T027 → T028  (enhanced routing)
Developer B (US3): T029 → T030 → T031          (transport coordination)
Developer C (US4): T032 → T033 → T034          (timeline estimation)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T017) — **CRITICAL: blocks all stories**
3. Complete Phase 3: User Story 1 (T018–T024)
4. **STOP and VALIDATE**: Test US1 independently with synthetic handoffs
5. Deploy/demo if ready — agent produces basic evacuation plans from handoffs

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy (MVP! Agent generates evacuation plans)
3. Add US2 → Test independently → Deploy (enhanced routing with constraints)
4. Add US3 → Test independently → Deploy (transport coordination for vulnerable populations)
5. Add US4 → Test independently → Deploy (phased timelines, shelter-in-place)
6. Add US5 → Test independently → Deploy (dynamic replanning)
7. Add US6 → Test independently → Deploy (LLM summaries, commander API)
8. Add US7 → Test independently → Deploy (simulation mode)
9. Add US8 → Test independently → Deploy (full audit trail verification)
10. Polish → Health endpoint, observability, integration tests → Production ready

### Parallel Team Strategy

With 3 developers:

1. **Week 1**: All three complete Setup + Foundational together
2. **Week 2**: Developer A does US1 (MVP pipeline)
3. **Week 3**: Developer A does US2, Developer B does US3, Developer C does US4 (parallel)
4. **Week 4**: Developer A does US5, Developer B does US6, Developer C does US7+US8 (parallel)
5. **Week 5**: All three collaborate on Polish phase

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps each task to a specific user story for traceability
- Each user story is independently completable and testable after US1 (MVP)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The existing `apps/agents/evacuation/agent.py` is a stub that must be fully replaced (T021)
- Port 8082 avoids conflicts with monitoring (8080) and risk assessment (8081)
- All Cosmos DB containers: `evacuation-plans` (plans + version counters), `evacuation-decisions` (audit records)
- Latency budget: 30s initial plan generation, 15s replanning — see contracts/evacuation-pipeline.md
