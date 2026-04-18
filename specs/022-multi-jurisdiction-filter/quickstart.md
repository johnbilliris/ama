# Quickstart: Multi-Jurisdiction Filter for Preparedness Page

**Feature**: 022-multi-jurisdiction-filter | **Date**: 2025-07-20

## Prerequisites

- Node.js 20+ and pnpm 9+ (frontend)
- Python 3.12+ and pip (backend)
- Git (with branch `022-multi-jurisdiction-filter` checked out)

## Setup

### 1. Clone and checkout

```bash
git checkout 022-multi-jurisdiction-filter
```

### 2. Install dependencies

```bash
# Frontend
cd apps/web
pnpm install

# Backend
cd apps/api
pip install -r requirements.txt
```

### 3. Start the backend API

```bash
cd apps/api
uvicorn app.main:create_app --factory --reload --port 8000
```

Verify the API is running:

```bash
# New jurisdictions endpoint
curl http://localhost:8000/api/jurisdictions
# Expected: JSON array of 9 jurisdictions

# Multi-jurisdiction organisations
curl "http://localhost:8000/api/organisations?jurisdictionId=nsw&jurisdictionId=vic"
# Expected: JSON array of NSW + VIC organisations

# Multi-jurisdiction frameworks
curl "http://localhost:8000/api/frameworks?jurisdictionId=nsw&jurisdictionId=vic"
# Expected: JSON array of frameworks assigned to NSW or VIC

# Backward-compatible single jurisdiction
curl "http://localhost:8000/api/organisations?jurisdictionId=nsw"
# Expected: JSON array of NSW organisations (same as before)
```

### 4. Start the frontend

```bash
cd apps/web
pnpm dev
```

Open http://localhost:3000/preparedness in your browser.

## Development Workflow

### Key files to modify

| Layer | File | Change |
|-------|------|--------|
| **Backend route** | `apps/api/app/api/routes/jurisdictions.py` | NEW: `GET /api/jurisdictions` endpoint |
| **Backend route** | `apps/api/app/api/routes/organisations.py` | MODIFY: `list[str]` query param |
| **Backend route** | `apps/api/app/api/routes/frameworks.py` | MODIFY: `list[str]` query param + assignment-based filter |
| **Backend router** | `apps/api/app/api/router.py` | MODIFY: register jurisdictions router |
| **Backend service** | `apps/api/app/services/organisation_intelligence_service.py` | MODIFY: `list[str]` filter |
| **Backend service** | `apps/api/app/services/preparedness_analysis_service.py` | MODIFY: framework filtering via assignments |
| **Seed data** | `packages/domain/src/domain/seed/framework_assignments_australia.json` | NEW: framework-jurisdiction mappings |
| **Seed bootstrap** | `packages/domain/src/domain/seed/bootstrap.py` | MODIFY: load framework_assignments |
| **Frontend page** | `apps/web/src/app/preparedness/page.tsx` | MODIFY: hybrid server/client |
| **Frontend component** | `apps/web/src/components/preparedness/preparedness-client.tsx` | NEW: client orchestrator |
| **Frontend component** | `apps/web/src/components/preparedness/jurisdiction-selector.tsx` | NEW: multi-select control |
| **Frontend component** | `apps/web/src/components/preparedness/operating-model-analyzer.tsx` | MODIFY: accept jurisdictions prop |
| **Frontend API client** | `apps/web/src/lib/api/jurisdictions.ts` | NEW: jurisdiction list fetch |
| **Frontend API client** | `apps/web/src/lib/api/organisations.ts` | MODIFY: multi-value query |
| **Frontend API client** | `apps/web/src/lib/api/frameworks.ts` | MODIFY: multi-value query |

### Running tests

```bash
# Backend unit + integration + contract tests
cd apps/api
python -m pytest tests/ -v

# Specific multi-jurisdiction tests
python -m pytest tests/unit/test_multi_jurisdiction_filter.py -v
python -m pytest tests/integration/test_multi_jurisdiction_api.py -v
python -m pytest tests/contract/test_preparedness_contract.py -v

# Frontend E2E tests (requires both backend and frontend running)
cd apps/web
pnpm test:e2e
```

### Manual testing checklist

1. **Empty state**: Load `/preparedness` (no URL params) → see "Select jurisdictions" prompt
2. **Single selection**: Select "NSW" → Organisation and Framework catalogs update
3. **Multi selection**: Select "NSW" + "VIC" → combined results, no duplicates
4. **Select All**: Click "Select All" → all 9 jurisdictions selected, catalogs show full dataset
5. **Clear All**: Click "Clear All" → empty state returns
6. **URL persistence**: Select "NSW" + "QLD" → URL shows `?jurisdictions=nsw,qld`. Copy URL, open in new tab → same selection restored
7. **Invalid URL**: Navigate to `?jurisdictions=nsw,invalid,vic` → only NSW + VIC selected, "invalid" silently dropped
8. **Rehearsal replay**: Select jurisdictions → Run rehearsal → results reflect selections → change jurisdictions → stale notice shown
9. **Replay disabled**: Clear All → "Run rehearsal replay" button is disabled
10. **Loading states**: Select jurisdictions → inline loading indicators appear per catalog
11. **Error handling**: Stop the API → select jurisdictions → inline error with retry per catalog
12. **Keyboard**: Tab to selector → Enter to open → Arrow keys to navigate → Space to toggle → Escape to close
13. **Debounce**: Rapidly toggle jurisdictions → only one API call fires after 300ms pause

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api` | Backend API base URL |

No new environment variables are needed for this feature.

## Architecture Notes

### Data flow

```
URL params → page.tsx (server) → PreparednessClient (client)
                                        │
                                        ├── JurisdictionSelector (user interaction)
                                        │       │
                                        │       └── selectedJurisdictionIds (state)
                                        │               │
                                        │               ├── 300ms debounce
                                        │               │
                                        │               ├── GET /api/organisations?jurisdictionId=...
                                        │               ├── GET /api/frameworks?jurisdictionId=...
                                        │               └── URL update via router.replace()
                                        │
                                        └── OperatingModelAnalyzer (presentation)
                                                ├── Organisation Catalog
                                                ├── Framework Catalog
                                                └── Rehearsal Replay
```

### API call pattern

The frontend constructs API URLs by appending repeated query parameters:

```typescript
// For selectedIds = ["nsw", "vic", "qld"]
const params = new URLSearchParams();
selectedIds.forEach(id => params.append("jurisdictionId", id));
// Result: jurisdictionId=nsw&jurisdictionId=vic&jurisdictionId=qld

const response = await fetch(`${API_BASE}/organisations?${params}`);
```

The backend FastAPI handler receives this as `list[str]`:

```python
@router.get("")
async def list_organisations(jurisdictionId: list[str] = Query(default=[])):
    # jurisdictionId = ["nsw", "vic", "qld"]
```
