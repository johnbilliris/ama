# Architecture: Autonomous Disaster Response Coordination Hub

## Overview

The Disaster Response Coordination Hub is built as a cloud-native monorepo delivering three coordinated services on Azure, purpose-built for Australian multi-agency disaster coordination.

```
                        ┌────────────────────────┐
                        │     Azure App Service   │
                        │      apps/web (Next.js) │
                        └────────────┬───────────┘
                                     │ HTTPS
                        ┌────────────▼───────────┐
                        │  Azure Container Apps   │
                        │  apps/api (FastAPI)     │
                        │  apps/agents (Python)   │
                        └──┬────┬────┬────┬──────┘
                           │    │    │    │
              ┌────────────▼┐ ┌▼────▼┐ ┌─▼──────────┐
              │ Cosmos DB   │ │Redis │ │ Blob Storage│
              │ (state)     │ │(cache)│ │ (audit)    │
              └─────────────┘ └──────┘ └────────────┘
```

## Components

### Web Client (`apps/web`)

- **Runtime**: Next.js 15 on Azure App Service
- **Rendering**: Client components for dynamic pages (incidents, workspaces); static pages for home and preparedness catalog
- **Design system**: Shared `@ama/ui` package with CSS token system and `AppShell` layout
- **Pages**:
  - `/` — Hub entry point
  - `/incidents/[incidentId]` — Incident commander shared operating picture
  - `/workspaces/[personaId]` — Role-specific operational workspace
  - `/preparedness` — Agency operating model analyser and scenario replay
- **Accessibility**: Language switcher (6 languages, RTL support), connectivity banner, multilingual alert preview

### API Service (`apps/api`)

- **Runtime**: FastAPI on Azure Container Apps
- **Authentication**: Entra ID with jurisdiction-scoped RBAC
- **Routes**: `/signals`, `/incidents`, `/recommendations`, `/alerts`, `/personas`, `/tasks`, `/organisations`, `/frameworks`, `/scenarios`
- **Middleware**: Resilience middleware (correlation IDs, circuit breaker, degraded-mode headers)
- **Services**:
  - Signal ingestion (authoritative, IoT, community pipelines)
  - Provenance scoring (trust-weighted multi-source fusion)
  - Dashboard aggregation
  - Recommendation approval workflow
  - Public alert lifecycle (templates, channel adapters, publish validation, supersede)
  - Persona workspace assembly with cross-agency isolation
  - Task orchestration with dependency enforcement
  - Organisation intelligence and preparedness analysis
  - Rehearsal orchestration
  - Degraded-mode evaluation and recommendation guardrails
  - Tenant partitioning (Cosmos, Redis, event channels)

### Agent Runtime (`apps/agents`)

- **Architecture**: Deterministic orchestration with explicit typed handoffs (not prompt-defined routing)
- **Agents**:
  - **Monitoring agent** — Signal summarization and classification
  - **Risk assessment agent** — Recommendation generation with confidence scoring
  - **Communication agent** — Alert drafting with multilingual content
  - **Evacuation agent** — Route pressure analysis and assembly area validation
  - **Resource allocation agent** — Task prioritization by severity
  - **Dependency notifier** — Cross-agency change propagation

### Shared Packages

- `packages/domain` — Pydantic domain models, seed data, bootstrap utilities
- `packages/schemas` — OpenAPI contract and signal envelope JSON schema
- `packages/ui` — Design tokens, AppShell component, shared styles

## Data Architecture

| Store | Purpose | Partitioning |
|-------|---------|--------------|
| Azure Cosmos DB | Incident state, signals, recommendations, tasks, approvals | Tenant scope (agency + jurisdiction) |
| Azure Blob Storage | Immutable audit artifacts, replay payloads, evidence bundles | Incident ID prefix |
| Azure Cache for Redis | Dashboard cache, coordination state, session data | Tenant-scoped namespace |

## Security Model

- **Authentication**: Microsoft Entra ID
- **Authorization**: Jurisdiction-scoped RBAC with role-based route guards
- **Tenant isolation**: Enforced at storage partition, cache namespace, event channel, and API authorization layers
- **Safety guardrails**: OPA policies for approval requirements, content validation, confidence gating, degraded-mode holds
- **Audit**: Append-only timeline events with provenance records

## Observability

- **Monitoring**: Azure Monitor with Log Analytics + Application Insights
- **Alerts**: High error rate (>10 failures/15min), API latency P99 (>5s)
- **Tracing**: Correlation ID propagation via resilience middleware
- **Degraded mode**: Circuit breaker tracking with automatic `X-Degraded-Mode` header

## Deployment

- All resources in Australian Azure regions (Australia East primary)
- Web → Azure App Service
- API + Agents → Azure Container Apps
- Infrastructure as Code via Bicep (`infra/bicep/`)
- CI via GitHub Actions (`.github/workflows/ci.yml`)
