# Tasks: Governance Dashboard

**Input**: Design documents from `/specs/021-governance-dashboard/`
**Prerequisites**: plan.md ✓, spec.md ✓, data-model.md ✓, contracts/ ✓, research.md ✓, quickstart.md ✓

**Tests**: Included — unit, integration, contract, and E2E tests are explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `apps/web/src/` (Next.js 16.2 + React 19 + TypeScript 5.8)
- **Backend**: `apps/api/app/` (FastAPI 0.115 + Pydantic 2.10)
- **Domain**: `packages/domain/src/domain/models/` (shared Pydantic models)
- **Shared UI**: `packages/ui/src/components/` (cross-app reusable widgets)
- **Tests**: `tests/` (pytest backend), `apps/web/` (Vitest frontend), `tests/e2e/` (Playwright)
- **Infrastructure**: `infra/` (Bicep IaC)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and install dependencies for the governance dashboard feature.

- [x] T001 Create directory structure for new dashboard files: `apps/web/src/app/governance/dashboard/`, `apps/web/src/app/governance/dashboard/compliance/`, `apps/web/src/app/governance/dashboard/audit/`, `apps/web/src/app/governance/dashboard/readiness/`, `apps/web/src/app/governance/dashboard/recovery/`, `apps/web/src/app/governance/dashboard/risk/`, `apps/web/src/components/governance/dashboard/`, `apps/web/src/components/governance/a11y/`, `packages/ui/src/components/governance/`
- [x] T002 [P] Add Python dependencies for audit export (ReportLab for PDF generation) to `apps/api/pyproject.toml` and run `uv sync`
- [x] T003 [P] Extend `apps/web/src/app/governance/page.tsx` to redirect to `/governance/dashboard` as the new default entry point

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain models, API infrastructure, shared UI, and frontend client that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Domain Models

- [x] T004 [P] Create GovernanceHealthScore, DimensionScore, and ConstitutionalGateStatus models in `packages/domain/src/domain/models/governance_health_score.py` per data-model.md — Pydantic BaseModel with Literal types, Field validation (score 0–100, 4 dimensions summing to weight 1.0, 10 gates, traffic light derivation)
- [x] T005 [P] Create RoleWidgetMapping, WidgetDefinition, and AIIMSRole Literal type in `packages/domain/src/domain/models/dashboard_widget_config.py` per data-model.md — 10 AIIMS roles, authority_rank 1–10, widget_type enum, refresh_group enum
- [x] T006 [P] Create AuditExportJob and ExportFormat models in `packages/domain/src/domain/models/audit_export.py` per data-model.md — state machine (queued → processing → complete | failed), download_url with 24h TTL, filter_params dict
- [x] T007 Extend GovernanceAuditEntry in `packages/domain/src/domain/models/governance_audit.py` to add 6 new dashboard action types to the GovernanceAction Literal ("dashboard_view", "dashboard_filter", "dashboard_search", "dashboard_export", "dashboard_drill_down", "dashboard_navigate_to_crud") and new optional fields (tenant_id, view_context, session_id)
- [x] T008 Extend DataSource model in `packages/domain/src/domain/models/data_source.py` to add next_assessment_due_date (datetime | None), governance_gap_count (int, ge=0), grace_period_expiry (datetime | None), grace_period_reason (str | None) fields

### Backend Infrastructure

- [x] T009 Create dashboard API response models (view models) in `apps/api/app/models/governance_health.py` — ExecutiveSummaryResponse, ComplianceMatrixResponse, ComplianceMatrixEntry, ComplianceDetailResponse, AuditTrailResponse, AuditEventSummary, AuditDecisionChainResponse, DecisionChainStep, OperationalReadinessResponse, PPRRPhaseStatus, EmergencyPlanSummary, AIIMSRoleCoverage, RecoveryProgressResponse, RecoveryDomainProgress, RecoveryDomainDetail, RiskWarningResponse, RiskSeverityBreakdown, AWSPrincipleCompliance, AlertComplianceMetrics, DashboardConfigResponse per data-model.md view models section
- [x] T010 [P] Create audit export request/response models in `apps/api/app/models/audit_export.py` — AuditExportRequest (format, filter_params, record_ids) and AuditExportJobResponse (id, status, download_url, progress) per OpenAPI contract
- [x] T011 Create governance dashboard router skeleton with all 13 endpoint stubs in `apps/api/app/api/routes/governance_dashboard.py` per OpenAPI contract — GET config, GET summary, GET compliance, GET compliance/{dataSourceId}, GET audit, GET audit/{eventId}/chain, POST audit/export, GET audit/export/{jobId}, GET readiness, GET recovery, GET recovery/{domain}, GET risk, GET risk/{riskId} (return 501 Not Implemented initially)
- [x] T012 Register governance dashboard router in `apps/api/app/api/router.py` under prefix `/governance/dashboard` with tags `["governance-dashboard"]`
- [x] T013 Extend tenant middleware in `apps/api/app/middleware/tenant_middleware.py` to create TenantContext FastAPI dependency that extracts tenant_id from Entra ID claims, defaults to "live" when no simulation claim present, and injects into request context for all dashboard endpoints
- [x] T014 Extend governance_repository in `apps/api/app/repositories/governance_repository.py` with dashboard query methods: get_health_inputs(), get_compliance_matrix(), search_audit_events(), get_readiness_data(), get_recovery_progress(), get_risk_data() — all with mandatory tenant_id parameter and Cosmos DB continuation token pagination
- [x] T015 Extend governance_cache in `apps/api/app/services/governance_cache.py` with dashboard-level cache keys per tenant_id, 5-minute TTL, and manual refresh bypass via Cache-Control: no-cache header detection
- [x] T016 [P] Extend governance validators in `apps/api/app/validators/governance_validators.py` with export filter validation (format enum, max record count) and audit search parameter validation (date ranges, action type enum)

