# Implementation Plan: AIDR Additional Guidance Integration

**Branch**: `019-aidr-additional-guidances` | **Date**: 2025-07-19 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/019-aidr-additional-guidances/spec.md`

## Summary

Integrate three additional AIDR guidance documents — Emergency Planning Handbook (2020), Monitoring and Evaluation Framework for Disaster Recovery Programs (v2), and Outcomes, Activities and Indicators for Recovery Programs — into the disaster response platform. This extends spec 018's foundation with: (1) a new **Planning Agent** (`apps/agents/planning/`) implementing the nine-step AIDR emergency planning process with plan lifecycle state machine and AIIMS role-based authorization; (2) extended **Monitoring Agent** M&E capabilities including program logic models, five evaluation question domains, and structured evaluation reporting; (3) a comprehensive **AIDR recovery catalogue** (~61 outcomes, ~200 activities, ~300 indicators across 5 domains) seeded as immutable reference data in Cosmos DB; (4) AI-assisted cross-domain correlation analysis and activity recommendations via Azure OpenAI. Implementation creates 6 new domain models, extends 1 existing model, adds 3 new Cosmos DB containers, creates 1 new Bicep infrastructure module, and introduces the new Planning Agent following the existing `create_app()` factory pattern.

## Technical Context

**Language/Version**: Python 3.10+ (confirmed from `pyproject.toml` and existing agents)  
**Primary Dependencies**: FastAPI (ASGI agents + API), Pydantic (domain models with `Literal[]` unions, no Enums), Azure OpenAI SDK via `LLMClient`/`LLMCallMixin` (AI analysis), azure-servicebus (agent handoffs), azure-cosmos (state store), tenacity (retry logic)  
**Storage**: Azure Cosmos DB (extending existing DB with 3 new containers: `emergency-plans`, `recovery-programmes`, `recovery-catalogue`; existing containers `recovery`, `lessons` from spec 018 retained). Azure Blob Storage for audit blobs and plan document exports.  
**Testing**: pytest with FastAPI `TestClient`; test tiers: unit, contract, integration, simulation  
**Target Platform**: Azure Container Apps (Linux containers), Azure Australia East / Australia Southeast only (Constitution §Non-Negotiable 2)  
**Project Type**: Distributed multi-agent web service (pnpm monorepo)  
**Performance Goals**: Emergency plan generation ≤15s (NFR-001), M&E framework config within 30-min session (NFR-002), recovery indicator dashboard ≤10s (NFR-003), AI cross-domain analysis ≤30s (NFR-004), health endpoints ≤1s  
**Constraints**: ≥20 concurrent active emergency plans (NFR-005), ≥10 concurrent M&E frameworks (NFR-006), all data in Australian Azure regions (NFR-008), k-anonymity ≥10 for social recovery data (NFR-009), content safety validation on all AI outputs (FR-028)  
**Scale/Scope**: 1 new agent (planning), 1 extended agent (monitoring), 6 new domain models, 1 extended model, 3 new Cosmos containers, ~561 catalogue entries seeded, 34 FRs + 9 NFRs + 10 SCs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Constitution Requirement | Spec Coverage | Status |
|---|-------------------------|--------------|--------|
| I | Primacy of Life and Harm Reduction | Emergency planning directly supports risk reduction (FR-001–007); plan activation during incidents surfaces life-safety arrangements (FR-007); AI recommendations pass content safety (FR-028) | ✅ PASS |
| II | National EM Principles (11 principles) | Eight planning principles mapped to AIDR (FR-004); comprehensive PPRR coverage via plan sections (FR-002); collaborative via stakeholder engagement (FR-001 step 3); continual improvement via M&E evaluation loop (FR-008, FR-033) | ✅ PASS |
| II-A | AIIMS Functional Alignment | Planning Agent maps to AIIMS Planning function (spec Assumptions); AIIMS role-based authorization governs plan access (FR-007a); plan activation requires Incident Controller authorization | ✅ PASS |
| III | Multi-Hazard Multi-Agency | Emergency plans support all hazard types (FR-003 risk assessment across 4 environments); plan hierarchy supports multi-agency coordination (FR-005) | ✅ PASS |
| IV | Transparency and Auditability | Plan lifecycle state transitions fully audited (FR-006); M&E evaluation reports with evidence trails (FR-014); planning process records track all 9 steps (Key Entity: Planning Process Record) | ✅ PASS |
| V | Warning and Public Information | Emergency plans include public information and warnings section (FR-002 element 23); plan activation surfaces communication protocols (FR-007) | ✅ PASS |
| VI | Evacuation Framework | Emergency plans include evacuation management section (FR-002 element 24); plan-to-incident linking surfaces evacuation arrangements (FR-007) | ✅ PASS |
| VI-C | Vulnerable Populations | FR-024 mandates disaggregated indicator tracking for vulnerable populations; FR-022 supports community-specific outcome restatements for vulnerable groups | ✅ PASS |
| VII | Recovery Support | Full AIDR M&E Framework implementation (FR-008–014); outcomes-based tracking across all 5 domains (FR-015–024); program logic models connecting activities to outcomes (FR-010) | ✅ PASS |
| VII-A | Six National Recovery Principles | M&E framework aligns with all 6 principles; community-led approaches via FR-022 (community-specific restatements) and FR-032 (stakeholder engagement continuity) | ✅ PASS |
| VII-B | Four Recovery Environments | Full AIDR catalogue covers Social (FR-016), Economic (FR-017), Built (FR-018), Natural (FR-019), plus Overarching domain (FR-009, FR-015) | ✅ PASS |
| VII-C | Recovery Transition | Emergency plans include recovery arrangements section (FR-002 element 26); plan activation to recovery linkage (FR-029); M&E overlaps with response phase | ✅ PASS |
| VIII | Cloud Platform (Azure only) | All new Cosmos containers in Australian regions (NFR-008); Azure OpenAI for AI analysis (FR-025–027); Bicep IaC for infrastructure (infra module) | ✅ PASS |
| NN-1 | Human-in-the-loop | Plan endorsement requires human designated authority (FR-006, FR-007a); plan activation requires IC approval; AI recommendations are advisory only (FR-026) | ✅ PASS |
| NN-2 | Data sovereignty (Australia) | NFR-008 mandates Australia East / Southeast only for all new data | ✅ PASS |
| NN-3 | Privacy by design | NFR-009 extends spec 018 k-anonymity ≥10 to new M&E indicator data; social data classification enforced | ✅ PASS |
| NN-4 | Interoperability (CAP, EDXL, GeoJSON, OpenAPI) | New Planning Agent and M&E endpoints expose OpenAPI schemas; emergency plans export as structured JSON (spec Assumptions); CSV import for indicator bulk entry | ✅ PASS |
| NN-5 | Graceful degradation | Emergency plan retrieval falls back to last-endorsed version (edge case: activation during revision); M&E reporting proceeds with available data (edge case: indicator data unavailable); staleness indicators on delayed data | ✅ PASS |
| QG | Quality Gates (PR tests, IaC review, human review) | FR-033 feeds M&E lessons into lessons management; existing CI/CD pipeline applies to all new code | ✅ PASS |

**Gate Result**: ✅ PASS — All Constitution requirements are covered by the spec. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/019-aidr-additional-guidances/
├── plan.md                  # This file
├── research.md              # Phase 0 output — research decisions
├── data-model.md            # Phase 1 output — domain model specifications
├── quickstart.md            # Phase 1 output — developer quickstart
├── contracts/               # Phase 1 output — API contracts
│   ├── planning-api.yaml          # Emergency planning agent endpoints
│   ├── me-framework-api.yaml      # M&E framework endpoints (monitoring agent extension)
│   ├── recovery-catalogue-api.yaml # AIDR outcomes/activities/indicators catalogue
│   └── ai-analysis-api.yaml       # AI-assisted cross-domain analysis
├── checklists/
│   ├── deep-review.md             # Deep requirements quality checklist (70 items)
│   └── requirements.md            # Requirements summary
└── tasks.md                 # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
packages/domain/src/domain/models/
├── recovery_environment_tracker.py  # EXTEND: +catalogue_indicator_id on RecoveryIndicator
├── emergency_plan.py                # NEW: EmergencyPlan with 7-state lifecycle, 27 plan sections
├── planning_process_record.py       # NEW: 9-step AIDR planning process tracker
├── me_framework.py                  # NEW: M&E Framework config with program logic, evaluation domains
├── program_logic_model.py           # NEW: structured resource→activity→output→outcome chains
├── recovery_outcome.py              # NEW: catalogue models (RecoveryOutcome, CatalogueActivity, CatalogueIndicator)
└── evaluation_report.py             # NEW: structured evaluation report across 5 KEQ domains

packages/domain/src/domain/seed/
└── recovery-catalogue/              # NEW: AIDR catalogue seed data (JSON)
    ├── overarching.json             # ~7 outcomes + activities + indicators
    ├── social.json                  # ~24 outcomes + activities + indicators
    ├── economic.json                # ~19 outcomes + activities + indicators
    ├── built.json                   # ~5 outcomes + activities + indicators
    ├── natural.json                 # ~6 outcomes + activities + indicators
    └── evaluation-questions.json    # Standard KEQ questions per domain

apps/agents/
├── planning/                        # NEW: Planning Agent (AIIMS Planning function)
│   ├── __init__.py
│   ├── __main__.py                  # Entrypoint: uvicorn runner
│   ├── agent.py                     # PlanningAgent class + create_app() factory
│   ├── config.py                    # PlanningConfig (frozen dataclass, env vars)
│   ├── models.py                    # Request/response models for planning endpoints
│   ├── pipeline.py                  # Emergency plan assembly pipeline
│   ├── plan_lifecycle.py            # State machine: Draft→...→Superseded transitions
│   ├── risk_assessment.py           # Multi-environment risk analysis (4 environments)
│   ├── audit.py                     # Planning decision audit records
│   └── telemetry.py                 # Planning-specific metrics
├── monitoring/
│   ├── agent.py                     # EXTEND: +M&E framework endpoints, +catalogue lookup
│   ├── config.py                    # EXTEND: +M&E config parameters
│   ├── models.py                    # EXTEND: +M&E request/response models
│   ├── me_framework_service.py      # NEW: M&E framework lifecycle management
│   ├── indicator_analysis.py        # NEW: AI-assisted cross-domain correlation analysis
│   ├── evaluation_service.py        # NEW: evaluation report generation
│   └── catalogue_service.py         # NEW: AIDR catalogue lookup and indicator suggestion
├── common/
│   ├── handoffs.py                  # EXTEND: +planning and M&E handoff builders
│   └── plan_activation.py           # NEW: plan activation logic (plan↔incident linking)

apps/api/
├── app/api/routes/
│   ├── emergency_plans.py           # NEW: emergency plan CRUD, lifecycle, hierarchy
│   ├── me_frameworks.py             # NEW: M&E framework configuration, program logic
│   ├── recovery_catalogue.py        # NEW: AIDR catalogue browsing, outcome selection
│   └── ai_analysis.py              # NEW: AI-assisted analysis and recommendation endpoints
├── app/services/
│   ├── emergency_plan_service.py    # NEW: plan lifecycle business logic
│   ├── me_framework_service.py      # NEW: M&E framework business logic
│   ├── recovery_catalogue_service.py # NEW: catalogue query and seed management
│   └── ai_analysis_service.py       # NEW: cross-domain correlation + recommendation logic
├── app/repositories/
│   ├── emergency_plan_repository.py # NEW: Cosmos DB access for emergency-plans container
│   ├── me_framework_repository.py   # NEW: Cosmos DB access for recovery-programmes container
│   └── recovery_catalogue_repository.py # NEW: Cosmos DB access for recovery-catalogue container

infra/
├── main.bicep                       # EXTEND: +emergency-planning module reference
└── modules/
    └── emergency-planning.bicep     # NEW: 3 Cosmos containers (emergency-plans, recovery-programmes, recovery-catalogue)

scripts/
└── seed_loader.py                   # EXTEND: +recovery-catalogue seeding from domain/seed/

tests/
├── unit/
│   ├── test_emergency_plan.py               # NEW: plan model + lifecycle state machine
│   ├── test_planning_process_record.py      # NEW: 9-step process tracking
│   ├── test_me_framework.py                 # NEW: M&E framework model + program logic
│   ├── test_recovery_outcome.py             # NEW: catalogue models + hierarchical IDs
│   ├── test_evaluation_report.py            # NEW: evaluation report generation
│   ├── test_plan_lifecycle.py               # NEW: state transition validation
│   ├── test_indicator_analysis.py           # NEW: cross-domain correlation logic
│   └── test_catalogue_service.py            # NEW: catalogue lookup and suggestions
├── contract/
│   ├── test_planning_api_contract.py        # NEW: planning agent endpoint contracts
│   ├── test_me_framework_api_contract.py    # NEW: M&E framework endpoint contracts
│   └── test_recovery_catalogue_contract.py  # NEW: catalogue browsing endpoint contracts
├── integration/
│   ├── test_emergency_plans_cosmos.py       # NEW: plan persistence + lifecycle in Cosmos
│   ├── test_me_framework_cosmos.py          # NEW: M&E framework persistence
│   └── test_recovery_catalogue_cosmos.py    # NEW: catalogue seeding + queries
└── simulation/
    └── test_planning_me_scenarios.py        # NEW: end-to-end planning + M&E workflow tests
```

