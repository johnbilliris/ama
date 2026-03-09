# Tasks: Autonomous Disaster Response Coordination Hub

**Input**: Design documents from `/specs/001-disaster-response-hub/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/openapi.yaml`, `contracts/signal-envelope.schema.json`

**Tests**: Test-driven development is mandatory for this feature. Each user story begins with failing contract, integration, simulation, or end-to-end tests.

**Organization**: Tasks are grouped by user story to preserve independently testable increments for live multi-agency coordination, role-specific operational workspaces, and preparedness analysis.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the monorepo structure, developer tooling, and test harnesses required by all feature slices.

- [x] T001 Create the monorepo application and package skeleton in `apps/api/`, `apps/web/`, `apps/agents/`, `packages/domain/`, `packages/schemas/`, `packages/ui/`, `infra/bicep/`, `infra/policies/`, and `tests/`
- [x] T002 Initialize Python runtime manifests in `pyproject.toml`, `apps/api/pyproject.toml`, and `apps/agents/pyproject.toml`
- [x] T003 [P] Initialize the web workspace in `package.json`, `pnpm-workspace.yaml`, `apps/web/package.json`, and `packages/ui/package.json`
- [x] T004 [P] Configure repository-wide quality gates in `.github/workflows/ci.yml`, `ruff.toml`, `apps/web/eslint.config.mjs`, and `apps/web/playwright.config.ts`
- [x] T005 [P] Create shared environment templates in `.env.example`, `apps/api/.env.example`, `apps/agents/.env.example`, and `apps/web/.env.local.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared runtime, security, trust, and design-system foundations that block all user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Create the FastAPI orchestration bootstrap in `apps/api/app/main.py`, `apps/api/app/api/router.py`, and `apps/api/app/core/settings.py`
- [x] T007 [P] Implement Azure clients and Australia-region residency configuration in `apps/api/app/core/azure_clients.py` and `apps/api/app/core/residency.py`
- [x] T008 [P] Implement Entra ID authentication, jurisdiction RBAC, and scoped tenant-context resolution in `apps/api/app/core/auth.py`, `apps/api/app/api/dependencies/rbac.py`, and `apps/api/app/core/tenant_context.py`
- [x] T009 [P] Create append-only audit, timeline, and provenance primitives in `packages/domain/src/domain/models/timeline_event.py`, `packages/domain/src/domain/models/provenance.py`, and `apps/api/app/services/audit_service.py`
- [x] T010 [P] Publish shared schema artifacts from the feature contracts in `packages/schemas/openapi.yaml` and `packages/schemas/signal-envelope.schema.json`
- [x] T011 Implement event bus and explicit agent handoff adapters in `apps/api/app/services/event_bus.py` and `apps/agents/common/handoffs.py`
- [x] T012 [P] Create the shared design tokens and application shell foundation in `packages/ui/src/styles/tokens.css`, `packages/ui/src/components/layout/app-shell.tsx`, and `apps/web/src/app/globals.css`
- [x] T013 Implement seed loading, jurisdiction policy bootstrap, and agency-region isolation metadata in `packages/domain/src/domain/seed/bootstrap.py`, `apps/api/app/services/seed_service.py`, and `packages/domain/src/domain/models/jurisdiction_policy.py`
- [x] T014 [P] Write failing integration tests for cross-agency and cross-region isolation boundaries in `tests/integration/test_tenant_isolation.py`
- [x] T015 Implement scoped storage, cache, and event-channel partition enforcement in `apps/api/app/services/tenant_partitioning.py`, `apps/api/app/repositories/cosmos_scope.py`, `apps/api/app/services/cache_scope.py`, and `apps/api/app/services/event_scope.py`
- [x] T016 [P] Write failing integration tests for degraded-source and reduced-function behavior in `tests/integration/test_reduced_function_mode.py`
- [x] T017 Implement reduced-function state evaluation and recommendation suppression rules in `apps/api/app/services/degraded_mode_service.py` and `apps/api/app/services/recommendation_guardrails.py`

**Checkpoint**: Foundation ready. User story implementation can now proceed in priority order or in parallel.

---

## Phase 3: User Story 1 - Coordinate a live multi-agency incident (Priority: P1) 🎯 MVP

**Goal**: Give incident commanders a live shared operating picture with authoritative and community signals, participating organisations, framework context, recommended actions, approval flows, and human-reviewed public alert capability.

**Independent Test**: Simulate a multi-jurisdiction flood or bushfire incident, ingest representative signals, and verify that an incident commander can see the incident dashboard, participating agencies, current frameworks, coordinated actions, recommendation approval outcomes, and publish a reviewed multilingual public alert without relying on later stories.

### Tests for User Story 1 ⚠️

- [x] T018 [P] [US1] Write failing contract tests for signal ingestion, incident dashboard, recommendation approval, and public alert endpoints in `tests/contract/test_live_incident_contract.py`
- [x] T019 [P] [US1] Write failing integration tests for authoritative signal fusion, recommendation-to-alert approval flow, and shared operating picture updates in `tests/integration/test_live_incident_coordination.py`
- [x] T020 [P] [US1] Write failing Playwright coverage for the incident commander dashboard and alert approval workflow in `tests/e2e/test_incident_commander_dashboard.spec.ts`

### Implementation for User Story 1

- [x] T021 [P] [US1] Create incident, data source, signal, hazard assessment, recommendation, approval, and public-alert domain models in `packages/domain/src/domain/models/incident.py`, `packages/domain/src/domain/models/data_source.py`, `packages/domain/src/domain/models/signal.py`, `packages/domain/src/domain/models/hazard_assessment.py`, `packages/domain/src/domain/models/recommendation.py`, `packages/domain/src/domain/models/approval_decision.py`, and `packages/domain/src/domain/models/public_alert.py`
- [x] T022 [P] [US1] Implement signal envelope validation and provenance scoring in `apps/api/app/validators/signal_envelope.py` and `apps/api/app/services/provenance_scoring_service.py`
- [x] T023 [US1] Implement authoritative, IoT, and community ingestion services in `apps/api/app/services/ingestion/authoritative_ingestion.py`, `apps/api/app/services/ingestion/iot_ingestion.py`, and `apps/api/app/services/ingestion/community_ingestion.py`
- [x] T024 [US1] Implement monitoring, risk-assessment, and communication agents in `apps/agents/monitoring/agent.py`, `apps/agents/risk_assessment/agent.py`, and `apps/agents/communication/agent.py`
- [x] T025 [US1] Implement dashboard aggregation, recommendation approval, and public alert services in `apps/api/app/services/dashboard_service.py`, `apps/api/app/services/recommendation_service.py`, and `apps/api/app/services/public_alert_service.py`
- [x] T026 [US1] Implement signal, incident dashboard, recommendation approval, and alert routes in `apps/api/app/api/routes/signals.py`, `apps/api/app/api/routes/incidents.py`, `apps/api/app/api/routes/recommendations.py`, and `apps/api/app/api/routes/alerts.py`
- [x] T027 [P] [US1] Implement incident dashboard and alert API clients in `apps/web/src/lib/api/signals.ts`, `apps/web/src/lib/api/dashboard.ts`, `apps/web/src/lib/api/recommendations.ts`, and `apps/web/src/lib/api/alerts.ts`
- [x] T028 [US1] Build the incident commander operating picture and alert approval workflow in `apps/web/src/app/incidents/[incidentId]/page.tsx`, `apps/web/src/components/dashboard/shared-operating-picture.tsx`, `apps/web/src/components/dashboard/degraded-mode-banner.tsx`, `apps/web/src/components/dashboard/source-health-panel.tsx`, and `apps/web/src/components/alerts/public-alert-composer.tsx`

**Checkpoint**: User Story 1 delivers the MVP shared operating picture and reviewed public alert workflow for live multi-agency coordination.

---

## Phase 4: User Story 2 - Work through a role-specific operational view (Priority: P2)

**Goal**: Provide organisation- and persona-specific workspaces that surface the right tasks, requests, approvals, and dependencies for each operator while keeping them linked to the wider incident.

**Independent Test**: Assign multiple personas from different organisations to one incident and verify each user sees the correct task list, dependency chain, approvals, and status changes through their role-specific workspace.

### Tests for User Story 2 ⚠️

- [x] T029 [P] [US2] Write failing contract tests for persona workspace and task update endpoints in `tests/contract/test_persona_workspace_contract.py`
- [x] T030 [P] [US2] Write failing integration tests for task ownership, dependency visibility, shared state updates, and unauthorized cross-agency visibility in `tests/integration/test_persona_workspace_flow.py`
- [x] T031 [P] [US2] Write failing Playwright coverage for role-specific operational views in `tests/e2e/test_persona_workspace.spec.ts`

### Implementation for User Story 2

- [x] T032 [P] [US2] Create persona and coordination-task domain models in `packages/domain/src/domain/models/persona.py` and `packages/domain/src/domain/models/coordination_task.py`
- [x] T033 [US2] Implement persona workspace assembly and task orchestration services in `apps/api/app/services/persona_workspace_service.py` and `apps/api/app/services/task_orchestration_service.py`
- [x] T034 [US2] Implement resource allocation and dependency notification agents in `apps/agents/resource_allocation/agent.py` and `apps/agents/common/dependency_notifier.py`
- [x] T035 [US2] Implement persona workspace and task routes in `apps/api/app/api/routes/personas.py` and `apps/api/app/api/routes/tasks.py`
- [x] T036 [P] [US2] Implement persona workspace and task API clients in `apps/web/src/lib/api/personas.ts` and `apps/web/src/lib/api/tasks.ts`
- [x] T037 [US2] Build the role-specific workspace experience in `apps/web/src/app/workspaces/[personaId]/page.tsx` and `apps/web/src/components/workspaces/persona-workspace.tsx`
- [x] T038 [US2] Add task status synchronization and cross-agency notification handling in `apps/api/app/services/task_status_sync.py` and `apps/web/src/components/workspaces/task-status-panel.tsx`

**Checkpoint**: User Story 2 delivers independently testable, role-specific operational workspaces.

---

## Phase 5: User Story 3 - Prepare and analyse agency operating models before an event (Priority: P3)

**Goal**: Allow planners to model jurisdictions, organisations, frameworks, and rehearsals so they can analyse collective operations and expose coordination gaps before live incidents.

**Independent Test**: Onboard a jurisdiction with organisations, personas, and framework assignments, then run a rehearsal scenario and verify that planners can review agency relationships, escalation paths, and coordination-gap analysis without running a live incident.

### Tests for User Story 3 ⚠️

- [x] T039 [P] [US3] Write failing contract tests for organisation catalog, framework catalog, and scenario replay endpoints in `tests/contract/test_preparedness_contract.py`
- [x] T040 [P] [US3] Write failing integration tests for jurisdiction modelling and rehearsal analysis in `tests/integration/test_preparedness_analysis.py`
- [x] T041 [P] [US3] Write failing simulation coverage for bushfire, flood, and cyclone preparedness replays in `tests/simulation/test_preparedness_replays.py`

### Implementation for User Story 3

- [x] T042 [P] [US3] Create organisation, jurisdiction, operating-framework, framework-assignment, jurisdiction-policy, and scenario-run domain models in `packages/domain/src/domain/models/organisation.py`, `packages/domain/src/domain/models/jurisdiction.py`, `packages/domain/src/domain/models/operating_framework.py`, `packages/domain/src/domain/models/framework_assignment.py`, `packages/domain/src/domain/models/jurisdiction_policy.py`, and `packages/domain/src/domain/models/scenario_run.py`
- [x] T043 [P] [US3] Add curated Australian seed datasets in `packages/domain/src/domain/seed/organisations_australia.json`, `packages/domain/src/domain/seed/frameworks_australia.json`, and `packages/domain/src/domain/seed/jurisdictions_australia.json`
- [x] T044 [US3] Implement organisation intelligence and preparedness analysis services in `apps/api/app/services/organisation_intelligence_service.py` and `apps/api/app/services/preparedness_analysis_service.py`
- [x] T045 [US3] Implement evacuation agent and rehearsal orchestration service in `apps/agents/evacuation/agent.py` and `apps/api/app/services/rehearsal_orchestrator.py`
- [x] T046 [US3] Implement organisation, framework, and scenario routes in `apps/api/app/api/routes/organisations.py`, `apps/api/app/api/routes/frameworks.py`, and `apps/api/app/api/routes/scenarios.py`
- [x] T047 [P] [US3] Implement preparedness API clients in `apps/web/src/lib/api/organisations.ts`, `apps/web/src/lib/api/frameworks.ts`, and `apps/web/src/lib/api/scenarios.ts`
- [x] T048 [US3] Build the preparedness analysis experience in `apps/web/src/app/preparedness/page.tsx` and `apps/web/src/components/preparedness/operating-model-analyzer.tsx`

**Checkpoint**: User Story 3 delivers independently testable preparedness modelling and rehearsal analysis.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete advanced alert-delivery refinements, accessibility hardening, observability, evaluation instrumentation, and operational runbook work that spans multiple user stories.

- [x] T049 [P] Add expanded multilingual accessibility, localization, and offline-ready refinements in `apps/web/src/components/accessibility/language-switcher.tsx`, `apps/web/src/components/offline/connectivity-banner.tsx`, and `apps/web/src/components/alerts/alert-language-preview.tsx`
- [x] T050 [P] Implement advanced public alert delivery templates, channel adapters, and publish-workflow hardening in `apps/api/app/services/public_alert_service.py`, `apps/api/app/api/routes/alerts.py`, and `apps/web/src/components/alerts/public-alert-composer.tsx`
- [x] T051 Harden observability, resilience, rollback controls, and isolation guardrails in `infra/bicep/monitoring.bicep`, `infra/policies/safety-guardrails.rego`, `infra/policies/tenant-isolation.rego`, and `apps/api/app/middleware/resilience.py`
- [x] T052 [P] Document architecture, operator workflows, and response runbooks in `docs/disaster-response-hub/architecture.md` and `docs/disaster-response-hub/operator-runbooks.md`
- [x] T053 [P] Define baseline exercise packs, KPI capture templates, and the UX evaluation rubric in `docs/disaster-response-hub/evaluation/baseline-metrics.md`, `docs/disaster-response-hub/evaluation/kpi-template.csv`, `docs/disaster-response-hub/evaluation/ux-rubric.md`, and `docs/disaster-response-hub/evaluation/post-exercise-survey.md`
- [x] T054 [P] Instrument scenario replay metrics and dashboard decision-support validation in `apps/api/app/services/exercise_metrics_service.py`, `tests/simulation/test_exercise_metrics.py`, and `tests/e2e/test_dashboard_decision_support.spec.ts`
- [x] T055 Run the quickstart rehearsal flow and capture final validation guidance in `specs/001-disaster-response-hub/quickstart.md` and `tests/simulation/test_quickstart_rehearsals.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies and can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Stories (Phases 3-5)**: All depend on Foundational completion.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the MVP.
- **User Story 2 (P2)**: Starts after Foundational and integrates with US1 incident state, while remaining independently testable.
- **User Story 3 (P3)**: Starts after Foundational and can proceed in parallel with US2, while feeding richer data back into live operations.

