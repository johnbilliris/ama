# Research: Governance Dashboard

**Feature**: 021-governance-dashboard
**Date**: 2025-07-18
**Status**: Complete — all NEEDS CLARIFICATION items resolved

---

## Research Summary

This document resolves all unknowns identified during Technical Context analysis, documents technology decisions with rationale, and records checklist conflict resolutions that inform the implementation plan.

---

## R-001: Audit Search Performance Target

**Decision**: Use 2-second target with server-side Cosmos DB pagination

**Rationale**: The spec contains two conflicting performance requirements — SC-003 specifies "5 seconds for search and retrieval" while US3-AS2 specifies "filtered results within 2 seconds." The stricter 2-second target is adopted as the primary requirement. Cosmos DB cross-partition queries with properly indexed fields (`timestamp`, `actor`, `action_type`, `affected_entity`) and server-side pagination (50 records per page with continuation tokens) can achieve this. The 5-second SC-003 value becomes the degraded-mode fallback threshold — if response time exceeds 2s but stays under 5s, the UI shows results with a "slow query" indicator rather than timing out.

**Alternatives Considered**:
- **5-second target everywhere**: Rejected — US3-AS2 is a user acceptance scenario with a tighter bound; ignoring it creates a testability gap.
- **Client-side filtering**: Rejected — audit data volumes during major incidents (~10k records/day) make client-side approaches impractical and create data transfer overhead.
- **Dedicated search index (Azure Cognitive Search)**: Rejected as premature — Cosmos DB's built-in indexing with composite indexes on audit fields should achieve 2s for the expected data volumes. Can be reconsidered if volumes exceed 1M records.

**Implementation Notes**:
- Add composite index on `(tenant_id, timestamp DESC, action_type)` to the audit container
- Use `continuation_token` pattern (existing in `governance_repository.py`) for pagination
- Return `total_count` via a separate lightweight count query with same filters
- Cache count query results for 30s to avoid double-counting cost

---

## R-002: Read-Only Dashboard vs State Changes

**Decision**: Dashboard is strictly read-only. "Governance state changes initiated from dashboard" (FR-028) means the dashboard provides navigation links to existing CRUD pages.

**Rationale**: The spec's Assumptions section explicitly states "The dashboard is a read-only reporting interface for governance data. Any governance state changes (e.g., triggering reassessment) are submitted as requests that go through existing human-in-the-loop approval workflows." FR-028's reference to "state changes initiated from the dashboard" describes the user journey, not inline mutations — the user sees a non-compliant item, clicks a link ("Request Reassessment"), and is navigated to the existing assessment workflow page.

**Alternatives Considered**:
- **Inline mutation with confirmation dialogs**: Rejected — adds complexity and new mutation endpoints; conflicts with read-only assumption; duplicates existing CRUD workflows.
- **Dashboard-specific API for state transitions**: Rejected — creates parallel mutation paths, complicating audit trails and increasing the attack surface.

**Implementation Notes**:
- FR-028 confirmation dialogs are implemented as "are you sure you want to leave?" interstitials before navigating to CRUD pages
- The audit trail records the navigation intent (e.g., "user initiated reassessment request from compliance view") before redirecting
- No new POST/PUT/DELETE endpoints on the dashboard API (except export, which is a read operation producing a file)

---

## R-003: Refresh Interval Strategy

**Decision**: 30-second polling for active-incident views; 5-minute polling for all other views

**Rationale**: FR-029 defines "30s during active incidents and 5min for steady-state dashboard views." SC-005 says "default 30 seconds" for health score updates, which applies specifically during active incidents when the health score is most volatile. During peacetime, 5-minute refresh is sufficient and significantly reduces API load. The determination of "active incident" is server-driven — the `/governance/dashboard/config` endpoint returns the current polling interval based on whether any active incidents exist.

**View-to-Interval Mapping**:

| View | Active Incident Interval | Peacetime Interval |
|------|--------------------------|-------------------|
| Executive Summary | 30s | 5min |
| Risk & Warning | 30s | 5min |
| Compliance Matrix | 5min | 5min |
| Audit Trail | Manual only (search-driven) | Manual only |
| Operational Readiness | 5min | 5min |
| Recovery Progress | 5min | 5min |

**Alternatives Considered**:
- **30s everywhere**: Rejected — unnecessary load; compliance and recovery data rarely changes within 30s.
- **WebSocket push**: Rejected — spec explicitly states REST polling consistent with existing platform patterns. WebSocket would require new infrastructure.
- **Client-determined intervals**: Rejected — server should determine tempo based on incident status; client can override with manual refresh.

