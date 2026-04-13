# Quick Start: Disaster Mapper UI

**Feature**: 020-disaster-mapper-ui
**Branch**: `020-disaster-mapper-ui`

---

## Prerequisites

- Node.js 18+ and pnpm 10.6+
- Python 3.11+ and uv (Python package manager)
- Azure subscription with Azure Maps account provisioned (or use local dev mode)
- Cosmos DB emulator or Azure Cosmos DB connection for API testing

## Getting Started

### 1. Clone and checkout branch

```bash
git checkout 020-disaster-mapper-ui
```

### 2. Install dependencies

```bash
# Root monorepo dependencies
pnpm install

# Python API dependencies
cd apps/api
uv sync
cd ../..
```

### 3. Environment variables

Create `apps/web/.env.local`:

```env
# Azure Maps subscription key (for development)
NEXT_PUBLIC_AZURE_MAPS_KEY=<your-azure-maps-subscription-key>

# API base URL (FastAPI backend)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Create or update `apps/api/.env`:

```env
# Cosmos DB connection (existing)
COSMOS_ENDPOINT=https://<your-cosmos-account>.documents.azure.com:443/
COSMOS_DATABASE=disaster-hub

# Azure Maps (for server-side validation if needed)
AZURE_MAPS_CLIENT_ID=<your-maps-client-id>
```

### 4. Start development servers

**Terminal 1 — FastAPI backend:**

```bash
cd apps/api
uvicorn app.main:create_app --factory --reload --port 8000
```

**Terminal 2 — Next.js frontend:**

```bash
cd apps/web
pnpm dev
```

### 5. Access the Disaster Mapper

Open [http://localhost:3000/disasters](http://localhost:3000/disasters)

## Key Paths

| What | Where |
|------|-------|
| **Page route** | `apps/web/src/app/disasters/page.tsx` |
| **Map component** | `packages/ui/src/components/disaster-map/disaster-map.tsx` |
| **Filter panel** | `packages/ui/src/components/disaster-map/filter-panel.tsx` |
| **Detail sidebar** | `packages/ui/src/components/disaster-map/incident-sidebar.tsx` |
| **Search bar** | `packages/ui/src/components/disaster-map/search-bar.tsx` |
| **List fallback** | `packages/ui/src/components/disaster-map/list-view-fallback.tsx` |
| **Filter hook** | `packages/ui/src/components/disaster-map/use-disaster-map-filters.ts` |
| **API client** | `apps/web/src/lib/api/incidents-map.ts` |
| **API endpoint** | `apps/api/app/api/routes/incidents_map.py` |
| **Repository** | `apps/api/app/repositories/incident_map_repository.py` |
| **GeoJSON models** | `apps/api/app/models/geojson.py` |
| **Domain model** | `packages/domain/src/domain/models/incident.py` |
| **Design tokens** | `packages/ui/src/styles/tokens.css` |
| **Bicep module** | `infra/modules/azure-maps.bicep` |
| **Main Bicep** | `infra/main.bicep` |

## Running Tests

### Python (API + domain)

```bash
# Unit tests for the map repository
cd apps/api
python -m pytest ../../tests/unit/test_incident_map_repository.py -v

# Contract tests for the map endpoint
python -m pytest ../../tests/contract/test_incidents_map_contract.py -v
```

### Frontend (lint + e2e)

```bash
# ESLint
pnpm lint:web

# Playwright e2e tests
cd apps/web
pnpm test:e2e
```

### Infrastructure

```bash
# Bicep what-if (requires Azure CLI + active subscription)
az deployment group what-if \
  --resource-group <your-rg> \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json
```

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                        Browser (Desktop / Mobile)                │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  /disasters      │  │ Azure Maps   │  │  Filter Panel      │  │
│  │  page.tsx        │──│ JS SDK       │  │  + Search Bar      │  │
│  │  (Next.js 15)   │  │ (atlas.Map)  │  │  + Detail Sidebar  │  │
│  └────────┬─────────┘  └──────┬───────┘  └────────┬───────────┘  │
│           │                   │                    │              │
│           │    API calls      │   Map tiles        │              │
└───────────┼───────────────────┼────────────────────┼──────────────┘
            │                   │                    │
            ▼                   ▼                    │
┌───────────────────┐  ┌───────────────────┐         │
│  FastAPI Backend   │  │  Azure Maps       │         │
│  /api/v1/incidents │  │  Tile Service     │         │
│  /map              │  │  (Australia East) │         │
│  (GeoJSON response)│  └───────────────────┘         │
└────────┬──────────┘                                 │
         │                                            │
         ▼                                            │
┌───────────────────┐  ┌───────────────────┐          │
│  Azure Cosmos DB   │  │  Azure Monitor /  │◄─────────┘
│  disaster-hub      │  │  App Insights     │  (telemetry)
│  incidents         │  │  (5 named metrics)│
│  (Australia East)  │  └───────────────────┘
└───────────────────┘
```

## Severity Colour Quick Reference

| Domain Value | AWS Tier | Colour | Shape | CSS Token |
|---|---|---|---|---|
| `advisory` | Advice | 🟡 #FFC107 | Circle | `--ama-aws-advice` |
| `watch` | Watch and Act | 🟠 #FF8C00 | Triangle | `--ama-aws-watch` |
| `warning` | Emergency Warning | 🔴 #D32F2F | Diamond | `--ama-aws-emergency` |
| `emergency` | Emergency Warning | 🔴 #D32F2F | Diamond | `--ama-aws-emergency` |

## URL Filter Parameters

The filter state is persisted in URL query parameters for bookmarkability:

```
/disasters?type=bushfire,flood&severity=advisory&status=active&pprr_phase=response&keyword=nsw&year_start=2020&year_end=2024
```

| Parameter | Format | Example |
|-----------|--------|---------|
| `type` | Comma-separated | `type=bushfire,flood` |
| `severity` | Comma-separated | `severity=advisory,watch` |
| `status` | Comma-separated | `status=active,monitoring` |
| `pprr_phase` | Comma-separated | `pprr_phase=response` |
| `keyword` | Single string | `keyword=sydney` |
| `year_start` | Integer | `year_start=2020` |
| `year_end` | Integer | `year_end=2024` |
