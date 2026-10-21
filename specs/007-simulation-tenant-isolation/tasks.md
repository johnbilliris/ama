# Tasks: Simulation-as-Tenant — Tenant-Partitioned Simulation Mode

**Input**: Design documents from `/specs/007-simulation-tenant-isolation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/simulation-api.md, contracts/tenant-middleware.md, quickstart.md

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and extend configuration for simulation features

- [X] T001 Create directory structure for simulation feature: `apps/api/app/middleware/`, `apps/web/src/app/simulations/`, `apps/web/src/app/simulations/[tenantId]/`, `apps/web/src/app/simulations/reports/[reportId]/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T002 [P] Extend simulation configuration in apps/api/app/core/settings.py with `max_concurrent_simulations` (default: 3), `simulation_ttl_hours` (default: 72), `throttle_threshold_pct` (default: 70), `incident_throttle_quota_pct` (default: 20), `simulation_archive_retention_days` (default: 90)
- [X] T003 [P] Add `__init__.py` files to new packages: `apps/api/app/middleware/__init__.py`, ensure `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/contract/__init__.py` exist

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core tenant infrastructure that MUST be complete before ANY user story can be implemented. Establishes tenant context propagation, middleware, storage isolation, and agent handoff support.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Extend TenantContext dataclass in apps/api/app/core/tenant_context.py: add `tenant_id: str` field (default `"live"`), add `is_simulation` property (`tenant_id != "live"`), update `scope_key` property to include `tenant_id` as outermost prefix. Add `get_current_tenant()` and `set_current_tenant()` functions using `contextvars.ContextVar`
- [X] T005 [P] Extend auth.py in apps/api/app/core/auth.py: extract `SimulationUser` app role from Entra ID token claims in `extract_principal_from_claims()`, add `has_simulation_role` property to `AuthenticatedPrincipal`
- [X] T006 [P] Create SimulationTenant domain model in packages/domain/src/domain/models/simulation_tenant.py with all fields from data-model.md: `tenant_id`, `scenario_id`, `scenario_run_id`, `scenario_type` enum, `status` enum with state transitions (`provisioning → active ↔ paused → archiving → archived → deleted`), `participants` list, `resource_limits`, `resource_consumption`, `throttle_mode`, `throttle_quota_pct`. Include validation for `tenant_id` pattern `^sim-[a-z0-9-]{36}$`
- [X] T007 [P] Extend ScenarioRun model in packages/domain/src/domain/models/scenario_run.py: add `tenant_id`, `exercise_report_uri`, `archive_status` enum (`pending | archived | failed`), `resource_consumption`, `document_type` discriminator fields
- [X] T008 Extend cosmos_scope.py in apps/api/app/repositories/cosmos_scope.py: update `scoped_partition_key()` and `signal_partition_key()` to incorporate `tenant_id` from `TenantContext`. Add `simulation_partition_key(scenario_id)` builder for the simulation container. **Also**: audit and update all existing Redis callers across the codebase to use tenant-prefixed keys per pattern `{tenant_id}:{resource_type}:{resource_id}` (research R3), ensuring live callers use `live:` prefix and simulation callers use `sim-{id}:` prefix
- [X] T009 Create simulation_repository.py in apps/api/app/repositories/simulation_repository.py: Cosmos DB operations for SimulationTenant CRUD (create, read, update, list by status, list by participant OID), ScenarioTemplate read, point-read for participant validation. Use `simulation` container with `/scenario_id` partition key
- [X] T010 Implement tenant middleware in apps/api/app/middleware/tenant_middleware.py per contracts/tenant-middleware.md: extract authenticated principal → resolve `tenant_id` (path-based for `/api/simulations/{tenantId}/*`, participant lookup for other routes, default `live`) → build TenantContext → set in `contextvars` → add `tenant_id` custom dimension to telemetry. Implement error handling: 401/403/404/409/503 per contract. Register middleware in FastAPI app startup
- [X] T011 [P] Extend RBAC in apps/api/app/api/dependencies/rbac.py: add `require_simulation_role` dependency that checks `SimulationUser` app role. Add `require_simulation_participant(tenant_id)` dependency that validates user OID is in SimulationTenant.participants via simulation_repository point-read
- [X] T012 [P] Extend handoffs.py in apps/agents/common/handoffs.py: add `tenant_id` field to `AgentHandoffEvent`. Ensure `create_handoff_event()` inherits `tenant_id` from the triggering signal's scope. Ensure agent processing sets TenantContext from handoff payload before state writes
- [X] T012b [P] Create simulation_audit_writer.py in apps/api/app/services/simulation_audit_writer.py: on every safety-critical action within a simulation tenant (signal write, recommendation, approval, alert, agent handoff), write an audit event to blob storage at `audit/{tenant_id}/{date}/{event_id}.json` in append-only mode (FR-025). Must operate during active simulation, not only at archive time. Use the existing blob storage client from `apps/api/app/core/storage.py`

