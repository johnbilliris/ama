# Tasks: Multi-Jurisdiction Filter for Preparedness Page

**Input**: Design documents from `/specs/022-multi-jurisdiction-filter/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/jurisdiction-filter-api.yaml ✅, research.md ✅, quickstart.md ✅

**Tests**: Included — API tests (pytest unit/integration/contract) and Playwright E2E tests as requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `apps/web/src/` (Next.js 16.2 + React 19 + TypeScript 5.8)
- **Backend**: `apps/api/app/` (FastAPI 0.115 + Pydantic 2.10)
- **Domain**: `packages/domain/src/domain/` (shared models and seed data)
- **Tests**: `tests/` (pytest: unit, integration, contract) and `apps/web/` (Playwright E2E)

---

## Phase 1: Setup (Seed Data Infrastructure)

**Purpose**: Create the missing FrameworkAssignment seed data that enables jurisdiction-based framework filtering (per research R-006 — current codebase synthesises assignments on-the-fly but has no seed data, making framework filtering impossible).

- [ ] T001 Create framework-jurisdiction assignment seed data file at packages/domain/src/domain/seed/framework_assignments_australia.json following the pattern in data-model.md: each record links a framework_id to a jurisdiction_id with assignment_id pattern `assign-{framework_id}-{jurisdiction_id}`, effective_from date, and null effective_to for current assignments. National frameworks (e.g., aiims-national) must be assigned to all 9 jurisdictions; state-specific frameworks to their respective jurisdiction only.
- [ ] T002 Update bootstrap_seed_data() to load framework_assignments seed file in packages/domain/src/domain/seed/bootstrap.py — add `"framework_assignments": load_seed_file(seed_root / "framework_assignments_australia.json")` following the existing pattern for other seed files.

---

## Phase 2: Foundational — Backend Multi-Jurisdiction Data Layer

**Purpose**: Enable all API endpoints to accept multiple jurisdiction identifiers and return filtered, deduplicated results. This implements User Story 4 (P4) as foundational infrastructure because it BLOCKS all frontend user stories.

**⚠️ CRITICAL**: No frontend user story work can begin until this phase is complete.

### Tests for Foundational Phase ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T003 [P] Write unit tests for multi-jurisdiction organisation filtering in tests/unit/test_multi_jurisdiction_org_filter.py — test OrganisationIntelligenceService.list_organisations() with: empty list returns empty result, single jurisdiction returns matching orgs, multiple jurisdictions returns union with no duplicates, organisation with multiple jurisdiction_ids appears once when multiple of its jurisdictions are selected, jurisdiction with no matching organisations returns empty list
- [ ] T004 [P] Write unit tests for framework-by-jurisdiction filtering via FrameworkAssignment in tests/unit/test_multi_jurisdiction_framework_filter.py — test that: frameworks are returned only when a FrameworkAssignment links them to a selected jurisdiction, national frameworks appear for any jurisdiction, state-specific frameworks only appear for their jurisdiction, empty jurisdiction list returns empty result, jurisdiction with no framework assignments returns empty list
- [ ] T005 [P] Write integration tests for multi-jurisdiction API endpoints in tests/integration/test_multi_jurisdiction_api.py — test GET /api/jurisdictions returns 200 with 9 jurisdictions ordered by level; GET /api/organisations with repeated jurisdictionId params returns filtered orgs; GET /api/frameworks with repeated jurisdictionId params returns filtered frameworks via assignments; backward compatibility: single jurisdictionId=nsw still works; empty params return empty arrays per FR-006
- [ ] T006 [P] Add multi-jurisdiction contract tests in tests/contract/test_preparedness_contract.py — add tests verifying: GET /api/jurisdictions returns array of JurisdictionSummary objects with jurisdiction_id, name, level fields; GET /api/organisations?jurisdictionId=nsw&jurisdictionId=vic returns organisations matching either jurisdiction; GET /api/frameworks?jurisdictionId=nsw returns frameworks assigned to NSW; response schemas match contracts/jurisdiction-filter-api.yaml

### Implementation for Foundational Phase

- [ ] T007 [P] Update OrganisationIntelligenceService.list_organisations() to accept jurisdiction_ids: list[str] parameter (replacing jurisdiction_id: str | None) in apps/api/app/services/organisation_intelligence_service.py — filter with OR logic: return organisations where any of org.jurisdiction_ids overlaps with the requested list; return empty list when jurisdiction_ids is empty; maintain backward compatibility by accepting single-element lists
- [ ] T008 [P] Add list_frameworks_by_jurisdictions(jurisdiction_ids: list[str]) method to PreparednessAnalysisService in apps/api/app/services/preparedness_analysis_service.py — load FrameworkAssignment seed data, find assignments where jurisdiction_id is in the requested set and effective_to is None, return distinct OperatingFramework objects referenced by those assignments; return empty list when jurisdiction_ids is empty
- [ ] T009 [P] Create GET /api/jurisdictions endpoint in apps/api/app/api/routes/jurisdictions.py — return active jurisdictions from seed data as JurisdictionSummary objects (jurisdiction_id, name, level), ordered by level (commonwealth first, then states alphabetically, then territories alphabetically) per the contract; accept tenant_id from request.state.tenant_context as pass-through per FR-005/R-007
- [ ] T010 [P] Modify GET /api/organisations to accept list[str] jurisdictionId query parameter in apps/api/app/api/routes/organisations.py — change parameter from `jurisdictionId: str | None = None` to `jurisdictionId: list[str] = Query(default=[])` per research R-002; pass list to updated service method; empty list returns empty array per FR-006
- [ ] T011 [P] Modify GET /api/frameworks to accept list[str] jurisdictionId + FrameworkAssignment-based filtering in apps/api/app/api/routes/frameworks.py — change parameter from `jurisdictionId: str | None = None` to `jurisdictionId: list[str] = Query(default=[])` per research R-002; remove hardcoded `["nsw"]` fallback; call new list_frameworks_by_jurisdictions() service method; empty list returns empty array per FR-006
- [ ] T012 Register jurisdictions router in apps/api/app/api/router.py — add `api_router.include_router(jurisdictions_router, prefix="/jurisdictions", tags=["jurisdictions"])` following the existing router registration pattern

**Checkpoint**: Backend API supports multi-jurisdiction filtering. Verify: `curl http://localhost:8000/api/jurisdictions` returns 9 jurisdictions; `curl "http://localhost:8000/api/organisations?jurisdictionId=nsw&jurisdictionId=vic"` returns combined NSW+VIC orgs; all pytest tests pass.

