# Quickstart: Governance Dashboard

**Feature**: 021-governance-dashboard
**Date**: 2025-07-18

---

## Prerequisites

- **Node.js** ≥ 20.x (for Next.js 16.2)
- **pnpm** ≥ 9.x (monorepo package manager)
- **Python** ≥ 3.11 (for FastAPI backend)
- **uv** (Python package manager — used via `pyproject.toml`)
- **Azure CLI** (for Cosmos DB emulator or remote connection)
- **Git** (branch: `021-governance-dashboard`)

## Repository Setup

```bash
# Clone and checkout feature branch
git checkout 021-governance-dashboard

# Install frontend dependencies
pnpm install

# Install backend dependencies
cd apps/api
uv sync
cd ../..
```

## Running the Development Environment

### Frontend (Next.js)

```bash
cd apps/web
pnpm dev
# → http://localhost:3000
# → Governance Dashboard: http://localhost:3000/governance/dashboard
```

Next.js is configured to proxy `/api/*` requests to the FastAPI backend (see `next.config.ts:12-43`).

### Backend (FastAPI)

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)
# → Dashboard endpoints: /api/v1/governance/dashboard/*
```

### Both (recommended)

From the repo root:
```bash
# Terminal 1: Frontend
pnpm --filter @ama/web dev

# Terminal 2: Backend
cd apps/api && uvicorn app.main:app --reload --port 8000
```

## Key Development Paths

### Adding a New Dashboard View (Frontend)

1. Create a page file at `apps/web/src/app/governance/dashboard/{view-name}/page.tsx`
2. Add components to `apps/web/src/components/governance/dashboard/`
3. Add API calls using `apps/web/src/lib/api/governance.ts`
4. Add navigation link in the dashboard layout (`dashboard/layout.tsx`)

**Pattern** (from existing governance page):
```tsx
// apps/web/src/app/governance/dashboard/compliance/page.tsx
import { ComplianceMatrix } from "@/components/governance/dashboard/ComplianceMatrix";

export default async function CompliancePage() {
  // Server component — fetch data server-side
  const data = await fetch(`${process.env.API_URL}/api/v1/governance/dashboard/compliance`);
  const compliance = await data.json();
  
  return <ComplianceMatrix data={compliance} />;
}
```

### Adding a New Dashboard Endpoint (Backend)

1. Define Pydantic response model in `apps/api/app/models/`
2. Add service method in `apps/api/app/services/`
3. Add endpoint in `apps/api/app/api/routes/governance_dashboard.py`
4. Register route in `apps/api/app/api/router.py`

**Pattern** (from existing governance router):
```python
# apps/api/app/api/routes/governance_dashboard.py
from fastapi import APIRouter, Depends
from app.services.dashboard_aggregation_service import DashboardAggregationService

router = APIRouter(prefix="/governance/dashboard", tags=["governance-dashboard"])

@router.get("/summary")
async def get_executive_summary(
    service: DashboardAggregationService = Depends(),
    tenant: TenantContext = Depends(get_tenant_context),
):
    return await service.get_executive_summary(tenant.tenant_id)