**Checkpoint**: Tenant context propagation, middleware, storage isolation, agent handoff, and runtime audit trail all functional. User story implementation can begin.

---

## Phase 3: User Story 1 — Create and run a simulation exercise alongside live operations (Priority: P1) 🎯 MVP

**Goal**: Exercise coordinators can create simulation tenants, inject synthetic signals, and operate a simulation dashboard — all fully isolated from live data. Simulated alerts are blocked from real delivery channels.

**Independent Test**: Create a simulation tenant, inject synthetic signals, verify they appear only in the simulation view, confirm the live dashboard is unaffected, and verify simulated alerts are blocked from real channels.

### Implementation for User Story 1

- [X] T013 [P] [US1] Create signal_repository.py in apps/api/app/repositories/signal_repository.py: tenant-scoped signal read/write operations against the `signals` Cosmos DB container. Use `scope` field from `TenantContext.tenant_id` in partition key. Support `list_by_tenant()`, `create_signal()`, `get_signal()` operations
- [X] T014 [P] [US1] Create simulation_validators.py in apps/api/app/validators/simulation_validators.py: validate concurrency limits (max active simulations from settings), validate resource budget (max_signals, max_recommendations, max_duration_hours), validate participant list is non-empty and contains creator
- [X] T015 [US1] Create simulation_service.py in apps/api/app/services/simulation_service.py: implement `create_tenant()` (provision storage partition + cache namespace + audit prefix within 30s per NFR-001), `get_tenant()`, `list_tenants()`. Orchestrate SimulationRepository, SimulationValidators, and Redis namespace creation. Set initial status to `provisioning`, transition to `active` on completion
- [X] T016 [US1] Create simulations.py routes in apps/api/app/api/routes/simulations.py: implement `POST /api/simulations` (create tenant, 201), `GET /api/simulations` (list with status/limit/offset filtering, 200), `GET /api/simulations/{tenantId}` (detail, 200) per contracts/simulation-api.md. Wire RBAC dependencies (`require_simulation_role`, `require_simulation_participant`)
- [X] T017 [US1] Implement TenantAwareAlertGate: in the alert publication service, add a hard gate that checks `TenantContext.is_simulation` before delivering to any real channel (SMS, broadcast, social media). If simulation, record alert as `published (simulation)` in simulation audit trail and block delivery. Per research R8, this is a code-level gate with no bypass
- [X] T018 [P] [US1] Create simulation API client in apps/web/src/lib/api/simulations.ts: typed fetch wrappers for all simulation endpoints (create, list, get detail, pause, resume, archive, delete, seed, replay, participants, report) per contracts/simulation-api.md
- [X] T019 [P] [US1] Create simulation-banner component in apps/web/src/components/simulation-banner.tsx: persistent, prominent fixed-position banner displaying "SIMULATION" that cannot be dismissed, minimised, or obscured (FR-021). Rendered when route starts with `/simulations/`
- [X] T020 [US1] Create simulation list page in apps/web/src/app/simulations/page.tsx: display all accessible simulation tenants with tenant_id, scenario_type, status, created_at, participant_count, signal_count, storage_bytes. Include "Create Simulation" action for users with SimulationUser role
- [X] T021 [US1] Create simulation dashboard page in apps/web/src/app/simulations/[tenantId]/page.tsx: reuse existing live dashboard components but scoped to simulation tenant data via API calls with tenant context. Include persistent SIMULATION banner. Must be functionally identical to live dashboard per FR-020

**Checkpoint**: User Story 1 complete — simulation tenants can be created, signals injected, dashboard shows simulation-only data, live dashboard is unaffected, simulated alerts are blocked from real channels.

---

## Phase 4: User Story 2 — Seed a simulation with realistic scenario data (Priority: P2)

**Goal**: Exercise coordinators can seed simulations with curated scenario templates (bushfire, flood, cyclone) or replay historical live incidents, producing a realistic starting operational picture.

**Independent Test**: Load a bushfire scenario template into a simulation tenant and verify all seeded organisations, frameworks, and signals appear in the simulation dashboard with correct provenance and time offsets.

