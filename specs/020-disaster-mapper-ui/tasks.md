# Tasks: Disaster Mapper UI

**Input**: Design documents from `/specs/020-disaster-mapper-ui/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/incidents-map-api.md ✅

**Tests**: Included — the implementation plan explicitly defines unit and contract test files, and the constitution (§QG) mandates automated tests for PR merge.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Monorepo layout**: `apps/web` (Next.js 15), `apps/api` (FastAPI), `packages/ui` (shared components), `packages/domain` (domain models)
- **Infrastructure**: `infra/` (Bicep)
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and scaffold directory structure for new feature files

- [x] T001 Add `azure-maps-control` v3.x dependency to `packages/ui/package.json` and run `pnpm install` from repo root
- [x] T002 [P] Create directory scaffolding: `packages/ui/src/components/disaster-map/`, `apps/api/app/models/` (with `__init__.py`), `apps/web/src/app/disasters/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain model extension, API endpoint, GeoJSON response models, infrastructure, and design tokens that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Extend Incident model with `location: dict[str, Any] | None = None` field in `packages/domain/src/domain/models/incident.py` — add `Any` to typing imports, keep field optional for backwards compatibility per R-006
- [ ] T004 [P] Create GeoJSON Pydantic response models (`GeoJSONPoint`, `IncidentFeatureProperties`, `IncidentFeature`, `IncidentFeatureCollection`, `IncidentMapMetadata`) with `SEVERITY_TO_AWS_TIER` mapping dict in `apps/api/app/models/geojson.py` per data-model.md schema
- [ ] T005 [P] Add Australian Warning System severity colour tokens (`--ama-aws-advice: #FFC107`, `--ama-aws-watch: #FF8C00`, `--ama-aws-emergency: #D32F2F`) to `packages/ui/src/styles/tokens.css`
- [ ] T006 [P] Create Azure Maps Bicep module (`Microsoft.Maps/accounts@2024-07-01-preview`, Gen2 SKU, `australiaeast` only via `@allowed`, `disableLocalAuth: true`) in `infra/modules/azure-maps.bicep` following `monitoring.bicep` pattern per R-004
- [ ] T007 Wire Azure Maps module into `infra/main.bicep` with parameter bindings, outputs (account name, resource ID), and CORS configuration for web app origin
- [ ] T008 Create `IncidentMapRepository` with dynamic Cosmos DB query builder — base query excludes `rehearsal` status and requires `IS_DEFINED(c.location) AND c.location.type = 'Point'`, dynamic WHERE clauses for type/severity/status/pprr_phase/keyword/year_start/year_end, `ORDER BY c.started_at DESC` with OFFSET/LIMIT pagination, and separate unmapped count query — in `apps/api/app/repositories/incident_map_repository.py` per data-model.md query shape
- [ ] T009 Create `GET /api/v1/incidents/map` endpoint with query parameter validation (type, severity, status, pprr_phase, keyword, year_start, year_end, page default 1, page_size default 200 max 500), input sanitisation, and GeoJSON FeatureCollection response in `apps/api/app/api/routes/incidents_map.py` per contracts/incidents-map-api.md
- [ ] T010 Register `incidents_map` router import and `api_router.include_router()` call in `apps/api/app/api/router.py`

**Checkpoint**: Foundation ready — backend API, infrastructure, domain model, and shared design tokens all in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — View Incidents on a Map (Priority: P1) 🎯 MVP

**Goal**: Display an interactive Azure Maps map of Australia at `/disasters` with severity-coded incident markers (yellow circle for Advice, orange triangle for Watch and Act, red diamond for Emergency Warning) loaded from the API

**Independent Test**: Navigate to `/disasters` → map renders centred on Australia → incident markers appear colour/shape-coded by severity → pan and zoom work smoothly → markers cluster at low zoom and expand on click

### Implementation for User Story 1

