# Implementation Plan: Multi-Jurisdiction Filter for Preparedness Page

**Branch**: `022-multi-jurisdiction-filter` | **Date**: 2025-07-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/022-multi-jurisdiction-filter/spec.md`

## Summary

Enhance the preparedness page to replace the hardcoded single-jurisdiction ("nsw") data fetching with a dynamic multi-select jurisdiction control that filters Organisation Catalog, Framework Catalog, and rehearsal replay data across any combination of nine Australian jurisdictions. The implementation adds a new `GET /api/jurisdictions` endpoint, extends the existing `/api/organisations` and `/api/frameworks` endpoints to accept repeated `jurisdictionId` query parameters, introduces a WCAG 2.1 AA-compliant multi-select `JurisdictionSelector` component with Select All/Clear All, converts the preparedness page to a hybrid server/client architecture with URL query parameter persistence, and adds 300ms debounced client-side data fetching. No new Azure resources are required.

## Technical Context

**Language/Version**: TypeScript 5.8 (frontend), Python 3.12+ (backend)
**Primary Dependencies**: Next.js 16.2, React 19, FastAPI 0.115, Pydantic 2.10, Uvicorn
**UI Framework**: `@ama/ui` shared component library (packages/ui)
**Storage**: Seed JSON files (jurisdictions_australia.json, organisations_australia.json, frameworks_australia.json) loaded via SeedService → bootstrap_seed_data
**Testing**: pytest (backend unit/integration/contract), Playwright (frontend E2E)
**Target Platform**: Azure Container Apps (Linux containers), desktop-primary (EOC), responsive
**Project Type**: Web application (monorepo — pnpm workspaces: apps/web, apps/api, packages/domain, packages/ui)
**Performance Goals**: Catalog results updated within 2 seconds of jurisdiction selection change (SC-001), 300ms debounce on selection changes (NFR-002)
**Constraints**: Australian data sovereignty (Azure Australia East/Southeast), WCAG 2.1 AA, no PII in telemetry, tenant_id required in data layer queries (specs 007, 021)
**Scale/Scope**: 9 jurisdictions, ~40–60 organisations, ~40–60 frameworks, no pagination required at current volume

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Constitution Requirement | Feature Coverage | Status |
|------|--------------------------|-----------------|--------|
| Gate 1 — Primacy of Life | All decisions prioritise human life | Preparedness page helps planners coordinate multi-jurisdiction response; improved coverage supports life-safety planning | ✅ PASS |
| Gate 2 — National EM Principles | Align with 11 Australian EM principles | Principle 3 (Collaborative): cross-jurisdiction selection. Principle 5 (Flexible): any combination of jurisdictions. Principle 9 (Communication): URL-shareable views. Principle 10 (Integrated): seamless multi-agency view | ✅ PASS |
| Gate 3 — Multi-Hazard Design | Support all hazard types | Feature is hazard-agnostic — filters jurisdictions, not hazard types. Rehearsal replay already supports flood/bushfire/cyclone | ✅ PASS |
| Gate 4 — Transparency & Auditability | Every action logged with provenance | API requests include tenant_id; filter state visible in URL; no new irreversible actions | ✅ PASS |
| Gate 5 — Warning Compliance | AWS warning standards | No public-facing warnings affected by this feature | ✅ PASS (N/A) |
| Gate 6 — Evacuation Framework | 5-stage evacuation support | No evacuation functionality affected | ✅ PASS (N/A) |
| Gate 7 — Recovery Support | 6 principles, 5 domains | No recovery functionality affected | ✅ PASS (N/A) |
| Gate 8 — Cloud Platform | Azure-only, IaC, CI/CD | No new Azure resources; extends existing Azure Container Apps deployment; GitHub Actions CI/CD unchanged | ✅ PASS |
| Gate 9 — PPRR Lifecycle | All four phases | Preparedness page is the PPRR "Preparedness" phase entry point; multi-jurisdiction filter strengthens preparedness planning | ✅ PASS |
| Gate 10 — Governance & Quality | Quality gates, PR reviews | All changes covered by unit/integration/contract tests; existing PR review process applies | ✅ PASS |
| Non-Negotiable 1 — Human-in-the-loop | No irreversible action without human auth | Feature is read-only filtering + rehearsal replay (advisory only) — no irreversible actions | ✅ PASS |
| Non-Negotiable 2 — Data Sovereignty | All data in Australian regions | No data storage changes; seed data served from existing Azure Container Apps in Australian regions | ✅ PASS |
| Non-Negotiable 3 — Privacy | Australian Privacy Act compliance | No PII involved in jurisdiction filtering; tenant_id from Entra ID claims for data scoping | ✅ PASS |
| Non-Negotiable 4 — Interoperability | Standards-based APIs | REST endpoints with OpenAPI-documented query parameters; backward-compatible single-value still works | ✅ PASS |
| Non-Negotiable 5 — Graceful Degradation | Continue at reduced capability | FR-012: inline error with retry on API failure; FR-014: invalid URL params silently ignored; jurisdiction selector remains functional during partial failures | ✅ PASS |

**Post-Phase 1 Re-check**: All gates remain PASS. The design maintains backward compatibility (single `jurisdictionId` still works), adds no irreversible actions, and implements graceful degradation for API failures and invalid URL parameters. Tenant isolation is preserved through the existing middleware pattern.

## Project Structure

### Documentation (this feature)

```text
specs/022-multi-jurisdiction-filter/
├── plan.md                        # This file
├── research.md                    # Phase 0: technology decisions, patterns
├── data-model.md                  # Phase 1: entity definitions, relationships
├── quickstart.md                  # Phase 1: developer setup guide
├── contracts/
│   └── jurisdiction-filter-api.yaml  # Phase 1: OpenAPI contract for new/modified endpoints
└── tasks.md                       # Phase 2: implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Frontend (Next.js 16.2 + React 19 + TypeScript 5.8)
apps/web/src/
├── app/preparedness/
│   └── page.tsx                                   # MODIFY: hybrid server/client with URL state
├── components/preparedness/
│   ├── operating-model-analyzer.tsx                # MODIFY: accept jurisdictions prop, remove hardcoded "nsw"
│   ├── jurisdiction-selector.tsx                   # NEW: multi-select with Select All/Clear All
│   └── preparedness-client.tsx                     # NEW: client component orchestrating state + data fetching
└── lib/api/
    ├── organisations.ts                            # MODIFY: support multi-jurisdiction query params
    ├── frameworks.ts                               # MODIFY: support multi-jurisdiction query params
    └── jurisdictions.ts                            # NEW: GET /api/jurisdictions client