---

## Phase 3: User Story 1 — Select Jurisdictions to View Organisations and Frameworks (Priority: P1) 🎯 MVP

**Goal**: Enable users to select one or more jurisdictions from a dropdown and dynamically filter Organisation Catalog and Framework Catalog based on the selection, with URL persistence, debounced fetching, and inline loading/error states.

**Independent Test**: Load `/preparedness`, select "VIC" → Organisation and Framework catalogs update to show only VIC data. Select "NSW" and "QLD" → combined results with no duplicates. Clear all → empty state prompt. Copy URL → open in new tab → same selection restored.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create jurisdictions API client in apps/web/src/lib/api/jurisdictions.ts — export JurisdictionSummary interface (jurisdiction_id, name, level) and async function listJurisdictions() that fetches GET /api/jurisdictions with cache: "no-store", following the existing API client pattern in organisations.ts
- [ ] T014 [P] [US1] Modify organisations API client to support repeated query params in apps/web/src/lib/api/organisations.ts — change listPreparednessOrganisations(jurisdictionId: string) to listPreparednessOrganisations(jurisdictionIds: string[]) that builds URL with URLSearchParams.append("jurisdictionId", id) for each ID per quickstart.md API call pattern
- [ ] T015 [P] [US1] Modify frameworks API client to support repeated query params in apps/web/src/lib/api/frameworks.ts — change listPreparednessFrameworks(jurisdictionId: string) to listPreparednessFrameworks(jurisdictionIds: string[]) that builds URL with URLSearchParams.append("jurisdictionId", id) for each ID, following the same pattern as T014
- [ ] T016 [P] [US1] Create JurisdictionSelector component in apps/web/src/components/preparedness/jurisdiction-selector.tsx — WCAG 2.1 AA-compliant multi-select listbox with checkboxes per research R-005: button trigger showing "{n} jurisdictions selected" with aria-expanded; dropdown panel with role="listbox"; items with role="option" and aria-selected; "Select All" and "Clear All" buttons (FR-001); keyboard navigation: Tab to focus, Enter/Space to open, Arrow Up/Down to navigate, Space to toggle, Escape to close (NFR-001); group by level: commonwealth first, then states, then territories; display full names (FR-008); props: jurisdictions: JurisdictionSummary[], selectedIds: string[], onChange: (ids: string[]) => void
- [ ] T017 [US1] Refactor OperatingModelAnalyzer to accept data as props in apps/web/src/components/preparedness/operating-model-analyzer.tsx — change from internal data fetching to receiving organisations, frameworks, selectedJurisdictionIds, and isLoading/error states as props; remove hardcoded "nsw" from DEFAULT_SCENARIO.jurisdiction_ids; remove internal fetch calls; keep replay UI and scenario configuration; add empty state display when no jurisdictions selected (FR-006); add inline loading indicators per catalog (FR-013); add inline error with retry action per catalog (FR-012)
- [ ] T018 [US1] Create PreparednessClient component in apps/web/src/components/preparedness/preparedness-client.tsx — client component ("use client") orchestrating all state per research R-001/R-004: manage selectedJurisdictionIds state initialized from URL params; implement useDebounce hook with 300ms delay (NFR-002); fetch organisations and frameworks in parallel using AbortController for stale request cancellation; manage per-catalog loading and error states; sync selection to URL via router.replace() with comma-separated format /preparedness?jurisdictions=nsw,vic (FR-014 per research R-003); silently ignore invalid jurisdiction IDs from URL (FR-014); render JurisdictionSelector and OperatingModelAnalyzer passing all state as props
- [ ] T019 [US1] Convert page.tsx to hybrid server/client architecture in apps/web/src/app/preparedness/page.tsx — change from fetching hardcoded "nsw" orgs/frameworks to: server-side fetch jurisdiction list via listJurisdictions(); read searchParams.jurisdictions and split on comma; validate IDs against jurisdiction list, silently drop invalid ones (FR-014); pass jurisdictions list and initialSelectedIds to PreparednessClient; remove direct import of OperatingModelAnalyzer (now rendered by PreparednessClient)