### Frontend Infrastructure

- [x] T017 Create typed API client for all governance dashboard endpoints in `apps/web/src/lib/api/governance.ts` — typed request/response interfaces matching OpenAPI contract, error handling with typed error responses, continuation token pagination helpers, Cache-Control header support for manual refresh
- [x] T018 Create dashboard layout shell in `apps/web/src/app/governance/dashboard/layout.tsx` — sub-navigation bar for 6 views (Executive Summary, Compliance, Audit Trail, Readiness, Recovery, Risk & Warning), refresh controls slot, tenant indicator slot, active view highlighting, breadcrumbs
- [x] T019 [P] Create WidgetErrorBoundary component in `apps/web/src/components/governance/dashboard/WidgetErrorBoundary.tsx` — per-widget error display with "data unavailable" message, last-known timestamp, and retry button per FR-031
- [x] T020 [P] Create DataFreshnessIndicator component in `apps/web/src/components/governance/dashboard/DataFreshnessIndicator.tsx` — staleness badge showing age of displayed data per widget per FR-030
- [x] T021 [P] Create DegradedModeBanner component in `apps/web/src/components/governance/dashboard/DegradedModeBanner.tsx` — system-wide degradation alert banner listing unavailable data sources per FR-031
- [x] T022 [P] Create RefreshControls component in `apps/web/src/components/governance/dashboard/RefreshControls.tsx` — auto/manual refresh toggle, polling interval display (30s/5min), manual refresh button that sends Cache-Control: no-cache per FR-029
- [x] T023 [P] Create TenantBanner component in `apps/web/src/components/governance/dashboard/TenantBanner.tsx` — persistent non-dismissible "SIMULATION — {scenario name}" banner using `--ama-sim-banner` colour token per FR-026A
- [x] T024 [P] Create CompanionDataTable accessibility component in `apps/web/src/components/governance/a11y/CompanionDataTable.tsx` — visually hidden data table (sr-only), "Show data table" toggle button, proper table semantics with caption, scope attributes per FR-032
- [x] T025 [P] Create ChartAriaLabel utility in `apps/web/src/components/governance/a11y/ChartAriaLabel.tsx` — ARIA label generator for chart/gauge widgets (e.g., "Governance health score: 78 out of 100, Amber status") per FR-032

### Shared UI Components

- [x] T026 [P] Create TrafficLightIndicator component in `packages/ui/src/components/governance/TrafficLightIndicator.tsx` — Green/Amber/Red status indicator with icon + text label (colour never sole means of conveying information per WCAG)
- [x] T027 [P] Create HealthScoreGauge component shell in `packages/ui/src/components/governance/HealthScoreGauge.tsx` — 0–100 gauge with traffic light status, CompanionDataTable integration for dimension breakdown, ARIA label via ChartAriaLabel
- [x] T028 Create barrel export in `packages/ui/src/components/governance/index.ts` re-exporting HealthScoreGauge and TrafficLightIndicator

### Foundational Tests

- [x] T029 [P] Write unit tests for GovernanceHealthScore domain model validation in `tests/unit/test_governance_health_score_model.py` — score ranges (0–100), status derivation (green ≥80, amber 50–79, red <50), dimension weights sum to 1.0, ConstitutionalGateStatus gate_number 1–10
- [x] T030 [P] Write unit tests for AuditExportJob state machine transitions in `tests/unit/test_audit_export_model.py` — valid transitions (queued→processing→complete, queued→processing→failed), field constraints, download_url only set when complete
- [x] T031 [P] Create API contract conformance test skeleton in `tests/contract/test_governance_dashboard_contract.py` validating all 13 endpoint response shapes against OpenAPI schema in `specs/021-governance-dashboard/contracts/governance-dashboard-api.yaml`

**Checkpoint**: Foundation ready — all domain models, API routing, frontend client, shared components, and infrastructure in place. User story implementation can begin.

---

## Phase 3: User Story 1 — Executive Governance Health Overview (Priority: P1) 🎯 MVP

**Goal**: Deliver the "single pane of glass" executive summary with health score, constitutional gates, incident count, resource utilisation, and risk summary.

**Independent Test**: Navigate to `/governance/dashboard`, verify health score gauge (0–100, traffic light), 10 constitutional gates with compliance indicators, active incident count, resource utilisation %, and risk summary by severity all render with data. Widgets show skeleton loaders, error boundaries, and staleness indicators.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T032 [P] [US1] Write unit tests for HealthScoreService calculation algorithm in `tests/unit/test_health_score_service.py` — weighted dimensions (constitutional 40%, readiness 25%, data source 20%, recovery 15%), traffic light thresholds, assessment_pending gate exclusion from denominator, stale data handling, all-missing-data edge case (score = 0)
- [x] T033 [P] [US1] Write unit tests for DashboardAggregationService.get_executive_summary() in `tests/unit/test_dashboard_aggregation.py` — correct ExecutiveSummaryResponse shape, constitutional_gates count = 10, risk_summary with 4 severity levels, active_incident_count ≥ 0
- [x] T034 [P] [US1] Write integration test for GET /governance/dashboard/summary endpoint in `tests/integration/test_governance_dashboard_api.py` — 200 response with all required fields, X-Data-Freshness and X-Cache-Status headers present, 503 DegradedMode when backend sources unavailable

