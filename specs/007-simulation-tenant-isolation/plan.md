# Implementation Plan: Simulation-as-Tenant — Tenant-Partitioned Simulation Mode

**Branch**: `007-simulation-tenant-isolation` | **Date**: 2026-04-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-simulation-tenant-isolation/spec.md`

## Summary

Enable the disaster response hub to run simulation exercises alongside live operations by modelling each simulation as an independent logical tenant. The system extends the existing `TenantContext` and `cosmos_scope` patterns to include a simulation tenant identifier (`sim-{scenarioRunId}`) that partitions Cosmos DB, Redis, Blob Storage, and audit trails. The live tenant (`live`) is always the default. Tenant context is server-derived from Entra ID token claims with internal participant lists in Cosmos DB. Simulation tenants share compute infrastructure but are structurally isolated at the storage layer.

## Technical Context

**Language/Version**: Python 3.12 (API + Agents + Ingestion), TypeScript 5.6 (Next.js 15 Web)
**Primary Dependencies**: FastAPI, azure-cosmos, azure-identity, redis, azure-storage-blob, Next.js 15, @ama/ui
**Storage**: Cosmos DB (disaster-hub database — signals, simulation, seed, governance containers), Redis (distributed cache/dedup), Azure Blob Storage (raw-payloads, audit, simulation containers)
**Testing**: pytest (unit + integration + contract), Playwright (E2E)
**Target Platform**: Azure Container Apps (API, Agents, Ingestion, Web)
**Project Type**: Multi-service web platform (4 services: API, Agents, Ingestion, Web)
**Performance Goals**: 50,000 signals/hour live throughput; simulation tenant provisioning <30s; live latency impact <10% with 3 concurrent simulations
**Constraints**: Azure AU regions only; Entra ID for authn; all simulation data structurally isolated from live; simulated alerts must never reach real channels
**Scale/Scope**: 3 concurrent simulation tenants (default), 10,000 synthetic signals per exercise, 20+ live ingestion pipelines uninterrupted

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Life Safety First | PASS | FR-019 blocks simulated alerts from real channels. FR-028 auto-throttles simulations during live incidents. FR-003 enforces storage-layer isolation preventing cross-tenant data leakage. |
| II | Multi-Agent Coordination | PASS | FR-016 processes simulation signals through the identical agent chain. FR-017 scopes all agent-generated artefacts to the simulation tenant. Handoff patterns preserved. |
| III | Data Trust & Provenance | PASS | FR-015 generates synthetic signals with full provenance metadata. SimulationSignal carries `source_context: "simulation"`. FR-004 routes real-world data exclusively to live tenant. |
| IV | Privacy & Security | PASS | FR-002 derives tenant context server-side from Entra ID claims (never client-supplied). FR-006 uses internal participant lists in Cosmos DB. NFR-003 mandates fail-safe (error, not redirect to live). |
| V | Multilingual & Accessible | PASS | FR-020/021 simulation dashboard functionally identical to live. FR-021 adds persistent SIMULATION banner (cannot be dismissed). No new language/accessibility regressions. |
| VI | Azure AU Platform | PASS | All infrastructure remains on existing Azure AU resources (Cosmos DB, Redis, Blob Storage, Container Apps). No new regions or services introduced. |
| NFR | Multi-tenancy boundaries | PASS | Constitution explicitly requires "multi-tenancy boundaries where required for different agencies/regions (data and policy isolation)" — this feature implements that requirement for simulation. |
| NFR | Scenario-based testing | PASS | Constitution requires "scenario-based testing for at least: bushfire, cyclone, flood" — FR-012 delivers exactly this. |
| NFR | Drills/tabletop exercises | PASS | Constitution states "the system SHOULD support drills/tabletop exercises with stored scenarios and replayable decision logs" — this is the core deliverable. |

**Pre-design gate: PASS** — No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/007-simulation-tenant-isolation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── simulation-api.md
│   └── tenant-middleware.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
packages/domain/src/domain/models/
├── signal.py                    # Existing — no changes needed (partition-scoped already)
├── scenario_run.py              # EXTEND — add tenant_id, exercise_report_uri, archive_status
├── simulation_tenant.py         # NEW — SimulationTenant entity
├── scenario_template.py         # NEW — ScenarioTemplate entity
└── exercise_report.py           # NEW — ExerciseReport entity

apps/api/app/
├── core/
│   ├── tenant_context.py        # EXTEND — add simulation tenant ID field, tenant_type property
│   ├── auth.py                  # EXTEND — extract simulation tenant claim from Entra ID token
│   └── settings.py              # EXTEND — add simulation config (max tenants, TTL, throttle threshold)
├── middleware/
│   └── tenant_middleware.py     # NEW — global middleware enforcing tenant context on all requests
├── api/
│   ├── dependencies/
│   │   └── rbac.py              # EXTEND — check participant list for simulation tenant access
│   └── routes/
│       └── simulations.py       # NEW — CRUD for simulation tenants, lifecycle, seeding, reports
├── repositories/
│   ├── cosmos_scope.py          # EXTEND — add simulation partition key builders
│   ├── simulation_repository.py # NEW — Cosmos DB operations for SimulationTenant, templates
│   └── signal_repository.py     # NEW — tenant-scoped signal read/write (replaces in-memory)
├── services/
│   ├── simulation_service.py    # NEW — tenant lifecycle, provisioning, archival, throttling
│   ├── scenario_seeding_service.py  # NEW — template loading, historical replay, signal injection
│   ├── exercise_report_service.py   # NEW — report generation, benchmark comparison
│   └── resource_governor.py     # NEW — throughput monitoring, auto-throttle logic
└── validators/
    └── simulation_validators.py # NEW — concurrency limits, resource budget validation

apps/web/src/
├── app/
│   └── simulations/             # NEW — simulation management pages
│       ├── page.tsx             # Simulation list/management
│       ├── [tenantId]/
│       │   └── page.tsx         # Simulation dashboard (same layout as live, with SIMULATION banner)
│       └── reports/
│           └── [reportId]/page.tsx  # Exercise report view
├── components/
│   └── simulation-banner.tsx    # NEW — persistent SIMULATION identification banner
└── lib/api/
    └── simulations.ts           # NEW — API client for simulation endpoints

apps/agents/
└── common/
    └── handoffs.py              # EXTEND — include tenant_id in AgentHandoffEvent payload

apps/ingestion/
└── (no changes)                 # Ingestion always writes to live tenant — no simulation routing

infra/
├── main.bicep                   # EXTEND — add simulation Cosmos DB container if not present
└── modules/
    └── monitoring.bicep         # EXTEND — add tenant_id custom dimension to App Insights

tests/
├── unit/
│   ├── test_tenant_context.py           # NEW
│   ├── test_simulation_service.py       # NEW
│   ├── test_resource_governor.py        # NEW
│   └── test_scenario_seeding.py         # NEW
├── integration/
│   ├── test_tenant_isolation.py         # NEW — cross-tenant leakage tests
│   └── test_simulation_lifecycle.py     # NEW
└── contract/
    └── test_simulation_api_contract.py  # NEW
```

**Structure Decision**: Extends the existing monorepo structure (apps/api, apps/agents, apps/web, apps/ingestion, packages/domain). New domain models in the shared domain package. New routes, services, and repositories in the API app. New pages in the web app. Ingestion app is unchanged — it always targets the live tenant. No new top-level projects.

## Complexity Tracking

No constitution violations. No additional complexity justification needed.
