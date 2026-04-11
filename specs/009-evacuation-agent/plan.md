# Implementation Plan: Evacuation Agent — Route Optimisation, Transport Coordination, and Evacuation Planning

**Branch**: `009-evacuation-agent` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/009-evacuation-agent/spec.md`  
**Checklist**: [checklists/requirements.md](checklists/requirements.md) (100 items)

## Summary

The Evacuation Agent is the third agent in the disaster response pipeline. It receives `AgentHandoffEvent` messages from the Risk Assessment Agent containing escalated evacuation recommendations and performs:

1. **Handoff intake and validation** — Pydantic v2 boundary validation with time-bounded idempotency checking and assessment existence verification
2. **Hazard assessment retrieval** — Retrieve the referenced HazardAssessment with GeoJSON hazard map from Cosmos DB
3. **Evacuation zone computation** — Concentric zones (1/2/3) from hazard GeoJSON using Shapely polygon operations, with multi-hazard merging via geometric union
4. **Road network preparation** — Zone-based capacity reduction (Zone 1: closed, Zone 2: −50%, Zone 3: −25%) on the in-memory road graph using Shapely intersection
5. **Graph-based route computation** — Dijkstra's algorithm with capacity-weighted edges, multi-path distribution for congestion avoidance, hazard-type-aware routing strategies
6. **Transport coordination** — Vulnerable population identification and transport requirement generation across four categories (mobility-impaired, medical-dependent, elderly/aged care, children/schools)
7. **Phased timeline estimation** — Five-phase evacuation sequence with time-based and estimated-population-based phase transitions, shelter-in-place decision logic, and shelter-to-evacuation recovery
8. **Human-readable plan generation** — LLM-powered plan summaries with AIIMS terminology and template fallback
9. **Dynamic replanning** — Five trigger conditions (road closure, hazard expansion >10%, progress delay >30%, higher-severity assessment, manual trigger) with rate limiting and no-change detection
10. **Append-only audit trail** — Every processing step persisted to Cosmos DB with three-tier degradation (Cosmos → memory buffer → file spill)

**Critical checklist resolutions** incorporated from `checklists/requirements.md`:
- **CHK055**: Audit field conflict — merged FR-028/FR-029 into one canonical `EvacuationDecisionRecord` schema matching monitoring/risk assessment pattern
- **CHK025**: Phase progress — estimated departure rates from pre-loaded population data (not real-time GPS); time-based thresholds as primary, estimated population moved as secondary
- **CHK042**: Shelter-to-evacuation recovery — allow transition back to evacuation when new route available; logged as replanning event
- **CHK063**: Confidence reduction — multiplicative (`adjusted = confidence × 0.8`), same as risk assessment
- **CHK080**: Duplicate handoff for existing plan — create new plan version incorporating new assessment data; do not reject

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, tenacity, shapely  
**Storage**: Azure Cosmos DB (evacuation-plans, evacuation-decisions containers, append-only audit), Azure Service Bus (handoff intake queue)  
**Testing**: pytest (unit, contract, integration, simulation tests — existing test structure)  
**Target Platform**: Linux containers on Azure Container Apps (australiaeast primary, australiasoutheast DR)  
**Project Type**: Agent worker (message-driven microservice with health HTTP endpoint)  
**Performance Goals**: 50 concurrent evacuation plans during peak; 30-second SLA for initial plan generation; 15-second SLA for dynamic replanning  
**Constraints**: ≤30s p95 plan generation; ≤15s p95 replanning; ≤1s health endpoint; Australian data residency; append-only audit with infinite retention  
**Scale/Scope**: Multi-instance auto-scaling on queue depth; single downstream consumer (incident commander dashboard); static road network for MVP (max 1,000 nodes, 5,000 edges)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (passed)

| # | Constitution Principle | Requirement | Status | Notes |
|---|----------------------|-------------|--------|-------|
| 1 | **I. Life Safety First** — Safety-critical outputs prioritised | Evacuation plans generated within 30s SLA; shelter-in-place when no viable routes; emergency escalation for immediate threats | ✅ PASS | FR-014, SC-001 |
| 2 | **I. Life Safety First** — Human override and emergency stop | Incident commanders can override routes, zone boundaries, phases, cancel/pause plans; all overrides immutably logged | ✅ PASS | FR-022, FR-023 |
| 3 | **I. Life Safety First** — Explanations for incident commanders | Plan summaries include traceable references, route rationale, confidence scores, assumptions; plain language with AIIMS terminology | ✅ PASS | FR-019, FR-020, FR-021 |
| 4 | **I. Life Safety First** — Safe degradation on low confidence/stale data | Template fallback when LLM unavailable (20% confidence reduction); degraded plans with generic guidance when road data stale; no halt for single dependency failure | ✅ PASS | FR-031, FR-033, FR-035 |
| 5 | **II. Multi-Agent Coordination** — Explicit handoffs with confidence/timestamps | Consumes `AgentHandoffEvent` from Risk Assessment with full payload validation; all consumed data carries confidence and timestamps | ✅ PASS | FR-001, FR-002, FR-004 |
| 6 | **II. Multi-Agent Coordination** — No silent shared state changes | All plan versions are immutable once persisted; status transitions are the only mutation; every change produces audit records | ✅ PASS | FR-017, FR-028, FR-029 |
| 7 | **II. Multi-Agent Coordination** — AIIMS alignment | Agent proposes plans but does not execute evacuation orders; all plans remain `proposed` until commander approval; `required_approval_level=incident_commander` | ✅ PASS | FR-024 |
| 8 | **III. Data Trust & Provenance** — Provenance metadata carried | Complete data snapshot stored per plan (road network version, population data version, facility data version, assembly area version) | ✅ PASS | FR-027 |
| 9 | **III. Data Trust & Provenance** — Data freshness indicator | Road network staleness window (6h default); stale data flagged in plan assumptions and reduces confidence | ✅ PASS | FR-031 |
| 10 | **III. Data Trust & Provenance** — Versioned, reproducible predictions | Monotonically increasing versions per incident with optimistic concurrency; identical inputs → identical outputs (FR-026, SC-006) | ✅ PASS | FR-017, FR-026, FR-027 |
| 11 | **IV. Privacy & Security** — Data minimisation | Only structured plan data persisted; population data is aggregate estimates, not individual records | ✅ PASS | FR-019 |
| 12 | **IV. Privacy & Security** — Australian data residency | All Azure resources in australiaeast/australiasoutheast | ✅ PASS | Constitution §VI |
| 13 | **IV. Privacy & Security** — Tenant isolation | Simulation/live boundaries enforced at all stages; simulation plans isolated from live incident queries | ✅ PASS | FR-025 |
| 14 | **IV. Privacy & Security** — Prompt injection protection | System prompts scope LLM role to evacuation planning; ContentSafetyValidator on all LLM outputs | ✅ PASS | FR-036 |
| 15 | **V. Communication** — Content safety | All LLM outputs validated through ContentSafetyValidator before inclusion in plan summaries | ✅ PASS | FR-036 |
| 16 | **VI. Cloud Platform** — Azure, Australian regions only | ACA, Cosmos DB, Azure OpenAI, App Insights, Service Bus — all australiaeast | ✅ PASS | Constitution §VI |
| 17 | **NFR** — Resilience to partial outages | Three-tier audit degradation; LLM template fallback; road data staleness handling; population data gap handling | ✅ PASS | FR-031–FR-035 |
| 18 | **NFR** — Append-only audit trail | `EvacuationDecisionRecord` in Cosmos DB, no TTL, no updates/deletes | ✅ PASS | FR-028, FR-029, FR-030 |
| 19 | **NFR** — WAF compliance | Observability via Application Insights; auto-scaling via ACA; security via MI + content safety | ✅ PASS | NFR-001, NFR-002 |
| 20 | **NFR** — Scenario-based testing | Simulation mode via tenant isolation; reproducibility verification; bushfire/cyclone/flood scenarios | ✅ PASS | FR-025, FR-026, SC-006 |

### Post-Design Re-check (passed)

All 20 gates re-evaluated after Phase 1 design — no regressions. Key design decisions that strengthened compliance:
- **Shapely-based zone computation** ensures accurate geospatial intersection for road capacity reduction (gates 1, 10)
- **10-stage pipeline** with explicit stage boundaries produces granular audit trail entries (gates 6, 18)
- **Shelter-to-evacuation recovery** as a standard replanning event ensures dynamic safety improvements are captured (gate 1, 4)
- **Conservative partial-overlap rule** (highest-severity zone applies) aligns with Life Safety First principle (gate 1)
- **Three-tier audit degradation** replicates proven monitoring/risk assessment pattern (gates 17, 18)
- **Rate-limited replanning** prevents version churn while maintaining responsiveness (gate 10)

## Project Structure

### Documentation (this feature)

```text
specs/009-evacuation-agent/
├── plan.md                            # This file
├── research.md                        # Phase 0 output — 10 research decisions
├── data-model.md                      # Phase 1 output — 14 entities, configurable parameters
├── quickstart.md                      # Phase 1 output — setup, run, verify
├── contracts/                         # Phase 1 output
│   ├── evacuation-pipeline.md         # 10-stage pipeline contract with latency budget
│   ├── health-endpoint.md             # GET /health + POST /override + POST /replan contracts
│   └── telemetry.md                   # 30+ metrics, traces, events, alerting thresholds
├── checklists/
│   └── requirements.md                # 100-item requirements quality checklist
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
├── evacuation/                                # Evacuation Agent (this feature)
│   ├── __init__.py                            # Package init (NEW)
│   ├── agent.py                               # EvacuationAgent class (existing stub, to be replaced)
│   ├── models.py                              # EvacuationDecisionRecord, DecisionType, enums, embedded models (NEW)
│   ├── config.py                              # EvacuationConfig from environment variables (NEW)
│   ├── audit.py                               # AuditWriter with three-tier degradation (NEW)
│   ├── dedup.py                               # HandoffDeduplicator with TTL cache (NEW)
│   ├── road_network.py                        # RoadNetworkLoader — JSON parsing, graph construction, validation (NEW)
│   ├── zones.py                               # ZoneComputer — Shapely-based zone computation, multi-hazard merging (NEW)
│   ├── router.py                              # RouteComputer — Dijkstra's pathfinding, multi-path, hazard-type strategies (NEW)
│   ├── transport.py                           # TransportCoordinator — vulnerability categories, vehicle estimation (NEW)
│   ├── timeline.py                            # TimelineEstimator — phased evacuation, shelter-in-place, recovery (NEW)
│   ├── versioning.py                          # Optimistic concurrency version counter (NEW)
│   ├── templates.py                           # Template-based fallback text generators (NEW)
│   ├── pipeline.py                            # EvacuationProcessingPipeline orchestrator — 10 stages (NEW)
│   └── replanner.py                           # DynamicReplanner — trigger evaluation, incremental updates, rate limiting (NEW)
└── pyproject.toml                             # Agent workspace deps (existing, add shapely)