### Implementation for User Story 1

- [x] T035 [US1] Implement HealthScoreService in `apps/api/app/services/health_score_service.py` — calculate composite score from 4 weighted dimensions per R-004 algorithm: (constitutional_compliance × 0.40) + (operational_readiness × 0.25) + (data_source_governance × 0.20) + (recovery_progress × 0.15); derive traffic light (Green ≥80, Amber 50–79, Red <50); exclude assessment_pending gates from denominator; handle no active recovery as 100%
- [x] T036 [US1] Implement DashboardAggregationService.get_executive_summary() in `apps/api/app/services/dashboard_aggregation_service.py` — aggregate health score via HealthScoreService, fetch 10 constitutional gate statuses, count active incidents, compute resource utilisation, build risk severity breakdown; cache result with 5min TTL per tenant_id
- [x] T037 [US1] Implement GET /governance/dashboard/config endpoint in `apps/api/app/api/routes/governance_dashboard.py` — return DashboardConfigResponse with user_roles from Entra ID claims, poll_interval_ms (30000 during active incident, 300000 steady-state), tenant context, has_active_incident flag, cache_ttl_s
- [x] T038 [US1] Implement GET /governance/dashboard/summary endpoint in `apps/api/app/api/routes/governance_dashboard.py` — return ExecutiveSummaryResponse from aggregation service, respect Cache-Control: no-cache for manual refresh bypass, set X-Data-Freshness header (oldest data source timestamp), set X-Cache-Status header (HIT/MISS/BYPASS), return 503 with degraded_sources list when backend unavailable
- [x] T039 [P] [US1] Create ConstitutionalGates component in `apps/web/src/components/governance/dashboard/ConstitutionalGates.tsx` — 10-gate compliance grid with colour-coded status badges (compliant/non-compliant/partially-compliant/pending), severity indicators for non-compliant gates, drill-down links to detailed compliance view per FR-002
- [x] T040 [US1] Create executive summary page in `apps/web/src/app/governance/dashboard/page.tsx` — server component fetching from /config and /summary endpoints; render HealthScoreGauge with dimension breakdown, ConstitutionalGates grid, active incident counter, resource utilisation gauge, risk summary by severity; wrap each widget in WidgetErrorBoundary; show skeleton loaders during fetch; display DataFreshnessIndicator and DegradedModeBanner when applicable
- [x] T041 [US1] Implement useGovernancePolling hook in `apps/web/src/lib/api/governance.ts` — consume poll_interval_ms from /config, auto-refresh data at interval, adjust interval when has_active_incident changes, support manual refresh that bypasses cache

**Checkpoint**: Executive summary view fully functional. Navigate to `/governance/dashboard` to see health score, gates, incidents, resources, and risks. Skeleton loading, error boundaries, and cache refresh working.

---

## Phase 4: User Story 2 — Compliance Matrix and Assessment Tracking (Priority: P1)

**Goal**: Full data source compliance matrix with filtering, sorting, pagination, drill-down to assessment history and remediation actions.

**Independent Test**: Navigate to `/governance/dashboard/compliance`, verify matrix rows match registered data sources, filter by "non-compliant" to see only non-compliant sources sorted by most overdue, click a row to see assessment history and remediation actions in detail panel.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T042 [P] [US2] Write unit tests for DashboardAggregationService.get_compliance_matrix() in `tests/unit/test_dashboard_aggregation.py` — pagination with continuation tokens (50/page), filtering by compliance_status, grace period countdown calculation (days remaining), governance gap count aggregation
- [x] T043 [P] [US2] Write integration test for GET /governance/dashboard/compliance and GET /compliance/{dataSourceId} endpoints in `tests/integration/test_governance_dashboard_api.py` — paginated ComplianceMatrixResponse with correct entries, filter params echoed, ComplianceDetailResponse with assessment_history array, 404 for non-existent data source

### Implementation for User Story 2

- [x] T044 [US2] Implement DashboardAggregationService.get_compliance_matrix() and get_compliance_detail() in `apps/api/app/services/dashboard_aggregation_service.py` — query data sources with compliance status from governance registry, join assessment history, compute grace period countdown days, detect governance gaps via detect_governance_gaps(); paginate with Cosmos DB continuation tokens (50/page)
- [x] T045 [US2] Implement GET /governance/dashboard/compliance endpoint in `apps/api/app/api/routes/governance_dashboard.py` — filter by compliance_status, category; sort by last_assessment_date, next_due_date, gap_count, name; paginate with page_size and continuation_token; return ComplianceMatrixResponse
- [x] T046 [US2] Implement GET /governance/dashboard/compliance/{dataSourceId} endpoint in `apps/api/app/api/routes/governance_dashboard.py` — return ComplianceDetailResponse with full assessment_history (date, assessor, result, notes), remediation_actions (action, status, due_date), related_audit_urls; 404 if data source not found
- [x] T047 [P] [US2] Create ComplianceMatrix component in `apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx` — sortable table with columns (source name, compliance status badge, last assessment date, next due date, gap count, grace period countdown), filter toolbar (status dropdown, category dropdown), pagination controls, row click for detail panel
- [x] T048 [US2] Create compliance view page in `apps/web/src/app/governance/dashboard/compliance/page.tsx` — render ComplianceMatrix with server-side data fetching, URL-driven filter/sort state, pagination via continuation tokens, slide-out detail panel for selected data source showing assessment history timeline and remediation actions

