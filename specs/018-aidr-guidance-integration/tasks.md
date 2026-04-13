# Tasks: AIDR Guidance Integration

**Input**: Design documents from `/specs/018-aidr-guidance-integration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Domain models**: `packages/domain/src/domain/models/`
- **Agent logic**: `apps/agents/` (per-agent subfolders)
- **Agent shared**: `apps/agents/common/`
- **Platform API routes**: `apps/api/app/api/routes/`
- **Platform services**: `apps/api/app/services/`
- **Infrastructure**: `infra/`
- **Tests**: `tests/` (unit, contract, integration, simulation)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialisation, branch creation, and infrastructure provisioning for five new Cosmos DB containers

- [X] T001 Create and checkout feature branch `018-aidr-guidance-integration` from main
- [X] T002 [P] Create Cosmos DB infrastructure module for five new containers (recovery, lessons, aiims-assignments, evacuation-stages, pprr-contexts) in `infra/modules/recovery-lessons.bicep` with partition keys per R-013: `/incident_id` for recovery, lessons, aiims-assignments, evacuation-stages; `/context_reference_id` for pprr-contexts
- [X] T003 [P] Extend `infra/main.bicep` to reference the new `recovery-lessons.bicep` module, scoped to Azure Australia East (NFR-015)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain models and shared utilities that ALL user stories depend on. MUST complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Domain Model Extensions (Existing Models)

- [X] T004 [P] Extend `Incident` model with `pprr_phase: Literal["prevention", "preparedness", "response", "recovery"] | None = None`, `incident_level: Literal[1, 2, 3] = 1`, and expanded `incident_type` Literal adding `"tsunami"`, `"extreme_heat"`, `"pandemic"` in `packages/domain/src/domain/models/incident.py` per E-001
- [X] T005 [P] Extend `PublicAlert` model with AWS warning fields (`warning_tier`, `colour_code`, `hazard_icon`, `action_statement`, `superseded_warning_id`, `tier_skip_justification`, `is_all_clear`, `warning_principles_checklist`) in `packages/domain/src/domain/models/public_alert.py` per E-002, including Pydantic validators for tier-to-colour mapping and all-clear constraints
- [X] T006 [P] Extend `HandoffChainDefinition` `SignalCategory` Literal with `"recovery_assessment"` and `"lessons_capture"` values in `packages/domain/src/domain/models/handoff_chain.py` per E-003

### New Domain Models

- [X] T007 [P] Create `AiimsRoleAssignment` model in `packages/domain/src/domain/models/aiims_role_assignment.py` per N-001 with `AiimsFunction` Literal type, assignment tracking fields, delegation support, and validation rules (one function per agent per incident)
- [X] T008 [P] Create `EvacuationStage` model in `packages/domain/src/domain/models/evacuation_stage.py` per N-002 with `EvacStageName`, `EvacuationType`, `EvacuationApproach`, `EvacuationScope` Literal types, five-stage fields, shelter-in-place fields, re-entry counter, and audit fields
- [X] T009 [P] Create `RecoveryEnvironmentTracker` and `RecoveryIndicator` models in `packages/domain/src/domain/models/recovery_environment_tracker.py` per N-003 with 21 AIDR-defined indicators, `RecoveryEnvironment`/`IndicatorUpdateSource`/`DataClassification` Literals, k-anonymity validator (population_coverage ≥ 10 for sensitive social data per R-012), and regression detection fields
- [X] T010 [P] Create `Lesson` model in `packages/domain/src/domain/models/lesson.py` per N-004 with `LessonStatus`/`LessonSeverity` Literals, AIIMS function and PPRR phase categorisation, assignment tracking, contradictory-lesson fields, and validator requiring at least one of `incident_id` or `scenario_run_id`
- [X] T011 [P] Create `PprrPhaseContext` model in `packages/domain/src/domain/models/pprr_phase_context.py` per N-005/R-001 with `context_type: Literal["region", "scenario"]`, phase restricted to prevention/preparedness, and transition-to-incident linkage

### Shared Agent Utilities

- [X] T012 [P] Create AIIMS role constants, default agent-to-function mapping, and static fallback validation in `apps/agents/common/aiims_mapping.py` per R-005 three-tier hierarchy (OperatingFramework → FrameworkAssignment → AiimsRoleAssignment)
- [X] T013 [P] Create PPRR phase transition logic with managed transition validation, overlap period tracking, and TimelineEvent payload generation in `apps/agents/common/pprr_lifecycle.py` per R-001/FR-031/FR-053
- [X] T014 [P] Create AWS three-tier warning compliance validator and ten-principle checker in `apps/agents/common/warning_compliance.py` per FR-006/SC-006 — validates tier/colour/icon consistency, action statement presence, and all 10 warning principles (life_saving, empowering, trusted, risk_scaled, timely_targeted, impact_conveying, action_calling, clearly_communicated, accessible, bigger_picture)
- [X] **T085** [P] Create shared vulnerable population constants and utility in `apps/agents/common/vulnerable_populations.py` defining canonical population groups per Constitution §VI-C and AIDR Evacuation Planning Handbook extensions (elderly, children, people with disabilities, CALD communities, pregnant/breastfeeding women, people with health needs, people with pets/assistance animals)

### Handoff Chain Extensions

- [X] T015 Extend handoff builders in `apps/agents/common/handoffs.py` with recovery-phase handoff (Risk Assessment → recovery agents, `category_filter=["recovery_assessment"]`) and lessons-capture handoff (incident closure Level 2+ → lessons service, `category_filter=["lessons_capture"]`) per FR-054

### TimelineEvent Payload Schemas

- [X] T016 Document and validate new TimelineEvent payload schemas (PPRR phase transition, incident level change, evacuation stage transition, lessons capture trigger) as structured dict schemas referenced in `packages/domain/src/domain/models/timeline_event.py` per FR-053

**Checkpoint**: All domain models, shared utilities, and infrastructure ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Three-Tier Australian Warning System Alerts (Priority: P1) 🎯 MVP

**Goal**: Communication Agent generates AWS-compliant three-tier warnings (Advice/Watch and Act/Emergency Warning) with nested model, hazard icons, de-escalation, all-clear, and singly-linked warning chains

**Independent Test**: Simulate a hazard escalation sequence → verify each warning has correct tier label, colour code, hazard icon, action statement, warning principles checklist, and chain linkage

**FRs**: FR-001–007, FR-048 | **NFRs**: NFR-001, NFR-013 | **SCs**: SC-001, SC-006

### Implementation for User Story 1

- [X] T017 [P] [US1] Create AWS nested-model warning builder with tier-colour mapping, hazard icon selection, action statement templates, and supersession chain management in `apps/agents/communication/warning_builder.py` per FR-002/FR-003/R-004
- [X] T018 [P] [US1] Extend Communication Agent models with AWS warning request/response schemas in `apps/agents/communication/models.py` per FR-048
- [X] T019 [US1] Extend Communication Agent in `apps/agents/communication/agent.py` to generate three-tier AWS warnings using the warning builder, support tier escalation/de-escalation (FR-004), issue all-clear notifications (FR-005), handle tier-skip for sudden-onset hazards with justification logging, and enforce IC approval with AIIMS delegation chain timeout (5 min Emergency Warning, 15 min lower tiers)
- [X] T020 [US1] Add warning compliance validation call within the Communication Agent's warning generation flow — invoke `warning_compliance.py` validator before publish, populate `warning_principles_checklist` on `PublicAlert`, enforce NFR-001 ≤5s validation time
- [X] T021 [US1] Add vulnerable population accessibility handling in Communication Agent — CALD translations, disability-accessible formats, extended population groups per FR-007/Constitution §VI-C and AIDR Evacuation Planning Handbook 2023
- [X] T022 [US1] Implement graceful degradation for AWS warnings — template-based fallback when LLM unavailable (`generation_method = "template_fallback"`), local buffering when Cosmos unavailable, local-only validation per R-002
- [X] T023 [US1] Add warning chain query endpoint `GET /api/alerts/{alert_id}/chain` — traverse singly-linked `superseded_warning_id` chain, return ordered chain with tier/status/timestamp per warning-api.yaml contract
- [X] T024 [US1] Add CAP (Common Alerting Protocol) XML rendering endpoint `GET /api/alerts/{alert_id}/cap` per R-009 — serialize `PublicAlert` with AWS fields to CAP 1.2 XML format
- [X] T025 [US1] Add warning compliance validation endpoint `POST /api/alerts/{alert_id}/validate-compliance` returning AWS compliance status and ten-principle checklist per warning-api.yaml contract
- [X] T026 [US1] Add observability metrics for US1 — emit `warning_compliance_rate` and `tier_transition_latency` telemetry per NFR-010

**Checkpoint**: AWS three-tier warning generation fully functional — warnings have correct tiers, colours, icons, action statements, chain linkage, and 100% principle compliance (SC-001, SC-006)

---

## Phase 4: User Story 2 — AIIMS-Aligned Incident Management Structure (Priority: P1)

**Goal**: Every active incident maps agents to six AIIMS functional roles (Control, Intelligence, Planning, Operations, Logistics, Public Information), supports three incident levels, and displays structure in COP

**Independent Test**: Create a simulated incident → verify each agent is mapped to exactly one AIIMS function, role boundaries respected, incident level escalation activates correct coordination behaviours, COP displays full AIIMS structure

**FRs**: FR-013–017, FR-049 | **NFRs**: NFR-002 | **SCs**: SC-002

### Implementation for User Story 2

- [X] T027 [P] [US2] Create AIIMS service with role assignment CRUD, one-function-per-agent-per-incident enforcement, coverage ratio calculation, Level 3 full-coverage validation, and incident level change logic in `apps/api/app/services/aiims_service.py`
- [X] T028 [US2] Create AIIMS API routes in `apps/api/app/api/routes/aiims.py` per aiims-api.yaml contract — `POST /api/incidents/{incident_id}/aiims/assignments` (assign agent to AIIMS function), `GET /api/incidents/{incident_id}/aiims/structure` (COP display), `PUT /api/incidents/{incident_id}/aiims/assignments/{assignment_id}` (reassign/deactivate), `POST /api/incidents/{incident_id}/level` (change incident level with TimelineEvent creation)
- [X] T029 [US2] Wire AIIMS role consultation into agent startup — when incident starts, check `FrameworkAssignment` for AIIMS applicability, create `AiimsRoleAssignment` records for each agent using default mapping from `aiims_mapping.py`, agents query own assignment for current AIIMS function per R-005
- [X] T030 [US2] Add Level 2+ shared COP establishment — when incident escalates to Level 2, ensure shared COP includes AIIMS structure display; at Level 3, validate all six functions assigned per FR-016/FR-017
- [X] T031 [US2] Implement graceful degradation for AIIMS — static fallback to default AIIMS mapping from configuration when role assignment service unavailable, COP displays last-known assignments with staleness indicator per R-002
- [X] T032 [US2] Add Level 2+ incident closure auto-trigger for lessons capture — create `TimelineEvent` with `lessons_capture_triggered` payload when Level 2+ incident transitions to `closed` per FR-038/R-007
- [X] T033 [US2] Add observability metric `aiims_role_coverage_ratio` per NFR-010

**Checkpoint**: AIIMS role management fully operational — every incident has six-function mapping visible in COP, incident levels escalate/de-escalate correctly (SC-002)

---

## Phase 5: User Story 3 — Five-Stage Evacuation Process (Priority: P1)

**Goal**: Evacuation Agent operates through five mandatory stages (Decision, Warning, Withdrawal, Shelter, Return) with state machine transitions, shelter-in-place support, re-entry, and vulnerable population prioritisation

**Independent Test**: Simulate a cyclone scenario → step Evacuation Agent through all five stages → verify each stage produces required outputs, decision records, and vulnerable-population accommodations

**FRs**: FR-018–025 | **SCs**: SC-003, SC-009

### Implementation for User Story 3

- [X] T034 [P] [US3] Create evacuation stage state machine logic in `apps/agents/evacuation/stages.py` per R-010 — implement valid forward transitions (decision→warning→withdrawal→shelter→return→completed), re-entry transitions (any stage → decision), shelter-in-place path (decision → shelter_in_place → decision), re_entry_count increment, TimelineEvent generation for each transition
- [X] T035 [P] [US3] Extend Evacuation Agent models in `apps/agents/evacuation/models.py` with `EvacuationStage` integration — request/response schemas for stage initialisation, transition, withdrawal tracking, shelter tracking, and return tracking per evacuation-api.yaml
- [X] T036 [US3] Extend Evacuation Agent in `apps/agents/evacuation/agent.py` with five-stage lifecycle management — Decision stage captures authority/rationale/type/approach/scope (FR-019), Warning stage coordinates with Communication Agent (FR-020), Withdrawal stage tracks population movement with vulnerable priority (FR-021), Shelter stage tracks capacity/welfare/vulnerable status (FR-022), Return stage manages phased re-entry with safety validation (FR-023)
- [X] T037 [US3] Add shelter-in-place support in Evacuation Agent — rationale capture, ongoing condition monitoring, re-evaluation path back to Decision stage per FR-024
- [X] T038 [US3] Add support for both pre-warned and immediate evacuation types per FR-025, including tier-skip integration with US1 warning builder for sudden-onset events
- [X] T039 [US3] Create evacuation API routes in `apps/api/app/api/routes/evacuation.py` (if not already handled by agent endpoints) per evacuation-api.yaml — `POST .../evacuation/stages` (initialise), `POST .../stages/{stage_id}/transition` (advance), `GET .../stages/{stage_id}` (status), `PUT .../stages/{stage_id}/withdrawal` (progress), `PUT .../stages/{stage_id}/shelter` (capacity), `PUT .../stages/{stage_id}/return` (safety)
- [X] T040 [US3] Implement graceful degradation for evacuation stages — use existing circuit breaker pattern in `apps/agents/common/circuit_breaker.py`, buffer stage transitions locally when API unavailable, persist to local audit before Cosmos write per R-002
- [X] T041 [US3] Add observability metric `evacuation_stage_duration` per NFR-010

**Checkpoint**: Five-stage evacuation lifecycle fully functional — stages progress sequentially with re-entry support, shelter-in-place alternative, and vulnerable population prioritisation at every stage (SC-003, SC-009)

---

## Phase 6: User Story 4 — PPRR Lifecycle Integration (Priority: P2)

**Goal**: Platform supports all four PPRR phases (Prevention, Preparedness, Response, Recovery) with managed transitions, overlap periods, non-incident phase contexts, and COP visibility

**Independent Test**: Configure a flood scenario → verify distinct capabilities in each PPRR phase, managed phase transitions with overlap, concurrent phases across incidents, and PprrPhaseContext for pre-incident phases

**FRs**: FR-026–031, FR-050, FR-053 | **NFRs**: NFR-003 | **SCs**: SC-004

### Implementation for User Story 4

- [X] T042 [P] [US4] Create PPRR service with phase transition logic, overlap period management, TimelineEvent creation (FR-053 payload), PprrPhaseContext CRUD for non-incident phases, and transition-to-incident linkage in `apps/api/app/services/pprr_service.py`
- [X] T043 [US4] Create PPRR API routes in `apps/api/app/api/routes/pprr.py` per pprr-api.yaml — `POST /api/incidents/{incident_id}/pprr/transition` (phase transition with overlap), `GET /api/incidents/{incident_id}/pprr` (current phase + history), `POST /api/pprr/contexts` (create non-incident phase context), `GET /api/pprr/contexts` (list active contexts), `PUT /api/pprr/contexts/{context_id}/transition-to-incident` (link to incident)
- [X] T044 [US4] Implement Prevention phase capabilities — hazard risk assessment support and mitigation-option analysis integration per FR-028
- [X] T045 [US4] Implement Preparedness phase capabilities — scenario rehearsal integration with existing simulation (spec 007), community readiness assessment, resource pre-positioning plans, warning system testing per FR-029
- [X] T046 [US4] Implement Response phase concurrent recovery planning — when in Response phase, enable parallel Recovery phase activation per FR-030/FR-035
- [X] T047 [US4] Implement managed transition logic — overlap periods where multiple phases active simultaneously, non-abrupt phase switching per FR-031, and concurrent phase support for overlapping incidents (edge case: conflicting PPRR phases)
- [X] T048 [US4] Implement graceful degradation for PPRR transitions — agents continue in current phase when transition service unavailable, phase transition requests queued and applied on recovery per R-002
- [X] T049 [US4] Add observability metric `pprr_phase_transition_count` per NFR-010

**Checkpoint**: Full PPRR lifecycle operational — Prevention and Preparedness work without incidents, Response enables concurrent Recovery, transitions are managed with overlap, concurrent phases for overlapping incidents (SC-004)

---

## Phase 7: User Story 5 — Community Recovery Support (Priority: P2)

**Goal**: Platform tracks post-disaster recovery across four environments (Social, Built, Economic, Natural) with 21 AIDR indicators, six National Recovery Principles, community-led approaches, longitudinal tracking, and community visibility

**Independent Test**: Simulate a post-flood recovery → verify dashboard covers all four environments with 21 indicators, principle alignment on recommendations, community input mechanisms, regression detection, and k-anonymity compliance for social data

**FRs**: FR-032–037 | **NFRs**: NFR-004, NFR-007, NFR-012, NFR-013, NFR-014 | **SCs**: SC-005, SC-010

### Implementation for User Story 5

- [X] T050 [P] [US5] Create recovery service with tracker initialisation (21 AIDR indicators), indicator CRUD, regression detection logic, staleness tracking (24-hour SLA for community-response per SC-010), recovery principle validation, and dashboard data assembly in `apps/api/app/services/recovery_service.py` per R-003/R-006
- [X] T051 [US5] Create recovery API routes in `apps/api/app/api/routes/recovery.py` per recovery-api.yaml — `POST /api/incidents/{incident_id}/recovery` (initialise tracker), `GET /api/incidents/{incident_id}/recovery/dashboard` (dashboard ≤10s per NFR-004), `PUT /api/incidents/{incident_id}/recovery/indicators/{indicator_name}` (update indicator), `POST /api/incidents/{incident_id}/recovery/indicators/batch` (batch import for future automation), `GET /api/incidents/{incident_id}/recovery/community` (community-visible view per FR-037)
- [X] T052 [US5] Implement k-anonymity enforcement — Pydantic validator rejects Social environment sensitive indicators with `population_coverage < 10` per NFR-014/R-012, `data_classification` defaults to `"sensitive"` for health/employment social indicators
- [X] T053 [US5] Implement community-response indicator linkage for Total Warning System feedback loop — `linked_alert_id` on `RecoveryIndicator` references the originating `PublicAlert`, 24-hour SLA alerting when indicators not submitted after warning issuance per FR-012/SC-010/R-008
- [X] T054 [US5] Implement recovery-mode agent behaviour — Resource Allocation Agent prioritises reconstruction resources (FR-045 cross-ref), Communication Agent generates community-facing recovery updates aligned with six principles (FR-033), Monitoring Agent monitors recovery indicators for regression (edge case) in respective agent files per R-006
- [X] T055 [US5] Add content safety validation for LLM-generated recovery recommendations and community-facing content using existing content safety pipeline per NFR-013
- [X] T056 [US5] Implement graceful degradation for recovery dashboard — display last-known indicator values with staleness indicator when data sources unavailable per NFR-012/R-002
- [X] T057 [US5] Add observability metric `recovery_indicator_update_frequency` per NFR-010

**Checkpoint**: Recovery tracking fully operational — dashboard shows all 21 indicators across four environments, regression detected, community view available, social data privacy enforced (SC-005, SC-010)

---

## Phase 8: User Story 6 — Total Warning System Implementation (Priority: P2)

**Goal**: Platform implements all six elements of the Total Warning System (situational awareness, monitoring/prediction, message construction, interpretation, communication, community response) as an end-to-end warning lifecycle

**Independent Test**: Trace a single warning through all six elements — Monitoring Agent produces situational awareness → Risk Assessment Agent produces prediction → Communication Agent constructs/delivers message with interpretation aids → community-response indicators captured within 24 hours

**FRs**: FR-008–012 | **SCs**: SC-010

**Dependencies**: Requires US1 (warning generation) and US5 (community-response indicators) to be complete

### Implementation for User Story 6

- [X] T058 [US6] Extend Monitoring Agent in `apps/agents/monitoring/agent.py` to produce explicit situational-awareness output that feeds the Total Warning System monitoring-and-prediction element per FR-009/FR-043
- [X] T059 [US6] Extend Risk Assessment Agent in `apps/agents/risk_assessment/agent.py` to produce hazard prediction outputs that satisfy the monitoring-and-prediction element per FR-010/FR-044
- [X] T060 [US6] Ensure Communication Agent's message construction (US1) satisfies the message-construction and communication elements, with interpretation aids — plain language summaries, CALD translations, accessibility formats per FR-011
- [X] T061 [US6] Wire community-response indicator capture (US5) as the feedback-loop closure element — verify indicators link to originating warning via `linked_alert_id`, 24-hour SLA enforced per FR-012/SC-010

**Checkpoint**: Total Warning System fully connected — all six elements produce outputs that feed the next, community-response feedback loop closed within 24 hours (SC-010)

---

## Phase 9: User Story 7 — Lessons Management Framework (Priority: P3)

**Goal**: Platform provides structured lessons capture (auto-triggered for Level 2+ incidents and exercises), categorisation by AIIMS function/PPRR phase/severity, trend analysis, assignment tracking, PR quality gate verification, and contradictory-lesson handling

**Independent Test**: Complete a simulation exercise → capture lessons with AIIMS/PPRR categorisation → assign to responsible parties → analyse trends → verify PR quality gate links resolution back to lesson

**FRs**: FR-038–042, FR-052 | **NFRs**: NFR-005, NFR-006, NFR-008, NFR-011 | **SCs**: SC-007

### Implementation for User Story 7

- [X] T062 [P] [US7] Create lessons service with lesson CRUD, auto-trigger logic (Level 2+ closure or exercise completion creates lessons-capture event), AIIMS/PPRR categorisation, assignment tracking with target resolution dates, trend analysis engine (recurring themes, unresolved items, by-function/by-phase breakdown), and SC-007 closure rate tracking (90% within 90 days) in `apps/api/app/services/lessons_service.py` per R-007
- [X] T063 [US7] Create lessons API routes in `apps/api/app/api/routes/lessons.py` per lessons-api.yaml — `POST /api/lessons` (capture, ≤5s per NFR-005), `GET /api/lessons` (register with filtering), `GET /api/lessons/{lesson_id}` (detail), `PUT /api/lessons/{lesson_id}/assign` (assignment per FR-041), `PUT /api/lessons/{lesson_id}/resolve` (resolution with PR reference), `PUT /api/lessons/{lesson_id}/flag-contradictory` (edge case), `GET /api/lessons/trends` (trend analysis ≤30s per NFR-006), `GET /api/lessons/verify-pr` (quality gate verification per FR-042)
- [X] T064 [US7] Implement exercise-to-lesson linkage — connect lessons captured from exercises to `ExerciseReport` via `scenario_run_id`, enabling correlation with exercise performance metrics (`coordination_gaps`, `benchmark_comparison`) per FR-052
- [X] T065 [US7] Implement contradictory-lesson handling — flag lessons that contradict existing agent config, require escalated IC/admin approval before resolution, link conflicting config and lesson for audit per edge case spec
- [X] T066 [US7] Implement PR quality gate CI script — lightweight GitHub Actions check that verifies PR descriptions referencing lesson IDs match open lessons in the register per FR-042/R-007
- [X] T067 [US7] Implement graceful degradation for lessons — buffer lessons locally when register/Cosmos unavailable, sync on recovery, ensure incident operations not blocked by lessons subsystem failures per NFR-011/R-002
- [X] T068 [US7] Add observability metrics `lesson_resolution_time` per NFR-010

**Checkpoint**: Lessons management fully operational — auto-capture after Level 2+ incidents and exercises, trend analysis surfaces recurring themes, PR quality gate enforces lesson-linked changes (SC-007)

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span multiple user stories, NFR compliance verification, and final integration

### Graceful Degradation Verification

- [X] T069 [P] Verify graceful degradation for all AIDR capabilities per R-002/Constitution NN-5 — AWS warnings (template fallback), AIIMS (static mapping fallback), PPRR (queue transitions), evacuation (circuit breaker), recovery (staleness indicator), lessons (local buffer) — ensure no single service failure blocks platform operation

### Existing Spec Alignment (FR-043–047)

- [X] T070 [P] Update Monitoring Agent spec (010) to include AIDR-aligned warning classifications, escalation thresholds, and explicit Total Warning System situational-awareness role per FR-043
- [X] T071 [P] Update Risk Assessment Agent spec (012) to align hazard-severity scales with AIDR guidance and explicit monitoring-and-prediction role per FR-044
- [X] T072 [P] Update Resource Allocation Agent in `apps/agents/resource_allocation/agent.py` to use AIDR/AIIMS-aligned prioritisation language and support recovery-phase resource allocation mode per FR-045
- [X] T073 [P] Update disaster response hub spec (001) to reference AIIMS functional structure, PPRR lifecycle, and Shared Responsibility Model per FR-046
- [X] T074 [P] Add AIIMS role mapping section to all agent specifications identifying which AIIMS function each agent fulfils per FR-047/SC-008

### Health Endpoints and Observability

- [X] T075 [P] Add health endpoints for each new AIDR capability (AIIMS service, PPRR service, recovery service, lessons service) responding ≤1s per NFR-009
- [X] T076 Verify all seven telemetry metrics are emitted correctly — `warning_compliance_rate`, `tier_transition_latency`, `evacuation_stage_duration`, `recovery_indicator_update_frequency`, `lesson_resolution_time`, `pprr_phase_transition_count`, `aiims_role_coverage_ratio` per NFR-010

### Data Sovereignty and Interoperability

- [X] T077 [P] Verify all AIDR data (warnings, recovery, lessons, evacuation, PPRR) resides exclusively in Azure Australia East and Australia Southeast per NFR-015/Constitution NN-2
- [X] T078 [P] Ensure all new FastAPI endpoints expose OpenAPI schemas (built-in) and verify GeoJSON format usage for location data in warnings, evacuation zones, and recovery areas per R-009/Constitution NN-4

### Final Validation

- [X] **T080** [P] [US1] Implement EDXL-DE message envelope serialiser for warning delivery pipeline per R-009/Constitution NN-4 — serialize PublicAlert with AWS fields to EDXL-DE XML format, add endpoint `GET /api/alerts/{alert_id}/edxl`, include contract test in `tests/contract/test_edxl_contract.py` (`apps/agents/communication/edxl_serialiser.py`)
- [X] **T081** [P] Create contract tests for all 6 API contracts validating request/response schemas against YAML definitions (`tests/contract/test_warning_contract.py`, `tests/contract/test_aiims_contract.py`, `tests/contract/test_evacuation_contract.py`, `tests/contract/test_pprr_contract.py`, `tests/contract/test_recovery_contract.py`, `tests/contract/test_lessons_contract.py`)
- [X] **T082** [P] Create integration tests for 5 Cosmos DB containers verifying CRUD operations, partition key routing, and TTL policies (`tests/integration/test_aidr_cosmos.py`)
- [X] **T083** [P] Create simulation scenario tests validating end-to-end AIDR flows: bushfire escalation (AWS → evacuation), cyclone multi-stage evacuation, flood PPRR lifecycle, post-disaster recovery tracking (`tests/simulation/test_aidr_scenarios.py`)
- [X] **T084** [P] Create benchmark tests validating NFR-001–008 performance and concurrency targets: warning generation ≤2s, AIIMS assignment ≤5s, PPRR transition ≤5s, evacuation stage ≤3s, ≥10 concurrent recovery ops, ≥50 concurrent lessons (`tests/benchmark/test_aidr_performance.py`)

### Final Validation

- [X] T079 Run `specs/018-aidr-guidance-integration/quickstart.md` validation end-to-end to confirm developer onboarding path works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T002–T003 for Cosmos containers) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — T005 (PublicAlert extension), T014 (warning compliance), T015 (handoffs)
- **US2 (Phase 4)**: Depends on Foundational — T007 (AiimsRoleAssignment), T012 (AIIMS mapping)
- **US3 (Phase 5)**: Depends on Foundational — T008 (EvacuationStage), T014 (warning compliance for evacuation warnings)
- **US4 (Phase 6)**: Depends on Foundational — T004 (Incident pprr_phase), T011 (PprrPhaseContext), T013 (PPRR lifecycle)
- **US5 (Phase 7)**: Depends on Foundational — T009 (RecoveryEnvironmentTracker), T015 (handoffs)
- **US6 (Phase 8)**: Depends on US1 (warning generation) AND US5 (community-response indicators)
- **US7 (Phase 9)**: Depends on Foundational — T010 (Lesson), T015 (handoffs); benefits from US2 (AIIMS for categorisation) and US4 (PPRR for categorisation)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Independence Matrix

| Story | Can Start After | Independent of | Integrates With |
|-------|----------------|----------------|-----------------|
| US1 (AWS Warnings) | Phase 2 | US2, US3, US4, US5, US7 | US3 (evacuation warnings), US6 (TWS) |
| US2 (AIIMS) | Phase 2 | US1, US3, US4, US5 | US7 (lessons categorisation) |
| US3 (Evacuation) | Phase 2 | US2, US4, US5, US7 | US1 (evacuation warnings via Communication Agent) |
| US4 (PPRR) | Phase 2 | US1, US2, US3 | US5 (recovery phase), US7 (lessons categorisation) |
| US5 (Recovery) | Phase 2 | US1, US2, US3, US7 | US4 (PPRR recovery phase), US6 (TWS feedback) |
| US6 (Total Warning System) | US1 + US5 | US2, US3, US4, US7 | US1 (warnings), US5 (indicators) |
| US7 (Lessons) | Phase 2 | US1, US3, US5 | US2 (AIIMS categorisation), US4 (PPRR categorisation) |

### Within Each User Story

- Models before services (Phase 2 models must be done)
- Services before API routes
- Core implementation before graceful degradation
- Graceful degradation before observability
- Story complete and independently testable before moving to next priority

### Parallel Opportunities

- **Phase 2**: All domain model tasks (T004–T011) can run in parallel — different files
- **Phase 2**: All shared utility tasks (T012–T014) can run in parallel — different files
- **Phase 3–5 (P1 stories)**: US1, US2, US3 can start in parallel after Phase 2 completes
- **Phase 6–7 (P2 stories)**: US4, US5 can start in parallel after Phase 2; US7 can start in parallel
- **Phase 10**: Most polish tasks can run in parallel — different concerns

---

## Parallel Example: Phase 2 (Foundational)

```text
# All domain model tasks in parallel (different files):
T004: Extend Incident model in packages/domain/src/domain/models/incident.py
T005: Extend PublicAlert model in packages/domain/src/domain/models/public_alert.py
T006: Extend HandoffChainDefinition in packages/domain/src/domain/models/handoff_chain.py
T007: Create AiimsRoleAssignment in packages/domain/src/domain/models/aiims_role_assignment.py
T008: Create EvacuationStage in packages/domain/src/domain/models/evacuation_stage.py
T009: Create RecoveryEnvironmentTracker in packages/domain/src/domain/models/recovery_environment_tracker.py
T010: Create Lesson in packages/domain/src/domain/models/lesson.py
T011: Create PprrPhaseContext in packages/domain/src/domain/models/pprr_phase_context.py