- [ ] T011 [P] [US1] Create typed API client with progressive loading (fetch page 1 of 200, then background-fetch subsequent pages until `features.length < page_size`) for `GET /api/v1/incidents/map` in `apps/web/src/lib/api/incidents-map.ts` — export types matching GeoJSON FeatureCollection response schema from contracts/incidents-map-api.md
- [ ] T012 [P] [US1] Create marker rendering module: register three custom SVG severity icons via `map.imageSprite.add()` (circle/yellow for advice, triangle/orange for watch, diamond/red for emergency), configure `atlas.source.DataSource` with `cluster: true` and `clusterRadius: 60`, add `SymbolLayer` with data-driven `['match', ['get', 'severityTier'], ...]` image expression for individual markers, `BubbleLayer` with `['has', 'point_count']` filter for cluster circles, `SymbolLayer` for cluster count labels, and cluster click-to-expand via `getClusterExpansionZoom()` in `packages/ui/src/components/disaster-map/marker-cluster.tsx` per R-002 and R-003
- [ ] T013 [US1] Create Azure Maps wrapper client component: `"use client"` directive, `useRef` for map container + `useEffect` for `new atlas.Map()` lifecycle (centre `[134.0, -25.5]`, zoom 4, `authOptions` from `NEXT_PUBLIC_AZURE_MAPS_KEY`), import `azure-maps-control/dist/atlas.min.css`, `map.dispose()` on cleanup, accept GeoJSON data prop and render markers via marker-cluster module in `packages/ui/src/components/disaster-map/disaster-map.tsx` per R-001
- [ ] T014 [US1] Create `/disasters` route page: `dynamic(() => import('...disaster-map'), { ssr: false })`, fetch initial incident data via API client on mount, pass data to map component, render within application shell layout in `apps/web/src/app/disasters/page.tsx`
- [ ] T015 [US1] Add disaster mapper page layout styles (full-height map container, side-panel grid for desktop) to `apps/web/src/app/globals.css`

**Checkpoint**: User Story 1 complete — `/disasters` shows an interactive Azure Maps map of Australia with severity-coded, clustered incident markers. Fully functional and testable as standalone MVP.

---

## Phase 4: User Story 2 — Filter Incidents by Criteria (Priority: P2)

**Goal**: Add a multi-criteria filter panel alongside the map with URL-synced state, real-time map updates, Select All/Reset controls, and visible incident count

**Independent Test**: Open filter panel → select date range, incident type, severity, status, and/or PPRR phase → map markers update to show only matching incidents → URL updates with filter query params → copy URL and reload to restore filters → reset button clears all → incident count reflects visible markers

### Implementation for User Story 2

- [ ] T016 [P] [US2] Create `useDisasterMapFilters` hook: read/write URL query params via `useSearchParams` from `next/navigation`, manage filter state for type (comma-separated), severity, status, pprr_phase, year_start, year_end, and keyword, expose typed getter/setter functions, apply 300ms debounce on keyword changes only (immediate for checkbox/dropdown), integrate with browser back/forward history in `packages/ui/src/components/disaster-map/use-disaster-map-filters.ts` per R-007
- [ ] T017 [US2] Create filter panel component: date range year selectors (dynamic range from earliest incident to current year), incident type checkboxes (9 types: bushfire, flood, cyclone, storm, earthquake, tsunami, extreme_heat, pandemic, other), severity tier checkboxes (3 AWS tiers mapping to 4 domain values), status checkboxes (5 operational statuses excluding rehearsal), PPRR phase checkboxes (4 phases), Select All and Reset controls per category — consume filter hook for state management — in `packages/ui/src/components/disaster-map/filter-panel.tsx`
- [ ] T018 [US2] Integrate filter panel and hook into page: pass filter params to API client calls, re-fetch data on filter change (restart from page 1), update map markers via disaster-map component, display visible incident count (FR-015) above the map in `apps/web/src/app/disasters/page.tsx`