**Structure Decision**: Follows the existing pnpm monorepo structure. The new Planning Agent is created under `apps/agents/planning/` using the established `create_app()` factory pattern identical to `monitoring/`, `communication/`, `evacuation/`, and `risk_assessment/`. M&E capabilities extend the existing Monitoring Agent rather than creating a separate agent (per spec Assumptions). Domain models go in `packages/domain/src/domain/models/`, catalogue seed data in `packages/domain/src/domain/seed/recovery-catalogue/`, infrastructure in `infra/modules/`. Platform API routes for plan management and catalogue browsing are added to `apps/api/` following the existing repository pattern used by `GovernanceRepository`, `SimulationRepository`, and `SignalRepository`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `RecoveryDomain` 5-value type alongside existing `RecoveryEnvironment` 4-value type | AIDR M&E Framework introduces "Overarching (Resilience & Sustainability)" as a fifth cross-cutting domain that doesn't map to any single environment. Catalogue entities need all 5 values. | Extending `RecoveryEnvironment` to 5 values rejected because it would break backward compatibility with spec 018's `RecoveryEnvironmentTracker` which is semantically bound to the 4 concrete environments. Overarching indicators roll up into concrete domain trackers. |
| Separate `recovery-catalogue` Cosmos container for immutable reference data | AIDR catalogue (~561 entries) is immutable reference data seeded at deployment, fundamentally different from mutable operational data in `recovery` container. Partition by `domain` enables efficient per-domain catalogue browsing. | Storing catalogue entries in the existing `recovery` container rejected because mixing immutable reference data with mutable tracker data complicates partition key design, indexing, and TTL policies. The `seed` container was considered but rejected because catalogue data is queried at runtime (not just at startup). |
| EmergencyPlan 7-state lifecycle state machine | AIDR Emergency Planning Handbook defines a formal 9-step process that maps to 7 lifecycle states with specific authorization requirements at each transition. Simpler Draft→Endorsed→Active would not capture the consultation, review, post-event review, and supersession semantics required by AIDR compliance. | 3-state lifecycle (Draft→Active→Archived) rejected because it cannot enforce AIDR's required separation of consultation, formal review/endorsement, incident activation, and post-event review — each requiring different AIIMS role authorization. |
