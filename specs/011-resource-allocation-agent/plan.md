# Implementation Plan: Resource Allocation Agent — Demand Prioritisation, Resource Matching, Deployment Planning, and Multi-Incident Coordination

**Branch**: `011-resource-allocation-agent` | **Date**: 2026-04-17 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/011-resource-allocation-agent/spec.md`  
**Checklist**: [checklists/allocation.md](checklists/allocation.md) (48 items, 4 critical)

## Summary

The Resource Allocation Agent is the fourth agent in the disaster response pipeline. It receives `AgentHandoffEvent` messages from the Risk Assessment Agent (coordination tasks) and the Evacuation Agent (transport dispatch requests), and performs:

1. **Handoff intake and validation** — Pydantic v2 boundary validation with time-bounded idempotency checking, incident existence verification, and dual-source intake (risk_assessment + evacuation)
2. **Demand identification and prioritisation** — Three-tier priority hierarchy (life safety > property > environment) with four-level urgency ordering (critical > high > moderate > low), consolidated demand queue across all active incidents
3. **Resource inventory matching** — Greedy scoring algorithm: `score = capability_match × (1/distance) × availability_factor × priority_weight` with binary capability match, Haversine distance (floor 0.1 km), and configurable priority weights
4. **Deployment plan generation** — Versioned `ResourceDeploymentPlan` with optimistic concurrency, LLM-powered rationale with template fallback, and AIIMS-consistent summaries
5. **Resource status tracking** — Formal state machine (available → assigned → en_route → deployed → returning → available), operational limit flagging (12h rotation, 20% replenishment, mechanical issues)
6. **Cross-incident allocation** — Four-level tiebreaking (life safety → severity → proximity → timestamp), proportional distribution for true ties, mandatory commander approval for reallocation
7. **Human override** — Reassign, add, remove resources; change priority; approve/reject/cancel plans; all overrides produce immutable audit records with new plan version
8. **Append-only audit trail** — Every processing step persisted to Cosmos DB with three-tier degradation (Cosmos → memory buffer → file spill)

**Critical checklist resolutions** incorporated from `checklists/allocation.md`:
- **CHK001**: Priority weights: `critical=4.0, high=3.0, moderate=2.0, low=1.0` (configurable via environment variables)
- **CHK020**: Priority taxonomy conflict: Normalise all incoming priorities to AIDR 4-level (low/moderate/high/critical). Map evacuation's `immediate` → `critical`
- **CHK035**: Division-by-zero in 1/distance: Use `max(distance_km, 0.1)` floor to prevent infinity
- **CHK025**: "30% improvement" baseline: Document as aspirational; measure against manual allocation times from training exercises

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, tenacity  
**Storage**: Azure Cosmos DB (resource-deployment-plans, resource-allocation-decisions containers, append-only audit), Azure Service Bus (handoff intake queue)  
**Testing**: pytest (unit, contract, integration, simulation tests — existing test structure)  
**Target Platform**: Linux containers on Azure Container Apps (australiaeast primary, australiasoutheast DR)  
**Project Type**: Agent worker (message-driven microservice with health HTTP endpoint)  
**Performance Goals**: 30 concurrent deployment plans during peak; 15-second SLA for allocation plans; 5-second SLA for status updates; 30-second SLA for cross-incident analysis  
**Constraints**: ≤15s p95 allocation latency; ≤5s p95 status update latency; ≤1s health endpoint; Australian data residency; append-only audit with infinite retention  
**Scale/Scope**: Multi-instance auto-scaling on queue depth; two upstream consumers (Risk Assessment, Evacuation agents); single downstream consumer (incident commander dashboard)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (passed)

| # | Constitution Principle | Requirement | Status | Notes |
|---|----------------------|-------------|--------|-------|
| 1 | **I. Life Safety First** — Safety-critical outputs prioritised | Deployment plans generated within 15s SLA; life-safety demands (Tier 1) allocated before property (Tier 2) and environment (Tier 3) | ✅ PASS | FR-007, SC-001 |
| 2 | **I. Life Safety First** — Human override and emergency stop | Incident commanders can override any assignment (reassign, add, remove, change priority, approve/reject/cancel); all overrides immutably logged | ✅ PASS | FR-024, FR-025, FR-026 |
| 3 | **I. Life Safety First** — Explanations for incident commanders | Plan summaries include resource assignments, scoring rationale, trade-off analysis, shortfall details; plain language with AIIMS terminology | ✅ PASS | FR-016, FR-012 |
| 4 | **I. Life Safety First** — Safe degradation on low confidence/stale data | Template fallback when LLM unavailable (20% confidence reduction); stale inventory handled with last-known-good snapshot (30 min window); never halt for single dependency | ✅ PASS | FR-033, FR-034, FR-036 |
| 5 | **II. Multi-Agent Coordination** — Explicit handoffs with confidence/timestamps | Consumes `AgentHandoffEvent` from Risk Assessment and Evacuation with full payload validation; all consumed data carries confidence and timestamps | ✅ PASS | FR-001, FR-005 |
| 6 | **II. Multi-Agent Coordination** — No silent shared state changes | All plan versions are immutable once persisted; status transitions are the only mutation; every state change produces audit records | ✅ PASS | FR-015, FR-030, FR-031 |
| 7 | **II. Multi-Agent Coordination** — AIIMS alignment | Agent proposes plans but does not dispatch resources; all plans remain `proposed` until commander approval; `required_approval_level=incident_commander` | ✅ PASS | FR-026 |
| 8 | **III. Data Trust & Provenance** — Provenance metadata carried | Complete input snapshot stored per plan (demands, inventory snapshot, config version, scoring parameters) | ✅ PASS | FR-029 |
| 9 | **III. Data Trust & Provenance** — Data freshness indicator | Resource inventory staleness window (30 min default); stale data flagged in plan and reduces confidence | ✅ PASS | FR-034 |
| 10 | **III. Data Trust & Provenance** — Versioned, reproducible predictions | Monotonically increasing versions per incident with optimistic concurrency; identical inputs → identical outputs (FR-028, SC-007) | ✅ PASS | FR-015, FR-028, FR-029 |
| 11 | **IV. Privacy & Security** — Data minimisation | Only structured allocation data persisted; resource inventory contains equipment/facility identifiers, not personal data | ✅ PASS | FR-030 |
| 12 | **IV. Privacy & Security** — Australian data residency | All Azure resources in australiaeast/australiasoutheast | ✅ PASS | Constitution §VI |
| 13 | **IV. Privacy & Security** — Tenant isolation | Simulation/live boundaries enforced at all stages; simulation plans isolated from live incident queries | ✅ PASS | FR-027 |
| 14 | **IV. Privacy & Security** — Prompt injection protection | System prompts scope LLM role to resource allocation rationale; ContentSafetyValidator on all LLM outputs | ✅ PASS | FR-037 |
| 15 | **V. Communication** — Content safety | All LLM outputs validated through ContentSafetyValidator before inclusion in plan summaries | ✅ PASS | FR-037 |
| 16 | **VI. Cloud Platform** — Azure, Australian regions only | ACA, Cosmos DB, Azure OpenAI, App Insights, Service Bus — all australiaeast | ✅ PASS | Constitution §VI |
| 17 | **NFR** — Resilience to partial outages | Three-tier audit degradation; LLM template fallback; inventory staleness handling; never halt for single failure | ✅ PASS | FR-031a, FR-033, FR-034, FR-036 |
| 18 | **NFR** — Append-only audit trail | `AllocationDecisionRecord` in Cosmos DB, no TTL, no updates/deletes | ✅ PASS | FR-030, FR-031 |
| 19 | **NFR** — WAF compliance | Observability via Application Insights; auto-scaling via ACA; security via MI + content safety | ✅ PASS | NFR-001, NFR-002 |
| 20 | **NFR** — Scenario-based testing | Simulation mode via tenant isolation; reproducibility verification; bushfire/cyclone/flood scenarios | ✅ PASS | FR-027, FR-028, SC-007 |

### Post-Design Re-check (passed)

All 20 gates re-evaluated after Phase 1 design — no regressions. Key design decisions that strengthened compliance:
- **Normalised priority taxonomy** (CHK020) ensures consistent cross-agent prioritisation by mapping all incoming priorities to AIDR 4-level (gates 1, 5)
- **Distance floor** (CHK035) `max(distance_km, 0.1)` prevents infinity in scoring while preserving co-located resource preference (gate 1)
- **Optimistic concurrency** for version numbering eliminates race conditions in concurrent plan generation (gate 10)
- **Three-tier audit degradation** replicates proven monitoring/risk/evacuation agent pattern (gates 17, 18)
- **Plan expiry** (CHK008) 4-hour timeout on pending plans prevents stale proposals from consuming resources (gate 4)

## Project Structure

### Documentation (this feature)

```text
specs/011-resource-allocation-agent/
├── plan.md                            # This file
├── research.md                        # Phase 0 output — 12 research decisions
├── data-model.md                      # Phase 1 output — 8 entities, configurable parameters
├── quickstart.md                      # Phase 1 output — setup, run, verify
├── contracts/                         # Phase 1 output
│   ├── allocation-pipeline.md         # 9-stage pipeline contract with latency budget
│   ├── health-endpoint.md             # GET /health + POST /override contracts
│   └── telemetry.md                   # 25+ metrics, traces, events, alerting thresholds
├── checklists/
│   └── allocation.md                  # 48-item requirements quality checklist
└── tasks.md                           # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/agents/
├── common/                                    # Shared agent infrastructure (existing)
│   ├── content_safety.py                      # ContentSafetyValidator (existing)
│   ├── handoffs.py                            # AgentHandoffEvent, build_handoff, deliver_with_retry (existing)
│   ├── llm_client.py                          # LLMClient wrapping Azure OpenAI (existing)
│   ├── llm_mixin.py                           # LLMCallMixin with fallback (existing)
│   └── dependency_notifier.py                 # Dependency health notification (existing)
├── resource_allocation/                       # Resource Allocation Agent (this feature)
│   ├── __init__.py                            # Package init (NEW)
│   ├── agent.py                               # ResourceAllocationAgent class + FastAPI app (existing stub, to be replaced)
│   ├── models.py                              # All Pydantic v2 models, enums, embedded models (NEW)
│   ├── config.py                              # ResourceAllocationConfig from environment variables (NEW)
│   ├── audit.py                               # AuditWriter with three-tier degradation (NEW)
│   ├── dedup.py                               # HandoffDeduplicator with TTL cache (NEW)
│   ├── scoring.py                             # Greedy scoring algorithm, Haversine distance, priority weights (NEW)
│   ├── matcher.py                             # Resource-demand matching, partial allocation, tie-breaking (NEW)
│   ├── inventory.py                           # Resource inventory manager, state machine, status tracking (NEW)
│   ├── versioning.py                          # Optimistic concurrency version counter (NEW)
│   ├── templates.py                           # Template-based fallback text generators (NEW)
│   ├── priority.py                            # Priority normalisation, demand queue, cross-incident tiebreaking (NEW)
│   └── pipeline.py                            # AllocationProcessingPipeline orchestrator — 9 stages (NEW)
└── pyproject.toml                             # Agent workspace deps (existing, no new deps beyond existing)

