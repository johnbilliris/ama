# Implementation Plan: Data Source Identification, Constitutional Review, and Governance Assignment

**Branch**: `005-data-source-governance` | **Date**: 2026-03-24 | **Spec**: `c:\code\ama\specs\005-data-source-governance\spec.md`
**Input**: Feature specification from `/specs/005-data-source-governance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a comprehensive data source governance layer that catalogues every external and internal data source feeding the disaster response hub, structures constitutional compliance assessments against each principle, assigns agent responsibilities with validated handoff chains, and provides a consolidated governance dashboard. The feature delivers a machine-loadable seed catalogue of named Australian data sources, a governance registry with ≤50ms p95 handoff-chain lookups, agent-side caching with configurable TTL, grace-period compliance lapsing, functional-domain precedence with jurisdictional inheritance, and an immutable audit trail. The governance registry exposes structured handoff definitions that agents can query at runtime, while agent-side refactoring to consume those definitions is deferred to a downstream spec.

## Technical Context

**Language/Version**: Python 3.12 for API, domain models, and governance services; TypeScript 5.6 for governance dashboard UI  
**Primary Dependencies**: FastAPI, Pydantic v2, Azure Cosmos DB SDK, Azure Cache for Redis SDK; Next.js 15, React 19, Tailwind CSS, Playwright  
**Storage**: Azure Cosmos DB for governance registry entries, constitutional assessments, agent assignments, handoff chains, and audit trail; Azure Cache for Redis for low-latency handoff-chain lookups and agent-side governance cache  
**Testing**: pytest (contract, integration), Playwright e2e, governance-specific contract tests for handoff validation and constitutional assessment workflows  
**Target Platform**: Azure Container Apps (API + governance service); Azure App Service (web dashboard); modern browsers  
**Project Type**: Multi-service extension to existing web application with governance registry backend  
**Performance Goals**: Handoff-chain lookup ≤50ms p95 (NFR-001); governance cache TTL 5 minutes default (NFR-002); dashboard load <2s  
**Constraints**: Australian Azure regions only; human-led constitutional assessments (no automated scoring); role-based access for governance mutations; grace period before auto-blocking lapsed sources (default 72h); agent refactoring deferred  
**Scale/Scope**: 50–100 data sources in seed catalogue; 6 constitutional principles per source; 5 recognised agents for assignments; jurisdictional precedence for 8 states/territories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate Review

- **Life Safety First**: PASS. The governance registry enforces that non-compliant data sources cannot feed safety-critical decisions (FR-006). Grace-period blocking (FR-012b) prevents abrupt removal during active incidents while ensuring lapsed sources are remediated. All governance actions are audited (FR-013).
- **Multi-Agent Coordination With Clear Roles**: PASS. Agent governance assignments (FR-007) and handoff chain definitions (FR-008) make routing explicit and auditable. Validated against agent catalogue (FR-009c). Shared-responsibility sources are recorded with precedence rules (FR-010, FR-010a).
- **Data Trust, Provenance, and Freshness**: PASS. Each data source is catalogued with trust tier, provenance metadata, and update frequency (FR-002, FR-002a). Constitutional assessments enforce provenance standards (FR-004a). Contradictory signal precedence resolved via functional-domain authority (FR-010a).
- **Privacy, Security, and Regional Policy Compliance**: PASS. Constitutional assessments evaluate privacy compliance per source (FR-004a Principle IV). Governance registry is role-protected (FR-015) and treated as a sensitive asset (FR-016). Australian data residency maintained.
- **Multilingual, Accessible, and Actionable Communication**: PASS. Constitutional assessments evaluate multilingual requirements for sources feeding public alerts (FR-004a Principle V). No new alert generation in this feature.
- **Cloud Platform**: PASS. All storage and services target Azure in Australian regions. Registry uses Cosmos DB and Redis consistent with existing infrastructure.
- **Quality Gates and Operational Readiness**: PASS. Observability signals (NFR-005) integrate with existing monitoring. Governance dashboard (FR-011) surfaces gaps and lapsed sources. Audit trail (FR-013) provides full traceability.

### Post-Design Gate Review

- **Life Safety First**: PASS. The data model enforces that non-compliant data sources cannot receive agent assignments (AgentGovernanceAssignment validation rule). Grace-period lifecycle (DataSourceRegistryEntry compliance_status state transitions) prevents abrupt removal of safety-critical feeds while ensuring governance remediation. GovernanceAuditEntry provides an immutable audit trail for all governance actions affecting data source availability.
- **Multi-Agent Coordination With Clear Roles**: PASS. HandoffChainDefinition validates chain continuity (step N target = step N+1 source), validates agent names against the spec 004 catalogue, and records confidence thresholds and category filters. AgentGovernanceAssignment distinguishes primary and secondary roles with explicit scope of responsibility. FunctionalDomainPrecedence resolves contradictory signals using jurisdictional inheritance rather than ambiguous tie-breaking.
- **Data Trust, Provenance, and Freshness**: PASS. DataSourceRegistryEntry extends the existing DataSource with 7-level trust tiers mapped to authority_rank, two-level categorisation (kind + sub_category), and provenance fields (provider, collection_method). ConstitutionalAssessment includes principle-specific evaluation of data trust (provenance metadata, freshness detection, contradiction identification). The seed catalogue provides a structured denominator for SC-001 catalogue completeness measurement.
- **Privacy, Security, and Regional Policy Compliance**: PASS. ConstitutionalAssessment evaluates each source against Privacy, Security & Regional Policy (Principle IV), recording PII concerns, data-sharing agreements, and jurisdictional data residency. The governance API contract enforces role-based access (bearerAuth, 403 responses on governance mutations). FR-016 treats the registry as a sensitive asset with access controls and audit logging.
- **Multilingual, Accessible, and Actionable Communication**: PASS. ConstitutionalAssessment evaluates sources feeding public alerts against the multilingual principle (Principle V). No new alert generation is introduced by this feature; governance ensures upstream source quality for the existing communication workflows.
- **Cloud Platform**: PASS. All storage uses Azure Cosmos DB and Azure Cache for Redis in Australian regions, consistent with the existing infrastructure. The OpenAPI contract defines no non-Azure dependencies.
- **Quality Gates and Operational Readiness**: PASS. The quickstart defines phased test-first validation (Phases A–H) covering every functional requirement and NFR. Observability signals (NFR-005) for query latency, cache hit/miss, governance gaps, grace-period warnings, and audit failures integrate with existing monitoring. SC-001 through SC-006 provide measurable acceptance criteria.

## Project Structure

### Documentation (this feature)

```text
specs/005-data-source-governance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi-governance.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/
├── api/
│   └── app/
│       ├── api/
│       │   ├── data_sources.py            # NEW — data source registry CRUD routes (FR-001–003)
│       │   └── governance.py              # NEW — compliance, assignment, dashboard routes (FR-004–014)
│       ├── services/
│       │   ├── governance_registry.py     # NEW — governance registry service (FR-001–014, NFR-001–005)
│       │   └── governance_cache.py        # NEW — Redis-backed governance cache (NFR-001, NFR-002)
│       ├── repositories/
│       │   └── governance_repository.py   # NEW — Cosmos DB governance data access (FR-001–014)
│       └── validators/
│           └── governance_validators.py   # NEW — handoff chain + agent catalogue validation (FR-009, FR-009c)
├── agents/                                 # NO CHANGES — agent refactoring deferred per FR-009b
└── web/
    └── src/
        ├── app/
        │   └── governance/
        │       ├── page.tsx               # NEW — governance dashboard (FR-011, US-4)
        │       └── [dataSourceId]/
        │           ├── compliance/
        │           │   └── page.tsx       # NEW — constitutional compliance view (FR-004, US-2)
        │           └── assignments/
        │               └── page.tsx       # NEW — agent assignment view (FR-007–009, US-3)
        └── components/
            └── governance/
                ├── DataSourceTable.tsx     # NEW — filterable data source catalogue (US-1)
                ├── ComplianceCard.tsx      # NEW — per-principle assessment card (US-2)
                ├── HandoffChainEditor.tsx  # NEW — handoff chain definition UI (US-3)
                └── GovernanceSummary.tsx   # NEW — dashboard summary counters (US-4)

