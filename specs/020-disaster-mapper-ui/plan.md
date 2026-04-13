# Implementation Plan: Disaster Mapper UI

**Branch**: `020-disaster-mapper-ui` | **Date**: 2025-07-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/020-disaster-mapper-ui/spec.md`

## Summary

Build an interactive Disaster Mapper page at `/disasters` that displays incident markers on an Azure Maps map of Australia. Markers are colour-coded and shape-coded by Australian Warning System severity tiers (Advice/yellow circle, Watch and Act/orange triangle, Emergency Warning/red diamond). The page provides a filter panel (date range, incident type, severity, status, PPRR phase), keyword search, incident detail sidebar with workspace link, marker clustering, mobile-responsive layout, and a list-view fallback when the map service is unavailable. A new `GET /api/v1/incidents/map` FastAPI endpoint serves GeoJSON FeatureCollection data with server-side filtering and pagination. The Incident domain model is extended with an optional `location` GeoJSON Point field. A new Azure Maps account is provisioned via Bicep in Australia East. All five observability metrics are emitted to Azure Monitor.

## Technical Context

**Language/Version**: TypeScript 5.8 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: Next.js 15.5, React 19, `azure-maps-control` 3.x (frontend); FastAPI, Pydantic v2, `azure-cosmos` (backend)
**Storage**: Azure Cosmos DB (`disaster-hub` database, `incidents` container)
**Testing**: Playwright (e2e), pytest (unit/contract/integration), ESLint (frontend lint), Ruff (Python lint)
**Target Platform**: Web browser (desktop + mobile, minimum 360px viewport width)
**Project Type**: Web application (pnpm monorepo: `apps/web`, `apps/api`, `packages/ui`, `packages/domain`)
**Performance Goals**: ≤3s initial map render (SC-001), ≤1s filter update (SC-002), 500+ concurrent markers at ≥30 FPS (SC-004)
**Constraints**: Data sovereignty — all data and tiles from Azure Australia East only (NFR-001); WCAG 2.1 AA accessibility; read-only view (no mutations)
**Scale/Scope**: Initial load of 500 most recent incidents, progressive background fetch of full dataset at 200 per page

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Constitution Requirement | Spec Alignment | Status |
|---|--------------------------|----------------|--------|
| 1 | **Human-in-the-loop** (§1) — No irreversible action without human auth | FR-033: Page is read-only; no create/modify/delete. Links to workspace for operational actions. No agent handoff events. | ✅ PASS |
| 2 | **Data sovereignty** (§IV) — All data within Australian borders | NFR-001: Azure Maps account in Australia East. Incident data served from Australia East Cosmos DB. No third-party CDNs outside Australia. | ✅ PASS |
| 3 | **Privacy by design** (§IV) — PII compliance with Privacy Act 1988 | Incident data is operational metadata (title, type, status, jurisdiction). No personal PII displayed. Existing auth/authz controls apply (Assumption §7). | ✅ PASS |
| 4 | **Interoperability** (§IV) — Standards-based APIs (CAP, EDXL, GeoJSON, OpenAPI) | FR-029: API returns GeoJSON FeatureCollection. Key Entities: location as GeoJSON Point geometry. FastAPI auto-generates OpenAPI spec. | ✅ PASS |
| 5 | **Graceful degradation** (§V) — Continue at reduced capability if service unavailable | NFR-003 + FR-031: List-view fallback within 5s if Azure Maps fails. Retry option for API failures. | ✅ PASS |
| 6 | **Azure-native services** (§VIII) — Azure services preferred | Azure Maps for mapping (not Mapbox/Google). Azure Cosmos DB. Azure Monitor/App Insights for telemetry. | ✅ PASS |
| 7 | **Transparency & Auditability** (§IV) — Actions logged with provenance | NFR-002: Five named telemetry metrics emitted. All API requests logged with structured telemetry. | ✅ PASS |
| 8 | **Australian Warning System** (§V-A) — Three-tier warning levels | FR-003/FR-003a/FR-009: AWS tiers (Advice/Watch and Act/Emergency Warning) with correct colours and shapes. Domain mapping documented in Clarifications. | ✅ PASS |
| 9 | **PPRR lifecycle** (§PPRR) — Support all four phases | FR-011: PPRR phase filter covers Prevention, Preparedness, Response, Recovery. | ✅ PASS |
| 10 | **Quality gates** (§QG) — PR must pass linting, tests | Existing CI pipeline (ESLint, Ruff, pytest, Playwright). New tests added for map endpoint and components. | ✅ PASS |

**Gate result: ALL PASS — proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/020-disaster-mapper-ui/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research findings
├── data-model.md        # Phase 1: Entity and data model documentation
├── quickstart.md        # Phase 1: Developer quick start guide
├── contracts/           # Phase 1: API contracts
│   └── incidents-map-api.md
├── checklists/
│   └── requirements.md  # Pre-existing requirements checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# ── Domain model extension ──
packages/domain/src/domain/models/
└── incident.py                          # Add optional location: GeoJSONPoint field

# ── Backend API (FastAPI) ──
apps/api/app/
├── api/routes/
│   └── incidents_map.py                 # NEW: GET /api/v1/incidents/map endpoint
├── repositories/
│   └── incident_map_repository.py       # NEW: Cosmos DB query for map incidents
└── models/
    └── geojson.py                       # NEW: GeoJSON Pydantic response models

# ── Shared UI components ──
packages/ui/src/
├── components/disaster-map/
│   ├── disaster-map.tsx                 # NEW: Azure Maps wrapper (client component)
│   ├── filter-panel.tsx                 # NEW: Multi-criteria filter panel
│   ├── incident-sidebar.tsx             # NEW: Incident detail sidebar
│   ├── search-bar.tsx                   # NEW: Keyword search input
│   ├── marker-cluster.tsx               # NEW: Marker/cluster rendering logic
│   ├── list-view-fallback.tsx           # NEW: Table fallback view
│   └── use-disaster-map-filters.ts      # NEW: Filter state hook (URL sync)
└── styles/
    └── tokens.css                       # EXTEND: Add AWS severity colour tokens

# ── Web app page ──
apps/web/src/
├── app/disasters/
│   └── page.tsx                         # NEW: /disasters route page
├── lib/api/
│   └── incidents-map.ts                 # NEW: API client for /incidents/map
└── app/globals.css                      # EXTEND: Disaster mapper page styles

# ── Infrastructure ──
infra/
├── modules/
│   └── azure-maps.bicep                 # NEW: Azure Maps account module
└── main.bicep                           # EXTEND: Wire azure-maps module

# ── Tests ──
tests/
├── unit/
│   └── test_incident_map_repository.py  # NEW: Repository unit tests
├── contract/
│   └── test_incidents_map_contract.py   # NEW: API contract tests
└── e2e/                                 # NEW: Playwright e2e tests (via apps/web)
```

**Structure Decision**: Follows the existing monorepo structure. Frontend components go in `packages/ui/src/components/disaster-map/` (shared library pattern). The page route goes in `apps/web/src/app/disasters/`. Backend endpoint follows the existing router pattern in `apps/api/app/api/routes/`. Domain model extension is in-place on `packages/domain/`. Infrastructure module follows the existing `infra/modules/` pattern.

## Complexity Tracking

> No constitution violations detected. All gates pass. No complexity justifications required.
