# Tasks: AIDR Additional Guidance Integration

**Input**: Design documents from `/specs/019-aidr-additional-guidances/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — the spec defines a comprehensive test tier (unit, contract, integration, simulation) with explicit test files in the project structure.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Domain models**: `packages/domain/src/domain/models/`
- **Seed data**: `packages/domain/src/domain/seed/recovery-catalogue/`
- **Planning Agent**: `apps/agents/planning/`
- **Monitoring Agent**: `apps/agents/monitoring/`
- **Common agent infra**: `apps/agents/common/`
- **Platform API**: `apps/api/app/`
- **Infrastructure**: `infra/modules/`
- **Tests**: `tests/{unit,contract,integration,simulation}/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding, IaC, and agent skeleton — everything needed before domain logic.

- [X] T001 Create Planning Agent directory structure with `__init__.py` in `apps/agents/planning/`
- [X] T002 Create `apps/agents/planning/config.py` with frozen `PlanningConfig` dataclass reading `PLAN_GENERATION_TIMEOUT_SECONDS`, `PLAN_REVIEW_REMINDER_DAYS`, `AGENT_VERSION` from env vars (per quickstart.md pattern)
- [X] T003 Create `apps/agents/planning/__main__.py` with uvicorn entrypoint on port 8085 (R-012)
- [X] T004 Create `apps/agents/planning/agent.py` with `PlanningAgent` class stub and `create_app()` factory returning FastAPI app with `GET /health` endpoint (per quickstart.md pattern)
- [X] T005 [P] Create Bicep module `infra/modules/emergency-planning.bicep` defining 3 new Cosmos containers: `emergency-plans` (partition `/region_id`), `recovery-programmes` (partition `/incident_id`), `recovery-catalogue` (partition `/domain`) with composite indexes and autoscale max 1000 RU/s (R-003, data-model.md §Cosmos DB Container Summary)
- [X] T006 [P] Extend `infra/main.bicep` to reference the new `emergency-planning` module, passing `cosmosDbName` and `cosmosAccountName` parameters
- [X] T007 [P] Create seed data directory `packages/domain/src/domain/seed/recovery-catalogue/` with placeholder `__init__.py` or `.gitkeep`

**Checkpoint**: Planning Agent skeleton responds to `GET /health`, Bicep validates, seed directory exists.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain models, catalogue seed data, repositories, and shared agent infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Domain Models (all [P] — independent files)

- [X] T008 [P] Extend `RecoveryIndicator` in `packages/domain/src/domain/models/recovery_environment_tracker.py` — add optional `catalogue_indicator_id: str | None = None` field with regex validator for `aidr:{domain}:{outcome-slug}:ind:{index}` pattern (E-001, FR-015, R-011)
- [X] T009 [P] Create `packages/domain/src/domain/models/emergency_plan.py` — `EmergencyPlan` model with 7-state `PlanLifecycleState`, `PlanHierarchyLevel`, `SecurityRating` type aliases, nested `PlanSection`, `PlanActivationRecord`, `PlanAmendment` models, 27 section slugs constant, `planning_principles_checklist` with 8-key validation, model validators for endorsed_by/endorsed_at state requirements (N-001)
- [X] T010 [P] Create `packages/domain/src/domain/models/planning_process_record.py` — `PlanningProcessRecord` with 9-step tracking, nested `StepCompletion`, `TeamMember`, `EngagementEntry`, `EndorsementApproval` models (N-002)
- [X] T011 [P] Create `packages/domain/src/domain/models/me_framework.py` — `MEFramework` model with `EvaluationDomain`, `RecoveryDomain`, `ObjectiveType` type aliases, nested `SelectedOutcome`, `SuccessStandard`, `CollectionSchedule` models, framework lifecycle status (N-003)
- [X] T012 [P] Create `packages/domain/src/domain/models/program_logic_model.py` — `ProgramLogicModel` with ex_ante/ex_post model types, nested `LogicElement`, `FinalOutcome`, `OutcomeChainLink` models, outcome chain link validation (N-004)
- [X] T013 [P] Create `packages/domain/src/domain/models/recovery_outcome.py` — `RecoveryOutcome`, `CatalogueActivity`, `CatalogueIndicator` models with hierarchical ID scheme `aidr:{domain}:{outcome-slug}[:act|:ind:{index}]` (N-005)
- [X] T014 [P] Create `packages/domain/src/domain/models/evaluation_report.py` — `EvaluationReport` with nested `DomainFinding`, `Finding`, `Recommendation`, `DisseminationRecord` models, content_safety_result requirement for ai_assisted reports (N-006)