**Implementation Notes**:
- `/governance/dashboard/config` endpoint returns `{ poll_interval_ms, has_active_incident, cache_ttl_s }`
- Frontend `useGovernancePolling()` hook consumes this config and adjusts `setInterval`
- Manual refresh button always available, bypasses cache (sends `Cache-Control: no-cache` header)
- Cache invalidation on manual refresh: only the requesting user's view is refreshed, not the global cache

---

## R-004: Health Score Calculation Approach

**Decision**: Server-side aggregation in a dedicated `HealthScoreService` within FastAPI, with results cached in the existing governance cache (5-minute TTL)

**Rationale**: The health score is a composite of 4 weighted dimensions requiring data from multiple Cosmos DB containers. Computing this client-side would require multiple API calls and expose calculation logic. Server-side computation with caching ensures consistent scores across all users and reduces per-request cost.

**Calculation Algorithm**:
```
score = (constitutional_compliance_pct × 0.40)
      + (operational_readiness_pct × 0.25)
      + (data_source_governance_pct × 0.20)
      + (recovery_progress_pct × 0.15)

Where:
- constitutional_compliance_pct = (compliant_gates + 0.5 × partially_compliant_gates) / assessed_gates × 100
  - "assessment pending" gates are EXCLUDED from denominator (CHK020 resolution)
  - If no gates are assessed, this dimension contributes 0 to the score

- operational_readiness_pct = weighted average of:
  - AIIMS role coverage % (weight: 0.30)
  - Emergency plan currency % (endorsed + activated / total non-superseded, weight: 0.30)
  - Exercise completion rate % (weight: 0.20)
  - Capability gap inverse % (1 - gaps/total_capabilities, weight: 0.20)

- data_source_governance_pct = (compliant_sources + grace_period_sources × 0.5) / total_sources × 100

- recovery_progress_pct = average of 4 concrete domain completion percentages
  - Overarching domain is excluded (it's derived from the 4 concrete domains)
  - If no active recovery, this dimension = 100 (no recovery needed = fully recovered)

Traffic light: Green (≥80), Amber (50–79), Red (<50)
```

**Alternatives Considered**:
- **Client-side calculation**: Rejected — requires multiple API calls, exposes algorithm, inconsistent results across users.
- **Azure AI Foundry for anomaly detection**: Investigated — not needed for initial implementation. Health score is a deterministic calculation. Anomaly detection on health score trends could be a future enhancement but is out of scope.
- **Pre-computed in Cosmos DB change feed**: Rejected as premature optimisation — the aggregation queries are lightweight given expected data volumes. Can be reconsidered if computation exceeds 500ms.

---

## R-005: Audit Export Approach

**Decision**: Server-side export generation using Python libraries — ReportLab for PDF, built-in `csv` module for CSV, `json` module for JSON. Exports are async with progress tracking.

**Rationale**: Export must preserve all provenance metadata (FR-012). Server-side generation ensures data consistency (user sees exactly what they searched), proper formatting, and tamper-evident metadata headers. PDF requires a rendering engine that browsers can't reliably provide.

**Export Architecture**:
1. User selects records and format → POST `/governance/dashboard/audit/export`
2. Server creates an `AuditExportJob` record (status: `queued`)
3. Background task generates the file, stores in Azure Blob Storage (hot tier, 24h TTL)
4. Job status updated to `complete` with download URL
5. Frontend polls job status, shows progress bar, enables download when ready
6. Audit trail records the export action with scope, format, record count

**Alternatives Considered**:
- **Client-side PDF generation (jsPDF)**: Rejected — limited formatting, can't guarantee provenance metadata preservation, large bundle size.
- **Azure Functions for export**: Rejected — introduces new compute surface; FastAPI background tasks with Azure Blob Storage are sufficient.
- **Synchronous export**: Rejected — large audit exports (thousands of records) would block the API thread and timeout.

---

## R-006: Cosmos DB Query Optimisation for Dashboard

**Decision**: Extend existing partition key strategy with new composite indexes; add dashboard-specific materialised views via the aggregation service

**Rationale**: The existing repository uses `type` discriminator with partition keys per entity type. Dashboard queries need cross-entity aggregation that would otherwise require expensive cross-partition queries.

**Query Strategy**:

