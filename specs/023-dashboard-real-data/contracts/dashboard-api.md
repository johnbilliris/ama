# API Contract: Governance Dashboard Endpoints

**Feature**: 023-dashboard-real-data
**Date**: 2025-07-18
**Contract Type**: REST API (FastAPI/OpenAPI)
**Base Path**: `/governance/dashboard`

## Contract Stability Guarantee

All 13 endpoints listed below have established consumers (frontend TypeScript client, agent integrations). This feature makes **zero breaking changes**:

- ✅ No endpoint path changes
- ✅ No HTTP method changes
- ✅ No field removals from response bodies
- ✅ No field type changes
- ✅ No new required request parameters
- ✅ Response value ranges remain within existing model constraints

The **only change** is that previously hardcoded/stub values are replaced with real computed values. The response structures are identical.

---

## Endpoint Catalogue

### 1. GET /governance/dashboard/config

**Response**: `DashboardConfigResponse`
**Change**: None. Configuration is not affected by data source changes.

---

### 2. GET /governance/dashboard/summary

**Response**: `ExecutiveSummaryResponse`

| Field | Type | Before (stub) | After (real) |
|-------|------|---------------|--------------|
| `health_score` | `GovernanceHealthScore` | Computed from hardcoded inputs | Computed from seed/stored data |
| `health_score.dimensions[0]` (constitutional) | `DimensionScore` | Always ~90 | Reflects actual assessment pass rate |
| `health_score.dimensions[1]` (readiness) | `DimensionScore` | Always ~80 | Reflects org AIIMS coverage + framework data |
| `health_score.dimensions[2]` (data_source) | `DimensionScore` | Static 10/7/2 | Reflects 46 seed sources by status |
| `health_score.dimensions[3]` (recovery) | `DimensionScore` | Static "no active recovery" | Reflects catalogue structure + trackers |
| `constitutional_gates` | `list[ConstitutionalGateStatus]` (len=10) | All "compliant" | Status from stored assessments or "assessment_pending" |
| `active_incident_count` | `int` | Always 1 | From stored incidents or 0 |
| `resource_utilisation_pct` | `float` | Always 72.5 | Computed from org data or 0.0 |
| `risk_summary` | `dict[str, int]` | Static {extreme:2, high:5, medium:12, low:8} | From stored HazardAssessment or all zeros |

**Contract impact**: None. All field types and names unchanged. Value ranges remain within model constraints.

---

### 3. GET /governance/dashboard/compliance

**Query params**: `compliance_status`, `category`, `sort_by`, `sort_dir`, `page_size`, `continuation_token`
**Response**: `ComplianceMatrixResponse`

| Field | Before | After |
|-------|--------|-------|
| `entries` | From repo or empty | From stored assessments + seed data source baseline |
| `total_count` | Matches entries | Matches entries (up to 46 seed sources) |

**Contract impact**: None. Entry structure unchanged. More entries may be returned (up to 46 vs previous empty/repo-based).

---

### 4. GET /governance/dashboard/compliance/{data_source_id}

**Response**: `ComplianceDetailResponse`

| Field | Before | After |
|-------|--------|-------|
| All fields | Hardcoded stub | From stored assessment history for specific source |
| `assessment_history` | Static list | Actual stored assessments (is_current filtered) |

**Contract impact**: None.

---

### 5. GET /governance/dashboard/audit

**Query params**: `date_from`, `date_to`, `actor`, `action_type`, `affected_entity`, `keyword`, `page_size`, `continuation_token`
**Response**: `AuditTrailResponse`

| Field | Before | After |
|-------|--------|-------|
| `events` | Hardcoded 3-event stub | Actual stored GovernanceAuditEntry records |
| `total_count` | Always 3 | Actual count (0 when no actions taken) |

**Contract impact**: None. Initial state may show 0 events instead of 3 fake events. This is correct per spec clarification.

---

### 6. GET /governance/dashboard/audit/{event_id}/chain

**Response**: `AuditDecisionChainResponse`

| Field | Before | After |
|-------|--------|-------|
| `chain` | Hardcoded 2-step stub | Actual linked audit events |

**Contract impact**: None.

---

### 7. POST /governance/dashboard/audit/export

**Response**: `AuditExportJobResponse` (202 Accepted)
**Change**: None. Export operates on whatever audit data exists.