# All shared utilities in parallel (different files):
T012: AIIMS mapping in apps/agents/common/aiims_mapping.py
T013: PPRR lifecycle in apps/agents/common/pprr_lifecycle.py
T014: Warning compliance in apps/agents/common/warning_compliance.py
```

## Parallel Example: P1 User Stories (after Phase 2)

```text
# Three P1 stories can proceed simultaneously with separate developers:
Developer A (US1): T017–T026 (AWS warnings — Communication Agent + warning API)
Developer B (US2): T027–T033 (AIIMS — AIIMS service + AIIMS API)
Developer C (US3): T034–T041 (Evacuation — Evacuation Agent + evacuation API)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational — focus on T005, T014, T015, T016 (warning-critical subset)
3. Complete Phase 3: User Story 1 (T017–T026)
4. **STOP and VALIDATE**: Simulate a bushfire escalation (Advice → Watch and Act → Emergency Warning → de-escalation → all-clear) and verify SC-001 + SC-006
5. Deploy/demo if ready — the platform now generates AWS-compliant warnings

### Incremental Delivery

1. **Setup + Foundational** → All domain models and infrastructure ready
2. **US1 (AWS Warnings)** → Test independently → Deploy (MVP: compliant warnings)
3. **US2 (AIIMS)** → Test independently → Deploy (incidents have AIIMS structure)
4. **US3 (Evacuation)** → Test independently → Deploy (five-stage evacuation operational)
5. **US4 (PPRR)** → Test independently → Deploy (full lifecycle support)
6. **US5 (Recovery)** → Test independently → Deploy (recovery tracking live)
7. **US6 (TWS)** → Test independently → Deploy (end-to-end warning system)
8. **US7 (Lessons)** → Test independently → Deploy (continuous improvement)
9. **Polish** → All cross-cutting validations → Final release

### Parallel Team Strategy

With three developers after Foundational:

1. Team completes Setup + Foundational together
2. Sprint 1 (P1 stories in parallel):
   - Developer A: US1 (AWS Warnings)
   - Developer B: US2 (AIIMS)
   - Developer C: US3 (Evacuation)
3. Sprint 2 (P2 stories in parallel):
   - Developer A: US4 (PPRR) + US6 (TWS — after US1 and US5 done)
   - Developer B: US5 (Recovery)
   - Developer C: US7 (Lessons)
4. Sprint 3: Polish (all together)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Constitution requirements (NN-1 through NN-5) are non-negotiable — every task must satisfy them
- All Pydantic models use `Literal[...]` unions (no `Enum` classes), string IDs, and `Field(default_factory=...)` for mutable defaults
- Existing `create_app()` factory pattern and FastAPI router conventions must be followed
- All data must reside in Azure Australia East / Australia Southeast (NFR-015)