data/
├── road-networks/
│   └── far-north-qld-sample.json              # Sample road network for testing (NEW)
└── population/
    └── sample-population.json                 # Sample population/facility data for testing (NEW)

tests/
├── unit/
│   ├── test_evacuation_models.py              # Model validation tests (NEW)
│   ├── test_evacuation_config.py              # Config loading tests (NEW)
│   ├── test_evacuation_road_network.py        # Road network loading, validation, size limits (NEW)
│   ├── test_evacuation_zones.py               # Zone computation, multi-hazard merging, Shapely ops (NEW)
│   ├── test_evacuation_router.py              # Dijkstra's, multi-path, closed roads, hazard strategies (NEW)
│   ├── test_evacuation_transport.py           # Transport coordination, vehicle estimation (NEW)
│   ├── test_evacuation_timeline.py            # Phase computation, shelter-in-place, recovery (NEW)
│   ├── test_evacuation_versioning.py          # Optimistic concurrency (NEW)
│   ├── test_evacuation_dedup.py               # Handoff deduplication (NEW)
│   ├── test_evacuation_audit.py               # Audit writer degradation (NEW)
│   ├── test_evacuation_replanner.py           # Replanning triggers, rate limiting, no-change detection (NEW)
│   ├── test_evacuation_pipeline.py            # Pipeline stage unit tests (NEW)
│   └── test_evacuation_endpoints.py           # Health, override, replan endpoint tests (NEW)
├── contract/
│   ├── test_evacuation_handoff.py             # Handoff structure contract tests (NEW)
│   ├── test_evacuation_plan_schema.py         # Plan output schema contract tests (NEW)
│   └── test_evacuation_reproducibility.py     # Reproducibility contract tests (NEW)
├── integration/
│   ├── test_evacuation_cosmos.py              # Cosmos DB persistence integration (NEW)
│   └── test_evacuation_service_bus.py         # Service Bus handoff intake integration (NEW)
└── simulation/
    ├── test_cyclone_evacuation_scenario.py    # Cyclone evacuation scenario (NEW)
    ├── test_bushfire_evacuation_scenario.py   # Bushfire evacuation scenario (NEW — constitution §Quality Gates)
    └── test_flood_evacuation_scenario.py      # Flood evacuation scenario (NEW — constitution §Quality Gates)
