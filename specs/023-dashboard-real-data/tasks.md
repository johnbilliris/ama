# Tasks: Governance Dashboard Real Data Integration

**Input**: Design documents from `/specs/023-dashboard-real-data/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/dashboard-api.md ✅, quickstart.md ✅

**Tests**: Included — pytest unit tests and contract tests as specified in the feature requirements.

**Organization**: Tasks grouped by user story (6 stories from spec.md, P1–P6). Each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **API**: `apps/api/app/` (FastAPI backend)
- **Domain/Seed**: `packages/domain/src/domain/seed/` (shared models and seed data)
- **Web**: `apps/web/src/` (Next.js frontend)
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup

**Purpose**: Branch creation and recovery catalogue seed extension — the only structural change required before any user story work.

- [ ] T001 Create feature branch `023-dashboard-real-data` from main
- [ ] T002 Extend `bootstrap_seed_data()` to load recovery catalogue (5 domain JSON files) into a `recovery_catalogue` dict key in `packages/domain/src/domain/seed/bootstrap.py` (per RT-001 in research.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create `GovernanceDataService` skeleton and wire dependency injection so ALL user stories can delegate to it. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `GovernanceDataService` class skeleton with constructor (`seed_data: dict`, optional `governance_repo`) and pre-indexed seed lookups (`_frameworks_by_id`, `_orgs_by_id`) in `apps/api/app/services/governance_data_service.py` (per data-model.md class design)
- [ ] T004 Add FastAPI dependency function `get_seed_data()` using `SeedService.load()` in `apps/api/app/api/routes/governance_dashboard.py` and inject via `Depends()` into all 13 route functions (replacing module-level `_aggregation` singleton per RT-008)
- [ ] T005 Refactor `DashboardAggregationService.__init__()` to accept `GovernanceDataService` as a constructor parameter alongside existing `health_service` and `governance_repo` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T006 Update all 13 route functions in `apps/api/app/api/routes/governance_dashboard.py` to construct `GovernanceDataService` from injected seed data and pass it to `DashboardAggregationService` constructor

- [ ] T006a [P] Add optional `data_source_type: str | None` metadata field (values: "stored", "seed_fallback", "computed") to relevant Pydantic response models in `apps/api/app/models/governance_health.py` — additive only, defaults to None for backward compatibility (FR-005, finding C1)
- [ ] T006b [P] Update TypeScript types in `apps/web/src/lib/api/governance.ts` to include optional `dataSourceType?: string` on response interfaces (FR-005/FR-024, finding C1/C3)

**Checkpoint**: Foundation ready — `GovernanceDataService` exists, DI is wired, aggregation service accepts real data service. All existing tests must still pass (stubs remain until replaced per-story).

---

## Phase 3: User Story 1 — Accurate Health Score from Real Inputs (Priority: P1) 🎯 MVP

**Goal**: Replace hardcoded health score inputs so the composite score (constitutional 40%, readiness 25%, data source 20%, recovery 15%) derives from real seed/stored data. The executive summary endpoint returns trustworthy metrics.

**Independent Test**: Load `/governance/dashboard/summary` and verify each health score component returns values derived from actual seed data (46 data sources, 49 organisations, 27 frameworks, 5 recovery domains), not static constants.

### Tests for User Story 1

> **Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Unit test for `compute_constitutional_gates()` — verify 10 gates returned, status derived from assessment records when present, "assessment_pending" when absent, `is_current=True` filter applied (FR-028) in `tests/unit/test_governance_data_service.py`
- [ ] T008 [P] [US1] Unit test for `compute_data_source_stats()` — verify counts map seed `status` field (available→compliant, degraded→partially_compliant, offline→non_compliant) from 46 data sources in `tests/unit/test_governance_data_service.py`
- [ ] T009 [P] [US1] Unit test for health score integration — verify `get_executive_summary()` returns non-hardcoded values (constitutional_gates count=10, risk_summary derived, resource_utilisation != 72.5 stub) in `tests/unit/test_dashboard_aggregation.py`
- [ ] T010 [P] [US1] Contract test for `GET /governance/dashboard/summary` — verify response schema matches `ExecutiveSummaryResponse`, `health_score.dimensions` has 4 entries, `constitutional_gates` has 10 entries, field types unchanged in `tests/contract/test_governance_dashboard_contract.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `compute_constitutional_gates(tenant_id)` in `apps/api/app/services/governance_data_service.py` — query stored `ConstitutionalAssessment` (is_current=True), map 6 principles to 10 gates per RT-007 mapping, infer unmapped gates from seed data presence
- [ ] T012 [P] [US1] Implement `compute_data_source_stats(tenant_id)` in `apps/api/app/services/governance_data_service.py` — count seed data sources by status field (available/degraded/offline → compliant/partially_compliant/non_compliant)
- [ ] T013 [P] [US1] Implement `compute_readiness_inputs(tenant_id)` in `apps/api/app/services/governance_data_service.py` — compute `exercise_completion_rate`, `role_coverage_pct` from org AIIMS functions, `plan_currency_pct` from stored plans or 0.0 (simplified inputs for health score only)
- [ ] T014 [P] [US1] Implement `compute_recovery_inputs(tenant_id)` in `apps/api/app/services/governance_data_service.py` — compute `has_active_recovery` from stored trackers, `domains` summary from recovery catalogue (simplified inputs for health score only)
- [ ] T015 [US1] Replace `_get_constitutional_gates()` stub with delegation to `GovernanceDataService.compute_constitutional_gates()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T016 [US1] Replace `_get_data_source_stats()` stub (hardcoded total:10/compliant:7/partially_compliant:2) with delegation to `GovernanceDataService.compute_data_source_stats()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T017 [US1] Replace `_get_readiness_inputs()` stub (hardcoded 75/85/80) with delegation to `GovernanceDataService.compute_readiness_inputs()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T018 [US1] Replace `_get_recovery_inputs()` stub (hardcoded False) with delegation to `GovernanceDataService.compute_recovery_inputs()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T019 [US1] Replace `_get_risk_severity_counts()` stub (hardcoded 2/5/12/8) with delegation to `GovernanceDataService.compute_risk_severity()` for the executive summary `risk_summary` field in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T020 [US1] Replace `_get_active_incident_count()` stub (hardcoded 1) with query against stored incidents or 0 in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T021 [US1] Replace `_get_resource_utilisation()` stub (hardcoded 72.5) with computation from organisation data or 0.0 in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T022 [US1] Update `get_executive_summary()` in `apps/api/app/services/dashboard_aggregation_service.py` to pass all real inputs to `HealthScoreService.calculate()` — verify health_score algorithm receives structured seed data, not static values

