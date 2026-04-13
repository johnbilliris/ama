# Implementation Plan: AIDR Guidance Integration

**Branch**: `018-aidr-guidance-integration` | **Date**: 2025-07-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/018-aidr-guidance-integration/spec.md`

## Summary

Integrate AIDR (Australian Institute for Disaster Resilience) guidance into the Autonomous Disaster Response Agent Coordination Hub. This covers seven capability domains: Australian Warning System three-tier alerts (FR-001–007), Total Warning System cross-agent integration (FR-008–012), AIIMS functional alignment (FR-013–017), five-stage evacuation framework (FR-018–025), PPRR lifecycle (FR-026–031), community recovery (FR-032–037), and lessons management (FR-038–042). Implementation extends existing domain models (`PublicAlert`, `Incident`, `HandoffChainDefinition`), creates four new domain models (`AiimsRoleAssignment`, `EvacuationStage`, `RecoveryEnvironmentTracker`, `Lesson`), augments all five existing agents with AIDR behaviours, and adds four new platform services (AIIMS role management, PPRR lifecycle, recovery tracking, lessons management). All changes follow the existing create_app() factory pattern, Pydantic domain models, and FastAPI router conventions.

## Technical Context

**Language/Version**: Python 3.10+ (confirmed from existing agents and `pyproject.toml`)  
**Primary Dependencies**: FastAPI (ASGI agents + API), Pydantic (domain models), Azure OpenAI SDK (LLM), azure-servicebus (agent messaging), azure-cosmos (state store)  
**Storage**: Azure Cosmos DB (5 existing containers: `signals`, `disaster-hub`, `simulation`, `seed`, `governance`; new containers needed: `recovery`, `lessons`, `aiims-assignments`, `evacuation-stages`, `pprr-contexts`), Azure Blob Storage (audit blobs)  
**Testing**: pytest with FastAPI TestClient; test tiers: unit, contract, integration, simulation, benchmark  
**Target Platform**: Azure Container Apps (Linux containers), Azure Australia East / Australia Southeast only (Constitution §Non-Negotiable 2)  
**Project Type**: Distributed multi-agent web service (pnpm monorepo)  
**Performance Goals**: Warning compliance validation ≤5s, AIIMS role assignment ≤5s, PPRR phase transition ≤5s, recovery dashboard load ≤10s, lessons capture ≤5s, trend analysis ≤30s, health endpoints ≤1s  
**Constraints**: ≥10 concurrent recovery operations, ≥50 concurrent lessons, all data in Australian Azure regions, k-anonymity ≥10 for social recovery data (NFR-014)  
**Scale/Scope**: 5 existing agents augmented, 4 new platform services, 4 new domain models, 1 new context model, 3 extended domain models, 21 recovery indicators, 54 FRs + 15 NFRs + 10 SCs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Constitution Requirement | Spec Coverage | Status |
|---|-------------------------|--------------|--------|
| I | Primacy of Life and Harm Reduction | FR-001–007 (AWS warnings), FR-018–025 (evacuation), tiered escalation timeouts (5 min Emergency Warning) | ✅ PASS |
| II | National EM Principles (11 principles) | FR-026–031 (PPRR = Comprehensive), FR-013–017 (AIIMS = Coordinated), FR-038–042 (Lessons = Continual Improvement) | ✅ PASS |
| II-A | AIIMS Functional Alignment | FR-013–017 (role mapping, COP, incident levels, Command/Control/Coordination) | ✅ PASS |
| III | Multi-Hazard Multi-Agency | FR-051 extends incident_type to all Constitution §III hazards | ✅ PASS |
| IV | Transparency and Auditability | FR-053 (phase transition TimelineEvents), FR-019 (evacuation decision records), edge case audit requirements | ✅ PASS |
| V-A | Australian Warning System | FR-001–005 (three tiers, nested model, de-escalation, all-clear) | ✅ PASS |
| V-B | Ten Warning Principles | FR-006 (all 10 principles), SC-006 (100% compliance) | ✅ PASS |
| V-C | Total Warning System | FR-008–012 (all 6 elements) | ✅ PASS |
| VI | Evacuation Framework (five stages) | FR-018–025 (Decision, Warning, Withdrawal, Shelter, Return + shelter-in-place) | ✅ PASS |
| VI-C | Vulnerable Populations | FR-007, FR-021 (extended list per AIDR Handbook + Constitution) | ✅ PASS |
| VII | Recovery Support | FR-032–037 (four environments, six principles, community-led, longitudinal tracking) | ✅ PASS |
| VII-A | Six National Recovery Principles | FR-033 (alignment required for all recommendations) | ✅ PASS |
| VII-B | Four Recovery Environments | FR-032, SC-005 (21 indicators across Social/Built/Economic/Natural) | ✅ PASS |
| VII-C | Recovery Transition | FR-035 (parallel activation), FR-031 (managed transitions) | ✅ PASS |
| VIII | Cloud Platform (Azure only) | NFR-015 (Australian regions only), all infra via Bicep | ✅ PASS |
| NN-1 | Human-in-the-loop | Warning approval with IC delegation chain, evacuation decision authority capture, no auto-approved warnings | ✅ PASS |
| NN-2 | Data sovereignty (Australia) | NFR-015 (Australia East / Southeast only) | ✅ PASS |
| NN-3 | Privacy by design | NFR-014 (k-anonymity ≥10 for social recovery data) | ✅ PASS |
| NN-4 | Interoperability (CAP, EDXL, GeoJSON, OpenAPI) | Existing API uses OpenAPI; AWS warnings compatible with CAP alert structure; GeoJSON for location data | ⚠️ NOTE — Verify new endpoints expose OpenAPI schemas |
| NN-5 | Graceful degradation | NFR-011 (lessons buffering), NFR-012 (recovery staleness indicator) | ⚠️ NOTE — CHK069 identified gap: no explicit degradation for AWS warning generation or AIIMS role assignment |
| QG | Quality Gates (PR tests, IaC review, human review) | FR-042 (lessons-linked PR verification), existing CI/CD pipeline | ✅ PASS |

**Gate Result**: ✅ PASS with 2 notes to address in research phase (NN-4 interoperability for new endpoints, NN-5 graceful degradation gap for warnings/AIIMS).

## Project Structure

### Documentation (this feature)

```text
specs/018-aidr-guidance-integration/
├── plan.md              # This file
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — domain model specifications
├── quickstart.md        # Phase 1 output — developer quickstart
├── contracts/           # Phase 1 output — API contracts
│   ├── warning-api.yaml       # AWS warning endpoints
│   ├── aiims-api.yaml         # AIIMS role management endpoints
│   ├── evacuation-api.yaml    # Five-stage evacuation endpoints
│   ├── pprr-api.yaml          # PPRR lifecycle endpoints
│   ├── recovery-api.yaml      # Recovery tracking endpoints
│   └── lessons-api.yaml       # Lessons management endpoints
├── checklists/
│   ├── aidr-guidance.md       # Requirements quality checklist (98 items)
│   └── requirements.md        # Requirements summary
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
packages/domain/src/domain/models/
├── incident.py                    # EXTEND: +pprr_phase, +incident_level, +incident_type values
├── public_alert.py                # EXTEND: +warning_tier, +colour_code, +hazard_icon, +action_statement, +superseded_warning_id
├── timeline_event.py              # EXTEND: +pprr_transition payload schema
├── handoff_chain.py               # EXTEND: +recovery/lessons signal categories
├── aiims_role_assignment.py       # NEW: agent-to-AIIMS-function mapping per incident
├── evacuation_stage.py            # NEW: five-stage evacuation lifecycle tracking
├── recovery_environment_tracker.py # NEW: 21 indicators across 4 recovery environments
├── lesson.py                      # NEW: lessons management with AIIMS/PPRR categorisation
└── pprr_phase_context.py          # NEW: PPRR phase for non-incident contexts (region/scenario)