| Dashboard View | Primary Query | Partition Strategy | Target Latency |
|---------------|---------------|-------------------|----------------|
| Health Score | Aggregate across 4 dimensions | 4 parallel partition-aligned queries, combined in service | <500ms |
| Compliance Matrix | List data sources with assessment joins | Source partition + batch assessment lookups | <1s |
| Audit Trail Search | Filtered scan with pagination | Audit partition + composite index | <2s |
| Constitutional Gates | 10 gate status lookups | Assessment partition, gate-id aligned | <200ms |
| Risk Register | Risk entries by severity | Risk partition + severity index | <500ms |
| Recovery Progress | 4-domain progress lookups | Recovery partition, domain-id aligned | <500ms |
| PPRR Status | Phase indicator lookups | PPRR context partition | <200ms |

**New Indexes Required**:
- Audit container: composite index on `(tenant_id, timestamp DESC, action_type, actor)`
- Assessment container: composite index on `(gate_id, is_current, compliance_status)`
- Data source container: composite index on `(compliance_status, governance_status, kind)`

**Alternatives Considered**:
- **Separate read-model database**: Rejected — Cosmos DB with proper indexing handles the expected query patterns. CQRS read model adds operational complexity.
- **Azure Cognitive Search**: Rejected for initial implementation — Cosmos DB full-text search is not needed; structured filters on indexed fields are sufficient.

---

## R-007: Tenant Isolation for Dashboard

**Decision**: Extend existing middleware to extract `tenant_id` from Entra ID claims and inject into all dashboard API calls

**Rationale**: Per FR-026A, tenant context (`live` or `sim-{scenarioRunId}`) is server-derived from Entra ID claims — never client-selectable. The existing API has no tenant_id handling (confirmed by codebase exploration). This must be added as middleware that:
1. Extracts `tenant_id` from the authenticated user's Entra ID token claims
2. Defaults to `live` if no simulation claim is present
3. Injects `tenant_id` into the request context (FastAPI dependency)
4. All dashboard repository queries include `tenant_id` as a mandatory filter

**Implementation Notes**:
- Add `TenantContext` dependency to FastAPI that reads from middleware-set request state
- All governance dashboard endpoints require `TenantContext` as a parameter
- Repository methods gain a `tenant_id` parameter (non-optional)
- Frontend: `TenantBanner` component reads tenant context from the initial config endpoint
- Simulation banner: persistent, non-dismissible, uses `--ama-sim-banner` colour token

**Alternatives Considered**:
- **Client-side tenant selector**: Explicitly forbidden by spec — "no tenant switcher exposed to the client."
- **Cookie-based tenant context**: Rejected — server-derived from auth token is more secure and consistent with spec 007.

---

## R-008: Frontend Component Architecture

**Decision**: New dashboard components live in `apps/web/src/components/governance/dashboard/`; extract only `HealthScoreGauge` and `TrafficLightIndicator` to `packages/ui` for cross-app reuse potential.

**Rationale**: The existing governance components (`GovernanceSummary`, `DataSourceTable`, `ComplianceCard`, `HandoffChainEditor`) live in `apps/web/src/components/governance/` — not in the shared `packages/ui` package. The dashboard components follow this same pattern. Only truly reusable primitive widgets (gauge, traffic light) are candidates for `packages/ui`.

**Component Patterns (from codebase analysis)**:
- Components use React 19 with TypeScript, default exports
- Data fetching is done inline with `fetch()` in page components (no global state library)
- The `@ama/ui` AppShell provides navigation chrome; pages fill the content area
- Existing governance page fetches from `/api/v1/governance/dashboard` inline
- No API client library exists for governance endpoints (unlike other features which use `lib/api/*.ts`)

**New Pattern: `lib/api/governance.ts`**:
- Typed API client for all governance dashboard endpoints
- Consistent error handling with `WidgetErrorBoundary`
- Continuation token support for paginated endpoints
- Cache-control header support for manual refresh

**Alternatives Considered**:
- **Move all governance components to packages/ui**: Rejected — these components are AMA-specific, not generic UI primitives. Moving them would bloat the shared package.
- **Use a state management library (Zustand, Jotai)**: Rejected — React 19 `use()` + server components + polling is sufficient for the dashboard's read-only data flow pattern. Consistent with existing codebase.

---

## R-009: Accessibility Pattern for Dashboard Charts

**Decision**: Every chart/gauge widget has a companion data table (visually hidden, toggle-able) and ARIA labels. Implements FR-032 per spec clarification.

**Rationale**: WCAG 2.1 AA requires programmatic alternatives for visual content. The spec explicitly mandates companion data tables for all charts and visualisations.

**Pattern**:
```tsx
<HealthScoreGauge score={78} status="amber">
  <CompanionDataTable
    caption="Governance health score breakdown"
    data={[
      { dimension: "Constitutional Compliance", score: 85, weight: "40%" },
      { dimension: "Operational Readiness", score: 72, weight: "25%" },
      // ...
    ]}
  />
</HealthScoreGauge>
```