**Checkpoint**: Compliance matrix fully functional. Filter, sort, paginate, and drill into data source details.

---

## Phase 5: User Story 3 — Searchable Audit Trail (Priority: P1)

**Goal**: Searchable, filterable audit log with decision chain visualisation and async export (PDF/CSV/JSON).

**Independent Test**: Navigate to `/governance/dashboard/audit`, search by date range and actor, verify results appear within 2 seconds with total count. Click an event to see decision chain. Export selected records as CSV and verify download completes.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T049 [P] [US3] Write unit tests for AuditExportService in `tests/unit/test_audit_export_service.py` — PDF generation via ReportLab with provenance metadata headers, CSV with all fields preserved, JSON with complete schema; concurrent export limit enforcement (max 3 per user); job status transitions
- [x] T050 [P] [US3] Write integration test for audit trail endpoints in `tests/integration/test_governance_dashboard_api.py` — GET /audit with filters returns AuditTrailResponse within 2s, GET /audit/{eventId}/chain returns decision chain steps, POST /audit/export returns 202 with job ID, GET /audit/export/{jobId} returns status progression, 429 when exceeding concurrent limit

### Implementation for User Story 3

- [x] T051 [US3] Implement DashboardAggregationService.search_audit_events() and get_decision_chain() in `apps/api/app/services/dashboard_aggregation_service.py` — search with date_from/to, actor, action_type, affected_entity, keyword filters; paginate with Cosmos DB continuation tokens and composite index on (tenant_id, timestamp DESC, action_type, actor); return decision chain steps with evidence integrity status (verified/unverified/pending)
- [x] T052 [US3] Implement AuditExportService in `apps/api/app/services/audit_export_service.py` — async export generation: PDF via ReportLab (formatted report with provenance metadata headers), CSV via Python csv module, JSON via json module; store generated files in Azure Blob Storage (hot tier, 24h lifecycle TTL, `governance-exports` container); track job status in Cosmos DB (queued → processing → complete/failed); enforce max 3 concurrent exports per user
- [x] T053 [US3] Implement GET /governance/dashboard/audit endpoint in `apps/api/app/api/routes/governance_dashboard.py` — accept 6 filter parameters (date_from, date_to, actor, action_type, affected_entity, keyword), paginate with page_size and continuation_token, return AuditTrailResponse with total_count, target <2s response time
- [x] T054 [US3] Implement GET /governance/dashboard/audit/{eventId}/chain endpoint in `apps/api/app/api/routes/governance_dashboard.py` — return AuditDecisionChainResponse with ordered chain steps (trigger → approvals → action), chain_complete flag; 404 if event not found
- [x] T055 [US3] Implement POST /governance/dashboard/audit/export and GET /audit/export/{jobId} endpoints in `apps/api/app/api/routes/governance_dashboard.py` — create export job from AuditExportRequest (202 Accepted), poll job status with download_url when complete, 429 TooManyRequests when exceeding 3 concurrent exports per user
- [x] T056 [P] [US3] Create AuditTrailSearch component in `apps/web/src/components/governance/dashboard/AuditTrailSearch.tsx` — search form with date range pickers, actor input, action type dropdown, affected entity input, keyword text field; result table with columns (timestamp, actor, action, entity, outcome, provenance); pagination controls; row selection checkboxes for export
- [x] T057 [P] [US3] Create AuditDecisionChain component in `apps/web/src/components/governance/dashboard/AuditDecisionChain.tsx` — step-by-step timeline visualiser showing trigger → intermediate approvals → final action; each step shows actor, timestamp, description, rationale; evidence integrity badges (verified ✓ / unverified ⚠ / pending ⏳)
- [x] T058 [P] [US3] Create AuditExportDialog component in `apps/web/src/components/governance/dashboard/AuditExportDialog.tsx` — format selection (PDF/CSV/JSON radio buttons), scope summary (record count, applied filters), progress bar during generation, download link when complete, error display on failure
- [x] T059 [US3] Create audit trail page in `apps/web/src/app/governance/dashboard/audit/page.tsx` — render AuditTrailSearch with URL-driven filter state, AuditDecisionChain in slide-out panel on event click, AuditExportDialog modal, export job polling via useGovernancePolling

**Checkpoint**: Audit trail fully functional. Search, filter, view decision chains, and export records as PDF/CSV/JSON.

---

## Phase 6: User Story 4 — Operational Readiness Assessment (Priority: P2)

**Goal**: PPRR phase indicators, emergency plan lifecycle status with overdue flags, exercise completion rates, capability gaps, and AIIMS role coverage.