### Catalogue Seed Data (all [P] — independent JSON files)

- [X] T015 [P] Create `packages/domain/src/domain/seed/recovery-catalogue/overarching.json` — ~7 overarching outcomes with nested activities and indicators using hierarchical ID scheme (R-004)
- [X] T016 [P] Create `packages/domain/src/domain/seed/recovery-catalogue/social.json` — ~24 social domain outcomes with activities and indicators (FR-016)
- [X] T017 [P] Create `packages/domain/src/domain/seed/recovery-catalogue/economic.json` — ~19 economic domain outcomes with activities and indicators (FR-017)
- [X] T018 [P] Create `packages/domain/src/domain/seed/recovery-catalogue/built.json` — ~5 built environment outcomes with activities and indicators (FR-018)
- [X] T019 [P] Create `packages/domain/src/domain/seed/recovery-catalogue/natural.json` — ~6 natural environment outcomes with activities and indicators (FR-019)
- [X] T020 [P] Create `packages/domain/src/domain/seed/recovery-catalogue/evaluation-questions.json` — standard KEQ questions per evaluation domain from AIDR M&E Framework §5.2 (FR-011)

### Seed Loader Extension

- [X] T021 Extend `scripts/seed_loader.py` to load `recovery-catalogue/*.json` into the `recovery-catalogue` Cosmos container, upserting by hierarchical ID with `domain` partition key (~561 documents total) (R-004)

### Cosmos DB Repositories (all [P] — independent files)

- [X] T022 [P] Create `apps/api/app/repositories/emergency_plan_repository.py` — Cosmos DB repository for `emergency-plans` container with CRUD, query by region_id, filter by lifecycle_state/hierarchy_level/hazard_type, plan hierarchy queries
- [X] T023 [P] Create `apps/api/app/repositories/me_framework_repository.py` — Cosmos DB repository for `recovery-programmes` container with CRUD for MEFramework, ProgramLogicModel, EvaluationReport documents
- [X] T024 [P] Create `apps/api/app/repositories/recovery_catalogue_repository.py` — Cosmos DB repository for `recovery-catalogue` container with browse-by-domain, get-by-ID, activity/indicator lookups, domain summaries

### Shared Agent Infrastructure

- [X] T025 Extend `apps/agents/common/handoffs.py` — add `build_plan_activation_handoff()` and `build_me_framework_handoff()` handoff builders following existing `build_handoff()` pattern (quickstart.md §Agent Handoff Pattern, R-010)
- [X] T026 Create `apps/agents/common/plan_activation.py` — plan↔incident linking logic for plan activation during incidents and recovery transition (FR-007, FR-029, R-008)

### Plan Lifecycle State Machine

- [X] T027 Create `apps/agents/planning/plan_lifecycle.py` — `VALID_PLAN_TRANSITIONS` dict, `TRANSITION_ROLES` dict, `validate_plan_transition()` function returning `(bool, str)` following `common/pprr_lifecycle.py` pattern (R-002, FR-006, quickstart.md §State Machine Pattern)

### Unit Tests for Foundational Models

- [X] T028 [P] Create `tests/unit/test_emergency_plan.py` — test EmergencyPlan model validation: 7 lifecycle states, 27 section slugs, 8 planning principles, endorsed_by requirement for endorsed+ states, hazard_types non-empty, PlanActivationRecord/PlanAmendment nesting, catalogue_indicator_id regex on extended RecoveryIndicator
- [X] T029 [P] Create `tests/unit/test_planning_process_record.py` — test 9-step process tracking, step completion validation, team member/engagement entry nesting, endorsement approval records
- [X] T030 [P] Create `tests/unit/test_me_framework.py` — test MEFramework model: evaluation domain validation (5 KEQ domains), selected outcomes with community restatements, success standards referencing selected outcomes, collection schedule overdue detection
- [X] T031 [P] Create `tests/unit/test_recovery_outcome.py` — test catalogue models: hierarchical ID format validation, RecoveryDomain 5-value type, RecoveryOutcome/CatalogueActivity/CatalogueIndicator relationships, domain-partitioned structure
- [X] T032 [P] Create `tests/unit/test_evaluation_report.py` — test EvaluationReport: 5 KEQ domain findings, content_safety_result requirement for ai_assisted, evaluation period validation, DomainFinding/Finding/Recommendation nesting
- [X] T033 [P] Create `tests/unit/test_plan_lifecycle.py` — test all valid state transitions (8 transitions + system superseded), invalid transition rejection, role authorization enforcement per TRANSITION_ROLES, edge cases (superseded is terminal, activated requires incident_id)