apps/agents/
├── common/
│   ├── handoffs.py                # EXTEND: +recovery and lessons handoff builders
│   ├── aiims_mapping.py           # NEW: AIIMS role constants and validation
│   ├── pprr_lifecycle.py          # NEW: PPRR phase transition logic
│   └── warning_compliance.py      # NEW: AWS three-tier validation and 10-principle checker
├── monitoring/
│   └── agent.py                   # EXTEND: +situational awareness output for Total Warning System
├── risk_assessment/
│   └── agent.py                   # EXTEND: +monitoring-and-prediction output for Total Warning System
├── evacuation/
│   ├── agent.py                   # EXTEND: +five-stage lifecycle management
│   ├── models.py                  # EXTEND: +EvacuationStage integration
│   └── stages.py                  # NEW: stage-specific logic (Decision→Warning→Withdrawal→Shelter→Return)
├── resource_allocation/
│   └── agent.py                   # EXTEND: +recovery-phase resource allocation mode
├── communication/
│   ├── agent.py                   # EXTEND: +AWS three-tier warning generation
│   ├── models.py                  # EXTEND: +AWS warning fields
│   └── warning_builder.py         # NEW: AWS nested model builder + hazard icons

apps/api/
├── app/api/routes/
│   ├── recovery.py                # NEW: recovery dashboard and indicator endpoints
│   ├── lessons.py                 # NEW: lessons CRUD, trend analysis, register
│   ├── pprr.py                    # NEW: PPRR phase management endpoints
│   └── aiims.py                   # NEW: AIIMS role assignment and COP endpoints
├── app/services/
│   ├── recovery_service.py        # NEW: recovery tracking business logic
│   ├── lessons_service.py         # NEW: lessons management business logic
│   ├── pprr_service.py            # NEW: PPRR phase transition logic
│   └── aiims_service.py           # NEW: AIIMS role assignment logic