**Checkpoint**: `GET /governance/dashboard/summary` returns a health score computed from real seed data. Each of the 4 dimensions reflects actual system state. All contract tests pass with unchanged response structure.

---

## Phase 4: User Story 2 — Real Operational Readiness View (Priority: P2)

**Goal**: Replace hardcoded operational readiness data so PPRR distribution, AIIMS coverage, emergency plans, capability gaps, and volunteer readiness derive from real framework assignments (123), organisations (49), and frameworks (27).

**Independent Test**: Load `/governance/dashboard/readiness` and verify PPRR phase counts match framework assignment records, AIIMS coverage reflects 6 functions across 49 organisations, plan counts come from stored records or zeros.

### Tests for User Story 2

- [ ] T023 [P] [US2] Unit test for `compute_pprr_distribution()` — verify 4 PPRR phases returned with counts derived from joining 123 assignments to 27 frameworks in `tests/unit/test_governance_data_service.py`
- [ ] T024 [P] [US2] Unit test for `compute_aiims_role_coverage()` — verify 6 AIIMS functions returned with coverage percentages from 49 organisations' `aiims_functions` in `tests/unit/test_governance_data_service.py`
- [ ] T025 [P] [US2] Unit test for `compute_volunteer_readiness()` — verify metrics count organisations with `workforce_type` in [volunteer, mixed], jurisdiction distribution, and capability coverage in `tests/unit/test_governance_data_service.py`
- [ ] T026 [P] [US2] Unit test for `compute_capability_gaps()` — verify gaps identified by comparing framework `hazard_types` against org `primary_capabilities` per jurisdiction in `tests/unit/test_governance_data_service.py`
- [ ] T027 [P] [US2] Contract test for `GET /governance/dashboard/readiness` — verify response schema matches `OperationalReadinessResponse`, `pprr_phases` has 4 entries, field types unchanged in `tests/contract/test_governance_dashboard_contract.py`

