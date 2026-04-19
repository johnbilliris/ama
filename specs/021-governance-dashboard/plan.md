# Implementation Plan: Governance Dashboard

**Branch**: `021-governance-dashboard` | **Date**: 2025-07-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/021-governance-dashboard/spec.md`
**Checklist**: [governance.md](./checklists/governance.md)

## Summary

Build a comprehensive Governance Dashboard into the AMA web application that provides a unified, role-aware view of governance health, compliance status, audit trails, operational readiness, and recovery progress. The dashboard extends the existing `/governance` route with 6 new sub-views (executive summary, compliance matrix, audit trail, operational readiness, recovery progress, risk & warnings), adds 13 new API endpoints for aggregated governance data, introduces 5 new domain models, and implements role-based widget personalisation for all 10 AIIMS roles. The dashboard is read-only — state changes navigate to existing CRUD pages via the human-in-the-loop approval workflows.

## Technical Context

**Language/Version**: TypeScript 5.8 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: Next.js 16.2, React 19, FastAPI 0.115, Pydantic 2.10, Uvicorn
**UI Framework**: `@ama/ui` shared component library (packages/ui)
**Storage**: Azure Cosmos DB (autoscale, partition-per-entity pattern), Azure Storage (audit blob export)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Playwright (frontend), axe-core (a11y)
**Target Platform**: Azure Container Apps (Linux containers), desktop-primary (EOC), responsive to 375px
**Project Type**: Web application (monorepo — pnpm workspaces)
**Performance Goals**: 3s initial load (executive summary), 1s drill-down navigation, 2s audit search with pagination
**Constraints**: Australian data sovereignty (Azure Australia East/Southeast only), WCAG 2.1 AA, no PII in telemetry, 7-year audit retention
**Scale/Scope**: 10 AIIMS roles, concurrent EOC users during Level 2/3 incidents, ~10k audit records/day during major incidents

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Constitution Requirement | Dashboard Coverage | Status |
|------|--------------------------|-------------------|--------|
| Gate 1 — Primacy of Life | All decisions prioritise human life | Dashboard surfaces risk severity + active incident counts; high-severity risks displayed prominently (FR-020, FR-022) | ✅ PASS |
| Gate 2 — National EM Principles | Align with 11 Australian EM principles | PPRR lifecycle view (FR-013), shared responsibility via role-based access (FR-024), continuous improvement via M&E tracking (FR-018) | ✅ PASS |
| Gate 3 — Multi-Hazard Design | Support all hazard types | Dashboard is hazard-agnostic — aggregates governance data across all incident types | ✅ PASS |
| Gate 4 — Transparency & Auditability | Every action logged with provenance | FR-027 logs all dashboard interactions; FR-009–012 provide searchable audit trail with decision chains; FR-028 requires human confirmation for state changes | ✅ PASS |
| Gate 5 — Warning Compliance | AWS warning standards | FR-021/021A display AWS 3-tier usage, 10-principle compliance rates, broadcast reach; FR-033A enforces AWS colour tokens | ✅ PASS |
| Gate 6 — Evacuation Framework | 5-stage evacuation support | Dashboard displays operational readiness including evacuation-related emergency plans; evacuation data sourced from existing systems | ✅ PASS (read-only) |
| Gate 7 — Recovery Support | 6 principles, 5 domains | FR-017–019 track all 5 recovery domains with M&E framework results, trend indicators, and target trajectory warnings | ✅ PASS |
| Gate 8 — Cloud Platform | Azure-only, IaC, CI/CD | Extends existing Azure Container Apps + Cosmos DB; Bicep IaC; GitHub Actions CI/CD | ✅ PASS |
| Gate 9 — PPRR Lifecycle | All four phases | FR-013 displays PPRR phase indicators; emergency plan tracking covers all phases | ✅ PASS |
| Gate 10 — Governance & Quality | Quality gates, PR reviews | Compliance matrix (FR-005), health score (FR-001), and constitutional gate tracking (FR-002) make governance visible and measurable | ✅ PASS |
| Non-Negotiable 1 — Human-in-the-loop | No irreversible action without human auth | FR-028: human confirmation for any state change; dashboard is read-only by default | ✅ PASS |
| Non-Negotiable 2 — Data Sovereignty | All data in Australian regions | Enforced at infrastructure level; no dashboard-specific controls needed per spec assumptions | ✅ PASS |
| Non-Negotiable 3 — Privacy | Australian Privacy Act compliance | FR-035: no PII in telemetry; FR-027: audit records include identity for provenance only (Gate 4 requirement) | ✅ PASS |
| Non-Negotiable 4 — Interoperability | Standards-based APIs | JSON export (FR-012), OpenAPI-documented endpoints, existing CAP/EDXL patterns preserved | ✅ PASS |
| Non-Negotiable 5 — Graceful Degradation | Continue at reduced capability | FR-030/031: staleness indicators, last-known-good data, degraded-mode banners; SC-007: navigable at 50% backend unavailability | ✅ PASS |

**Post-Phase 1 Re-check**: All gates remain PASS. The read-only dashboard design with navigation links to existing CRUD pages avoids introducing new irreversible-action pathways. Tenant isolation (FR-026A) ensures simulation data cannot leak into live governance views.

## Checklist Conflict Resolutions

These conflicts were identified in the [governance checklist](./checklists/governance.md) and are resolved here with binding decisions for implementation:

| Checklist Item | Conflict | Resolution | Rationale |
|----------------|----------|------------|-----------|
| CHK029 | SC-003 says 5s audit search; US3-AS2 says 2s | **Use 2s target** with server-side Cosmos DB pagination (50 records/page, continuation tokens) | 2s is the stricter requirement; Cosmos DB with partition-key-aligned queries and cross-partition fan-out achieves this. SC-003's 5s becomes the degraded-mode fallback. |
| CHK068 | "Read-only interface" vs "governance state changes initiated from dashboard" (FR-028) | **Dashboard is read-only**. "State changes" means the dashboard provides navigation links to existing CRUD pages (e.g., "Trigger Reassessment" link → existing assessment workflow). FR-028 confirmation dialogs guard these navigation actions. | Preserves human-in-the-loop by routing through existing approval workflows rather than adding new mutation endpoints. |
| CHK063 | FR-029 says "30s active / 5min steady-state"; SC-005 says "default 30 seconds" | **30s for active-incident views** (executive summary during incident, risk register); **5min for all other dashboard views** (compliance matrix, audit trail, recovery, operational readiness in peacetime). SC-005 applies to health score during active incidents only. | Reduces unnecessary API load during steady-state while maintaining real-time awareness during incidents. |
| CHK010 | Role-to-widget mappings only specified for 3 of 10 AIIMS roles | **All 10 roles defined** — see [Role-to-Widget Mapping](#role-to-widget-mapping) section below | Spec provided examples for Operations Officer, PIO, Logistics Officer. Remaining 7 roles derived from AIIMS functional responsibilities and spec user stories. |
| CHK026 | Audit retention not specified | **7 years for compliance audit data** (regulatory); **90 days for dashboard interaction logs** (operational). Interaction logs archived to Azure Storage cold tier after 90 days, retained for 7 years. | 7-year retention aligns with Australian regulatory record-keeping requirements; 90-day hot storage balances cost with operational needs. |
| CHK078 | Per-view performance not specified beyond executive summary | **All views: 3s initial load, 1s drill-down**. Audit search: 2s (paginated). Export: async with progress indicator, no timeout for large exports. | Consistent UX across all views; async exports prevent blocking the UI. |

## Role-to-Widget Mapping

All 10 AIIMS roles with their default widget configurations:

| # | AIIMS Role | Primary Widgets (Ordered) | Default Landing View |
|---|------------|--------------------------|---------------------|
| 1 | **Incident Controller** | Health score gauge, Constitutional gates (10), Active incidents count, Resource utilisation, Strategic risk summary, PPRR phase indicator | Executive Summary |
| 2 | **Operations Officer** | Active incidents count, Resource utilisation, Task completion metrics (from operations data), PPRR phase (Response highlighted), Field safety indicators, Staging area utilisation | Executive Summary (ops-focused) |
| 3 | **Planning Officer** | Emergency plan status (7-state breakdown), PPRR phase indicators, Simulation exercise rates, Capability gap count, AIIMS role coverage, Recovery trajectory | Operational Readiness |
| 4 | **Intelligence Officer** | Data source compliance matrix (summary), Governance gap count, Health score trend, Assessment tracking timeline, Active incident intelligence feeds | Compliance View |
| 5 | **Logistics Officer** | Resource utilisation breakdown, Capability gap details, Supply chain readiness indicators, Emergency plan logistics components, Staging area capacity | Operational Readiness |
| 6 | **Public Information Officer** | Alert approval latency, Broadcast reach %, AWS warning principle compliance (10 principles), Multilingual coverage %, Accessibility compliance status, Warning tier usage (Advice/Watch/Emergency) | Risk & Warning View |
| 7 | **Executive Leader** | Health score gauge, Constitutional gates (10), Strategic risk summary, Recovery domain progress (5 domains), Compliance overview, Active incident count | Executive Summary |
| 8 | **Observer/Auditor** | Audit trail search, Compliance matrix (full), Constitutional gate details, Decision chain viewer, Export tools, Assessment history | Audit Trail View |
| 9 | **Risk Manager** | Risk register (severity breakdown), Treatment closure rate, Alert approval latency, AWS compliance metrics, Warning effectiveness, Risk trend analysis | Risk & Warning View |
| 10 | **Resilience Planner** | PPRR phase indicators, Emergency plan lifecycle, Simulation exercise completion, Recovery domain progress, Capability gaps, Community resilience indicators | Operational Readiness |

**Multi-role resolution**: When a user has multiple roles, widgets are merged (union) and ordered by highest-authority role first. Authority hierarchy: Incident Controller > Executive Leader > Operations Officer > Planning Officer > Intelligence Officer > Logistics Officer > Public Information Officer > Risk Manager > Resilience Planner > Observer/Auditor.

## Project Structure

### Documentation (this feature)

```text
specs/021-governance-dashboard/
├── plan.md                          # This file
├── research.md                      # Phase 0: conflict resolutions, technology decisions
├── data-model.md                    # Phase 1: entity definitions, relationships
├── quickstart.md                    # Phase 1: developer setup guide
├── checklists/
│   └── governance.md                # Specification quality checklist
├── contracts/
│   └── governance-dashboard-api.yaml  # Phase 1: OpenAPI contract for new endpoints
└── tasks.md                         # Phase 2: implementation tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Frontend (Next.js 16.2 + React 19 + TypeScript 5.8)
apps/web/
├── src/
│   ├── app/governance/
│   │   ├── page.tsx                          # EXTEND: add dashboard entry + redirect
│   │   ├── dashboard/
│   │   │   ├── page.tsx                      # NEW: executive summary view
│   │   │   ├── layout.tsx                    # NEW: dashboard shell with sub-nav + refresh
│   │   │   ├── compliance/page.tsx           # NEW: compliance matrix view
│   │   │   ├── audit/page.tsx                # NEW: audit trail view
│   │   │   ├── readiness/page.tsx            # NEW: operational readiness view
│   │   │   ├── recovery/page.tsx             # NEW: recovery progress view
│   │   │   └── risk/page.tsx                 # NEW: risk & warning view
│   │   └── [dataSourceId]/                   # EXISTING: keep current routes
│   │       ├── compliance/page.tsx
│   │       └── assignments/page.tsx
│   ├── components/governance/
│   │   ├── GovernanceSummary.tsx              # EXISTING: extend for dashboard
│   │   ├── DataSourceTable.tsx               # EXISTING: extend with compliance columns
│   │   ├── ComplianceCard.tsx                # EXISTING: keep
│   │   ├── HandoffChainEditor.tsx            # EXISTING: keep
│   │   ├── dashboard/                        # NEW: dashboard-specific components
│   │   │   ├── HealthScoreGauge.tsx          # NEW: 0-100 gauge with traffic light
│   │   │   ├── ConstitutionalGates.tsx       # NEW: 10-gate compliance grid
│   │   │   ├── ComplianceMatrix.tsx          # NEW: full data source matrix
│   │   │   ├── AuditTrailSearch.tsx          # NEW: search + filter + timeline
│   │   │   ├── AuditDecisionChain.tsx        # NEW: decision chain visualiser
│   │   │   ├── AuditExportDialog.tsx         # NEW: format selection + progress
│   │   │   ├── PPRRPhaseIndicator.tsx        # NEW: 4-phase indicator
│   │   │   ├── EmergencyPlanStatus.tsx       # NEW: 7-state lifecycle display
│   │   │   ├── RoleWidgetGrid.tsx            # NEW: role-aware widget layout
│   │   │   ├── RecoveryDomainTracker.tsx     # NEW: 5-domain progress view
│   │   │   ├── RiskRegisterView.tsx          # NEW: severity breakdown + treatments
│   │   │   ├── WarningCompliancePanel.tsx    # NEW: AWS 10-principle compliance
│   │   │   ├── DataFreshnessIndicator.tsx    # NEW: staleness badges per widget
│   │   │   ├── DegradedModeBanner.tsx        # NEW: system-wide degradation alert
│   │   │   ├── RefreshControls.tsx           # NEW: auto/manual refresh toggle
│   │   │   ├── TenantBanner.tsx              # NEW: simulation mode indicator
│   │   │   └── WidgetErrorBoundary.tsx       # NEW: per-widget error + retry
│   │   └── a11y/                             # NEW: accessibility helpers
│   │       ├── CompanionDataTable.tsx        # NEW: hidden data table for charts
│   │       └── ChartAriaLabel.tsx            # NEW: ARIA label generator
│   └── lib/api/
│       └── governance.ts                     # NEW: typed API client for governance endpoints
│
# Backend (FastAPI 0.115 + Pydantic 2.10)
apps/api/app/
├── api/
│   ├── governance.py                         # EXTEND: add dashboard aggregate endpoints
│   └── routes/
│       └── governance_dashboard.py           # NEW: dedicated dashboard router
├── models/
│   ├── governance_health.py                  # NEW: health score, gate status models
│   ├── dashboard_config.py                   # NEW: role-widget mapping, refresh config
│   └── audit_export.py                       # NEW: export job tracking
├── services/
│   ├── governance_registry.py                # EXTEND: add health score aggregation
│   ├── governance_cache.py                   # EXTEND: add dashboard-level caching
│   ├── health_score_service.py               # NEW: health score calculation engine
│   ├── audit_export_service.py               # NEW: PDF/CSV/JSON export generation
│   └── dashboard_aggregation_service.py      # NEW: cross-domain data aggregation
├── repositories/
│   └── governance_repository.py              # EXTEND: add dashboard query methods
├── middleware/
│   └── tenant_context.py                     # EXTEND: add tenant_id extraction for dashboard
└── validators/
    └── governance_validators.py              # EXTEND: add export/filter validation