**Checkpoint**: User Stories 1 AND 2 both work independently — map displays all incidents or filtered subsets with URL-persisted filter state.

---

## Phase 5: User Story 3 — View Incident Details from Map (Priority: P3)

**Goal**: Show a detail sidebar when a marker is clicked displaying full incident information with a workspace navigation link

**Independent Test**: Click any marker → sidebar slides in from right with incident title, type, severity (AWS-coloured), status, affected jurisdictions, start date, PPRR phase, incident level → click workspace link navigates to `/incidents/[id]` → close button dismisses sidebar → clicking a different marker updates sidebar content

### Implementation for User Story 3

- [ ] T019 [US3] Create incident detail sidebar component: display incident title, type, severity with AWS colour and tier label, status, affected jurisdiction IDs, start date (ISO 8601 formatted), PPRR phase, incident level (1–3), prominent workspace link (`<a>` or `<Link>`) to `/incidents/{incident_id}`, close button — accept selected incident Feature properties as prop — in `packages/ui/src/components/disaster-map/incident-sidebar.tsx`
- [ ] T020 [US3] Wire marker click events to sidebar: add `map.events.add('click', symbolLayer, ...)` handler on individual-marker SymbolLayer in disaster-map.tsx, extract clicked feature properties, lift selected-incident state to page, pass to sidebar component, handle close callback and marker-switch (clicking different marker updates selection) in `packages/ui/src/components/disaster-map/disaster-map.tsx` and `apps/web/src/app/disasters/page.tsx`

**Checkpoint**: User Stories 1, 2, AND 3 all work independently — map, filters, and incident detail drill-down all functional.

---

## Phase 6: User Story 4 — Search Incidents by Keyword (Priority: P4)

**Goal**: Add a keyword search bar that filters incidents by title match, combining with active filter criteria

**Independent Test**: Type keyword in search bar → map updates to show only title-matching incidents → search combines with active filters (AND logic) → clear search restores filter-only results → "No incidents match your criteria" message for zero matches

### Implementation for User Story 4

- [ ] T021 [US4] Create keyword search bar component: text input with placeholder, clear (×) button, 300ms debounce before emitting value change, consume `keyword` state from filter hook in `packages/ui/src/components/disaster-map/search-bar.tsx`
- [ ] T022 [US4] Integrate search bar into page layout: render above map alongside filter controls, wire keyword value to filter hook (triggers API re-fetch with `keyword` param), display "No incidents match your criteria" message with reset option when zero results returned in `apps/web/src/app/disasters/page.tsx`

**Checkpoint**: User Stories 1–4 all work independently — map, filters, detail sidebar, and keyword search all functional.

---

## Phase 7: User Story 5 — Use Disaster Mapper on Mobile (Priority: P5)

**Goal**: Responsive mobile layout with full-screen map, collapsible filter drawer, and overlay incident detail card for viewports down to 360px

**Independent Test**: Access `/disasters` on 360px viewport → map fills screen and is interactive → tap filter control to open bottom sheet (map remains partially visible) → tap marker to see detail overlay card → rotate device to verify layout adapts → no horizontal scroll or truncated controls

### Implementation for User Story 5

- [ ] T023 [US5] Add responsive breakpoint (768px) layout: full-screen map container on mobile, side-panel grid on desktop, mobile-friendly search bar sizing, and touch-gesture support (pinch-to-zoom, two-finger pan) in `apps/web/src/app/globals.css` and `packages/ui/src/components/disaster-map/disaster-map.tsx`
- [ ] T024 [US5] Implement collapsible bottom sheet behaviour for filter panel on viewports below 768px — toggle open/close via button, max-height constraint to keep map visible, swipe-to-dismiss gesture — in `packages/ui/src/components/disaster-map/filter-panel.tsx`
- [ ] T025 [US5] Implement overlay card variant for incident detail sidebar on viewports below 768px — replace side-panel with bottom card overlay, tap-outside-to-close, smooth entry/exit transition — in `packages/ui/src/components/disaster-map/incident-sidebar.tsx`