**Checkpoint**: User Story 1 is fully functional. Verify: jurisdiction selector shows all jurisdictions; selecting jurisdictions filters both catalogs; URL updates and is restorable; debounce prevents excessive API calls; loading/error states display correctly; empty state shown when nothing selected.

---

## Phase 4: User Story 2 — Run Rehearsal Replay Across Selected Jurisdictions (Priority: P2)

**Goal**: Ensure rehearsal replay uses the user's selected jurisdictions instead of hardcoded values, with stale replay detection when jurisdictions change after a replay.

**Independent Test**: Select "NSW" and "VIC", run bushfire rehearsal replay → findings and coordination gaps reflect both jurisdictions. Change selection to "SA" → previous replay results cleared with notice. Clear all jurisdictions → replay button disabled.

### Implementation for User Story 2

- [ ] T020 [US2] Add replay jurisdiction tracking and stale detection to PreparednessClient in apps/web/src/components/preparedness/preparedness-client.tsx — track replayJurisdictions state (the jurisdiction set at time of last replay); on replay completion, store current selectedJurisdictionIds as replayJurisdictions; on jurisdiction selection change, compare with replayJurisdictions using sorted array equality; if different, set replayStale flag; pass replayStale and onReplayComplete callback to OperatingModelAnalyzer
- [ ] T021 [US2] Update OperatingModelAnalyzer to pass selected jurisdictions to replay request in apps/web/src/components/preparedness/operating-model-analyzer.tsx — replace hardcoded `["nsw"]` in replayPreparednessScenario() call with selectedJurisdictionIds prop; when replayStale is true, clear displayed replay results and show notice: "Replay results were generated for different jurisdictions. Run a new replay for updated results." (FR-015); call onReplayComplete when replay finishes
- [ ] T022 [US2] Disable replay button when no jurisdictions selected in apps/web/src/components/preparedness/operating-model-analyzer.tsx — when selectedJurisdictionIds is empty, disable the "Run rehearsal replay" button and display message "Select at least one jurisdiction to run a rehearsal replay" (FR-006, FR-011)