packages/
├── domain/
│   └── src/domain/
│       ├── models/
│       │   ├── data_source.py             # MODIFY — extend with sub_category, trust_tier, governance fields
│       │   ├── constitutional_assessment.py # NEW — ConstitutionalAssessment entity (FR-004–006)
│       │   ├── agent_governance.py        # NEW — AgentGovernanceAssignment entity (FR-007–010)
│       │   ├── handoff_chain.py           # NEW — HandoffChainDefinition entity (FR-008–009)
│       │   ├── functional_domain_precedence.py # NEW — FunctionalDomainPrecedence entity (FR-010a)
│       │   └── governance_audit.py        # NEW — GovernanceAuditEntry entity (FR-013)
│       └── seed/
│           ├── data_sources_australia.json # NEW — seed catalogue (FR-001a)
│           └── bootstrap.py               # MODIFY — add data_sources key to bootstrap_seed_data()
└── schemas/                                # EXISTING

tests/
├── contract/
│   ├── test_data_source_registry.py       # NEW — registry CRUD contract tests (FR-001–003)
│   ├── test_constitutional_compliance.py  # NEW — assessment workflow tests (FR-004–006)
│   ├── test_governance_assignment.py      # NEW — agent assignment + handoff validation (FR-007–010)
│   └── test_governance_dashboard.py       # NEW — dashboard aggregation tests (FR-011, FR-014)
├── integration/
│   ├── test_governance_grace_period.py    # NEW — grace-period blocking workflow (FR-012b)
│   ├── test_governance_rereview.py        # NEW — re-review workflow (FR-012, FR-012a)
│   └── test_governance_cache.py           # NEW — cache TTL and fallback behavior (NFR-001–003)
└── e2e/
    └── test_governance_dashboard.spec.ts  # NEW — governance dashboard Playwright tests (US-4)
```

**Structure Decision**: Extend the existing monorepo. New governance routes and services slot into the existing API application structure. Domain models follow the established pattern in `packages/domain/src/domain/models/`. The seed catalogue follows the existing JSON seed data pattern in `packages/domain/src/domain/seed/`. Governance dashboard pages are added to the Next.js app under a `/governance` route group. No new top-level projects are introduced.

## Complexity Tracking

No constitution violations or justified exceptions were identified during planning.