# Domain models (packages/domain)
packages/domain/src/domain/models/
├── governance_health_score.py                # NEW: GovernanceHealthScore, ConstitutionalGateStatus
├── dashboard_widget_config.py                # NEW: RoleWidgetMapping, WidgetDefinition
└── audit_export.py                           # NEW: AuditExportJob, ExportFormat

# Shared UI components (packages/ui) — if dashboard widgets need cross-app reuse
packages/ui/src/components/
└── governance/                               # NEW: extracted shared governance components
    ├── index.ts                              # NEW: barrel export
    ├── HealthScoreGauge.tsx                  # NEW: reusable gauge widget
    └── TrafficLightIndicator.tsx             # NEW: Green/Amber/Red status indicator

# Infrastructure (Bicep)
infra/
└── modules/
    └── governance-dashboard.bicep            # NEW: if additional Azure resources needed

# Tests
tests/
├── unit/
│   ├── test_health_score_service.py          # NEW: health score calculation tests
│   ├── test_dashboard_aggregation.py         # NEW: aggregation logic tests
│   └── test_audit_export_service.py          # NEW: export generation tests
├── integration/
│   ├── test_governance_dashboard_api.py      # NEW: API endpoint integration tests
│   └── test_governance_dashboard_cache.py    # NEW: cache behaviour tests
├── contract/
│   └── test_governance_dashboard_contract.py # NEW: API contract conformance
└── e2e/
    └── governance-dashboard.spec.ts          # NEW: Playwright E2E tests
```

**Structure Decision**: Extends the existing monorepo structure. Frontend additions are co-located within the existing `apps/web/src/app/governance/` route tree using the Next.js App Router pattern. New dashboard views are nested under a `/governance/dashboard/` sub-route to avoid disrupting existing `/governance/[dataSourceId]/*` routes. Backend additions extend the existing FastAPI router pattern with a new dedicated `governance_dashboard.py` router mounted under the existing governance prefix. Domain models are added to `packages/domain` following the flat-file pattern. Shared UI components extracted to `packages/ui` only for widgets that need cross-application reuse (health score gauge, traffic light indicator).

## Complexity Tracking

> No constitution violations requiring justification. All gates pass.