```

**Structure Decision**: Follows the existing multi-agent workspace pattern under `apps/agents/`. New modules are added within `apps/agents/evacuation/` following the risk assessment agent's separation of concerns (agent logic, models, config, services, pipeline). The Evacuation Agent introduces domain-specific modules (`road_network.py`, `zones.py`, `router.py`, `transport.py`, `timeline.py`, `replanner.py`) that have no equivalent in other agents, reflecting its unique geospatial and algorithmic complexity. Test files follow the existing test directory structure with the same tier separation (unit, contract, integration, simulation).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Three-tier audit degradation (memory + file + Cosmos) | Constitution mandates unbroken audit trail even during infrastructure failures; same pattern as monitoring/risk assessment | Single-tier (Cosmos-only) would silently lose audit records during Cosmos outages, violating constitutional NFRs |
| Optimistic concurrency with version counter docs | FR-017 mandates monotonically increasing versions under concurrent replanning; multiple replanning triggers could fire simultaneously | Simple increment-on-write could produce duplicate version numbers when concurrent replans arrive for the same incident |
| 10-stage pipeline (vs 6-stage monitoring / 8-stage risk assessment) | Evacuation requires geospatial zone computation, graph-based routing, transport coordination, and phased timeline estimation — each stage has distinct input/output boundaries and failure modes | Collapsing stages would lose granular audit trail visibility and make error handling ambiguous |
| Shapely dependency for geospatial operations | FR-009c mandates precise polygon intersection for zone-based road capacity reduction; FR-009d requires geometric union for multi-hazard merging | Manual coordinate math is error-prone for polygon operations and would not handle edge cases (partial overlap, complex polygons) correctly |
| Rate-limited replanning (CHK037) | Dynamic disaster conditions can produce rapid-fire replanning triggers; without rate limiting, version churn degrades plan clarity for commanders | No rate limiting could produce dozens of plan versions per minute during rapidly evolving conditions, overwhelming incident commanders |

## Checklist Resolution Summary

| Checklist Item | Category | Resolution | Reference |
|----------------|----------|------------|-----------|
| CHK001 | Clarity | Dijkstra's selected: optimal for positive-weight graphs, no heuristic needed for MVP network sizes; A* heuristic admissibility not guaranteed with capacity+hazard weights | research.md §9 |
| CHK002 | Completeness | Road network JSON schema fully specified with all node/edge attributes, data types, and valid ranges | research.md §6, data-model.md §RoadNetwork |
| CHK007 | Gap | Tie-breaking: prefer lower congestion risk, then shorter distance | contracts/evacuation-pipeline.md §Stage 5 |
| CHK013 | Gap | Partial overlap: highest-severity zone applies (conservative, Life Safety First) | research.md §7 |
| CHK025 | Measurability | Phase transitions: time-based primary, estimated population departure rate secondary; no real-time GPS | research.md §2 |
| CHK037 | Gap | Replanning rate limit: minimum 30s between replans for same incident, configurable via `REPLAN_RATE_LIMIT_SECONDS` | data-model.md §Parameters, contracts/evacuation-pipeline.md |
| CHK042 | Gap | Shelter-to-evacuation recovery: allow transition when new route available; logged as replanning event | research.md §3 |
| CHK055 | Conflict | Merged FR-028/FR-029 into canonical 22-field `EvacuationDecisionRecord` matching monitoring/risk assessment pattern | research.md §1, data-model.md §EvacuationDecisionRecord |
| CHK059 | Clarity | MVP road network: max 1,000 nodes, 5,000 edges; validated on load; supports 30s SLA with ample headroom | research.md §10 |
| CHK063 | Ambiguity | Confidence reduction is multiplicative: `adjusted = confidence × 0.8` | research.md §4 |
| CHK080 | Gap | Duplicate handoff for existing plan: create new version in `proposed` status; do not reject; commander decides | research.md §5 |

## Azure Resources

| Resource | SKU/Tier | Region | Purpose |
|----------|----------|--------|---------|
| Azure Container Apps | Consumption | australiaeast | Agent hosting with auto-scaling on queue depth |
| Azure Cosmos DB | Serverless | australiaeast | Evacuation plans and audit trail (2 containers) |
| Azure OpenAI | Standard (GPT-4o) | australiaeast | Plan summary generation + route rationale |
| Azure Application Insights | Standard | australiaeast | Telemetry, metrics, distributed tracing |
| Azure Service Bus | Standard | australiaeast | Handoff intake queue (from risk assessment) |
| Azure Container Apps (DR) | Consumption | australiasoutheast | DR deployment (LLM fallback to templates) |
| Azure Cosmos DB (DR) | Multi-region write | australiasoutheast | DR replication |

## Implementation Phases

### Phase 1: Core Models and Configuration (Foundation)

- Create `evacuation/__init__.py` package init
- Create `evacuation/config.py` with `EvacuationConfig` class reading all environment variables (same pattern as risk assessment `config.py`) — 21 configurable parameters
- Create `evacuation/models.py` with all Pydantic v2 models:
  - Enums: `DecisionType` (14 values), `ConfidenceLevel`, `PlanStatus`, `VulnerabilityCategory`, `ClosureReason`
  - Embedded models: `EvacuationZone`, `EvacuationRoute`, `ExcludedRoad`, `TransportRequirement`, `EvacuationPhase`, `HazardSummary`, `Traceability`, `OverrideMetadata`, `DataSnapshot`, `AssemblyArea`
  - Primary model: `EvacuationPlan` with validation rules and status transitions
  - Audit model: `EvacuationDecisionRecord` (canonical 22-field schema, append-only)
  - Buffer model: `AuditBufferEntry` for degraded writes
- Write unit tests for all models, enums, and config

### Phase 2: Road Network and Geospatial (Data Layer)

- Create `evacuation/road_network.py` with `RoadNetworkLoader`:
  - JSON parsing with Pydantic validation for nodes, edges, assembly areas
  - Graph construction (adjacency list) from edges
  - Size validation (max 1,000 nodes, 5,000 edges)
  - Edge geometry as Shapely `LineString` objects for zone intersection
  - Road closure status management (apply/remove closures)
- Create `evacuation/zones.py` with `ZoneComputer`:
  - Zone boundary computation from hazard GeoJSON using Shapely `buffer()`
  - Road segment zone membership via `polygon.contains()` / `polygon.intersects()`
  - Multi-hazard zone merging via `shapely.ops.unary_union()`
  - Capacity reduction application (Zone 1: 0%, Zone 2: 50%, Zone 3: 75%)
  - Conservative partial-overlap rule (highest severity applies)
- Create sample road network JSON at `data/road-networks/far-north-qld-sample.json`
- Write unit tests for road network loading, zone computation, multi-hazard merging, edge cases

### Phase 3: Route Computation (Core Algorithm)

- Create `evacuation/router.py` with `RouteComputer`:
  - Dijkstra's algorithm with priority queue (min-heap) on capacity-weighted edges
  - Multi-path distribution: penalise first-path edges and re-run for load balancing
  - Hazard-type-aware routing strategies (bushfire, cyclone, flood, earthquake, tsunami)
  - Congestion risk flagging (>80% utilisation)
  - Vehicle suitability assessment per route (standard, heavy, accessible)
  - Tie-breaking: lower congestion risk, then shorter distance
  - No-route detection → return empty routes for shelter-in-place processing
- Write unit tests for all 5 disaster types, multi-path, closed roads, tie-breaking, no viable routes

### Phase 4: Transport Coordination (Vulnerability)

- Create `evacuation/transport.py` with `TransportCoordinator`:
  - Facility query by zone (aged care, disability care, hospital, school/childcare)
  - `TransportRequirement` generation per facility with category, vehicle type, priority
  - Vehicle estimation using capacity assumptions (bus: 50, wheelchair: 4, ambulance: 2, medical: 6)
  - Missing population data handling (skip coordination, note data gap)
- Write unit tests for all vulnerability categories, vehicle estimation, missing data

### Phase 5: Timeline Estimation and Shelter-in-Place (Decision Logic)

- Create `evacuation/timeline.py` with `TimelineEstimator`:
  - Phase-by-phase timeline computation using clearance_time formula
  - Mobilisation time defaults per hazard type (configurable)
  - 1.5x buffer multiplier for vulnerable populations
  - Phase transition criteria: time-based primary, estimated departure secondary
  - Shelter-in-place decision logic (no viable route + hazard timeline evaluation)
  - Emergency escalation (no route + immediate threat)
  - Clearance time vs hazard arrival window comparison
- Write unit tests for timeline computation, phase transitions, shelter-in-place, emergency escalation, time deficit

### Phase 6: Deduplication, Versioning, and Audit (Resilience)

- Create `evacuation/dedup.py` with `HandoffDeduplicator` (TTL cache, configurable window — same pattern as risk assessment)
- Create `evacuation/versioning.py` with `VersionCounter` (Cosmos DB etag-based OCC — same pattern as risk assessment)
- Create `evacuation/audit.py` with `AuditWriter` class — replicating monitoring/risk assessment three-tier pattern:
  - Tier 1: Cosmos DB `create_item()` (evacuation-decisions container)
  - Tier 2: In-memory ring buffer (10K capacity)
  - Tier 3: File spill (JSONL to configurable path)
  - Recovery flush: memory → file → Cosmos in chronological order
- Write unit tests for dedup edge cases, version counter conflicts, all three audit tiers, recovery flush

### Phase 7: Dynamic Replanning (Responsiveness)

- Create `evacuation/replanner.py` with `DynamicReplanner`:
  - Trigger evaluation for all 5 conditions (FR-016) + shelter-to-evacuation recovery
  - Rate limiting (minimum `REPLAN_RATE_LIMIT_SECONDS` between replans)
  - No-change detection (skip version creation when no material change)
  - Incremental update path (changed edges only → recompute affected routes)
  - Change summary generation (routes changed, assembly areas changed, transport changes, timeline changes, triggering event)
  - Multiple simultaneous trigger handling (merge triggers, single replan)
- Write unit tests for each trigger, rate limiting, no-change detection, simultaneous triggers

### Phase 8: Pipeline Orchestrator and Templates (Integration)

- Create `evacuation/templates.py` with template-based fallback generators:
  - Plan summary template per hazard type
  - Route rationale template
  - Change summary template for replans
- Create `evacuation/pipeline.py` with `EvacuationProcessingPipeline` orchestrating all 10 stages:
  - Wire handoff intake → assessment retrieval → zone computation → road prep → routing → transport → timeline → summary → versioning → audit
  - Wire replanning path (trigger evaluation → incremental update → summary → versioning → audit)
  - Integrate `_generate_with_fallback()` from `LLMCallMixin` for plan summaries
  - Content safety validation on all LLM outputs
- Replace existing `evacuation/agent.py` stub with full `EvacuationAgent` class:
  - Subclass `LLMCallMixin`
  - `process_handoff()` — main pipeline entry point
  - `process_replan()` — replanning entry point
  - Integration with pipeline and all services
- Write integration tests for end-to-end handoff flow, replanning flow

### Phase 9: Health Endpoint and API (Operations)

- Extend `evacuation/agent.py` with FastAPI app factory `create_app()`:
  - `GET /health` — checks per contracts/health-endpoint.md (road_network_loaded, llm_connectivity, cosmos_connectivity, active_plan_count, processing_queue_depth, audit_store)
  - `POST /override` — incident commander plan overrides (approve, reject, cancel, pause, resume, modify)
  - `POST /replan` — manual replanning trigger
- Wire health checks to road network loader, LLM client, Cosmos client, pipeline state, audit writer
- Port 8082 (avoiding monitoring 8080, risk assessment 8081)
- Write contract tests for health response schema, override schemas, replan schemas

### Phase 10: Observability and Telemetry (WAF)

- Add OpenTelemetry instrumentation for distributed tracing (span hierarchy per contracts/telemetry.md)
- Emit all metrics defined in contracts/telemetry.md (processing, safety, transport, zone/population, override, degradation, version, handoff)
- Emit custom events for key decision points (12 event types)
- Configure Application Insights alerting thresholds (12 alert rules)
- Write tests verifying metric emission

### Phase 11: Infrastructure (Deployment)

- Add/update Bicep modules for Cosmos DB containers (evacuation-plans, evacuation-decisions), Service Bus queue, Container Apps scaling rules
- Configure auto-scaling rules based on queue depth
- Add managed identity for Cosmos DB and Service Bus access
- Configure port 8082
- Add Shapely to agent workspace dependencies

## Identified Issues in Existing Code

1. **Stub-only implementation** (`evacuation/agent.py`): The current `EvacuationAgent.review()` returns a hardcoded dict with `scenarioType`, `jurisdictions`, `routePressure`, and a canned recommendation. It has no models, no FastAPI endpoints, no handoff processing, no LLM integration, no audit trail. The entire file must be replaced with the full agent implementation.

## Artifacts Generated

| Artifact | Path | Content |
|----------|------|---------|
| Research | `specs/009-evacuation-agent/research.md` | 10 research decisions resolving CHK unknowns |
| Data Model | `specs/009-evacuation-agent/data-model.md` | 14 entities, relationships, configurable parameters |
| Evacuation Pipeline Contract | `specs/009-evacuation-agent/contracts/evacuation-pipeline.md` | 10-stage pipeline with latency budget (30s initial, 15s replan) |
| Health Endpoint Contract | `specs/009-evacuation-agent/contracts/health-endpoint.md` | GET /health + POST /override + POST /replan schemas |
| Telemetry Contract | `specs/009-evacuation-agent/contracts/telemetry.md` | 30+ metrics, traces, events, 12 alert thresholds |
| Quickstart | `specs/009-evacuation-agent/quickstart.md` | Setup, run, verify instructions |