**Independent Test**: Navigate to `/governance/dashboard/readiness`, verify 4 PPRR phase indicators with current phase highlighted, emergency plan counts by 7 lifecycle states with overdue flags, exercise completion rate %, capability gap count, and role coverage percentage with under-staffed role details.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T060 [P] [US4] Write unit tests for DashboardAggregationService.get_operational_readiness() in `tests/unit/test_dashboard_aggregation.py` — 4 PPRR phases with active phase, emergency plan overdue calculation (compare next_review_date to UTC now, convert display to AEST), exercise rate aggregation by type, role coverage percentage for all 10 AIIMS roles
- [x] T061 [P] [US4] Write integration test for GET /governance/dashboard/readiness endpoint in `tests/integration/test_governance_dashboard_api.py` — OperationalReadinessResponse with exactly 4 PPRR phases, 7 plan lifecycle states, 10 roles in aiims_role_coverage, capability_gap_count ≥ 0

### Implementation for User Story 4

- [x] T062 [US4] Implement DashboardAggregationService.get_operational_readiness() in `apps/api/app/services/dashboard_aggregation_service.py` — aggregate PPRR phase status from pprr_phase_context data, emergency plan counts by 7 lifecycle states (Draft through Superseded) with overdue review flags (next_review_date < utcnow), exercise completion rates by type from exercise reports, AIIMS role coverage (assigned_count / required_count per role), capability gap count
- [x] T063 [US4] Implement GET /governance/dashboard/readiness endpoint in `apps/api/app/api/routes/governance_dashboard.py` — return OperationalReadinessResponse with pprr_phases, emergency_plans, exercise stats, role coverage, capability gaps
- [x] T064 [P] [US4] Create PPRRPhaseIndicator component in `apps/web/src/components/governance/dashboard/PPRRPhaseIndicator.tsx` — 4-phase horizontal indicator (Prevention, Preparedness, Response, Recovery) with active phase highlighted, elevated state styling, ARIA labels per phase
- [x] T065 [P] [US4] Create EmergencyPlanStatus component in `apps/web/src/components/governance/dashboard/EmergencyPlanStatus.tsx` — 7-state lifecycle breakdown with count per state, "⚠ OVERDUE" overlay badge with days-past-due count, "Expired" as display-level overlay condition (not a lifecycle state) per R-012
- [x] T066 [US4] Create operational readiness page in `apps/web/src/app/governance/dashboard/readiness/page.tsx` — render PPRRPhaseIndicator, EmergencyPlanStatus, exercise completion rate widget with breakdown by type, capability gap counter, AIIMS role coverage table (role, assigned, required, coverage %)

**Checkpoint**: Operational readiness view fully functional. PPRR phases, plan statuses, exercises, gaps, and role coverage all displayed.

---

## Phase 7: User Story 5 — Recovery Progress Tracking (Priority: P2)

**Goal**: Recovery progress across 5 domains (overarching, social, economic, built, natural) with trend indicators, target tracking, M&E results, and incident selector.

**Independent Test**: Navigate to `/governance/dashboard/recovery`, verify 5 domain progress bars with trend direction, click a domain to see outcome targets, activity completion, community indicators, and M&E results. Verify "no active recovery" empty state when no data exists.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T067 [P] [US5] Write unit tests for DashboardAggregationService.get_recovery_progress() and get_recovery_domain_detail() in `tests/unit/test_dashboard_aggregation.py` — 5 domains returned, overarching domain aggregates average of 4 concrete domains per R-013, target variance calculation (positive = ahead, negative = behind), no active recovery returns has_active_recovery=false with empty state
- [x] T068 [P] [US5] Write integration test for GET /governance/dashboard/recovery and GET /recovery/{domain} endpoints in `tests/integration/test_governance_dashboard_api.py` — RecoveryProgressResponse with 5 domains, incident_id filter, RecoveryDomainDetailResponse with outcome targets and M&E results, 404 for invalid domain name

### Implementation for User Story 5

- [x] T069 [US5] Implement DashboardAggregationService.get_recovery_progress() and get_recovery_domain_detail() in `apps/api/app/services/dashboard_aggregation_service.py` — map RecoveryDomain 5-value display type to RecoveryEnvironmentTracker 4-value data type per R-013; calculate overarching domain as average of 4 concrete domain completion percentages; compute target variance per domain; support incident_id filter with default to most recent active recovery; return has_active_recovery=false with empty domains when no recovery programme exists
- [x] T070 [US5] Implement GET /governance/dashboard/recovery and GET /recovery/{domain} endpoints in `apps/api/app/api/routes/governance_dashboard.py` — return RecoveryProgressResponse with 5 domains and available_incidents list; domain detail returns RecoveryDomainDetailResponse with outcome_targets, activity_completion_rates, community_indicators, me_evaluation_results; validate domain enum (overarching/social/economic/built/natural); 404 for no active recovery on domain detail
- [x] T071 [P] [US5] Create RecoveryDomainTracker component in `apps/web/src/components/governance/dashboard/RecoveryDomainTracker.tsx` — 5-domain progress display with completion % bars, trend direction arrows (improving ↑ / stable → / declining ↓), target variance warnings (below-target flagged), overarching row styled as cross-cutting summary, CompanionDataTable for accessibility
- [x] T072 [US5] Create recovery progress page in `apps/web/src/app/governance/dashboard/recovery/page.tsx` — render RecoveryDomainTracker with incident selector dropdown (available_incidents), domain detail slide-out panel on domain click, empty state message with link to recovery catalogue when has_active_recovery=false

