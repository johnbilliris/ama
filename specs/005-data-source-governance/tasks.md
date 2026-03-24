# Tasks: Data Source Identification, Constitutional Review, and Governance Assignment

**Input**: Design documents from `/specs/005-data-source-governance/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi-governance.yaml, quickstart.md

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in every description

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Extend existing monorepo with governance feature structure

- [X] T001 Create governance API route files in apps/api/app/api/data_sources.py and apps/api/app/api/governance.py with empty router stubs
- [X] T002 [P] Create governance service stubs in apps/api/app/services/governance_registry.py and apps/api/app/services/governance_cache.py
- [X] T003 [P] Create governance repository stub in apps/api/app/repositories/governance_repository.py
- [X] T004 [P] Create governance validator stub in apps/api/app/validators/governance_validators.py
- [X] T005 Register governance routers in apps/api/app/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain models, seed data, and shared infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Extend DataSource model with governance fields (sub_category, trust_tier, provider, collection_method, data_type, update_frequency, geographic_coverage, compliance_status, governance_status, grace_period_start, grace_period_end, deactivated_at, created_at, updated_at) in packages/domain/src/domain/models/data_source.py
- [X] T007 [P] Create ConstitutionalAssessment model in packages/domain/src/domain/models/constitutional_assessment.py
- [X] T008 [P] Create AgentGovernanceAssignment model in packages/domain/src/domain/models/agent_governance.py
- [X] T009 [P] Create HandoffChainDefinition and HandoffStep models in packages/domain/src/domain/models/handoff_chain.py
- [X] T010 [P] Create FunctionalDomainPrecedence model in packages/domain/src/domain/models/functional_domain_precedence.py
- [X] T011 [P] Create GovernanceAuditEntry model in packages/domain/src/domain/models/governance_audit.py
- [X] T012 Create data_sources_australia.json seed catalogue with all named Australian data sources (FR-001a) in packages/domain/src/domain/seed/data_sources_australia.json
- [X] T013 Extend bootstrap_seed_data() to include data_sources key loading data_sources_australia.json in packages/domain/src/domain/seed/bootstrap.py
- [X] T014 Implement governance repository with Cosmos DB data access for all governance entities in apps/api/app/repositories/governance_repository.py
- [X] T015 Implement governance validators for agent catalogue validation (FR-009c) and handoff chain continuity (FR-009) in apps/api/app/validators/governance_validators.py
- [X] T016 Implement GovernanceAuditEntry append-only write service within apps/api/app/services/governance_registry.py

**Checkpoint**: Foundation ready — all domain models exist, seed data loadable, repository and validators operational

---

## Phase 3: User Story 1 — Catalogue all data sources that feed the hub (Priority: P1) MVP

**Goal**: Deliver a complete, filterable data source registry with seed catalogue bootstrap, CRUD operations, and deactivation workflow

**Independent Test**: Load the catalogue, verify all Australian disaster-relevant data sources are listed with complete metadata, add a new source, filter by category, deactivate a source

### Implementation for User Story 1

- [X] T017 [US1] Implement data source registration endpoint (POST /data-sources) with validation and audit trail in apps/api/app/api/data_sources.py
- [X] T018 [US1] Implement data source listing endpoint (GET /data-sources) with filtering by kind, sub_category, trust_tier, compliance_status, governance_status, status, agent_name, geographic_coverage in apps/api/app/api/data_sources.py
- [X] T019 [US1] Implement single data source retrieval endpoint (GET /data-sources/{dataSourceId}) in apps/api/app/api/data_sources.py
- [X] T020 [US1] Implement data source update endpoint (PATCH /data-sources/{dataSourceId}) with audit trail in apps/api/app/api/data_sources.py
- [X] T021 [US1] Implement data source deactivation endpoint (POST /data-sources/{dataSourceId}/deactivate) with active-incident guard and audit trail in apps/api/app/api/data_sources.py
- [X] T022 [US1] Implement seed catalogue import function in governance registry service that loads data_sources_australia.json via bootstrap_seed_data() in apps/api/app/services/governance_registry.py
- [X] T023 [P] [US1] Create DataSourceTable component with filtering by kind, sub_category, trust_tier, status in apps/web/src/components/governance/DataSourceTable.tsx
- [X] T024 [US1] Write contract tests for data source CRUD, filtering, deactivation, and seed catalogue loading in tests/contract/test_data_source_registry.py

**Checkpoint**: Data source registry is fully functional — sources can be listed, added, updated, filtered, and deactivated; seed catalogue loads successfully

---

## Phase 4: User Story 2 — Review each data source against the Constitution (Priority: P2)

**Goal**: Deliver constitutional compliance assessments per principle, non-compliant source blocking, re-review workflows, and grace-period compliance lapsing

**Independent Test**: Select a registered data source, view its compliance assessment for all 6 principles, record an approval with conditions, verify a non-compliant source is blocked, test grace-period workflow

### Implementation for User Story 2

- [X] T025 [US2] Implement compliance profile retrieval endpoint (GET /data-sources/{dataSourceId}/compliance) returning current and historical assessments in apps/api/app/api/governance.py
- [X] T026 [US2] Implement constitutional assessment creation endpoint (POST /data-sources/{dataSourceId}/compliance) with principle-specific validation, supersession logic, is_current management, and audit trail in apps/api/app/api/governance.py
- [X] T027 [US2] Implement compliance-status derivation logic in governance registry service — aggregate per-principle assessments into source-level compliance_status (FR-006 blocking) in apps/api/app/services/governance_registry.py
- [X] T028 [US2] Implement re-review trigger on data source update (FR-012) in apps/api/app/services/governance_registry.py
- [X] T029 [US2] Implement constitution-amendment re-review trigger (FR-012a) that flags all existing assessments as requiring re-evaluation in apps/api/app/services/governance_registry.py
- [X] T030 [US2] Implement grace-period lifecycle for compliance-lapsed sources (FR-012b) — start grace period, configurable 72h default, auto-block on expiry in apps/api/app/services/governance_registry.py
- [X] T031 [US2] Implement grace-period management endpoint (POST /data-sources/{dataSourceId}/governance/grace-period) for extend and immediate-block overrides in apps/api/app/api/governance.py
- [X] T032 [P] [US2] Create ComplianceCard component displaying per-principle assessment with status, explanation, conditions, gaps in apps/web/src/components/governance/ComplianceCard.tsx
- [X] T033 [P] [US2] Create constitutional compliance view page at apps/web/src/app/governance/[dataSourceId]/compliance/page.tsx
- [X] T034 [US2] Write contract tests for assessment creation, supersession, compliance derivation, and non-compliant blocking in tests/contract/test_constitutional_compliance.py
- [X] T035 [US2] Write integration tests for re-review trigger (source change and constitution amendment) and grace-period lifecycle (start, warning, auto-block, extend, immediate-block) in tests/integration/test_governance_rereview.py and tests/integration/test_governance_grace_period.py

**Checkpoint**: Constitutional compliance workflow is complete — assessments recorded per principle, non-compliant sources blocked, re-review workflows operational, grace-period lifecycle enforced

---

## Phase 5: User Story 3 — Assign agent governance and define handoffs for each data source (Priority: P3)

**Goal**: Deliver agent assignment with primary/secondary roles, validated handoff chain definitions, shared-responsibility support, functional-domain precedence, and runtime handoff lookup with Redis caching

**Independent Test**: Assign an agent to a data source, define the handoff chain, verify chain validation against agent catalogue, test shared-responsibility assignment, verify handoff-chain lookup latency

### Implementation for User Story 3

- [X] T036 [US3] Implement agent governance retrieval endpoint (GET /data-sources/{dataSourceId}/governance) returning assignments and handoff chain in apps/api/app/api/governance.py
- [X] T037 [US3] Implement agent assignment endpoint (POST /data-sources/{dataSourceId}/governance/assignments) with agent catalogue validation, compliance gate (FR-006), primary/secondary role management, and audit trail in apps/api/app/api/governance.py
- [X] T038 [US3] Implement handoff chain definition endpoint (PUT /data-sources/{dataSourceId}/governance/handoff-chain) with chain continuity validation, agent catalogue validation, confidence threshold validation, and audit trail in apps/api/app/api/governance.py
- [X] T039 [US3] Implement functional-domain precedence endpoints (GET /governance/precedence and POST /governance/precedence) with jurisdictional inheritance logic in apps/api/app/api/governance.py
- [X] T040 [US3] Implement low-latency handoff-chain lookup endpoint (GET /governance/handoff-lookup) with Redis cache integration and X-Cache-Status header in apps/api/app/api/governance.py
- [X] T041 [US3] Implement Redis-backed governance cache service with configurable TTL (default 5 min), cache invalidation on governance mutations, hit/miss tracking, and fallback behavior (NFR-001–003) in apps/api/app/services/governance_cache.py
- [X] T042 [US3] Implement governance_status derivation logic — update source governance_status to assigned/fully_governed when assignments and chains are complete in apps/api/app/services/governance_registry.py
- [X] T043 [P] [US3] Create HandoffChainEditor component for defining handoff steps with source_agent, target_agent, confidence_threshold, category_filter in apps/web/src/components/governance/HandoffChainEditor.tsx
- [X] T044 [P] [US3] Create agent assignment view page at apps/web/src/app/governance/[dataSourceId]/assignments/page.tsx
- [X] T045 [US3] Write contract tests for agent assignment, handoff chain validation (valid + invalid chains), compliance gate, shared-responsibility, and functional-domain precedence in tests/contract/test_governance_assignment.py
- [X] T046 [US3] Write integration tests for governance cache TTL, cache hit/miss tracking, fallback to cached data on registry unavailability, and safe default routing in tests/integration/test_governance_cache.py

**Checkpoint**: Agent governance is complete — agents assigned to data sources, handoff chains validated and cached, precedence rules operational, handoff lookup returns in ≤50ms p95

---

## Phase 6: User Story 4 — View a consolidated data source governance dashboard (Priority: P4)

**Goal**: Deliver a single-page governance dashboard with summary counts, filtering, governance gap flagging, and drill-down to compliance and assignment views

**Independent Test**: Load the dashboard with a mix of compliant/non-compliant/assigned/unassigned sources, verify summary counts, apply filters, confirm governance gaps are flagged

### Implementation for User Story 4

- [X] T047 [US4] Implement governance dashboard endpoint (GET /governance/dashboard) with summary counts (total, compliant, partially_compliant, non_compliant, unassessed, compliance_lapsed, assigned, unassigned, fully_governed, rereview_pending) and filtered source list in apps/api/app/api/governance.py
- [X] T048 [US4] Implement governance gap detection logic (FR-014) — flag sources without assessments or without agent assignments in apps/api/app/services/governance_registry.py
- [X] T049 [US4] Implement audit trail retrieval endpoint (GET /data-sources/{dataSourceId}/audit) with action type and date range filters in apps/api/app/api/governance.py
- [X] T050 [P] [US4] Create GovernanceSummary component displaying total/compliant/non-compliant/assigned/unassigned/gap counts in apps/web/src/components/governance/GovernanceSummary.tsx
- [X] T051 [US4] Create governance dashboard page integrating GovernanceSummary, DataSourceTable with compliance/governance filters, and gap flagging indicators at apps/web/src/app/governance/page.tsx
- [X] T052 [US4] Write contract tests for dashboard summary counts, filtering by compliance_status/governance_status/kind/agent_name, governance gap flagging, and audit trail retrieval in tests/contract/test_governance_dashboard.py
- [X] T053 [US4] Write Playwright e2e tests for dashboard load, filtering, governance gap visual indicators, and drill-down navigation in tests/e2e/test_governance_dashboard.spec.ts

**Checkpoint**: Governance dashboard is complete — summary counts accurate, filters operational, governance gaps flagged, drill-down to compliance and assignment views works

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Observability, security hardening, and validation across all user stories

- [X] T054 [P] Implement structured observability signals (NFR-005) — registry query latency, cache hit/miss rate, governance-gap counts, grace-period expiry warnings, audit-trail write failures in apps/api/app/services/governance_registry.py
- [X] T055 [P] Implement role-based access control for governance endpoints (FR-015, FR-016) — governance leads/safety leads/architects for write operations, broader read access for dashboard in apps/api/app/api/governance.py and apps/api/app/api/data_sources.py
- [X] T056 Run quickstart.md scenario rehearsal steps 1–8 to validate end-to-end governance workflow
- [X] T057 Verify SC-001 through SC-006 measurable outcomes per spec.md success criteria

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — can start immediately after
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — benefits from US1–US3 being complete for full integration, but can start independently
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Phase 2 — no dependencies on other stories
- **User Story 2 (P2)**: Independent after Phase 2 — uses DataSourceRegistryEntry from Phase 2 models, does not require US1 API endpoints
- **User Story 3 (P3)**: Independent after Phase 2 — uses compliance_status from US2 models for compliance gate (FR-006), but the model exists in Phase 2
- **User Story 4 (P4)**: Aggregates data from US1–US3 — can be implemented with stub data but full integration requires US1–US3 endpoints

### Within Each User Story

1. Backend API endpoints first (service layer + routes)
2. Frontend components in parallel with API work (marked [P])
3. Contract/integration tests after implementation
4. Story checkpoint validation before proceeding

### Parallel Opportunities per User Story

**User Story 1**:
```
T017, T018, T019 ─── sequential (shared route file)
T023 ────────────── parallel with T017–T022 (different file: web component)
T024 ────────────── after T017–T022 (tests require implementation)
```

**User Story 2**:
```
T025, T026 ──────── sequential (shared route file)
T027–T031 ───────── sequential (shared service file, dependent logic)
T032, T033 ──────── parallel with T025–T031 (web components)
T034, T035 ──────── after T025–T031 (tests require implementation)
```

**User Story 3**:
```
T036–T040 ───────── sequential (shared route file)
T041 ────────────── parallel with T036–T040 (separate cache service file)
T043, T044 ──────── parallel with T036–T042 (web components)
T045, T046 ──────── after T036–T042 (tests require implementation)
```

**User Story 4**:
```
T047–T049 ───────── sequential (shared route file)
T050 ────────────── parallel with T047–T049 (web component)
T051 ────────────── after T050 + T047 (page integrates component + API)
T052, T053 ──────── after T047–T051 (tests require implementation)
```

---

## Implementation Strategy

### MVP Scope

User Story 1 (Phase 3) alone delivers a valuable, independently testable increment: a complete data source catalogue with seed data, filtering, and CRUD operations. This is the recommended MVP.

### Incremental Delivery

1. **MVP**: Phase 1 + Phase 2 + Phase 3 (Setup + Foundational + US1) — data source catalogue operational
2. **Increment 2**: Phase 4 (US2) — constitutional compliance layer added
3. **Increment 3**: Phase 5 (US3) — agent governance and handoff chains added
4. **Increment 4**: Phase 6 (US4) — consolidated dashboard added
5. **Final**: Phase 7 — observability, RBAC, and end-to-end validation