### Implementation for User Story 2

- [ ] T028 [P] [US2] Implement `compute_pprr_distribution(tenant_id)` in `apps/api/app/services/governance_data_service.py` — join `framework_assignments` to `frameworks` by `framework_id`, aggregate `pprr_phases` counts, return exactly 4 `PPRRPhaseStatus` entries
- [ ] T029 [P] [US2] Implement `compute_aiims_role_coverage(tenant_id)` in `apps/api/app/services/governance_data_service.py` — aggregate `aiims_functions` across 49 organisations for all 6 AIIMS functions (Control, Planning, Intelligence, Public Information, Operations, Logistics)
- [ ] T030 [P] [US2] Implement `compute_emergency_plan_summaries(tenant_id)` in `apps/api/app/services/governance_data_service.py` — query stored `EmergencyPlan` records grouped by 7 lifecycle states, return zero-count summaries when no plans exist
- [ ] T031 [P] [US2] Implement `compute_volunteer_readiness(tenant_id)` in `apps/api/app/services/governance_data_service.py` — filter organisations by `workforce_type` in [volunteer, mixed], compute count, jurisdiction distribution, capability coverage
- [ ] T032 [P] [US2] Implement `compute_capability_gaps(tenant_id)` in `apps/api/app/services/governance_data_service.py` — per jurisdiction: compare framework `hazard_types` requirements against org `primary_capabilities` to identify unmet capabilities (per RT-009 heuristic)
- [ ] T033 [US2] Replace `_get_emergency_plan_summaries()` stub (fixed 7 states × 3 each) with delegation to `GovernanceDataService.compute_emergency_plan_summaries()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T034 [US2] Replace `_get_role_coverage()` stub (fixed 10 custom roles) with delegation to `GovernanceDataService.compute_aiims_role_coverage()` returning 6 AIIMS functions in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T035 [US2] Wire real PPRR, AIIMS, plans, volunteer readiness, and capability gaps into `get_operational_readiness()` in `apps/api/app/services/dashboard_aggregation_service.py` — replace all hardcoded sections with `GovernanceDataService` calls

**Checkpoint**: `GET /governance/dashboard/readiness` returns PPRR distribution from 123 real assignments, AIIMS coverage for 6 real functions, emergency plan counts from stored records, capability gaps from real comparisons, and volunteer metrics from 24 volunteer/mixed organisations.

---

## Phase 5: User Story 3 — Real Recovery Progress View (Priority: P3)

**Goal**: Replace hardcoded recovery data so all 5 domains (overarching, social, economic, built, natural) derive from recovery catalogue seed data with actual outcome/activity/indicator counts and 0% baseline completion when no active trackers exist.

**Independent Test**: Load `/governance/dashboard/recovery` and verify 5 domains returned (was 4 hardcoded), domain breakdowns match recovery catalogue structure, completion shows 0% baseline or real tracker progress.

### Tests for User Story 3

- [ ] T036 [P] [US3] Unit test for `compute_recovery_domains()` — verify 5 domains returned from recovery catalogue with correct outcome/activity/indicator counts per domain, 0% completion baseline without trackers in `tests/unit/test_governance_data_service.py`
- [ ] T037 [P] [US3] Unit test for `compute_recovery_domain_detail()` — verify social domain returns 24 outcomes, 57 activities, 53 indicators matching catalogue structure in `tests/unit/test_governance_data_service.py`
- [ ] T038 [P] [US3] Contract test for `GET /governance/dashboard/recovery` — verify response matches `RecoveryProgressResponse`, `domains` length ≤5, `domain` values in Literal union, field types unchanged in `tests/contract/test_governance_dashboard_contract.py`

### Implementation for User Story 3

- [ ] T039 [P] [US3] Implement `compute_recovery_domains(tenant_id, incident_id)` in `apps/api/app/services/governance_data_service.py` — iterate 5 catalogue domains, count outcomes/activities/indicators per domain, merge active tracker progress when present, return 0% baseline otherwise
- [ ] T040 [P] [US3] Implement `compute_recovery_domain_detail(domain, tenant_id)` in `apps/api/app/services/governance_data_service.py` — return detailed outcomes with activities and indicators from catalogue, merge tracker data for completion rates
- [ ] T041 [US3] Replace `_has_active_recovery()` stub (always True) with delegation to `GovernanceDataService` checking stored recovery trackers in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T042 [US3] Replace `_get_recovery_domains()` stub (4 hardcoded domains with fake percentages) with delegation to `GovernanceDataService.compute_recovery_domains()` returning up to 5 domains in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T043 [US3] Wire real data into `get_recovery_progress()` and `get_recovery_domain_detail()` in `apps/api/app/services/dashboard_aggregation_service.py` — replace all hardcoded recovery sections with `GovernanceDataService` calls

**Checkpoint**: `GET /governance/dashboard/recovery` returns 5 domains from real catalogue data. `GET /governance/dashboard/recovery/social` returns actual counts (24 outcomes, 57 activities, 53 indicators). Domain count increased from 4→5 (overarching now populated). Contract tests confirm response structure unchanged.

---

## Phase 6: User Story 4 — Real Risk & Warning View (Priority: P4)

**Goal**: Replace hardcoded risk data so severity counts derive from stored hazard assessments (zero when none exist), top risks from real records ranked by severity/confidence, and AWS principle compliance from data source trust tier analysis.

**Independent Test**: Load `/governance/dashboard/risk` and verify severity counts come from stored `HazardAssessment` records (or all zeros if none exist), not the hardcoded extreme:2/high:5/medium:12/low:8 distribution.

### Tests for User Story 4

- [ ] T044 [P] [US4] Unit test for `compute_risk_severity()` — verify zero counts when no hazard assessments exist (FR-017), correct grouping by severity_level when assessments present in `tests/unit/test_governance_data_service.py`
- [ ] T045 [P] [US4] Unit test for `compute_top_risks()` — verify ranking by severity then confidence, empty list when no assessments in `tests/unit/test_governance_data_service.py`
- [ ] T046 [P] [US4] Unit test for `compute_aws_compliance()` — verify 10 AWS principles computed from data source trust tier configurations in `tests/unit/test_governance_data_service.py`
- [ ] T047 [P] [US4] Contract test for `GET /governance/dashboard/risk` — verify response matches `RiskWarningResponse`, `risk_severity` has 5 fields (extreme/high/medium/low/total), field types unchanged in `tests/contract/test_governance_dashboard_contract.py`

### Implementation for User Story 4

- [ ] T048 [P] [US4] Implement `compute_risk_severity(tenant_id)` in `apps/api/app/services/governance_data_service.py` — query stored `HazardAssessment` records grouped by `severity_level`, return `RiskSeverityBreakdown` with zero counts when none exist
- [ ] T049 [P] [US4] Implement `compute_top_risks(tenant_id)` in `apps/api/app/services/governance_data_service.py` — query stored `HazardAssessment` records ordered by severity_level desc then confidence_score desc, return ranked list
- [ ] T050 [P] [US4] Implement `compute_aws_compliance(tenant_id)` in `apps/api/app/services/governance_data_service.py` — analyse data source `trust_tier` alignment with 10 AWS warning system principles per existing `AWS_PRINCIPLES` constant
- [ ] T051 [US4] Replace `_get_risk_severity_breakdown()` stub (hardcoded total:27) with delegation to `GovernanceDataService.compute_risk_severity()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T052 [US4] Wire real top risks and AWS compliance into `get_risk_and_warning()` in `apps/api/app/services/dashboard_aggregation_service.py` — replace hardcoded top_risks list and principle_compliance with `GovernanceDataService` calls
- [ ] T053 [US4] Wire real data into `get_risk_detail()` in `apps/api/app/services/dashboard_aggregation_service.py` — return actual `HazardAssessment` record for the given risk_id or 404