**Checkpoint**: Recovery progress view fully functional. All 5 domains with progress, trends, detail panels, incident selector, and empty state.

---

## Phase 8: User Story 6 — Risk Register and Warning Compliance (Priority: P2)

**Goal**: Active risk register with severity breakdown, treatment rates, alert compliance metrics, AWS 3-tier usage, broadcast reach, and per-principle warning compliance for all 10 AWS principles.

**Independent Test**: Navigate to `/governance/dashboard/risk`, verify risk counts by severity, treatment closure rate, alert approval latency with threshold-exceeded flags, AWS tier breakdown, broadcast reach %, and per-principle compliance rates for 10 AWS principles. Click a risk to see detail with treatments and audit links.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T073 [P] [US6] Write unit tests for DashboardAggregationService.get_risk_and_warning() in `tests/unit/test_dashboard_aggregation.py` — risk severity counts (extreme/high/medium/low), treatment closure rate, alert latency threshold comparison (exceeds flag), 10 AWS principle compliance rates, broadcast reach percentage, non-compliant warning IDs for drill-down
- [x] T074 [P] [US6] Write integration test for GET /governance/dashboard/risk and GET /risk/{riskId} endpoints in `tests/integration/test_governance_dashboard_api.py` — RiskWarningResponse with correct shape, principle_compliance array length = 10, top_risks ordered by severity, RiskDetailResponse with treatment history, 404 for non-existent risk

### Implementation for User Story 6

- [x] T075 [US6] Implement DashboardAggregationService.get_risk_and_warning() and get_risk_detail() in `apps/api/app/services/dashboard_aggregation_service.py` — aggregate risk severity counts, treatment closure rate, average alert approval latency (flag if exceeds threshold from spec 008 configuration), AWS 3-tier usage breakdown, broadcast reach %, 10 AWS warning principle compliance rates with non-compliant warning IDs for drill-down; risk detail with description, likelihood, consequence, treatments, treatment history, related audit URLs
- [x] T076 [US6] Implement GET /governance/dashboard/risk and GET /risk/{riskId} endpoints in `apps/api/app/api/routes/governance_dashboard.py` — return RiskWarningResponse with risk_severity, treatment_closure_rate_pct, alert_compliance, top_risks; risk detail returns RiskDetailResponse; 404 for non-existent risk
- [x] T077 [P] [US6] Create RiskRegisterView component in `apps/web/src/components/governance/dashboard/RiskRegisterView.tsx` — severity breakdown cards (extreme/high/medium/low with counts), treatment closure rate gauge, top risks table with columns (description, severity, treatment due, responsible), row click for detail slide-out with treatment history and audit links
- [x] T078 [P] [US6] Create WarningCompliancePanel component in `apps/web/src/components/governance/dashboard/WarningCompliancePanel.tsx` — AWS 10-principle compliance grid showing per-principle rate %, drill-down to non-compliant warnings on principle click, overall compliance score, AWS tier usage breakdown (Advice/Watch/Emergency), broadcast reach gauge, latency threshold alert indicators; use AWS severity colour tokens (`--ama-aws-advice` yellow, `--ama-aws-watch` orange, `--ama-aws-emergency` red) per FR-033A
- [x] T079 [US6] Create risk & warning page in `apps/web/src/app/governance/dashboard/risk/page.tsx` — render RiskRegisterView and WarningCompliancePanel side-by-side, risk detail slide-out panel, non-compliant warning drill-down panel

**Checkpoint**: Risk & warning view fully functional. Risk register, treatments, alert compliance, AWS principle compliance all displayed.

---

## Phase 9: User Story 7 — Role-Based Dashboard Personalisation (Priority: P3)

**Goal**: Personalised dashboard landing experience for all 10 AIIMS roles with role-appropriate widget layouts, multi-role resolution, and restricted view for no-role users.

**Independent Test**: Log in with different AIIMS roles (Operations Officer, PIO, Logistics Officer, etc.) and verify the default dashboard view and widget order change per role-to-widget mapping table in plan.md. Log in with multiple roles and verify widgets merge with highest-authority role first. Log in with no role and verify restricted access message.

### Tests for User Story 7

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T080 [P] [US7] Write unit tests for role-to-widget resolution logic in `tests/unit/test_dashboard_config.py` — all 10 roles map to correct default_view and widget sets per plan.md mapping table, multi-role merge produces union of widgets ordered by highest authority_rank, no-role user gets empty widget list with restricted flag
- [x] T081 [P] [US7] Write integration test for GET /governance/dashboard/config with different role claims in `tests/integration/test_governance_dashboard_api.py` — DashboardConfigResponse varies by role (different default_view, different widget_layout), multi-role returns merged widgets, 403 with RestrictedAccessResponse for no-role user

### Implementation for User Story 7