# Backend (FastAPI 0.115 + Pydantic 2.10)
apps/api/app/
├── api/
│   ├── router.py                                  # MODIFY: register jurisdictions router
│   └── routes/
│       ├── organisations.py                       # MODIFY: Query(list) for multi-value jurisdictionId
│       ├── frameworks.py                          # MODIFY: Query(list) for multi-value jurisdictionId
│       └── jurisdictions.py                       # NEW: GET /api/jurisdictions endpoint
└── services/
    ├── organisation_intelligence_service.py       # MODIFY: accept list[str] jurisdiction_ids
    └── preparedness_analysis_service.py           # EXISTING: already accepts list[str] — add framework filtering

# Tests
tests/
├── unit/
│   └── test_multi_jurisdiction_filter.py          # NEW: service-level multi-jurisdiction tests
├── integration/
│   └── test_multi_jurisdiction_api.py             # NEW: API endpoint integration tests
├── contract/
│   └── test_preparedness_contract.py              # MODIFY: add multi-jurisdiction contract tests
└── e2e/
    └── multi-jurisdiction-filter.spec.ts          # NEW: Playwright E2E tests
```

**Structure Decision**: Extends the existing monorepo structure. Frontend additions follow the established pattern in `apps/web/src/components/preparedness/` and `apps/web/src/lib/api/`. A new `preparedness-client.tsx` component handles client-side state management, debounced fetching, and URL synchronisation, while the server component (`page.tsx`) provides the initial jurisdiction list via server-side fetch. Backend additions follow the existing flat-router pattern in `apps/api/app/api/routes/` with a new `jurisdictions.py` router. No new packages, Azure resources, or architectural patterns are introduced.

## Complexity Tracking

> No constitution violations requiring justification. All gates pass.