**Checkpoint**: All five user stories functional — desktop and mobile layouts both work correctly down to 360px minimum viewport width.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Graceful degradation, accessibility, telemetry, error handling, and automated tests spanning multiple user stories

- [ ] T026 [P] Create list-view fallback table component (columns: Title, Type, Severity, Status, Date, Location; sortable by all columns; includes same filter controls as map view) in `packages/ui/src/components/disaster-map/list-view-fallback.tsx` per FR-031
- [ ] T027 Integrate list-view fallback with Azure Maps error detection (5-second timeout on tile load failure), automatic switch to table view, and manual retry button to re-attempt map load in `apps/web/src/app/disasters/page.tsx` per NFR-003 and SC-008
- [ ] T028 [P] Add loading indicator (skeleton or spinner) for initial map data fetch and visual progress for progressive background page loading in `packages/ui/src/components/disaster-map/disaster-map.tsx` per FR-032 and FR-035
- [ ] T029 [P] Add unmapped incidents notice displaying `metadata.unmapped_count` (e.g., "3 incidents could not be mapped due to missing location data") and "Last updated" timestamp from `metadata.fetched_at` to `apps/web/src/app/disasters/page.tsx` per FR-030 and FR-034
- [ ] T030 [P] Add ARIA accessibility: `aria-live="polite"` region for filter count announcements ("Showing 42 incidents"), keyboard Tab navigation through map markers with Enter/Space to open sidebar, visible focus indicators, ARIA landmark roles for map region, filter panel, sidebar, and search bar in `packages/ui/src/components/disaster-map/disaster-map.tsx`, `filter-panel.tsx`, `incident-sidebar.tsx`, and `search-bar.tsx` per FR-036, FR-037, and FR-038
- [ ] T031 [P] Integrate frontend telemetry: emit `disaster_mapper.page_load_ms` (navigation to map ready), `disaster_mapper.filter_apply_ms` (filter change to re-render), `disaster_mapper.map_render_ms` (data receipt to marker render), `disaster_mapper.incidents_displayed` (gauge on each render) via existing `@azure/monitor-opentelemetry` meter API in `packages/ui/src/components/disaster-map/disaster-map.tsx` and `apps/web/src/app/disasters/page.tsx` per NFR-002 and R-008
- [ ] T032 [P] Add backend `disaster_mapper.api_error_rate` telemetry metric via structured logging and HTTP response status code tracking (5xx count / total count) in `apps/api/app/api/routes/incidents_map.py` per NFR-002
- [ ] T033 [P] Create unit tests for `IncidentMapRepository`: test dynamic filter composition, pagination offset/limit, rehearsal exclusion, location-required filter, keyword search, year range, empty results — in `tests/unit/test_incident_map_repository.py`
- [ ] T034 [P] Create contract tests for `GET /api/v1/incidents/map`: validate GeoJSON FeatureCollection schema, all query parameter combinations, error responses (400 invalid params, 401/403 auth, 500/503 server errors), pagination metadata, unmapped count, severity-to-AWS-tier mapping — in `tests/contract/test_incidents_map_contract.py`
- [ ] T035 [P] Create Playwright E2E test suite in `tests/e2e/disasters.spec.ts`: test page load with map render, filter application updates markers, sidebar opens on marker click with workspace link, keyword search filters results, mobile viewport (360px) layout, list-view fallback when map unavailable. Use existing Playwright config at `apps/web/playwright.config.ts`
- [ ] T036 Run quickstart.md end-to-end validation: start FastAPI (`uvicorn`) and Next.js (`pnpm dev`) dev servers, navigate to `/disasters`, verify map renders with severity-coded markers, test all five filter types, confirm sidebar opens on marker click with workspace link, verify search filters by keyword, check mobile layout at 360px, trigger list-view fallback by simulating map failure

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–7)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3 → P4 → P5)
  - Or in parallel if team capacity allows (US1–US4 after Phase 2; US5 after US1+US2+US3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Start after Phase 2 — extends `page.tsx` created in US1 but independently testable
- **US3 (P3)**: Start after Phase 2 — extends `disaster-map.tsx` from US1 (marker click events) but independently testable
- **US4 (P4)**: Start after Phase 2 — extends filter hook from US2 (keyword param) but independently testable
- **US5 (P5)**: Start after US1+US2+US3 — adapts existing components for mobile viewports

### Internal Phase 2 Dependencies

- T003, T004, T005, T006 → all parallel (independent files, no interdependencies)
- T007 → depends on T006 (Bicep module must exist before wiring into main.bicep)
- T008 → depends on T004 (GeoJSON response models needed by repository return types)
- T009 → depends on T003 and T008 (domain model extension + repository needed by endpoint)
- T010 → depends on T009 (route file must exist before registering in router)

### Within Each User Story

- Hooks/modules before components that consume them
- Components before page integration
- Core implementation before cross-component wiring

---

## Parallel Opportunities

### Phase 2: Foundational (4 tasks simultaneously)

```text
Parallel: T003 (Incident model) | T004 (GeoJSON models) | T005 (CSS tokens) | T006 (Bicep module)
Then:     T007 (main.bicep)     | T008 (repository)
Then:     T009 (API endpoint)
Then:     T010 (router registration)
```

### Phase 3: User Story 1 (2 tasks simultaneously)

```text
Parallel: T011 (API client) | T012 (marker-cluster module)
Then:     T013 (disaster-map wrapper — needs T012)
Then:     T014 (page.tsx — needs T011, T013) | T015 (globals.css)
```

### Phase 8: Polish (8 tasks simultaneously)

```text
Parallel: T026 (list-view) | T028 (loading) | T029 (notices) | T030 (a11y) | T031 (frontend telemetry) | T032 (backend telemetry) | T033 (unit tests) | T034 (contract tests) | T035 (E2E tests)
Then:     T027 (list-view integration — needs T026)
Then:     T036 (quickstart validation — needs all above)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (2 tasks)
2. Complete Phase 2: Foundational (8 tasks) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (5 tasks)
4. **STOP and VALIDATE**: Navigate to `/disasters`, verify map + severity-coded markers render
5. Deploy/demo — delivers geographic situational awareness as standalone value

### Incremental Delivery

1. Setup + Foundational → Foundation ready (10 tasks)
2. Add US1 → Interactive map with markers → **MVP!** (15 tasks cumulative)
3. Add US2 → Filtered situational analysis → Demo (18 tasks cumulative)
4. Add US3 → Incident detail drill-down → Demo (20 tasks cumulative)
5. Add US4 → Keyword search → Demo (22 tasks cumulative)
6. Add US5 → Mobile field access → Demo (25 tasks cumulative)
7. Add Polish → Production-ready with a11y, telemetry, tests (36 tasks total)

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers after Foundational phase:

- **Developer A (Backend)**: T008 → T009 → T010, then T032 → T033 → T034
- **Developer B (Frontend — map core)**: T011 → T012 → T013 → T014 → T015, then T019 → T020
- **Developer C (Frontend — panels)**: T016 → T017 → T018, then T021 → T022
- **Developer D (Infra + Mobile + Polish)**: T006 → T007, then T023 → T024 → T025, then T026 → T027

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable at its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- The `rehearsal` status is excluded server-side — never appears in UI filter options
- Azure Maps requires `"use client"` + `dynamic()` with `{ ssr: false }` in Next.js (R-001)
- All marker rendering uses `SymbolLayer` pipeline, not `HtmlMarker`, for clustering compatibility (R-002)
- URL filter state enables bookmarkability and shareability of filtered views (R-007)
- Severity mapping: `advisory` → advice, `watch` → watch, `warning`/`emergency` → emergency (data-model.md)