**Checkpoint**: All 7 domain models pass unit tests, seed data loads, repositories initialise, state machine validates all transitions. Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Emergency Planning Guidance for Preparedness (Priority: P1) 🎯 MVP

**Goal**: Emergency planners can develop, document, and maintain AIDR-compliant emergency plans through the 9-step planning process with 27 plan sections, 8 planning principles, and plan hierarchy.

**Independent Test**: Initiate a new emergency plan for a simulated flood-prone region, step through each planning process phase, verify AIDR-compliant outputs with risk analysis, stakeholder engagement records, and all 27 plan documentation elements.

### Contract Tests for US1

- [X] T034 [P] [US1] Create `tests/contract/test_planning_api_contract.py` — contract tests for all Planning Agent endpoints: POST /plans, GET /plans/{id}, GET /plans, PUT /plans/{id}/sections/{slug}, POST /plans/{id}/transition, POST /plans/{id}/activate, GET /plans/by-region/{region_id}/hierarchy, PUT /plans/{id}/process/steps/{step}, GET /plans/{id}/completeness, GET /health

### Implementation for US1

- [X] T035 [P] [US1] Create `apps/agents/planning/models.py` — request/response Pydantic models for planning endpoints: CreatePlanRequest, PlanSummaryResponse, PlanTransitionRequest, PlanTransitionResponse, PlanActivationRequest, PlanActivationResponse, PlanCompletenessResponse, UpdateSectionRequest, UpdateStepRequest, PlanHierarchyResponse
- [X] T036 [P] [US1] Create `apps/agents/planning/telemetry.py` — planning-specific metrics: `emergency_plan_activation_count` counter, `plan_currency_compliance_ratio` gauge, `plan_section_completeness` gauge (NFR-007, R-013)
- [X] T037 [P] [US1] Create `apps/agents/planning/audit.py` — planning decision audit record helpers for state transitions, section edits, and endorsement decisions (FR-006, Constitution §IV)
- [X] T038 [US1] Create `apps/agents/planning/risk_assessment.py` — multi-environment risk analysis across 4 environments (social, built, economic, natural) supporting cascading, concurrent, and catastrophic scenarios (FR-003)
- [X] T039 [US1] Create `apps/agents/planning/pipeline.py` — emergency plan assembly pipeline: input validation → 27-section content assembly → 8-principle completeness check → output formatting (JSON + optional PDF), ≤15s target (NFR-001, R-007)
- [X] T040 [US1] Wire full Planning Agent in `apps/agents/planning/agent.py` — integrate plan_lifecycle, pipeline, risk_assessment, audit, telemetry; add all CRUD endpoints (POST /plans, GET /plans/{id}, GET /plans, PUT sections, POST transition, GET completeness), process step endpoints (PUT steps/{step_number}), plan hierarchy endpoint (GET by-region/{region_id}/hierarchy) per planning-api.yaml contract
- [X] T041 [US1] Create `apps/api/app/services/emergency_plan_service.py` — plan lifecycle business logic: create plan with PlanningProcessRecord, update sections (only in editable states), validate and execute transitions via plan_lifecycle.py, plan hierarchy tree building, completeness scoring
- [X] T042 [US1] Create `apps/api/app/api/routes/emergency_plans.py` — Platform API routes for emergency plan CRUD, lifecycle transitions, hierarchy views delegating to emergency_plan_service and emergency_plan_repository
- [X] T043 [US1] Create `tests/integration/test_emergency_plans_cosmos.py` — integration tests: plan persistence round-trip in Cosmos, lifecycle state transition persistence, plan hierarchy queries by region, section update persistence, PlanningProcessRecord co-storage

