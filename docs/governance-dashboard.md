# Governance Dashboard – Technical Documentation (T096)

## Overview

The Governance Dashboard provides a unified, read-only interface for monitoring governance health across six key views. It implements the AIIMS (Australasian Inter-Service Incident Management System) authority hierarchy for role-based widget personalization across 10 operational roles.

## Architecture

### Dashboard Views

| View | Endpoint | Description |
|------|----------|-------------|
| Executive Summary | `/governance/dashboard/executive-summary` | Health score, 10 constitutional gates, risk summary |
| Compliance Matrix | `/governance/dashboard/compliance-matrix` | Sortable/filterable data source compliance table |
| Audit Trail | `/governance/dashboard/audit-trail` | Searchable audit events with export capability |
| Operational Readiness | `/governance/dashboard/operational-readiness` | PPRR phases, emergency plans, role coverage |
| Recovery Progress | `/governance/dashboard/recovery-progress` | 5-domain recovery tracking |
| Risk & Warning | `/governance/dashboard/risk-warning` | Risk register, AWS alert compliance |

### API Endpoints (13 total)

```
GET  /governance/dashboard/executive-summary
GET  /governance/dashboard/health-score
GET  /governance/dashboard/constitutional-gates
GET  /governance/dashboard/compliance-matrix
GET  /governance/dashboard/audit-trail
GET  /governance/dashboard/audit-trail/{ds_id}/decision-chain
POST /governance/dashboard/audit-trail/export
GET  /governance/dashboard/audit-trail/export/{job_id}
GET  /governance/dashboard/operational-readiness
GET  /governance/dashboard/recovery-progress
GET  /governance/dashboard/recovery-progress/{domain}
GET  /governance/dashboard/risk-warning
GET  /governance/dashboard/config
```

## Health Score Algorithm (R-004)

The composite governance health score uses weighted dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Constitutional Compliance | 40% | 10 gates assessment (pending gates excluded from denominator) |
| Operational Readiness | 25% | Exercise completion, role coverage, plan currency |
| Data Source Governance | 20% | Compliant + partially compliant data sources |
| Recovery Progress | 15% | Domain completion (100% if no active recovery) |

**Traffic Light Thresholds:**
- 🟢 Green: ≥ 80
- 🟡 Amber: 50–79
- 🔴 Red: < 50

## AIIMS Role-Based Personalisation

All 10 AIIMS roles have configured default views and widget sets:

| Role | Authority Rank | Default View |
|------|---------------|--------------|
| Incident Controller | 1 | Executive Summary |
| Executive Leader | 2 | Executive Summary |
| Operations Officer | 3 | Operational Readiness |
| Planning Officer | 4 | Operational Readiness |
| Intelligence Officer | 5 | Compliance Matrix |
| Logistics Officer | 6 | Recovery Progress |
| Public Information Officer | 7 | Risk & Warning |
| Risk Manager | 8 | Risk & Warning |
| Resilience Planner | 9 | Recovery Progress |
| Observer/Auditor | 10 | Audit Trail |

**Multi-Role Resolution:** When a user holds multiple roles, widgets are merged (union of all role widgets), ordered by highest authority rank first.

## Data Freshness & Polling

- **Steady-state polling:** Every 5 minutes (300,000ms)
- **Active incident polling:** Every 30 seconds (30,000ms)
- **Manual refresh:** Via `Cache-Control: no-cache` header
- **Stale data indicator:** Badge shown when data exceeds freshness threshold

## Audit Export

- **Formats:** CSV, JSON, PDF
- **State machine:** `queued → processing → complete | failed`
- **Concurrent limit:** 3 active exports per user
- **Storage:** Azure Blob Storage with 90-day lifecycle policy

## Recovery Domain Mapping (R-013)

5 display domains with overarching as calculated average:

1. **Overarching** (cross-cutting): Average of Social + Economic + Built + Natural
2. **Social**: Community wellbeing, health services
3. **Economic**: Business, employment, financial systems
4. **Built**: Infrastructure, housing, transport
5. **Natural**: Environment, ecosystems, waterways

## Emergency Plan Lifecycle (R-012)

7 valid lifecycle states:
`draft → under_review → approved → active → suspended → archived → superseded`

**Note:** "Expired" is a display-level overlay condition, NOT a lifecycle state.

## AWS Warning System Compliance

10 principles checked for alert compliance:
1. Timely 2. Accurate 3. Trustworthy 4. Inclusive 5. Clear
6. Responsive 7. Respectful 8. Targeted 9. Interoperable 10. Monitored

## Infrastructure

- **Cosmos DB:** Governance dashboard container (partition: `/tenant_id`) with composite indexes
- **Health Score History:** Separate container with 90-day TTL
- **Blob Storage:** `audit-exports` container with lifecycle management
- **Bicep Module:** `infra/modules/governance-dashboard.bicep`

## Testing

### Unit Tests
- `tests/unit/test_governance_health_score_model.py` — Domain model validation
- `tests/unit/test_audit_export_model.py` — State machine transitions
- `tests/unit/test_health_score_service.py` — Weighted score calculation
- `tests/unit/test_dashboard_aggregation.py` — All 6 view aggregation
- `tests/unit/test_audit_export_service.py` — Export job processing
- `tests/unit/test_dashboard_config.py` — Role-widget config resolution
- `tests/unit/test_dashboard_audit_logging.py` — Audit action types

### Contract Tests
- `tests/contract/test_governance_dashboard_contract.py` — API response schemas

### Integration Tests
- `tests/integration/test_governance_dashboard_api.py` — All 13 endpoints

### E2E Tests
- `tests/e2e/governance-dashboard.spec.ts` — Playwright navigation + accessibility

## Performance Targets

| Metric | Target |
|--------|--------|
| Executive summary load | < 2 seconds |
| Compliance matrix sort | < 500ms |
| Audit trail search | < 1 second |
| Health score calculation | < 500ms |
| Export queue acceptance | < 200ms |

> **Spec-037 deprecation banner (T051, FR-022)**: For executive roll-up purposes this surface is consolidated into the [Executive KPI Surface](governance-hub/executive-kpi/surface.md). This file retains its operational governance dashboard role; the executive view is the single source of truth for capstone-criterion KPIs.