data/
└── resource-inventories/
    └── sample-inventory.json                  # Sample resource inventory for testing (NEW)

tests/
├── unit/
│   ├── test_resource_allocation_models.py     # Model validation tests (NEW)
│   ├── test_resource_allocation_config.py     # Config loading tests (NEW)
│   ├── test_resource_allocation_scoring.py    # Scoring algorithm, Haversine, distance floor (NEW)
│   ├── test_resource_allocation_matcher.py    # Matching, partial allocation, tie-breaking (NEW)
│   ├── test_resource_allocation_inventory.py  # State machine, status tracking, operational flags (NEW)
│   ├── test_resource_allocation_priority.py   # Priority normalisation, demand queue, cross-incident (NEW)
│   ├── test_resource_allocation_versioning.py # Optimistic concurrency (NEW)
│   ├── test_resource_allocation_dedup.py      # Handoff deduplication (NEW)
│   ├── test_resource_allocation_audit.py      # Audit writer degradation (NEW)
│   ├── test_resource_allocation_pipeline.py   # Pipeline stage unit tests (NEW)
│   └── test_resource_allocation_endpoints.py  # Health, override endpoint tests (NEW)
├── contract/
│   ├── test_resource_allocation_handoff.py    # Handoff structure contract tests (NEW)
│   ├── test_resource_allocation_plan_schema.py # Plan output schema contract tests (NEW)
│   └── test_resource_allocation_reproducibility.py # Reproducibility contract tests (NEW)
├── integration/
│   ├── test_resource_allocation_cosmos.py     # Cosmos DB persistence integration (NEW)
│   └── test_resource_allocation_service_bus.py # Service Bus handoff intake integration (NEW)
└── simulation/
    ├── test_flood_allocation_scenario.py      # Flood resource allocation scenario (NEW)
    ├── test_bushfire_allocation_scenario.py   # Bushfire resource allocation scenario (NEW)
    └── test_multi_incident_scenario.py        # Multi-incident cross-allocation scenario (NEW)