**Checkpoint**: Emergency plans can be created, edited section-by-section, transitioned through 7 lifecycle states with role authorization, viewed in regional hierarchies — all AIDR-compliant. US1 is independently testable.

---

## Phase 4: User Story 2 — Monitoring and Evaluation for Recovery Programs (Priority: P1)

**Goal**: Recovery Coordinators can set up M&E frameworks for recovery programs — select outcomes, build program logic, define success standards, establish collection schedules, and generate monitoring reports and evaluation reports across 5 KEQ domains.

**Independent Test**: Create a simulated bushfire recovery program, configure its M&E framework with selected outcomes and program logic, collect sample indicator data, verify monitoring and evaluation reports with appropriate standards of success.

### Contract Tests for US2

- [X] T044 [P] [US2] Create `tests/contract/test_me_framework_api_contract.py` — contract tests for M&E endpoints: POST /me-framework, GET /me-framework, POST /outcomes, POST /program-logic, POST /standards, POST /collection-schedule, GET /monitoring-report, POST /evaluation

### Implementation for US2

- [X] T045 [P] [US2] Extend `apps/agents/monitoring/models.py` — add M&E request/response models: CreateMEFrameworkRequest, SelectOutcomesRequest, CreateProgramLogicRequest, SetStandardsRequest, SetCollectionScheduleRequest, MonitoringReportResponse, EvaluationReportResponse
- [X] T046 [P] [US2] Extend `apps/agents/monitoring/config.py` — add M&E config parameters: `MAX_CONCURRENT_ME_FRAMEWORKS`, `INDICATOR_STALENESS_DAYS`, `AI_ANALYSIS_TIMEOUT_SECONDS`, `CATALOGUE_CACHE_TTL_SECONDS`
- [X] T047 [US2] Create `apps/agents/monitoring/me_framework_service.py` — M&E framework lifecycle: create framework linked to incident, select outcomes from AIDR catalogue with auto-suggested indicators/activities, build program logic, define standards of success, manage collection schedules with overdue detection (FR-008–013)
- [X] T048 [US2] Create `apps/agents/monitoring/evaluation_service.py` — evaluation report generation across 5 KEQ domains: pull indicator data, assess against standards, generate domain findings with evidence references, produce recommendations, support ai_assisted and manual modes, content safety validation for AI content (FR-014, SC-009)
- [X] T049 [US2] Extend `apps/agents/monitoring/agent.py` — add M&E framework endpoints and catalogue lookup routes to existing monitoring agent `create_app()` factory
- [X] T050 [US2] Create `apps/api/app/services/me_framework_service.py` — Platform API business logic: create M&E framework, outcome selection with catalogue validation, program logic CRUD, standards management, collection schedule management, monitoring report generation, evaluation report generation
- [X] T051 [US2] Create `apps/api/app/api/routes/me_frameworks.py` — Platform API routes for M&E framework CRUD and all sub-resource endpoints per me-framework-api.yaml contract
- [X] T052 [US2] Create `tests/integration/test_me_framework_cosmos.py` — integration tests: M&E framework persistence, outcome selection round-trip, program logic storage, evaluation report generation and storage in `recovery-programmes` container

**Checkpoint**: M&E frameworks can be configured, outcomes selected from AIDR catalogue, program logic built, standards defined, monitoring reports generated, evaluation reports produced across 5 KEQ domains. US2 is independently testable.

---

## Phase 5: User Story 3 — Outcomes-Based Recovery Tracking Across Four Domains (Priority: P1)

**Goal**: Recovery Coordinators can browse the full AIDR outcomes-activities-indicators catalogue across all 5 domains, select outcomes for tracking, link catalogue indicators to spec 018 tracker indicators, and separately track sustainability vs resilience objectives including disaggregated tracking for vulnerable populations.

**Independent Test**: Configure a cyclone recovery with outcomes from each domain, enter sample indicator data, verify tracking of sustainability and resilience objectives with AIDR activities linked to each outcome.

### Contract Tests for US3

- [X] T053 [P] [US3] Create `tests/contract/test_recovery_catalogue_contract.py` — contract tests for catalogue endpoints: GET /outcomes, GET /outcomes/{id}, GET /outcomes/{id}/activities, GET /outcomes/{id}/indicators, GET /domains/{domain}/summary, POST /suggest-activities, GET /evaluation-questions/{domain}

### Implementation for US3