**Checkpoint**: `GET /governance/dashboard/risk` returns zero severity counts when no hazard assessments exist, real counts when they do. AWS principle compliance derived from data source trust tiers. Contract tests pass.

---

## Phase 7: User Story 5 — Real Audit Trail (Priority: P5)

**Goal**: Replace hardcoded 3-event audit stub with actual stored `GovernanceAuditEntry` records. An empty audit trail when no actions have occurred is correct (per RT-010). Filtering and decision chain work on real records.

**Independent Test**: Query `GET /governance/dashboard/audit` and verify 0 events initially (not 3 fake events), then perform an auditable action and verify the entry appears with correct details.

### Tests for User Story 5

- [ ] T054 [P] [US5] Unit test for `query_audit_events()` — verify empty list when no entries exist, correct filtering by action_type/actor/date_range/keyword when entries present in `tests/unit/test_governance_data_service.py`
- [ ] T055 [P] [US5] Unit test for `query_decision_chain()` — verify actual linked events returned, None when event not found in `tests/unit/test_governance_data_service.py`
- [ ] T056 [P] [US5] Contract test for `GET /governance/dashboard/audit` — verify response matches `AuditTrailResponse`, events are `AuditEventSummary` type, total_count reflects actual count, field types unchanged in `tests/contract/test_governance_dashboard_contract.py`