```

**Structure Decision**: Follows the existing multi-agent workspace pattern under `apps/agents/`. New modules are added within `apps/agents/resource_allocation/` following the proven separation of concerns (agent logic, models, config, services, pipeline) established by monitoring, risk assessment, and evacuation agents. The Resource Allocation Agent introduces domain-specific modules (`scoring.py`, `matcher.py`, `inventory.py`, `priority.py`) that have no equivalent in other agents, reflecting its unique algorithmic matching and cross-incident coordination requirements. Test files follow the existing test directory structure with the same tier separation (unit, contract, integration, simulation).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Three-tier audit degradation (memory + file + Cosmos) | Constitution mandates unbroken audit trail even during infrastructure failures; same pattern as monitoring/risk/evacuation | Single-tier (Cosmos-only) would silently lose audit records during Cosmos outages, violating constitutional NFRs |
| Optimistic concurrency with version counter docs | FR-015 mandates monotonically increasing versions under concurrent processing; multiple handoffs for the same incident can arrive simultaneously | Simple increment-on-write could produce duplicate version numbers when two handoffs for the same incident arrive simultaneously |
| Priority normalisation layer (CHK020) | Risk Assessment uses `critical/high/medium/low`; Evacuation uses `critical/immediate/high`; Constitution requires consistent prioritisation across agents | Passing through raw priorities would produce inconsistent scoring and potentially incorrect life-safety ordering |
| Distance floor max(distance_km, 0.1) for scoring (CHK035) | Prevents division-by-zero / infinity in co-located resources while preserving strong proximity preference | Zero-distance check (if 0 then skip) would unfairly exclude co-located resources from scoring |
| Plan expiry timer (CHK008) | Prevents stale proposed plans from indefinitely reserving resources; incident conditions change rapidly | No expiry would allow proposed plans to block resources for hours/days after conditions have changed |

## Checklist Resolution Summary

| Checklist Item | Category | Resolution | Reference |
|----------------|----------|------------|-----------|
| CHK001 | Gap | Priority weights: `critical=4.0, high=3.0, moderate=2.0, low=1.0` — configurable via env vars | research.md §1 |
| CHK002 | Gap | Availability factor: `available=1.0, returning=0.5, all others=0.0` — simple step function for MVP | research.md §2 |
| CHK003 | Gap | Travel speed: configurable defaults per resource type (personnel=40km/h, vehicle=60km/h) plus mobilisation overhead | research.md §3 |
| CHK004 | Gap | Confidence: base = 0.9 (full inventory + LLM), reduced by stale data (×0.8), partial inventory (×0.7), template fallback (×0.8) | research.md §4 |
| CHK005 | Gap | Demand lifecycle: `pending → partially_met/fully_met/unmet → closed`. Cancellation via commander override | research.md §5 |
| CHK008 | Gap | Plan expiry: 4 hours if not approved. Expired plans release reserved resources; status → `expired` | research.md §6 |
| CHK009 | Gap | Optimistic concurrency with etag; retry up to 3 times with jitter; fail with conflict error if all retries exhausted | research.md §7 |
| CHK014 | Ambiguity | Tie-breaking: highest capability count wins, then alphabetical resource ID | research.md §8 |
| CHK020 | Conflict | Priority normalisation: all incoming priorities mapped to AIDR 4-level (low/moderate/high/critical). Evacuation `immediate` → `critical` | research.md §9 |
| CHK021 | Consistency | Reserved resources excluded from general matching but available for their reserved incident | research.md §10 |
| CHK025 | Measurability | "30% improvement" is aspirational; baseline = manual allocation times from training exercises; measured as time-to-arrival reduction + fulfilment rate improvement | research.md §11 |
| CHK032 | Coverage | On incident closure, release all assigned resources back to available pool; log bulk status transitions | research.md §5 |
| CHK033 | Coverage | When new resources become available, check pending unmet demands and trigger re-allocation automatically | research.md §5 |
| CHK035 | Edge Case | Distance floor: `max(distance_km, 0.1)` — prevents infinity; 100m minimum represents co-located resources | research.md §1 |
| CHK037 | Edge Case | Max 3 retries for optimistic concurrency with exponential backoff + jitter; fail with `409 Conflict` if exhausted | research.md §7 |
| CHK040 | Gap | RBAC deferred to v2; all overrides require `commander` role claim in JWT; validated at endpoint level | research.md §12 |
| CHK044 | Assumption | Static inventory loaded at startup from JSON config; dynamic status updates via Service Bus subscription; clear delineation in inventory.py | research.md §2 |

## Azure Resources

| Resource | SKU/Tier | Region | Purpose |
|----------|----------|--------|---------|
| Azure Container Apps | Consumption | australiaeast | Agent hosting with auto-scaling on queue depth |
| Azure Cosmos DB | Serverless | australiaeast | Deployment plans and audit trail (2 containers) |
| Azure OpenAI | Standard (GPT-4o) | australiaeast | Plan rationale/summary generation |
| Azure Application Insights | Standard | australiaeast | Telemetry, metrics, distributed tracing |
| Azure Service Bus | Standard | australiaeast | Handoff intake queue (from risk assessment + evacuation) |
| Azure Container Apps (DR) | Consumption | australiasoutheast | DR deployment (LLM fallback to templates) |
| Azure Cosmos DB (DR) | Multi-region write | australiasoutheast | DR replication |

## Implementation Phases

### Phase 1: Core Models and Configuration (Foundation)

- Create `resource_allocation/__init__.py` package init
- Create `resource_allocation/config.py` with `ResourceAllocationConfig` class reading all environment variables (same frozen dataclass pattern as risk_assessment/evacuation) — 25+ configurable parameters including priority weights, availability factors, distance floor, mobilisation times, plan expiry, dedup window
- Create `resource_allocation/models.py` with all Pydantic v2 models:
  - Enums: `DecisionType` (16 values), `ConfidenceLevel`, `PlanStatus`, `ResourceStatus`, `ResourceType`, `DemandFulfilmentStatus`, `PriorityTier`, `UrgencyLevel`
  - Embedded models: `ResourceDemand`, `ResourceAssignment`, `ResourceInventoryItem`, `DeploymentTimeline`, `ShortfallDetail`, `TradeOffAnalysis`, `Traceability`, `OverrideMetadata`, `ScoringRationale`, `InputSnapshot`
  - Primary model: `ResourceDeploymentPlan` with validation rules (plan_id regex, version ≥ 1, confidence clamping, status transitions)
  - Audit model: `AllocationDecisionRecord` (canonical 26-field schema, append-only)
  - Buffer model: `AuditBufferEntry` for degraded writes
- Write unit tests for all models, enums, and config

### Phase 2: Scoring Algorithm and Priority Normalisation (Core Algorithm)

- Create `resource_allocation/scoring.py` with scoring functions:
  - Haversine formula for distance calculation (returns km)
  - Distance floor enforcement: `max(distance_km, 0.1)` (CHK035)
  - Scoring formula: `score = capability_match × (1/max(distance, 0.1)) × availability_factor × priority_weight`
  - Binary capability matching (1.0 if all required capabilities present, 0.0 otherwise)
  - Type and sub-type compatibility checking
- Create `resource_allocation/priority.py` with priority normalisation:
  - AIDR 4-level normalisation: map all incoming urgencies to `low/moderate/high/critical`
  - Evacuation priority mapping: `immediate` → `critical` (CHK020)
  - Three-tier priority hierarchy (life safety > property > environment)
  - Consolidated demand queue with priority-ordered insertion
  - Four-level tiebreaking implementation (CHK014): life safety → severity → proximity → timestamp
  - Equal-priority proportional distribution (CHK022): by ratio of unmet demands
- Write unit tests for Haversine at equator/poles/antipodes, distance floor at 0/0.05/0.1/1.0, scoring formula components, priority normalisation, tiebreaking

### Phase 3: Resource Inventory and State Machine (Data Layer)

- Create `resource_allocation/inventory.py` with `ResourceInventoryManager`:
  - Static inventory loading from JSON configuration (CHK044)
  - State machine enforcement: `available → reserved/assigned → en_route → deployed → returning → available`; `unavailable` from any active state
  - State transition validation (reject invalid transitions per FR-018)
  - Operational flag management: rotation (12h deployment), replenishment (20% stock), mechanical issues
  - Reserved resource handling: excluded from general matching, available for reserved incident (CHK021)
  - Resource release on incident closure (CHK032): bulk transition assigned → available
  - Availability factor computation: `available=1.0, returning=0.5, all others=0.0` (CHK002)
  - Missing/invalid location handling: exclude from distance-based scoring, log warning
- Write unit tests for state machine transitions (all valid and invalid paths), operational flags, reservation lifecycle, bulk release

### Phase 4: Resource-Demand Matching (Core Logic)

- Create `resource_allocation/matcher.py` with `ResourceMatcher`:
  - Greedy assignment: iterate demands in priority order, assign highest-scoring eligible resource
  - Partial allocation handling (FR-012): assign available matches, mark unfulfilled demands with shortfall details
  - Tie-breaking: highest capability count wins, then alphabetical resource ID (CHK014)
  - Cross-incident contention detection: identify resources demanded by multiple incidents
  - Trade-off analysis generation for cross-incident reallocation (FR-021)
  - Re-allocation recommendation when new resources become available (CHK033)
  - Reallocation guard: require commander approval for reassigning from active plans (FR-013)
- Write unit tests for greedy assignment, partial allocation, tie-breaking, cross-incident contention, reallocation guards

### Phase 5: Deduplication, Versioning, and Audit (Resilience)

- Create `resource_allocation/dedup.py` with `HandoffDeduplicator` (TTL cache, configurable window — same pattern as risk assessment/evacuation)
- Create `resource_allocation/versioning.py` with `VersionCounter` (Cosmos DB etag-based OCC — same pattern as risk assessment/evacuation):
  - Counter document: `{id: "{incident_id}_plan_counter", current_version: N, _etag: "..."}`
  - Max 3 retries with jitter on conflict (CHK037)
  - Fallback to UUID-suffixed version on exhausted retries
- Create `resource_allocation/audit.py` with `AuditWriter` class — replicating proven three-tier pattern:
  - Tier 1: Cosmos DB `create_item()` (resource-allocation-decisions container)
  - Tier 2: In-memory ring buffer (10K capacity)
  - Tier 3: File spill (JSONL to configurable path)
  - Recovery flush: memory → file → Cosmos in chronological order
- Write unit tests for dedup edge cases, version counter conflicts, all three audit tiers, recovery flush

### Phase 6: Templates and Plan Generation (Integration)

- Create `resource_allocation/templates.py` with template-based fallback generators:
  - Plan summary template (assignments, shortfalls, priorities, trade-offs)
  - Assignment rationale template per resource-demand pair
  - Cross-incident trade-off template
  - Transport dispatch summary template
- Wire LLM-powered plan rationale generation via `LLMCallMixin._generate_with_fallback()`
- Content safety validation on all LLM outputs (FR-037)
- Plan expiry logic: 4-hour timeout, auto-transition to `expired`, resource release (CHK008)
- Confidence calculation: base 0.9, multiplicative penalties for stale data (×0.8), partial inventory (×0.7), template fallback (×0.8)
- Write unit and contract tests for template output, LLM fallback, plan expiry

### Phase 7: Pipeline Orchestrator (Integration)

- Create `resource_allocation/pipeline.py` with `AllocationProcessingPipeline` orchestrating all 9 stages:
  - Stage 1: Handoff intake and validation (schema, target_agent, incident_id, dedup, tenant)
  - Stage 2: Recommendation/assessment retrieval (Cosmos DB reads)
  - Stage 3: Demand identification and prioritisation (extract demands, normalise priorities, queue insertion)
  - Stage 4: Resource inventory query (load inventory, filter eligible, apply state machine)
  - Stage 5: Resource-demand matching (scoring, greedy assignment, partial allocation)
  - Stage 6: Cross-incident analysis (contention detection, trade-off analysis, reallocation recommendations)
  - Stage 7: Plan generation and summary (versioning, LLM/template summary, confidence, timeline)
  - Stage 8: Plan persistence (Cosmos DB write with OCC)
  - Stage 9: Audit finalisation (comprehensive audit records for each processing step)
- Wire transport dispatch path (FR-005): evacuation handoffs → Tier 1 demands → standard matching
- Wire re-allocation trigger (CHK033): new resource available → check unmet demands → auto-plan
- Write integration tests for end-to-end handoff flow, transport dispatch flow, cross-incident flow

### Phase 8: Health Endpoint and API (Operations)

- Replace existing `resource_allocation/agent.py` stub with full `ResourceAllocationAgent` class:
  - Subclass `LLMCallMixin`
  - `process_handoff()` — main pipeline entry point
  - `process_status_update()` — resource status signal processing
  - Integration with pipeline and all services
- Create FastAPI app factory `create_app()`:
  - `GET /health` — checks per contracts/health-endpoint.md (inventory_loaded, llm_connectivity, cosmos_connectivity, active_plan_count, pending_demands, processing_queue_depth, audit_store)
  - `POST /override` — incident commander plan overrides (reassign, add, remove, change priority, approve, reject, cancel)
- Wire health checks to inventory manager, LLM client, Cosmos client, pipeline state, audit writer
- Port 8083 (avoiding monitoring 8080, risk assessment 8081, evacuation 8082)
- Write contract tests for health response schema, override schemas

### Phase 9: Observability and Telemetry (WAF)

- Add OpenTelemetry instrumentation for distributed tracing (span hierarchy per contracts/telemetry.md)
- Emit all metrics defined in contracts/telemetry.md (processing, matching, cross-incident, override, degradation, version)
- Emit custom events for key decision points (10 event types)
- Configure Application Insights alerting thresholds (10 alert rules)
- Write tests verifying metric emission

### Phase 10: Infrastructure (Deployment)

- Add/update Bicep modules for Cosmos DB containers (resource-deployment-plans, resource-allocation-decisions), Service Bus queue, Container Apps scaling rules
- Configure auto-scaling rules based on queue depth
- Add managed identity for Cosmos DB and Service Bus access
- Configure port 8083

## Identified Issues in Existing Code

1. **Stub-only implementation** (`resource_allocation/agent.py`): The current `ResourceAllocationAgent.prioritize()` returns a simple sort by priority string using a hardcoded dict `{"critical": 0, "high": 1, "medium": 2, "low": 3}`. It has no models, no FastAPI endpoints, no handoff processing, no scoring algorithm, no LLM integration, no audit trail. The entire file must be replaced with the full agent implementation.

2. **Missing normalised priority** (`resource_allocation/agent.py:4`): The hardcoded priority map uses `medium` instead of `moderate` (AIDR standard). CHK020 requires normalisation to the AIDR 4-level taxonomy used across all agents.

## Artifacts Generated

| Artifact | Path | Content |
|----------|------|---------|
| Research | `specs/011-resource-allocation-agent/research.md` | 12 research decisions resolving CHK unknowns |
| Data Model | `specs/011-resource-allocation-agent/data-model.md` | 8 entities, relationships, configurable parameters |
| Allocation Pipeline Contract | `specs/011-resource-allocation-agent/contracts/allocation-pipeline.md` | 9-stage pipeline with latency budget (15s allocation, 30s cross-incident) |
| Health Endpoint Contract | `specs/011-resource-allocation-agent/contracts/health-endpoint.md` | GET /health + POST /override schemas |
| Telemetry Contract | `specs/011-resource-allocation-agent/contracts/telemetry.md` | 25+ metrics, traces, events, 10 alert thresholds |
| Quickstart | `specs/011-resource-allocation-agent/quickstart.md` | Setup, run, verify instructions |