- [X] T054 [US3] Create `apps/agents/monitoring/catalogue_service.py` — AIDR catalogue lookup service: browse outcomes by domain/objective_type, get outcome detail with activities and indicators, domain summaries, suggest activities for lagging indicators (catalogue-matched, optionally AI-enriched), evaluation question lookup (FR-015–024, FR-026)
- [X] T055 [US3] Create `apps/api/app/services/recovery_catalogue_service.py` — Platform API catalogue business logic: catalogue browsing, domain filtering, outcome detail with nested activities/indicators, activity suggestion for lagging indicators, catalogue seed status verification
- [X] T056 [US3] Create `apps/api/app/api/routes/recovery_catalogue.py` — Platform API routes for catalogue browsing, outcome detail, activity/indicator listing, domain summaries, activity suggestions, evaluation questions per recovery-catalogue-api.yaml contract
- [X] T057 [US3] Create `tests/unit/test_catalogue_service.py` — unit tests: catalogue lookup, domain filtering, activity suggestion matching, hierarchical ID parsing, domain summary computation
- [X] T058 [US3] Create `tests/integration/test_recovery_catalogue_cosmos.py` — integration tests: catalogue seeding verification (~561 docs), per-domain queries, outcome→activity→indicator traversal, domain summary accuracy

**Checkpoint**: Full AIDR catalogue browsable by domain, outcomes with activities and indicators accessible, activity suggestions for lagging indicators, sustainability/resilience separation working. US3 is independently testable.

---

## Phase 6: User Story 4 — AI-Assisted Indicator Analysis and Recommendations (Priority: P2)

**Goal**: AI-powered cross-domain correlation analysis, activity recommendations for lagging indicators, and natural-language community-facing recovery summaries — all with content safety validation.

**Independent Test**: Populate a recovery scenario with mixed indicator data, request AI analysis, verify cross-domain correlations, activity recommendations from AIDR catalogue, and coherent natural-language summaries.

### Implementation for US4

- [X] T059 [P] [US4] Create `apps/agents/monitoring/indicator_analysis.py` — AI-assisted cross-domain correlation analysis: query indicator data across domains, compute trend comparisons, send structured prompts to Azure OpenAI via LLMCallMixin, generate correlation descriptions and recommendations, all outputs through ContentSafetyValidator (FR-025–028, R-006)
- [X] T060 [US4] Create `apps/api/app/services/ai_analysis_service.py` — Platform API AI analysis business logic: cross-domain correlation endpoint, activity recommendation generation (catalogue-matched + LLM rationale), community-facing summary generation, content safety pipeline integration, graceful degradation when LLM unavailable
- [X] T061 [US4] Create `apps/api/app/api/routes/ai_analysis.py` — Platform API routes: POST /analysis/cross-domain, POST /analysis/recommendations, POST /analysis/community-summary per ai-analysis-api.yaml contract
- [X] T062 [US4] Create `tests/unit/test_indicator_analysis.py` — unit tests: cross-domain correlation logic, trend comparison algorithms, recommendation matching, content safety integration mock, graceful degradation (LLM unavailable, insufficient data)

**Checkpoint**: AI analysis identifies cross-domain correlations, recommends AIDR activities for lagging indicators, generates community-friendly summaries. Content safety validated. US4 is independently testable.

---

## Phase 7: User Story 5 — Emergency Plan Integration with Incident Response (Priority: P2)

**Goal**: Incident Controllers can activate pre-existing emergency plans during incidents, surface documented arrangements during response, link to recovery program M&E frameworks, and trigger post-event review.

**Independent Test**: Create an emergency plan, simulate a flood event, activate the plan, verify plan content surfaced during response with role assignments, resource triggers, and post-event review flagging.

### Implementation for US5

- [X] T063 [US5] Implement plan activation endpoint in `apps/agents/planning/agent.py` — POST /plans/{id}/activate: validate endorsed state, link to incident via PlanActivationRecord, surface response arrangements/roles/resources/communication, handle edge case of activation during revision (activate last endorsed version) (FR-007, SC-008)
- [X] T064 [US5] Wire plan activation handoff in `apps/agents/planning/agent.py` — consume `planning-handoffs` Service Bus queue for plan activation requests from incident management, produce handoffs to monitoring agent for M&E framework init when recovery arrangements activated (R-010)
- [X] T065 [US5] Extend `apps/agents/planning/agent.py` — add post-event review trigger: when incident concludes, flag plan for review, transition activated→post_event_review, create new draft version with original→superseded, link lessons to lessons management (FR-029, FR-033)
- [X] T066 [US5] Extend `apps/api/app/api/routes/emergency_plans.py` — add incident-linked plan lookup: given an incident in a region, identify and present relevant emergency plans with activation recommendations