infra/
├── main.bicep                     # EXTEND: +recovery and lessons Cosmos containers
└── modules/
    └── recovery-lessons.bicep     # NEW: Cosmos containers, any additional resources

tests/
├── unit/
│   ├── test_warning_compliance.py         # NEW
│   ├── test_aiims_role_assignment.py      # NEW
│   ├── test_evacuation_stages.py          # NEW
│   ├── test_pprr_lifecycle.py             # NEW
│   ├── test_recovery_tracker.py           # NEW
│   ├── test_lessons_management.py         # NEW
│   └── test_domain_models_aidr.py         # NEW
├── contract/
│   ├── test_warning_api_contract.py       # NEW
│   ├── test_recovery_api_contract.py      # NEW
│   └── test_lessons_api_contract.py       # NEW
├── integration/
│   ├── test_recovery_cosmos.py            # NEW
│   └── test_lessons_cosmos.py             # NEW
└── simulation/
    └── test_aidr_scenarios.py             # NEW: end-to-end AIDR scenario tests
```

**Structure Decision**: Follows the existing pnpm monorepo structure. Domain models go in `packages/domain/`, agent logic in `apps/agents/` subfolders, platform API routes in `apps/api/`, infrastructure in `infra/`. No new top-level packages introduced; new capabilities integrate into existing module boundaries. The only structural additions are new files within existing directories, consistent with the project's established patterns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `PprrPhaseContext` model (non-incident PPRR) | Prevention/Preparedness phases apply to regions/scenarios without active incidents (FR-050). The `Incident` model cannot host these phases when no incident exists. | Overloading `Incident` with phantom "non-incident" records rejected because it violates the Incident model's semantic contract and would require null-guarding all incident-required fields. |
| Graceful degradation additions beyond spec NFRs | Constitution NN-5 mandates degradation for any single service failure. CHK069 identified gaps for AWS warning generation and AIIMS role assignment. | Relying only on spec-defined NFR-011/012 rejected because Constitution non-negotiables are supreme; implementation must satisfy the Constitution even when the spec has gaps. |