### Implementation for User Story 2

- [X] T022 [P] [US2] Create ScenarioTemplate domain model in packages/domain/src/domain/models/scenario_template.py with all fields from data-model.md: `template_id`, `kind` (partition key = `"scenario_template"`), `scenario_type` enum, `seed_organisations`, `seed_jurisdictions`, `seed_framework_ids`, `signal_timeline` (list of `{offset_seconds, signal_envelope}`), `benchmark_targets`. Validate `signal_timeline` sorted ascending by `offset_seconds`
- [X] T023 [US2] Create scenario_seeding_service.py in apps/api/app/services/scenario_seeding_service.py: implement `seed_from_template(tenant_id, template_id)` — load ScenarioTemplate from seed container, create organisations/jurisdictions/frameworks in simulation partition, inject signals with provenance `source_context: "simulation"`. Implement `seed_from_replay(tenant_id, incident_id, start, end)` — copy historical signals from live partition into simulation partition with regenerated IDs and fresh provenance
- [X] T024 [US2] Implement real-time signal timeline replay in scenario_seeding_service.py: when `replay_mode = "real-time"`, schedule signal injection at `offset_seconds` from exercise start time using an async task scheduler. Support time compression via configurable multiplier
- [X] T025 [US2] Add seeding routes to apps/api/app/api/routes/simulations.py: `POST /api/simulations/{tenantId}/seed` (template-based, 202), `POST /api/simulations/{tenantId}/seed/replay` (historical replay, 202) per contracts/simulation-api.md. Validate tenant is in `active` status before seeding

**Checkpoint**: User Story 2 complete — simulation tenants can be seeded with curated scenario packs or historical replays. Signals appear with correct provenance and time offsets.

---

## Phase 5: User Story 3 — Operate a persona-specific workspace within a simulation (Priority: P2)

**Goal**: Participants are assigned persona roles within a simulation and see only simulation data scoped to their role and jurisdiction, with full approval workflow operating within the simulation boundary.

**Independent Test**: Assign an incident commander persona to a simulation tenant, verify the workspace shows only simulation-scoped tasks and recommendations, and confirm approval actions within the simulation do not generate live approvals.

### Implementation for User Story 3

- [X] T026 [US3] Add participants route to apps/api/app/api/routes/simulations.py: `POST /api/simulations/{tenantId}/participants` to add participants with persona assignments per contracts/simulation-api.md. Validate participant OIDs, update SimulationTenant.participants list, store persona assignments
- [X] T027 [US3] Extend simulation dashboard in apps/web/src/app/simulations/[tenantId]/page.tsx to apply persona-scoped workspace filtering: filter tasks, signals, and recommendations by logged-in participant's assigned persona role and jurisdiction, identically to live workspace filtering logic (FR-024)
- [X] T028 [US3] Verify existing approval workflow operates within simulation tenant boundary: ensure recommendation review, approval, rejection, escalation actions in the simulation are recorded in simulation audit trail only (FR-018). Confirm no cross-tenant state mutations

**Checkpoint**: User Story 3 complete — participants operate persona-scoped workspaces within simulations. Approval workflow is fully scoped to simulation tenant.

---

## Phase 6: User Story 4 — Review simulation outcomes and produce exercise reports (Priority: P3)

**Goal**: After an exercise, coordinators generate structured reports comparing simulation performance against benchmarks, with full decision timeline and coordination gap analysis.

**Independent Test**: Complete a short simulation exercise, trigger report generation, and verify the report includes decision timeline, coordination gaps, and performance metrics compared against scenario benchmarks.

### Implementation for User Story 4

- [X] T029 [P] [US4] Create ExerciseReport domain model in packages/domain/src/domain/models/exercise_report.py with all fields from data-model.md: `report_id`, `tenant_id`, `scenario_run_id`, `scenario_type`, `generated_at`, `exercise_timeline`, `participating_organisations`, `participating_personas`, `signal_summary`, `recommendation_summary`, `alert_summary`, `coordination_gaps`, `performance_metrics`, `benchmark_comparison`
- [X] T030 [US4] Create exercise_report_service.py in apps/api/app/services/exercise_report_service.py: query simulation tenant's Cosmos DB partition for all signals, recommendations, approvals, alerts, timeline events. Aggregate metrics (time_to_first_recommendation, time_to_alert_publication, coordination_coverage). Compare against benchmark_targets from ScenarioTemplate. Render report as JSON, store in blob storage at `simulation/{tenant_id}/reports/{report_id}.json`
- [X] T031 [US4] Add report route to apps/api/app/api/routes/simulations.py: `GET /api/simulations/{tenantId}/report` (200) per contracts/simulation-api.md. Return 404 if report not yet generated, 409 if simulation still active
- [X] T032 [US4] Create exercise report view page in apps/web/src/app/simulations/reports/[reportId]/page.tsx: display exercise timeline, participating organisations and personas, signal/recommendation/alert summaries, coordination gaps, performance metrics, and side-by-side benchmark comparison