**Checkpoint**: Plans activate during incidents, surface operational content in ≤10s, post-event review triggers correctly, M&E handoff fires for recovery transition. US5 is independently testable.

---

## Phase 8: User Story 6 — Program Logic Model Builder (Priority: P3)

**Goal**: Program designers can build and visualise program logic models mapping resources → activities → outputs → intermediate outcomes → final outcomes, supporting both ex ante and ex post approaches with AIDR catalogue linking.

**Independent Test**: Use the builder to create a program logic for a sample recovery program, verify resource→activity→output→outcome chains align with AIDR national structure.

### Implementation for US6

- [X] T067 [US6] Enhance program logic endpoints in `apps/api/app/api/routes/me_frameworks.py` — add ex post program logic support: reverse-engineer logic from existing program, trace from final outcomes back through intermediates to actual activities/resources, validate outcome chain link integrity (FR-010)
- [X] T068 [US6] Add program logic validation in `apps/api/app/services/me_framework_service.py` — validate outcome chain completeness (all elements connected), sustainability vs resilience final outcome separation, catalogue linkage for activities and outcomes, timeline projection validation

**Checkpoint**: Program logic models can be created (ex ante) and reverse-engineered (ex post), validated for AIDR compliance, with full catalogue linking. US6 is independently testable.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration, edge cases, telemetry, and cross-story validation.

- [X] T069 [P] Extend `apps/agents/monitoring/agent.py` telemetry — add M&E metrics: `me_framework_completion_rate`, `recovery_indicator_collection_rate`, `outcome_achievement_rate` gauges (NFR-007, R-013)
- [X] T070 [P] Extend stakeholder engagement continuity — link planning agent stakeholder engagement records (PlanningProcessRecord.stakeholder_engagement_log) to community-led recovery approach requirements in monitoring agent (FR-032)
- [X] T071 [P] Wire M&E evaluation lessons into lessons management system — evaluation report recommendations feed into existing lessons service (spec 018 FR-038–042) via lessons handoff (FR-033)
- [X] T072 [P] Handle edge case: overlapping recovery programs — support linking programs to shared indicator data while maintaining separate program logic and evaluation reports (spec edge case)
- [X] T073 [P] Handle edge case: indicator data unavailable/delayed — display last-known value with staleness indicator (`INDICATOR_STALENESS_DAYS`), flag gap in monitoring reports, allow reason recording (spec edge case)
- [X] T074 [P] Handle edge case: recovery outcome regression after program closure — flag regression, assess sustainability threshold compromise, recommend program reactivation consideration (spec edge case)
- [X] T075 [P] Handle edge case: conflicting standards of success across stakeholders — support multiple standards per indicator with stakeholder_label, present progress against each standard separately (spec edge case)
- [X] T076 [P] Handle edge case: plan hierarchy conflicts — flag inconsistencies between local and state plans during documentation, reference AIDR guidance on consistent terminology (spec edge case)
- [X] T077 Create `tests/simulation/test_planning_me_scenarios.py` — end-to-end simulation: create emergency plan → step through 9-step process → endorse → activate during incident → transition to recovery → set up M&E framework → select AIDR outcomes → collect indicators → run AI analysis → generate evaluation report → feed lessons back
- [X] T078 Run quickstart.md validation — verify all code patterns from quickstart.md (create_app factory, config pattern, entrypoint, state machine, seed data format, handoff pattern, testing pattern) are correctly implemented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 Emergency Planning (Phase 3)**: Depends on Phase 2 — specifically T009, T010, T027, T022
- **US2 M&E Framework (Phase 4)**: Depends on Phase 2 — specifically T011, T012, T014, T023, T024
- **US3 Recovery Catalogue (Phase 5)**: Depends on Phase 2 — specifically T013, T015–T021, T024
- **US4 AI Analysis (Phase 6)**: Depends on Phase 2 + Phase 5 (catalogue service) — specifically T054
- **US5 Plan–Incident Integration (Phase 7)**: Depends on Phase 3 (planning agent complete) — specifically T040
- **US6 Program Logic Builder (Phase 8)**: Depends on Phase 4 (M&E framework) — specifically T050, T051
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories; can run in parallel with US1
- **US3 (P1)**: Can start after Phase 2 — no dependencies on other stories; can run in parallel with US1 and US2
- **US4 (P2)**: Depends on US3 (catalogue service for activity recommendations) — start after T054
- **US5 (P2)**: Depends on US1 (planning agent must be wired) — start after T040
- **US6 (P3)**: Depends on US2 (M&E framework service) — start after T050