**Checkpoint**: Rehearsal replay uses selected jurisdictions. Verify: replay request includes selected jurisdiction IDs; changing jurisdictions after replay shows stale notice; replay button disabled when no jurisdictions selected.

---

## Phase 5: User Story 3 — View All Nine Jurisdictions in the Selector (Priority: P3)

**Goal**: Ensure the jurisdiction selector presents all nine Australian jurisdictions (Commonwealth + 6 states + 2 territories) with correct display names, enabling national-level disaster coordination planning.

**Independent Test**: Open the jurisdiction selector → verify all 9 jurisdictions listed: Commonwealth of Australia, New South Wales, Victoria, Queensland, South Australia, Western Australia, Tasmania, Australian Capital Territory, Northern Territory. Each shows full name, can be individually selected/deselected.

### Implementation for User Story 3

- [ ] T023 [US3] Validate jurisdiction seed data completeness in packages/domain/src/domain/seed/jurisdictions_australia.json — verify all 9 Australian jurisdictions are present with status "active": commonwealth (Commonwealth of Australia), nsw (New South Wales), vic (Victoria), qld (Queensland), sa (South Australia), wa (Western Australia), tas (Tasmania), act (Australian Capital Territory), nt (Northern Territory); verify level values are correct (1 commonwealth, 6 states, 2 territories)
- [ ] T024 [US3] Verify JurisdictionSelector displays jurisdictions grouped by level in apps/web/src/components/preparedness/jurisdiction-selector.tsx — ensure rendering order matches API contract: commonwealth first, then states alphabetically, then territories alphabetically; verify each option displays the full human-readable name from the name field, not the jurisdiction_id (FR-008); verify all 9 items render when the jurisdictions API returns the complete list

**Checkpoint**: All nine Australian jurisdictions are available in the selector with full names and correct grouping.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: E2E validation, documentation, and final quality checks.

- [ ] T025 [P] Create Playwright E2E test for multi-jurisdiction filter workflow in tests/e2e/multi-jurisdiction-filter.spec.ts — test scenarios from quickstart.md manual testing checklist: empty state on load; single jurisdiction selection updates catalogs; multi-jurisdiction selection shows combined results; Select All / Clear All; URL persistence (navigate, verify params, reload, verify restored); invalid URL params silently dropped; rehearsal replay uses selected jurisdictions; replay stale notice on jurisdiction change; replay button disabled when empty; keyboard navigation of selector
- [ ] T026 Run quickstart.md validation — execute all manual testing checklist steps from specs/022-multi-jurisdiction-filter/quickstart.md to verify the complete feature works end-to-end: empty state, single selection, multi selection, Select All, Clear All, URL persistence, invalid URL handling, rehearsal replay, replay disabled, loading states, error handling, keyboard navigation, debounce behavior
- [ ] T027 Final code review and cleanup — verify no remaining hardcoded "nsw" references in modified files; confirm all API responses match contracts/jurisdiction-filter-api.yaml schemas; verify tenant_id pass-through in all route handlers (FR-005); ensure no duplicate results when Commonwealth + state jurisdictions selected (FR-009); run full pytest suite and confirm all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001, T002) — seed data must be loadable for services and tests. **BLOCKS all frontend work**
- **User Story 1 (Phase 3)**: Depends on Foundational phase — backend must accept multi-jurisdiction queries
- **User Story 2 (Phase 4)**: Depends on User Story 1 — replay integration requires the selector and PreparednessClient to exist
- **User Story 3 (Phase 5)**: Depends on User Story 1 — selector must exist to validate display; can run in parallel with US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — core selector and catalog filtering
- **User Story 2 (P2)**: Depends on US1 — modifies PreparednessClient and OperatingModelAnalyzer created in US1
- **User Story 3 (P3)**: Depends on US1 — validates selector created in US1. Can run in parallel with US2
- **User Story 4 (P4)**: Implemented as Foundational (Phase 2) because it enables all other stories

### Within Each Phase

- Tests MUST be written and FAIL before implementation (Phases 2)
- Services before routes (Phase 2: T007-T008 before T009-T011)
- API clients before components (Phase 3: T013-T015 before T016-T018)
- Component refactor before orchestrator (Phase 3: T017 before T018)
- Orchestrator before page (Phase 3: T018 before T019)