### Within Each User Story

- Tests must be written and fail before implementation.
- Domain models before services.
- Services and agents before API routes.
- API routes before web integration.
- Story validation before advancing to the next release slice.

### Dependency Graph

- `Phase 1 -> Phase 2 -> US1`
- `Phase 1 -> Phase 2 -> US2`
- `Phase 1 -> Phase 2 -> US3`
- `US1 -> Phase 6`
- `US2 -> Phase 6`
- `US3 -> Phase 6`

---

## Parallel Opportunities

- Setup parallel work: `T003`, `T004`, and `T005`
- Foundational parallel work: `T007`, `T008`, `T009`, `T010`, `T012`, `T014`, and `T016`
- User Story 1 parallel work: `T018`, `T019`, `T020`, `T021`, `T022`, and `T027`
- User Story 2 parallel work: `T029`, `T030`, `T031`, `T032`, and `T036`
- User Story 3 parallel work: `T039`, `T040`, `T041`, `T042`, `T043`, and `T047`
- Polish parallel work: `T049`, `T050`, `T052`, and `T053`

## Parallel Example: User Story 1

```bash
# Launch failing verification together:
Task: "T018 Contract tests for live incident endpoints"
Task: "T019 Integration tests for signal fusion, alert approval, and dashboard updates"
Task: "T020 Playwright coverage for the incident commander dashboard"

# Build independent story assets together:
Task: "T021 Create incident, signal, recommendation, approval, and public-alert models"
Task: "T022 Implement signal validation and provenance scoring"
Task: "T027 Implement incident dashboard and alert API clients"
```