**Checkpoint**: User Story 4 complete — exercise reports generated with full decision timeline, coordination gap analysis, and benchmark comparison.

---

## Phase 7: User Story 5 — Manage simulation tenant lifecycle and resource governance (Priority: P3)

**Goal**: Administrators manage simulation lifecycle (pause, resume, archive, delete), enforce concurrency limits, resource budgets, TTL-based auto-cleanup, and auto-throttling during live incidents.

**Independent Test**: Create multiple simulation tenants, verify concurrency limits are enforced, trigger auto-archival of an expired simulation, and confirm that archived simulations retain audit trails but release operational resources.

### Implementation for User Story 5

- [X] T033 [P] [US5] Create resource_governor.py in apps/api/app/services/resource_governor.py: monitor shared resource utilisation (Cosmos DB RU consumption, Redis memory, LLM token usage). Implement token bucket rate limiter for simulation writes. When utilisation exceeds `throttle_threshold_pct` (70%), throttle simulation writes. When live incident declared, set all active simulations to `incident-throttled` mode at `incident_throttle_quota_pct` (20%) per research R6
- [X] T034 [US5] Add lifecycle routes to apps/api/app/api/routes/simulations.py: `POST /api/simulations/{tenantId}/pause` (200), `POST /api/simulations/{tenantId}/resume` (200), `POST /api/simulations/{tenantId}/archive` (202), `DELETE /api/simulations/{tenantId}` (204, requires `archived` status) per contracts/simulation-api.md. Validate state transitions per data-model.md lifecycle
- [X] T035 [US5] Implement archive workflow in simulation_service.py: trigger exercise report generation (ExerciseReportService), persist audit trail to immutable blob storage at `simulation/{tenant_id}/archive/`, clean up Cosmos DB partition contents and Redis namespace keys. Must complete within 5 minutes for up to 10,000 signals (NFR-005)
- [X] T036 [US5] Implement TTL monitoring and auto-archival in simulation_service.py: scheduled check for simulations past `expires_at`. Notify coordinator 24 hours before auto-archival (FR-011). Auto-trigger archive workflow for expired simulations
- [X] T037 [US5] Implement live incident auto-throttle in resource_governor.py: when a live incident is declared, automatically set all active simulation tenants to `throttle_mode: "incident-throttled"` with `throttle_quota_pct: 20`. Notify simulation participants. Restore `normal` mode when incident is resolved (FR-028)
- [X] T037b [US5] Create incident declaration endpoint in apps/api/app/api/routes/incidents.py: `POST /api/incidents/declare` (sets system to live-incident mode, triggers FR-028 auto-throttle) and `POST /api/incidents/resolve` (restores normal mode). Requires admin role. Stores incident state in governance Cosmos container. Referenced by resource_governor.py for throttle triggers (FR-031)
- [X] T038 [US5] Update simulation list page in apps/web/src/app/simulations/page.tsx: add resource consumption display (storage_bytes, cache_keys, signal_count), lifecycle controls (pause, resume, archive, delete buttons), and throttle status indicators

**Checkpoint**: User Story 5 complete — full lifecycle management, resource governance, TTL auto-cleanup, and live incident throttling operational.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Infrastructure updates, test coverage, and end-to-end validation across all user stories