### Parallel Opportunities

**Phase 1** (2 tasks — sequential, T002 depends on T001):
```
T001 → T002
```

**Phase 2** (10 tasks — significant parallelism):
```
# Tests first (all parallel):
T003 ─┐
T004 ─┤ (all different test files / sections)
T005 ─┤
T006 ─┘
      │
      ▼
# Services (parallel, different files):
T007 ─┐
T008 ─┘
      │
      ▼
# Routes (parallel, different files) + router registration:
T009 ─┐
T010 ─┤
T011 ─┘
      │
      ▼
T012 (register router — depends on T009 existing)
```

**Phase 3** (7 tasks):
```
# API clients + selector (all parallel, different files):
T013 ─┐
T014 ─┤
T015 ─┤
T016 ─┘
      │
      ▼
T017 (refactor OperatingModelAnalyzer — new prop interface)
      │
      ▼
T018 (PreparednessClient — orchestrates T013-T016 + T017)
      │
      ▼
T019 (page.tsx — renders T018)
```

**Phases 4 + 5** (can run in parallel with each other):
```
Phase 4: T020 → T021 → T022
Phase 5: T023 → T024
```

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all test-writing tasks together:
Task T003: "Unit tests for multi-jurisdiction org filtering in tests/unit/test_multi_jurisdiction_filter.py"
Task T004: "Unit tests for framework-by-jurisdiction filtering in tests/unit/test_multi_jurisdiction_filter.py"
Task T005: "Integration tests for multi-jurisdiction API in tests/integration/test_multi_jurisdiction_api.py"
Task T006: "Contract tests for multi-jurisdiction in tests/contract/test_preparedness_contract.py"

# Then launch service updates together:
Task T007: "Update OrganisationIntelligenceService in apps/api/app/services/organisation_intelligence_service.py"
Task T008: "Update PreparednessAnalysisService in apps/api/app/services/preparedness_analysis_service.py"

# Then launch route updates together:
Task T009: "Create jurisdictions route in apps/api/app/api/routes/jurisdictions.py"
Task T010: "Modify organisations route in apps/api/app/api/routes/organisations.py"
Task T011: "Modify frameworks route in apps/api/app/api/routes/frameworks.py"
```

## Parallel Example: Phase 3 User Story 1

```bash
# Launch all API clients + selector together:
Task T013: "Create jurisdictions API client in apps/web/src/lib/api/jurisdictions.ts"
Task T014: "Modify organisations API client in apps/web/src/lib/api/organisations.ts"
Task T015: "Modify frameworks API client in apps/web/src/lib/api/frameworks.ts"
Task T016: "Create JurisdictionSelector in apps/web/src/components/preparedness/jurisdiction-selector.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (seed data)
2. Complete Phase 2: Foundational backend (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (selector + catalog filtering)
4. **STOP and VALIDATE**: Test US1 independently — users can select jurisdictions and see filtered catalogs
5. Deploy/demo if ready — this alone replaces the hardcoded NSW filter

### Incremental Delivery

1. Setup + Foundational → Backend API ready for multi-jurisdiction
2. Add User Story 1 → Selector + filtering works → Deploy (MVP!)
3. Add User Story 2 → Rehearsal replay uses selections → Deploy
4. Add User Story 3 → Verify all 9 jurisdictions display correctly → Deploy
5. Polish → E2E tests + quickstart validation → Final deploy

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (frontend selector + filtering)
   - Developer B: Can prepare E2E test scaffolding (T025)
3. Once US1 is done:
   - Developer A: User Story 2 (replay integration)
   - Developer B: User Story 3 (jurisdiction completeness validation)
4. Polish phase: team validates together

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US4 (data layer) is implemented as Phase 2 Foundational because it enables all user stories
- No new Azure resources required — extends existing Azure Container Apps deployment
- Tenant_id is accepted as pass-through in all route handlers (FR-005) for future Cosmos DB migration
- Debounce (300ms) + AbortController prevents excessive/stale API calls (NFR-002)
- URL format: `/preparedness?jurisdictions=nsw,vic` (comma-separated for human readability per R-003)
- API format: `?jurisdictionId=nsw&jurisdictionId=vic` (repeated params per REST convention, R-002)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