- `CompanionDataTable` is visually hidden by default (`sr-only` class)
- A "Show data table" toggle button is adjacent to each chart
- ARIA labels: `aria-label="Governance health score: 78 out of 100, Amber status"`
- All interactive elements have `tabIndex`, `role`, and keyboard handlers
- AWS severity colours use tokens: `--ama-aws-advice`, `--ama-aws-watch`, `--ama-aws-emergency`
- Colour is never the sole means of conveying information (icons + text labels accompany all colour indicators)

---

## R-010: Observability and Telemetry

**Decision**: Extend existing Azure Monitor + Application Insights integration with structured telemetry for dashboard performance metrics. No PII in telemetry.

**Rationale**: FR-034 requires structured telemetry for page load time, API call latency, error rates, and widget render times. FR-035 requires no PII. The platform already uses App Insights (confirmed in `infra/bicep/monitoring.bicep`).

**Telemetry Schema**:
```json
{
  "event": "dashboard.widget.render",
  "properties": {
    "view": "executive_summary",
    "widget": "health_score_gauge",
    "render_time_ms": 145,
    "data_freshness_s": 28,
    "tenant_type": "live",
    "correlation_id": "anon-uuid-v4"
  }
}
```

- **Backend**: FastAPI middleware emits request duration, status code, endpoint path to App Insights
- **Frontend**: Custom `useWidgetTelemetry()` hook measures render time and reports via App Insights JS SDK
- **No PII**: User identity replaced with `correlation_id` (anonymous UUID per session)
- **Audit vs telemetry boundary**: Audit trail (FR-027) includes user identity; telemetry (FR-034/035) does not

---

## R-011: Audit Retention Strategy

**Decision**: 7-year retention for compliance audit data; 90-day hot storage for dashboard interaction logs with cold-tier archival

**Rationale**: Australian regulatory record-keeping requirements (particularly for emergency management compliance) suggest 7-year retention. Dashboard interaction logs are operational data with lower regulatory significance.

**Retention Architecture**:
- **Compliance audit records** (assessments, governance decisions, export records): Cosmos DB with 7-year TTL disabled (manual archival to Azure Storage archive tier after 2 years)
- **Dashboard interaction logs** (view access, filter, search, drill-down): Cosmos DB with 90-day TTL, then archived to Azure Blob Storage cool tier, retained for 7 years in archive tier
- **Telemetry data** (App Insights): 90-day retention per Azure Monitor defaults, no archival needed
- **Export files** (PDF/CSV/JSON in Azure Blob Storage): 24-hour hot tier TTL for download, then deleted

---

## R-012: Emergency Plan Lifecycle and "Expired" Overlay

**Decision**: "Expired" is a display-level condition applied as a visual overlay, not a lifecycle state. The 7 lifecycle states from spec 019 are: Draft, InConsultation, UnderReview, Endorsed, Activated, PostEventReview, Superseded.

**Rationale**: Per spec clarification (session 2026-04-17 Pass 2), "Expired" indicates that a plan's next review date has passed. This can apply to any lifecycle state (e.g., an Endorsed plan can be expired if its review is overdue). The overdue calculation compares `next_review_date` against the current date (UTC, converted to AEST for display).

**Implementation Notes**:
- `EmergencyPlanStatus` component shows 7-state badges with optional "⚠ OVERDUE" overlay
- Days overdue calculated as: `max(0, (today_utc - next_review_date).days)`
- Timezone: all dates stored as UTC; display converted to AEST (UTC+10) / AEDT (UTC+11) based on current offset
- Plans with `next_review_date = null` are excluded from overdue checks

---

## R-013: Recovery Domain Mapping

**Decision**: Display 5 `RecoveryDomain` values; map to 4 `RecoveryEnvironmentTracker` values for underlying data. The "Overarching" domain aggregates cross-cutting indicators from the 4 concrete domains.

**Rationale**: Per spec clarification and FR-017, the AIDR M&E Framework defines 5 recovery domains (including "Overarching — Resilience & Sustainability") but only 4 concrete recovery environments are tracked independently. The overarching domain is a derived view.

**Mapping**:
```
RecoveryDomain (display)         → RecoveryEnvironmentTracker (data)
─────────────────────────────────────────────────────────────────────
Overarching (Resilience)         → Aggregates all 4 below
Social                           → Social
Economic                         → Economic
Built                            → Built
Natural                          → Natural
```

**Overarching Calculation**: Average of the 4 concrete domain completion percentages, with additional cross-cutting resilience and sustainability indicators displayed in the detail panel.