### Implementation for User Story 5

- [ ] T057 [P] [US5] Implement `query_audit_events(tenant_id, date_from, date_to, actor, action_type, affected_entity, keyword)` in `apps/api/app/services/governance_data_service.py` — query stored `GovernanceAuditEntry` records with filters, return empty list when none exist
- [ ] T058 [P] [US5] Implement `query_decision_chain(event_id, tenant_id)` in `apps/api/app/services/governance_data_service.py` — find audit event by ID, traverse `related_entity_id` links to build decision chain, return None if not found
- [ ] T059 [US5] Wire real audit data into `search_audit_events()` in `apps/api/app/services/dashboard_aggregation_service.py` — replace hardcoded 3-event stub with delegation to `GovernanceDataService.query_audit_events()`
- [ ] T060 [US5] Wire real decision chain into `get_decision_chain()` in `apps/api/app/services/dashboard_aggregation_service.py` — replace hardcoded 2-step stub with delegation to `GovernanceDataService.query_decision_chain()`

**Checkpoint**: `GET /governance/dashboard/audit` returns actual stored entries (0 initially). Filtering by date, actor, action_type works on real records. Decision chain endpoint returns actual linked events. Contract tests pass.

---

## Phase 8: User Story 6 — Reliable Compliance Matrix with Seed Fallback (Priority: P6)

**Goal**: Replace the compliance matrix that silently falls back to empty with a matrix that uses stored constitutional assessments when available and falls back to seed-derived baselines (10 gates × 46 data sources) when not. Mixed scenarios (some assessed, some not) display both with distinction.

**Independent Test**: Load `/governance/dashboard/compliance` without stored assessments — verify seed-derived baseline entries for all data sources appear (not empty). Load with stored assessments — verify real assessment results used.

### Tests for User Story 6

- [ ] T061 [P] [US6] Unit test for `compute_compliance_entries()` — verify seed-derived baseline when no assessments exist (10 gates × N sources), real assessments used when present, mixed scenario handled correctly in `tests/unit/test_governance_data_service.py`
- [ ] T062 [P] [US6] Contract test for `GET /governance/dashboard/compliance` — verify response matches `ComplianceMatrixResponse`, entry structure matches `ComplianceMatrixEntry`, pagination fields present in `tests/contract/test_governance_dashboard_contract.py`

### Implementation for User Story 6

- [ ] T063 [US6] Implement `compute_compliance_entries(tenant_id)` in `apps/api/app/services/governance_data_service.py` — query stored `ConstitutionalAssessment` records (is_current=True), generate seed-derived baseline for unassessed data sources, merge real + baseline entries
- [ ] T064 [US6] Replace `_build_compliance_entries()` stub with delegation to `GovernanceDataService.compute_compliance_entries()` in `apps/api/app/services/dashboard_aggregation_service.py`
- [ ] T065 [US6] Wire real data into `get_compliance_matrix()` and `get_compliance_detail()` in `apps/api/app/services/dashboard_aggregation_service.py` — compliance matrix uses real entries, detail view returns actual assessment history for specific data source