- [x] T082 [US7] Create role-to-widget mapping configuration in `apps/api/app/models/dashboard_config.py` — define default widget sets for all 10 AIIMS roles per plan.md Role-to-Widget Mapping table (Incident Controller → Executive Summary, Operations Officer → Executive Summary ops-focused, Planning Officer → Operational Readiness, etc.), authority hierarchy 1–10 for multi-role resolution
- [x] T083 [US7] Implement role resolution logic in GET /governance/dashboard/config endpoint in `apps/api/app/api/routes/governance_dashboard.py` — extract user roles from Entra ID claims, resolve single-role → direct mapping, multi-role → union of widgets ordered by highest authority_rank, no-role → 403 with RestrictedAccessResponse and "request role assignment" message
- [x] T084 [P] [US7] Create RoleWidgetGrid component in `apps/web/src/components/governance/dashboard/RoleWidgetGrid.tsx` — dynamic widget layout that renders widgets from config.widget_layout in priority order, responsive grid adjusting for different widget counts, widget type → component mapping
- [x] T085 [US7] Integrate RoleWidgetGrid into dashboard layout in `apps/web/src/app/governance/dashboard/layout.tsx` — consume config.widget_layout and config.default_view on initial load, set landing view per role, show restricted access message with "request role assignment" guidance for no-role users per FR-026

**Checkpoint**: Role-based personalisation working. Each of 10 roles sees appropriate defaults; multi-role users see merged widgets; no-role users see restricted view.

---

## Phase 10: User Story 8 — Dashboard Interaction Audit Logging (Priority: P3)

**Goal**: Every dashboard interaction (view, filter, search, export, drill-down) is recorded in the audit trail with complete provenance metadata per FR-027 and Constitution Gate 4.

**Independent Test**: Perform dashboard actions (view page, apply filter, run search, export data, drill into detail), then search the audit trail for "dashboard_*" action types and verify all interactions appear with correct actor, timestamp, role, and action parameters.

### Tests for User Story 8

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T086 [P] [US8] Write unit tests for dashboard audit logging in `tests/unit/test_dashboard_audit_logging.py` — verify all 6 action types (dashboard_view, dashboard_filter, dashboard_search, dashboard_export, dashboard_drill_down, dashboard_navigate_to_crud) create correct DashboardInteractionAudit records with tenant_id, actor_id, actor_role, view, parameters, session_context
- [x] T087 [P] [US8] Write integration test verifying audit entries are created for dashboard API calls in `tests/integration/test_governance_dashboard_api.py` — call GET /summary, GET /compliance?compliance_status=non_compliant, GET /audit?actor=test, POST /audit/export and verify corresponding audit entries in the audit trail with correct action types and parameters

### Implementation for User Story 8

- [x] T088 [US8] Implement dashboard interaction audit logging in `apps/api/app/api/routes/governance_dashboard.py` — add audit entry creation to every endpoint: dashboard_view on all GET calls, dashboard_filter on filtered queries (compliance, audit search), dashboard_search on audit text search, dashboard_export on export creation, dashboard_drill_down on detail endpoints (/compliance/{id}, /audit/{id}/chain, /recovery/{domain}, /risk/{id}); record actor_id, actor_role, view, parameters, result_count, session_context per FR-027
- [x] T089 [US8] Implement FR-028 navigation confirmation in `apps/web/src/components/governance/dashboard/` — add "are you sure you want to leave the dashboard?" interstitial dialog before navigating to existing CRUD pages (e.g., "Request Reassessment" links in compliance view, "View Risk Assessment" links in risk view); log "dashboard_navigate_to_crud" audit entry with navigation target URL and intent description before redirecting
- [x] T090 [US8] Wire session correlation ID into all dashboard frontend API calls in `apps/web/src/lib/api/governance.ts` — generate anonymous session UUID on dashboard load, include as X-Session-Id header on all API requests, pass role context for complete provenance in audit entries

**Checkpoint**: All dashboard interactions recorded in audit trail. Auditors can search for dashboard_* events with complete provenance.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: E2E tests, infrastructure, documentation, accessibility hardening, and performance optimisation across all stories.

### End-to-End Tests

- [x] T091 [P] Create Playwright E2E test suite in `tests/e2e/governance-dashboard.spec.ts` — executive summary loads within 3s, compliance matrix filtering and pagination, audit trail search returns within 2s, export download flow (initiate → poll → download), sub-navigation between all 6 views, drill-down and slide-out panel interactions
- [x] T092 [P] Create accessibility E2E tests in `tests/e2e/governance-dashboard.spec.ts` — axe-core automated WCAG 2.1 AA checks on all 6 dashboard views, keyboard tab navigation through all widgets, CompanionDataTable toggle on/off verification, screen reader ARIA label validation on HealthScoreGauge and ConstitutionalGates

### Infrastructure

- [x] T093 [P] Create Cosmos DB composite index definitions in `infra/modules/governance-dashboard.bicep` — audit container index on (tenant_id ASC, timestamp DESC, action_type ASC, actor ASC), assessment container index on (gate_id, is_current, compliance_status), data source container index on (compliance_status, governance_status, kind) per R-006
- [x] T094 [P] Add Azure Blob Storage container configuration for audit exports in `infra/modules/governance-dashboard.bicep` — `governance-exports` container with 24-hour lifecycle management policy for automatic deletion of expired export files

### Documentation

- [x] T095 [P] Update `specs/021-governance-dashboard/quickstart.md` with verified development setup steps, new environment variables (EXPORT_BLOB_CONTAINER, EXPORT_TTL_HOURS, EXPORT_MAX_CONCURRENT, DASHBOARD_CACHE_TTL_S, DASHBOARD_ACTIVE_POLL_MS, DASHBOARD_STEADY_POLL_MS), and test commands
- [x] T096 [P] Add governance dashboard developer documentation to `docs/governance-dashboard.md` — endpoint reference, authentication requirements, pagination patterns, cache behaviour, role-to-widget mapping reference, export flow, audit logging scope