## Parallel Example: User Story 2

```bash
# Launch failing verification together:
Task: "T029 Contract tests for persona workspace and task endpoints"
Task: "T030 Integration tests for dependency visibility, isolation, and task updates"
Task: "T031 Playwright coverage for role-specific workspaces"

# Build independent story assets together:
Task: "T032 Create persona and coordination-task domain models"
Task: "T036 Implement persona workspace and task API clients"
```

## Parallel Example: User Story 3

```bash
# Launch failing verification together:
Task: "T039 Contract tests for preparedness endpoints"
Task: "T040 Integration tests for jurisdiction modelling and rehearsal analysis"
Task: "T041 Simulation coverage for preparedness replays"

# Build independent story assets together:
Task: "T042 Create organisation, framework, and scenario domain models"
Task: "T043 Add curated Australian seed datasets"
Task: "T047 Implement preparedness API clients"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the live multi-agency incident workflow independently with `T018` to `T020`.
5. Demo the incident commander experience before starting additional slices.

### Incremental Delivery

1. Deliver User Story 1 for the shared operating picture.
2. Add User Story 2 for role-specific operational execution.
3. Add User Story 3 for preparedness modelling and rehearsals.
4. Finish with advanced delivery refinements, accessibility, observability, and runbooks.

### Parallel Team Strategy

1. One platform stream completes Setup and Foundational work.
2. After Phase 2, one stream builds US1 while another prepares US3 data and modelling assets.
3. US2 starts once shared incident state and auth boundaries are stable.

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, required `[USx]` labels for story phases, and explicit file paths.
- TDD is mandatory throughout, so every story starts with failing tests before implementation.
- The earlier task file reflected a previous story split; this version is aligned to the current `spec.md`, `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, and contracts.