**Checkpoint**: `GET /governance/dashboard/compliance` returns entries for all registered data sources (up to 46) instead of empty. Assessed sources show real results. Unassessed sources show seed baseline. Contract tests pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Comprehensive validation, edge case handling, and documentation

- [ ] T066 [P] Add edge case handling for partial seed data loading (organisations loaded but frameworks missing) — each `GovernanceDataService` method must independently handle missing seed keys with graceful degradation in `apps/api/app/services/governance_data_service.py`
- [ ] T067 [P] Add edge case handling for malformed/missing recovery catalogue domain files — remaining domains must still display, missing domain reported as unavailable in `apps/api/app/services/governance_data_service.py`
- [ ] T068 [P] Add edge case handling for seed loading failure — return graceful error responses (503) instead of crashing, per spec edge cases in `apps/api/app/api/routes/governance_dashboard.py`
- [ ] T069 [P] Add edge case handling for superseded constitutional assessments — ensure only `is_current=True` assessments factor into health score and compliance matrix (FR-028) in `apps/api/app/services/governance_data_service.py`
- [ ] T070 Verify `lru_cache` consistency — ensure `SeedService.load()` resolves `seed_root` path consistently across all routes to avoid cache misses (per quickstart.md pitfall #6) in `apps/api/app/api/routes/governance_dashboard.py`
- [ ] T071 [P] Update existing unit tests in `tests/unit/test_dashboard_aggregation.py` to assert real data values instead of hardcoded stubs (executive summary non-static values, readiness counts from seed, recovery 5 domains)
- [ ] T072 [P] Update existing contract tests in `tests/contract/test_governance_dashboard.py` to validate dashboard summary, audit trail filtering, and gap detection against real data patterns
- [ ] T073 [P] Fix stale field name assertions in `tests/contract/test_governance_dashboard_contract.py` — update `entries` vs `events`, `roles`/`widgets`/`refresh_interval_ms` references to match current Pydantic models
- [ ] T074 [P] Update integration tests in `tests/integration/test_governance_dashboard_api.py` to assert real data in API responses (if file exists; create if not)
- [ ] T075 Run full test suite: `pytest tests/unit/test_governance_data_service.py tests/unit/test_dashboard_aggregation.py tests/contract/test_governance_dashboard.py tests/contract/test_governance_dashboard_contract.py -v` and verify all pass
- [ ] T076 Verify all 13 endpoints respond within 500ms p95 — run `pytest --benchmark` or equivalent with seed data loaded, 10 sequential requests per endpoint, assert p95 < 500ms (SC-007, finding A1)
- [ ] T077 Run quickstart.md validation — execute all test commands locally, then deploy: `azd deploy api --no-prompt && azd deploy web --no-prompt` (deployment is a manual CI step)
- [ ] T078 [P] Add tenant isolation test — create records for two tenants in `GovernanceDataService`, assert cross-tenant queries return zero results (FR-027, Constitution gate #2 data sovereignty, finding C4)
- [ ] T079 [P] Add frontend fallback indicators in `apps/web/src/components/governance/` — show "seed baseline" badge when `dataSourceType === 'seed_fallback'` on compliance matrix entries (FR-024, finding C3)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T002 bootstrap extension) — BLOCKS all user stories
- **User Stories (Phases 3–8)**: All depend on Phase 2 completion (T003–T006 skeleton + DI wiring)
  - User stories CAN proceed in parallel (they modify different methods in GovernanceDataService)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5 → P6)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories. Provides health score foundation.
- **US2 (P2)**: Can start after Phase 2 — Independent of US1. Readiness view is separate from health score view.
- **US3 (P3)**: Can start after Phase 2 — Independent. Recovery catalogue data loaded in Phase 1 (T002).
- **US4 (P4)**: Can start after Phase 2 — Independent. Risk data comes from stored HazardAssessment records.
- **US5 (P5)**: Can start after Phase 2 — Independent. Audit data comes from stored GovernanceAuditEntry records.
- **US6 (P6)**: Can start after Phase 2 — Independent. Compliance uses seed data sources + stored assessments.