### Performance & Accessibility Hardening

- [x] T097 Add server-side performance logging for dashboard endpoints in `apps/api/app/api/routes/governance_dashboard.py` — emit structured telemetry to App Insights per FR-034 with endpoint path, request duration, status code, cache status, tenant_type; validate audit search <2s and summary <3s targets
- [x] T098 [P] Implement useWidgetTelemetry hook in `apps/web/src/lib/api/governance.ts` — measure per-widget render time, report to App Insights JS SDK with anonymised correlation ID per FR-035 (no PII), include view name, widget type, data freshness, and tenant_type
- [x] T099 Verify WCAG 2.1 AA compliance across all dashboard components — colour contrast ratios meet 4.5:1 minimum, focus indicators visible on all interactive elements, tab order logical across widget grid, CompanionDataTable on every chart/gauge, ARIA labels per FR-032, AWS colour tokens always paired with icon + text per FR-033A
- [x] T100 Run quickstart.md validation — follow all setup steps from `specs/021-governance-dashboard/quickstart.md` on a clean environment, verify frontend + backend start, all dashboard views render, API endpoints respond, tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–10)**: All depend on Foundational phase completion
  - P1 stories (US1, US2, US3) can proceed in parallel after Phase 2
  - P2 stories (US4, US5, US6) can proceed in parallel after Phase 2
  - P3 stories (US7, US8) can proceed in parallel after Phase 2 (but benefit from US1–US6 being complete)
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US3 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US4 (P2)**: Can start after Phase 2 — no dependencies on other stories
- **US5 (P2)**: Can start after Phase 2 — no dependencies on other stories
- **US6 (P2)**: Can start after Phase 2 — no dependencies on other stories
- **US7 (P3)**: Can start after Phase 2 — integrates with US1 dashboard page but independently testable
- **US8 (P3)**: Can start after Phase 2 — integrates with all dashboard endpoints but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Backend service before API endpoint
- API endpoint before frontend component
- Frontend component before page integration
- Story complete before moving to next priority

### Parallel Opportunities

- All foundational [P] tasks (T004–T006, T010, T016, T019–T028, T029–T031) can run in parallel
- All P1 stories (US1, US2, US3) can start simultaneously after Phase 2
- All P2 stories (US4, US5, US6) can start simultaneously after Phase 2
- Both P3 stories (US7, US8) can start simultaneously
- All test tasks marked [P] within a story can run in parallel
- All frontend component tasks marked [P] within a story can run in parallel

---

## Parallel Example: Phases 3–5 (P1 Stories)

```bash
# After Phase 2 Foundation completes, launch all P1 stories in parallel:

# Developer A: US1 — Executive Summary
Task T032: "Unit tests for HealthScoreService in tests/unit/test_health_score_service.py"
Task T033: "Unit tests for aggregation service in tests/unit/test_dashboard_aggregation.py"
Task T034: "Integration test for summary endpoint in tests/integration/test_governance_dashboard_api.py"
# then T035-T041 implementation

# Developer B: US2 — Compliance Matrix
Task T042: "Unit tests for compliance matrix in tests/unit/test_dashboard_aggregation.py"
Task T043: "Integration test for compliance endpoints in tests/integration/test_governance_dashboard_api.py"
# then T044-T048 implementation

# Developer C: US3 — Audit Trail
Task T049: "Unit tests for audit export in tests/unit/test_audit_export_service.py"
Task T050: "Integration test for audit endpoints in tests/integration/test_governance_dashboard_api.py"
# then T051-T059 implementation
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 — Executive Summary
4. **STOP and VALIDATE**: Navigate to `/governance/dashboard`, verify health score, gates, incidents, resources, risks
5. Deploy/demo if ready — delivers immediate executive oversight value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Executive summary → Test independently → Deploy (MVP!)
3. US2 → Compliance matrix → Test independently → Deploy
4. US3 → Audit trail + export → Test independently → Deploy
5. US4 → Operational readiness → Test independently → Deploy
6. US5 → Recovery progress → Test independently → Deploy
7. US6 → Risk & warning → Test independently → Deploy
8. US7 → Role personalisation → Test independently → Deploy
9. US8 → Audit logging → Test independently → Deploy
10. Polish → E2E tests, infra, docs, a11y hardening → Final deploy

### Parallel Team Strategy

With 3+ developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Executive Summary) → US4 (Readiness) → US7 (Personalisation)
   - Developer B: US2 (Compliance Matrix) → US5 (Recovery) → US8 (Audit Logging)
   - Developer C: US3 (Audit Trail) → US6 (Risk & Warning) → Polish
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests MUST fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Dashboard is **read-only** — no mutation endpoints except audit export (which creates a file, not state change)
- All API calls must include `tenant_id` — no cross-tenant data leakage (FR-026A)
- AWS colour tokens: `--ama-aws-advice` (yellow), `--ama-aws-watch` (orange), `--ama-aws-emergency` (red)
- Performance targets: 3s initial load (executive summary), 1s drill-down navigation, 2s audit search
- Polling: 30s active incident, 5min steady-state, manual refresh bypasses cache
- Audit retention: 7 years compliance data, 90 days dashboard interaction logs (then cold archive)