```

### Adding a New Domain Model

1. Create model file in `packages/domain/src/domain/models/`
2. Use Pydantic `BaseModel` with `Literal` types for enums
3. Follow the flat-file pattern (one model per file, `Field` descriptions)

**Pattern** (from existing models):
```python
# packages/domain/src/domain/models/governance_health_score.py
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class GovernanceHealthScore(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    status: Literal["green", "amber", "red"]
    # ...
```

## Testing

### Backend Tests

```bash
cd apps/api

# Unit tests
python -m pytest tests/unit/ -v

# Integration tests (requires Cosmos DB connection)
python -m pytest tests/integration/ -v

# Contract tests
python -m pytest tests/contract/ -v

# All tests
python -m pytest tests/ -v
```

### Frontend Tests

```bash
cd apps/web

# Component tests (Vitest)
pnpm test

# E2E tests (Playwright)
pnpm e2e
```

### Accessibility Tests

```bash
# Automated a11y checks (axe-core via Playwright)
pnpm e2e -- --grep "accessibility"

# Manual: Use screen reader (NVDA/VoiceOver) to verify companion data tables
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COSMOS_ENDPOINT` | Cosmos DB endpoint URL | (required) |
| `COSMOS_KEY` | Cosmos DB access key | (required) |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage for exports | (required for exports) |
| `APPINSIGHTS_CONNECTION_STRING` | Application Insights for telemetry | (optional) |
| `DASHBOARD_CACHE_TTL_S` | Cache TTL in seconds | `300` |
| `DASHBOARD_ACTIVE_POLL_MS` | Active incident poll interval (ms) | `30000` |
| `DASHBOARD_STEADY_POLL_MS` | Steady-state poll interval (ms) | `300000` |
| `EXPORT_MAX_CONCURRENT` | Max concurrent exports per user | `3` |
| `EXPORT_BLOB_CONTAINER` | Azure Blob container for exports | `governance-exports` |
| `EXPORT_TTL_HOURS` | Export file download window | `24` |

### Cosmos DB Indexes

The following composite indexes should be added to support dashboard queries:

```json
{
  "compositeIndexes": [
    [
      { "path": "/tenant_id", "order": "ascending" },
      { "path": "/timestamp", "order": "descending" },
      { "path": "/action_type", "order": "ascending" },
      { "path": "/actor", "order": "ascending" }
    ]
  ]
}
```

## Architecture Quick Reference

```
Browser → Next.js (SSR/CSR) → /api/* proxy → FastAPI → Cosmos DB
                                                    → Azure Blob Storage (exports)
                                                    → App Insights (telemetry)

Dashboard Views:
  /governance/dashboard           → Executive Summary (default)
  /governance/dashboard/compliance → Compliance Matrix
  /governance/dashboard/audit      → Audit Trail
  /governance/dashboard/readiness  → Operational Readiness
  /governance/dashboard/recovery   → Recovery Progress
  /governance/dashboard/risk       → Risk & Warning

Existing routes (unchanged):
  /governance                      → Current governance page (redirect to dashboard)
  /governance/[id]/compliance      → Data source compliance detail
  /governance/[id]/assignments     → Data source assignments
```

## Related Specs & Documentation

- **This feature**: `specs/021-governance-dashboard/`
- **Constitution**: `.specify/memory/constitution.md`
- **Tenant isolation**: spec 007
- **Alert/warning system**: spec 008
- **AIIMS roles**: spec 018
- **Emergency plans & recovery**: spec 019
- **API contract**: `specs/021-governance-dashboard/contracts/governance-dashboard-api.yaml`
- **Data model**: `specs/021-governance-dashboard/data-model.md`
- **Research decisions**: `specs/021-governance-dashboard/research.md`
- **Developer docs**: `docs/governance-dashboard.md`

## Implementation Status

All 100 tasks from `specs/021-governance-dashboard/tasks.md` have been implemented:

- **Phase 1**: Setup (T001–T003) ✅
- **Phase 2**: Foundational models, API, frontend (T004–T031) ✅
- **Phase 3**: US1 Executive Summary (T032–T041) ✅
- **Phase 4**: US2 Compliance Matrix (T042–T048) ✅
- **Phase 5**: US3 Audit Trail (T049–T059) ✅
- **Phase 6**: US4 Operational Readiness (T060–T066) ✅
- **Phase 7**: US5 Recovery Progress (T067–T072) ✅
- **Phase 8**: US6 Risk & Warning (T073–T079) ✅
- **Phase 9**: US7 Role-Based Personalisation (T080–T085) ✅
- **Phase 10**: US8 Audit Logging (T086–T090) ✅
- **Phase 11**: Polish — E2E, Bicep, Docs, Perf (T091–T100) ✅