### Within Each User Story

- Contract tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints/routes
- Core implementation before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 2 domain model tasks (T008–T014) can run in parallel (7 independent files)
- All Phase 2 seed data tasks (T015–T020) can run in parallel (6 independent JSON files)
- All Phase 2 repository tasks (T022–T024) can run in parallel (3 independent files)
- All Phase 2 unit tests (T028–T033) can run in parallel (6 independent test files)
- US1, US2, US3 can all start in parallel after Phase 2 completes (3 independent P1 stories)
- Within US1: T035, T036, T037 can run in parallel (models, telemetry, audit — independent files)
- Within US2: T045, T046 can run in parallel (models, config — independent files)

---

## Parallel Example: Phase 2 Domain Models

```bash
# Launch all 7 domain model tasks together:
Task T008: "Extend RecoveryIndicator in recovery_environment_tracker.py"
Task T009: "Create EmergencyPlan model in emergency_plan.py"
Task T010: "Create PlanningProcessRecord model in planning_process_record.py"
Task T011: "Create MEFramework model in me_framework.py"
Task T012: "Create ProgramLogicModel model in program_logic_model.py"
Task T013: "Create catalogue models in recovery_outcome.py"
Task T014: "Create EvaluationReport model in evaluation_report.py"
```

## Parallel Example: P1 User Stories (after Phase 2)

```bash
# Developer A: US1 — Emergency Planning
Task T034: "Contract tests for planning API"
Task T035: "Planning Agent request/response models"
... through T043

# Developer B: US2 — M&E Framework
Task T044: "Contract tests for M&E framework API"
Task T045: "M&E request/response models"
... through T052

# Developer C: US3 — Recovery Catalogue
Task T053: "Contract tests for catalogue API"
Task T054: "Catalogue service"
... through T058
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001–T007)
2. Complete Phase 2: Foundational — focus on T008–T010, T022, T027–T029, T033 (emergency plan subset)
3. Complete Phase 3: US1 Emergency Planning (T034–T043)
4. **STOP and VALIDATE**: Test US1 independently — create plan, step through process, transition lifecycle
5. Deploy/demo: Planning Agent on port 8085, emergency plans in Cosmos

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready
2. + US1 (Emergency Planning) → MVP! Test and deploy
3. + US2 (M&E Framework) → Recovery evaluation capability. Test independently
4. + US3 (Recovery Catalogue) → AIDR catalogue browsable. Test independently
5. + US4 (AI Analysis) → Intelligent insights. Requires US3
6. + US5 (Plan–Incident Integration) → Operational plan activation. Requires US1
7. + US6 (Program Logic Builder) → Advanced M&E tooling. Requires US2
8. + Phase 9 (Polish) → Edge cases, simulation tests, cross-cutting concerns

### Parallel Team Strategy

With 3 developers after Phase 2:

1. Team completes Phase 1 + Phase 2 together
2. Once Phase 2 is done:
   - **Developer A**: US1 (Emergency Planning) → then US5 (Plan–Incident Integration)
   - **Developer B**: US2 (M&E Framework) → then US6 (Program Logic Builder)
   - **Developer C**: US3 (Recovery Catalogue) → then US4 (AI Analysis)
3. All converge for Phase 9 (Polish & Cross-Cutting)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Write contract tests first (FAIL) → then implement → tests PASS
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Domain models use `Literal[]` unions — never `Enum` classes (quickstart.md convention)
- All IDs are strings — no integer or UUID type fields
- Existing `RecoveryEnvironment` 4-value type preserved; new `RecoveryDomain` 5-value type for catalogue
- Total catalogue seed data: ~561 documents across 5 domains + evaluation questions