> **Note (C2 resolution)**: FR-019 (audit write path) is already implemented in `governance_registry.py` via `_record_audit()`. The dashboard audit trail endpoint reads these existing records. No new write-path tasks are needed — the governance registry creates `GovernanceAuditEntry` records for data source changes, assessments, and approvals.

> **Note**: US1 replaces `_get_risk_severity_counts()` for the executive summary's `risk_summary` field (T019). US4 replaces `_get_risk_severity_breakdown()` for the full risk view (T051). These are different stubs in the same file but do not conflict — US1's replacement feeds the summary endpoint; US4's replacement feeds the risk detail endpoint.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- `GovernanceDataService` methods before `DashboardAggregationService` stub replacements
- Stub replacements before view method wiring
- Story complete before moving to next priority

### Parallel Opportunities

- All test tasks (T007–T010, T023–T027, T036–T038, T044–T047, T054–T056, T061–T062) can run in parallel within their story
- All `GovernanceDataService` method implementations within a story marked [P] can run in parallel (different methods, same file — no conflict if each adds a new method)
- Different user stories can be worked on in parallel by different developers (each touches distinct GovernanceDataService methods and distinct DashboardAggregationService helpers)
- Phase 9 polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Phase 3)

```bash
# Launch all tests for US1 together (they FAIL initially):
Task: T007 — Unit test compute_constitutional_gates() in tests/unit/test_governance_data_service.py
Task: T008 — Unit test compute_data_source_stats() in tests/unit/test_governance_data_service.py
Task: T009 — Unit test health score integration in tests/unit/test_dashboard_aggregation.py
Task: T010 — Contract test GET /summary in tests/contract/test_governance_dashboard_contract.py

# Launch all GovernanceDataService implementations together:
Task: T011 — compute_constitutional_gates() in governance_data_service.py
Task: T012 — compute_data_source_stats() in governance_data_service.py
Task: T013 — compute_readiness_inputs() in governance_data_service.py
Task: T014 — compute_recovery_inputs() in governance_data_service.py

# Then sequentially wire stub replacements (same file, overlapping regions):
Task: T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022
```

## Parallel Example: User Stories 2–4 (Phases 4–6)

```bash
# After Phase 2 completes, three developers can work simultaneously:
Developer A (US2): T023–T035 (readiness view)
Developer B (US3): T036–T043 (recovery view)
Developer C (US4): T044–T053 (risk view)
# No conflicts — each touches unique GovernanceDataService methods and unique aggregation helpers
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T006)
3. Complete Phase 3: User Story 1 (T007–T022)
4. **STOP and VALIDATE**: Health score endpoint returns real data, contract tests pass
5. Deploy: `azd deploy api && azd deploy web`

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Health score real → Deploy (MVP!)
3. Add US2 → Readiness real → Deploy
4. Add US3 → Recovery real → Deploy
5. Add US4 → Risk real → Deploy
6. Add US5 → Audit real → Deploy
7. Add US6 → Compliance real → Deploy
8. Polish → Full validation → Final deploy

### Parallel Team Strategy

With 3 developers:

1. Team completes Setup + Foundational together (T001–T006)
2. Once Foundational is done:
   - Developer A: US1 (P1 — health score) then US5 (P5 — audit)
   - Developer B: US2 (P2 — readiness) then US6 (P6 — compliance)
   - Developer C: US3 (P3 — recovery) then US4 (P4 — risk)
3. All reconvene for Phase 9 Polish

---

## Notes

- [P] tasks = different files or different methods, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- `HealthScoreService.calculate()` algorithm is NOT changed — only the inputs passed to it
- `ConstitutionalPrinciple` enum is NOT extended — unmapped gates are inferred from seed data
- Audit trail is correctly empty initially — no seed fabrication (RT-010)
- Recovery domain count increases from 4→5 — `overarching` was always in Literal type
- Response model field names are NOT changed — backward compatibility guaranteed (FR-025)
- `lru_cache` on seed loading ensures O(1) subsequent access — no performance risk
- Commit after each task or logical group; stop at any checkpoint to validate independently