- [X] T039 [P] Extend infra/main.bicep: ensure `simulation` Cosmos DB container exists with `/scenario_id` partition key and composite indexes per data-model.md (`document_type + status`, `document_type + created_at`, `document_type + expires_at`)
- [X] T040 [P] Extend infra/modules/monitoring.bicep: add `tenant_id` custom dimension to Application Insights configuration for per-tenant filtering, dashboards, and alerting (NFR-006)
- [X] T041 [P] Create unit tests: tests/unit/test_tenant_context.py (tenant_id propagation, is_simulation, scope_key), tests/unit/test_simulation_service.py (lifecycle, provisioning, concurrency), tests/unit/test_resource_governor.py (token bucket, throttle modes), tests/unit/test_scenario_seeding.py (template loading, replay, signal injection)
- [X] T042 [P] Create integration tests: tests/integration/test_tenant_isolation.py (cross-tenant leakage tests — simulation signals invisible to live, live signals invisible to simulation, cross-simulation isolation, agent chain stays in tenant, partition key enforces scope, Redis keys prefixed, **ingestion pipelines cannot route data to simulation tenants (FR-004)**, **live dashboard contains no simulation data, tenant switcher, toggle, or controls; developer environments may link to the separate management area (FR-022)**), tests/integration/test_simulation_lifecycle.py (full lifecycle: create → seed → operate → archive → delete)
- [X] T043 [P] Create contract tests: tests/contract/test_simulation_api_contract.py (all endpoints from contracts/simulation-api.md — request/response schemas, status codes, error conditions)
- [X] T044 Run quickstart.md end-to-end validation: create simulation tenant, seed scenario, add participants, verify tenant isolation, run cross-tenant leakage checks, monitor via App Insights KQL, exercise lifecycle operations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational ← **MVP target**
- **User Story 2 (Phase 4)**: Depends on Foundational; uses SimulationRepository from Phase 2 and signal_repository from US1
- **User Story 3 (Phase 5)**: Depends on Foundational; uses simulation dashboard from US1
- **User Story 4 (Phase 6)**: Depends on US1 (tenant + signals); benefits from US2 (scenario templates for benchmarks)
- **User Story 5 (Phase 7)**: Depends on Foundational **and US4 (T030 ExerciseReportService)** — archive workflow calls report generation
- **Polish (Phase 8)**: Can start infrastructure tasks (T039, T040) in parallel with user stories; tests depend on corresponding story completion

### User Story Dependencies

```
Phase 1: Setup ──────────────────────────────────────────────────────────────────
                │
Phase 2: Foundational (BLOCKING) ───────────────────────────────────────────────
                │
                ├── Phase 3: US1 (P1) ── MVP ──────────────────────────────────
                │       │                    │
                │       ├── Phase 4: US2 (P2) ──── uses signal_repository
                │       │
                │       ├── Phase 5: US3 (P2) ──── uses simulation dashboard
                │       │
                │       └── Phase 6: US4 (P3) ──── uses tenant + signals
                │                       │
                │                       └── Phase 7: US5 (P3) ─── requires US4 T030 (ExerciseReportService)
                │
Phase 8: Polish (infra tasks can run any time; tests after stories) ────────────
```

### Within Each User Story

- Models/entities before services
- Services before routes/endpoints
- Backend before frontend
- Core implementation before integration

### Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel
- **Foundational**: T005, T006, T007 can run in parallel (different files, no dependencies). T011 and T012 can run in parallel after T004 and T009 complete
- **US1**: T013 and T014 can run in parallel. T018 and T019 can run in parallel (frontend components)
- **US2**: T022 can run in parallel with US1 tasks (different domain model file)
- **US4**: T029 can run in parallel with other story work (domain model file)
- **US5**: T033 can run in parallel with US4 tasks (different service file)
- **Polish**: T039, T040, T041, T042, T043 can all run in parallel

---

## Parallel Example: User Story 1 (MVP)

```text
T013 [signal_repository.py] ──┐
                               ├──→ T015 [simulation_service.py] ──→ T016 [simulations.py routes]
T014 [simulation_validators.py]┘                                         │
                                                                         ↓
T017 [TenantAwareAlertGate] ─────────────────────────────────────────── (done)

T018 [simulations.ts client] ──┐
                                ├──→ T020 [simulation list page] ──→ T021 [simulation dashboard]
T019 [simulation-banner.tsx] ──┘
```

Backend and frontend tracks can proceed in parallel once Phase 2 is complete.

---

## Implementation Strategy

### MVP Scope (Suggested: User Story 1 only)

Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1) delivers a functional simulation system where:
- Exercise coordinators create simulation tenants
- Synthetic signals are injected and fully isolated from live
- Simulation dashboard shows simulation-only data
- Live dashboard is completely unaffected
- Simulated alerts never reach real channels

This is the minimum viable product. All subsequent stories are incremental additions.

### Incremental Delivery Order

1. **MVP**: Setup → Foundational → US1 (tenant creation + isolation + dashboard)
2. **Scenario Seeding**: US2 (adds realistic exercise content)
3. **Persona Workspaces**: US3 (adds role-based participation)
4. **Exercise Reports**: US4 (adds post-exercise analysis)
5. **Lifecycle Governance**: US5 (adds operational hygiene + throttling)
6. **Polish**: Infrastructure + tests + validation