---

### 8. GET /governance/dashboard/audit/export/{job_id}

**Response**: `AuditExportJobResponse`
**Change**: None.

---

### 9. GET /governance/dashboard/readiness

**Response**: `OperationalReadinessResponse`

| Field | Before (stub) | After (real) |
|-------|---------------|--------------|
| `pprr_phases` (len=4) | Static active/inactive | Computed from 123 framework assignments |
| `emergency_plans` | 7 states × 3 each | From stored plans or zero counts |
| `total_plans` | Always 21 | Actual count |
| `exercise_completion_rate_pct` | Always 65.0 | From framework exercise metadata or 0.0 |
| `aiims_role_coverage` | Hardcoded 10 roles | Computed from 49 org AIIMS function assignments |
| `overall_role_coverage_pct` | Always 87.5 | Computed from actual coverage |
| `capability_gaps` | Empty list | Derived from framework vs org capability comparison |
| `volunteer_readiness` | Hardcoded metrics | Computed from volunteer/mixed workforce orgs |

**Contract impact**: None. All types preserved. May return different role names in AIIMS coverage (6 AIIMS functions vs previous 10 custom roles).

---

### 10. GET /governance/dashboard/recovery

**Response**: `RecoveryProgressResponse`

| Field | Before (stub) | After (real) |
|-------|---------------|--------------|
| `domains` | 4 domains (social, economic, built, natural) with fake % | Up to 5 domains (+ overarching) from recovery catalogue |
| `domains[].completion_pct` | 45–70% fake | 0% baseline (no trackers) or actual tracker % |
| `has_active_recovery` | Always True | From stored trackers |
| `available_incidents` | Static list | From stored incidents |

**Contract impact**: None. Domain count increases from 4→5 (within `max_length=5` constraint). The `overarching` domain was always in the Literal type but never populated.

---

### 11. GET /governance/dashboard/recovery/{domain}

**Path param**: `domain` ∈ {overarching, social, economic, built, natural}
**Response**: `RecoveryDomainDetail`

| Field | Before | After |
|-------|--------|-------|
| `outcome_targets` | Hardcoded stub | From recovery catalogue outcomes + indicators |
| `activity_completion_rates` | Hardcoded | From catalogue activities |
| `community_indicators` | Hardcoded | From catalogue indicators |

**Contract impact**: None.

---

### 12. GET /governance/dashboard/risk

**Response**: `RiskWarningResponse`

| Field | Before (stub) | After (real) |
|-------|---------------|--------------|
| `risk_severity` | {extreme:2, high:5, medium:12, low:8, total:27} | From stored HazardAssessment or all zeros |
| `top_risks` | Hardcoded list | From stored assessments ranked by severity |
| `alert_compliance.principle_compliance` | Hardcoded 10 principles | From data source trust tier analysis |
| `treatment_closure_rate_pct` | Always 68.0 | Computed or 0.0 |

**Contract impact**: None.

---

### 13. GET /governance/dashboard/risk/{risk_id}

**Response**: `RiskDetailResponse`

| Field | Before | After |
|-------|--------|-------|
| All fields | Hardcoded stub | From stored HazardAssessment record |

**Contract impact**: None.

---

## Frontend TypeScript Contract Alignment

The TypeScript types in `apps/web/src/lib/api/governance.ts` define 26 interfaces/types and 13 API call functions. All existing type definitions remain valid after this change. No new required properties are added.

**Key type validations**:
- `GovernanceHealthScore.dimensions` — still `DimensionScore[]` with 4 entries
- `ConstitutionalGateStatus` — same 7 fields; `status` values now include real `"assessment_pending"`
- `RecoveryDomainProgress.domain` — Literal union already includes `"overarching"`
- `RiskSeverityBreakdown` — same 5 numeric fields; values may now be 0

---

## Error Contract (unchanged)

| HTTP Status | Condition | Response Body |
|-------------|-----------|---------------|
| 200 | Success | Endpoint-specific response model |
| 202 | Export job created | `AuditExportJobResponse` |
| 404 | Resource not found | `{"detail": "..."}` |
| 422 | Validation error | FastAPI validation error response |
| 503 | Service unavailable | `{"detail": "Dashboard data temporarily unavailable"}` |
