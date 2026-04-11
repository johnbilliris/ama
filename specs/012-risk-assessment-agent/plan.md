# Implementation Plan: Risk Assessment Agent — Hazard Prediction, Recommendation Generation, and Multi-Agent Escalation

**Branch**: `012-risk-assessment-agent` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/012-risk-assessment-agent/spec.md`  
**Checklist**: [checklists/requirements.md](checklists/requirements.md) (102 items)

## Summary

The Risk Assessment Agent is the second agent in the disaster response pipeline. It receives `AgentHandoffEvent` messages from the Monitoring Agent containing escalated signals and performs:

1. **Handoff intake and validation** — Pydantic v2 boundary validation with time-bounded idempotency checking and incident existence verification
2. **Signal retrieval and multi-source correlation** — Weighted confidence averaging across authoritative (2×), IoT (1×), and social (0.5×) sources with per-signal freshness integration
3. **Contradiction detection** — Identification of opposing risk trajectories with 30% multiplicative confidence reduction and human review flagging
4. **Versioned hazard assessment generation** — LLM-powered impact predictions with template fallback, AIDR-aligned severity levels, and optimistic concurrency versioning via Cosmos DB etag
5. **Recommendation generation with signal traceability** — Actionable recommendations with mandatory signal ID references in all explanations
6. **Multi-agent downstream escalation** — Handoffs to Communication (confidence ≥ 0.7), Evacuation (severity ≥ high AND confidence ≥ 0.6), and Resource Allocation (coordination-task-based) agents
7. **Reproducible predictions** — Complete input snapshot storage with LLM temperature=0 for semantic equivalence across runs
8. **Append-only audit trail** — Every processing step persisted to Cosmos DB with three-tier degradation (Cosmos → memory buffer → file spill)

**Critical checklist resolutions** incorporated from `checklists/requirements.md`:
- **CHK018/019**: Weighted confidence formula: `Σ(confidence_i × weight_i × freshness_i) / Σ(weight_i × freshness_i)`
- **CHK025/026**: Contradiction reduction is multiplicative: `adjusted = confidence × 0.7`
- **CHK032**: Optimistic concurrency with Cosmos DB etag for version counter documents
- **CHK039**: Penalty order: freshness adjustment → contradiction reduction → fallback penalty
- **CHK048**: Canonical audit fields consolidated from FR-029 and Key Entities
- **CHK063**: All resources in australiaeast (primary) / australiasoutheast (DR)
- **CHK047**: Three-tier audit degradation (same as monitoring agent)
- **CHK056**: AIDR severity alignment is documentation-only, not runtime dependency

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, tenacity  
**Storage**: Azure Cosmos DB (risk-assessments, risk-recommendations, risk-assessment-decisions containers, append-only audit), Azure Service Bus (handoff intake queue)  
**Testing**: pytest (unit, contract, integration, simulation tests — existing test structure)  
**Target Platform**: Linux containers on Azure Container Apps (australiaeast primary, australiasoutheast DR)  
**Project Type**: Agent worker (message-driven microservice with health HTTP endpoint)  
**Performance Goals**: 100 concurrent assessments during peak; 10-second SLA per handoff; 15-second downstream escalation  
**Constraints**: ≤10s p95 assessment latency; ≤1s health endpoint; Australian data residency; append-only audit with infinite retention  
**Scale/Scope**: Multi-instance auto-scaling on queue depth; three downstream consumers (Communication, Evacuation, Resource Allocation agents)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (passed)

| # | Constitution Principle | Requirement | Status | Notes |
|---|----------------------|-------------|--------|-------|
| 1 | **I. Life Safety First** — Safety-critical outputs prioritised | Hazard predictions generated within 10s SLA; high-confidence recommendations trigger escalation to protective-action agents | ✅ PASS | FR-005, SC-001 |
| 2 | **I. Life Safety First** — Human override and emergency stop | Incident commanders can override any recommendation (approve/reject/modify); all overrides immutably logged | ✅ PASS | FR-037, FR-038 |
| 3 | **I. Life Safety First** — Explanations for incident commanders | Assessment summaries include traceable signal IDs, confidence scores, and decision rationale; LLM temperature=0 for reproducibility | ✅ PASS | FR-009, FR-025, FR-026 |
| 4 | **I. Life Safety First** — Safe degradation on low confidence/stale data | Template fallback when LLM unavailable (20% confidence reduction); all-stale signals produce low-confidence assessment with no escalation | ✅ PASS | FR-015, FR-016, FR-031 |
| 5 | **II. Multi-Agent Coordination** — Explicit handoffs with confidence/timestamps | AgentHandoffEvent includes all required fields per common/handoffs.py; escalation thresholds explicitly defined per downstream agent | ✅ PASS | FR-020–024 |
| 6 | **II. Multi-Agent Coordination** — No silent shared state changes | All state changes (assessments, recommendations, handoffs) produce audit records; versions are immutable | ✅ PASS | FR-006, FR-028 |
| 7 | **II. Multi-Agent Coordination** — AIIMS alignment | Agent recommends but does not execute protective actions; `required_approval_level=incident_commander` | ✅ PASS | FR-019 |
| 8 | **III. Data Trust & Provenance** — Provenance metadata carried | Input snapshot stored with each assessment including all signal provenance | ✅ PASS | FR-025 |
| 9 | **III. Data Trust & Provenance** — Authoritative source preference | Weighted averaging with BoM/GA at 2× weight; unverified-source reliance explicitly flagged | ✅ PASS | FR-011, FR-014, CHK018 |
| 10 | **III. Data Trust & Provenance** — Data freshness indicator | Per-signal freshness integrated into weighted confidence formula; stale signals flagged in summary | ✅ PASS | FR-015, FR-016 |
| 11 | **III. Data Trust & Provenance** — Contradiction/suspicious input detection | Opposing risk trajectories detected, flagged, confidence reduced 30%, human review flagged | ✅ PASS | FR-012, FR-013, CHK025 |
| 12 | **III. Data Trust & Provenance** — Versioned, reproducible predictions | Monotonically increasing versions per incident+type with optimistic concurrency; complete input snapshot for reproducibility | ✅ PASS | FR-006, FR-025, FR-026 |
| 13 | **IV. Privacy & Security** — Data minimisation | Only structured assessment data persisted; no raw user content beyond signal metadata | ✅ PASS | FR-025 |
| 14 | **IV. Privacy & Security** — Australian data residency | All Azure resources in australiaeast/australiasoutheast | ✅ PASS | CHK063 |
| 15 | **IV. Privacy & Security** — Tenant isolation | Simulation/live boundaries enforced at all stages; simulation assessments don't trigger live handoffs | ✅ PASS | FR-027 |
| 16 | **IV. Privacy & Security** — Prompt injection protection | System prompts scope LLM role to disaster risk assessment; ContentSafetyValidator on all LLM outputs | ✅ PASS | FR-035, FR-036 |
| 17 | **V. Communication** — Content safety | All LLM outputs validated through ContentSafetyValidator before inclusion in assessments, recommendations, or handoffs | ✅ PASS | FR-035 |
| 18 | **VI. Cloud Platform** — Azure, Australian regions only | ACA, Cosmos DB, Azure OpenAI, App Insights, Service Bus — all australiaeast | ✅ PASS | CHK063 |
| 19 | **NFR** — Resilience to partial outages | Three-tier audit degradation; LLM template fallback; signal store partial unavailability handling | ✅ PASS | FR-031, FR-032, FR-034, CHK047 |
| 20 | **NFR** — Append-only audit trail | RiskAssessmentDecisionRecord in Cosmos DB, no TTL, no updates/deletes | ✅ PASS | FR-029, FR-030 |
| 21 | **NFR** — WAF compliance | Observability via Application Insights; auto-scaling via ACA; security via MI + content safety | ✅ PASS | NFR-001, NFR-002 |

### Post-Design Re-check (passed)

All 21 gates re-evaluated after Phase 1 design — no regressions. Key design decisions that strengthened compliance:
- **Weighted confidence formula** mathematically incorporates source authority and freshness per-signal (gates 9, 10)
- **Multiplicative penalty stacking** (freshness → contradiction → fallback) keeps confidence bounded and each adjustment auditable (gates 4, 11)
- **Optimistic concurrency** for version numbering eliminates race conditions in concurrent processing (gate 12)
- **Three-tier audit degradation** replicates proven monitoring agent pattern (gate 19, 20)

## Project Structure

### Documentation (this feature)

```text
specs/012-risk-assessment-agent/
├── plan.md                            # This file
├── research.md                        # Phase 0 output — 9 research decisions
├── data-model.md                      # Phase 1 output — 7 entities, configurable parameters
├── quickstart.md                      # Phase 1 output — setup, run, verify
├── contracts/                         # Phase 1 output
│   ├── assessment-pipeline.md         # 8-stage pipeline contract with latency budget
│   ├── health-endpoint.md             # GET /health + POST /override contracts
│   └── telemetry.md                   # Metrics, traces, events, alerting thresholds
├── checklists/
│   └── requirements.md                # 102-item requirements quality checklist
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
├── risk_assessment/                           # Risk Assessment Agent (this feature)
│   ├── __init__.py                            # Package init (NEW)
│   ├── agent.py                               # RiskAssessmentAgent class (existing, to be extended)
│   ├── models.py                              # RiskAssessmentDecisionRecord, DecisionType, enums (NEW)
│   ├── config.py                              # RiskAssessmentConfig from environment variables (NEW)
│   ├── audit.py                               # AuditWriter with three-tier degradation (NEW)
│   ├── dedup.py                               # HandoffDeduplicator with TTL cache (NEW)
│   ├── correlation.py                         # Multi-source correlation and contradiction detection (NEW)
│   ├── versioning.py                          # Optimistic concurrency version counter (NEW)
│   ├── severity.py                            # AIDR-aligned severity computation (NEW)
│   ├── pipeline.py                            # AssessmentProcessingPipeline orchestrator (NEW)
│   └── templates.py                           # Template-based fallback text generators (NEW)
└── pyproject.toml                             # Agent workspace deps (existing, add azure-cosmos)

packages/domain/src/domain/models/
├── hazard_assessment.py                       # HazardAssessment domain model (existing, to be extended)
├── recommendation.py                          # Recommendation domain model (existing, to be extended)
└── signal.py                                  # Signal domain model (existing, consumed)

tests/
├── unit/
│   ├── test_risk_assessment_models.py         # Model validation tests (NEW)
│   ├── test_risk_assessment_config.py         # Config loading tests (NEW)
│   ├── test_risk_assessment_correlation.py    # Weighted averaging, contradiction detection (NEW)
│   ├── test_risk_assessment_severity.py       # AIDR severity computation (NEW)
│   ├── test_risk_assessment_versioning.py     # Optimistic concurrency (NEW)
│   ├── test_risk_assessment_dedup.py          # Handoff deduplication (NEW)
│   ├── test_risk_assessment_audit.py          # Audit writer degradation (NEW)
│   └── test_risk_assessment_pipeline.py       # Pipeline stage unit tests (NEW)
├── contract/
│   ├── test_risk_assessment_escalation.py     # Escalation threshold contract tests (NEW)
│   ├── test_risk_assessment_handoff.py        # Handoff structure contract tests (NEW)
│   └── test_risk_assessment_reproducibility.py # Reproducibility contract tests (NEW)
├── integration/
│   ├── test_risk_assessment_cosmos.py         # Cosmos DB persistence integration (NEW)
│   └── test_risk_assessment_service_bus.py    # Service Bus handoff intake integration (NEW)
└── simulation/
    └── test_bushfire_scenario.py              # Bushfire scenario simulation (existing, extend with risk assessment)
```

**Structure Decision**: Follows the existing multi-agent workspace pattern under `apps/agents/`. New modules are added within `apps/agents/risk_assessment/` following the monitoring agent's separation of concerns (agent logic, models, config, services, pipeline). The Risk Assessment Agent does not introduce a new top-level package — it extends the existing `risk_assessment/` package. Test files follow the existing test directory structure.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Three-tier audit degradation (memory + file + Cosmos) | Constitution mandates unbroken audit trail even during infrastructure failures; CHK047 explicitly identifies this as a conflict between FR-034 and FR-028/029 | Single-tier (Cosmos-only) would silently lose audit records during Cosmos outages, violating constitutional NFRs |
| Optimistic concurrency with version counter docs | FR-006 mandates monotonically increasing versions under concurrent processing; CHK032 explicitly identifies this race condition | Simple increment-on-write could produce duplicate version numbers when two handoffs for the same incident arrive simultaneously |
| Multiplicative penalty stacking (3 adjustments) | CHK039 identifies ambiguous penalty ordering; Constitution requires transparent, auditable confidence adjustments | Single combined penalty would lose individual adjustment visibility in the audit trail |
| Weighted confidence formula (per-signal freshness integration) | Constitution Principle III mandates freshness consideration; CHK018/019 identify unspecified aggregation method | Simple averaging without weights would violate authoritative-source preference mandate |

## Checklist Resolution Summary

| Checklist Item | Category | Resolution | Reference |
|----------------|----------|------------|-----------|
| CHK002 | Clarity | Confidence formula: `Σ(conf × weight × fresh) / Σ(weight × fresh)` with configurable weights | research.md §1 |
| CHK003 | Ambiguity | Boundary: low <0.4, medium [0.4, 0.7), high ≥0.7 — boundaries inclusive at lower end | data-model.md §HazardAssessment |
| CHK009 | Ambiguity | 10-second SLA measured from handoff receipt to assessment persistence; signal retrieval included | contracts/assessment-pipeline.md |
| CHK018 | Clarity | Weights are configurable defaults via environment variables, not fixed constants | research.md §1, data-model.md §Parameters |
| CHK019 | Ambiguity | Weighted mean formula explicitly defined with freshness integration | research.md §1 |
| CHK025 | Clarity | Opposing risk trajectories: one signal increasing, one decreasing for same hazard parameter | research.md §2 |
| CHK026 | Ambiguity | Multiplicative: `adjusted = confidence × 0.7` | research.md §2 |
| CHK027 | Coverage | Single 30% reduction regardless of contradiction count; each pair individually audited | research.md §2 |
| CHK032 | Edge Case | Optimistic concurrency via Cosmos DB etag on version counter document; retry with jitter | research.md §3 |
| CHK039 | Ambiguity | Order: freshness (in averaging) → contradiction (×0.7) → fallback (×0.8) | research.md §4 |
| CHK047 | Conflict | Three-tier audit degradation resolves FR-034 vs FR-028 conflict | research.md §8 |
| CHK048 | Consistency | Canonical 22-field audit record schema consolidated | research.md §5, data-model.md §DecisionRecord |
| CHK056 | Traceability | AIDR Handbook Collection reference — documentation-only, no runtime dependency | research.md §7 |
| CHK063 | Gap | australiaeast (primary) / australiasoutheast (DR) — same as monitoring agent | research.md §6 |
| CHK066 | Gap | Azure OpenAI confirmed in australiaeast; DR uses rule-based fallback | research.md §6 |

## Azure Resources

| Resource | SKU/Tier | Region | Purpose |
|----------|----------|--------|---------|
| Azure Container Apps | Consumption | australiaeast | Agent hosting with auto-scaling on queue depth |
| Azure Cosmos DB | Serverless | australiaeast | Assessments, recommendations, audit trail (3 containers) |
| Azure OpenAI | Standard (GPT-4o) | australiaeast | Hazard summary generation + recommendation explanations |
| Azure Application Insights | Standard | australiaeast | Telemetry, metrics, distributed tracing |
| Azure Service Bus | Standard | australiaeast | Handoff intake queue (from monitoring) + downstream delivery |
| Azure Container Apps (DR) | Consumption | australiasoutheast | DR deployment (LLM fallback to templates) |
| Azure Cosmos DB (DR) | Multi-region write | australiasoutheast | DR replication |

## Implementation Phases

### Phase 1: Core Models and Configuration (Foundation)

- Create `risk_assessment/config.py` with `RiskAssessmentConfig` class reading all environment variables (same pattern as monitoring `config.py`)
- Create `risk_assessment/models.py` with `RiskAssessmentDecisionRecord`, `DecisionType` enum (12 values), severity/confidence enums
- Extend `packages/domain/src/domain/models/hazard_assessment.py` with new fields: `version`, `confidence_score`, `confidence_adjusted`, `severity_level`, `valid_until`, `status`, `generation_method`, `input_snapshot`, `contradiction_detected`, `configuration_version`, `incident_scope_key`, `tenant_id`
- Extend `packages/domain/src/domain/models/recommendation.py` with new fields: `assessment_id`, `confidence_score`, `severity_level`, `override_*` fields
- Write unit tests for all models and config

### Phase 2: Deduplication and Signal Correlation (Services)

- Create `risk_assessment/dedup.py` with `HandoffDeduplicator` (TTL cache, configurable window — same pattern as monitoring `dedup.py`)
- Create `risk_assessment/correlation.py` with `SignalCorrelator`: weighted confidence averaging formula, stale signal flagging, source diversity analysis
- Create `risk_assessment/correlation.py` (continued) with `ContradictionDetector`: opposing risk trajectory detection, 30% multiplicative reduction, audit recording
- Write unit tests for dedup edge cases, weighted averaging with various source mixes, contradiction detection with 2+ signal scenarios

### Phase 3: Severity and Versioning (Services)

- Create `risk_assessment/severity.py` with `SeverityComputer`: signal-category-to-severity mapping, population-adjusted severity, fallback severity mapping, one-level downgrade logic
- Create `risk_assessment/versioning.py` with `VersionCounter`: Cosmos DB etag-based optimistic concurrency, counter document pattern, conflict retry with jitter
- Write unit tests for severity computation (all 5 disaster types), version counter conflict scenarios

### Phase 4: Audit Writer with Degradation (Resilience)

- Create `risk_assessment/audit.py` with `AuditWriter` class — replicating monitoring agent's three-tier pattern
- Implement primary Cosmos DB write path (risk-assessment-decisions container)
- Implement secondary in-memory ring buffer (10K capacity)
- Implement tertiary file spill (JSONL to configurable path)
- Implement recovery flush (memory → file → Cosmos in chronological order)
- Write unit tests for all three tiers and recovery

### Phase 5: Assessment and Recommendation Generation (Core Logic)

- Create `risk_assessment/templates.py` with template-based fallback generators (signal-ID-inclusive templates per assessment type and recommendation type)
- Extend `risk_assessment/agent.py` with full assessment generation pipeline:
  - Signal retrieval from signal store
  - Multi-source correlation (weighted averaging)
  - Contradiction detection
  - LLM summary generation with content safety and template fallback
  - Version assignment with optimistic concurrency
  - Severity computation
  - Assessment persistence
- Extend recommendation generation beyond `recommend_public_alert` to support all 5 recommendation types
- Enforce signal ID traceability in all explanations (append missing IDs)
- Write unit and contract tests for assessment and recommendation generation

### Phase 6: Pipeline Orchestrator (Integration)

- Create `risk_assessment/pipeline.py` with `AssessmentProcessingPipeline` orchestrating all 8 stages
- Wire up handoff intake validation, dedup, signal retrieval, correlation, contradiction detection, assessment generation, recommendation generation, downstream escalation, audit recording
- Implement escalation logic for all three downstream agents with threshold checks
- Wire up handoff delivery with retry via `deliver_handoff_with_retry`
- Write integration tests for end-to-end handoff flow

### Phase 7: Health Endpoint and API (Operations)

- Extend `risk_assessment/agent.py` with FastAPI app (health endpoint, override endpoint)
- Wire health checks to LLM connectivity, signal store, queue depth, audit store status
- Implement `POST /override` for incident commander recommendation overrides
- Write contract tests for health response and override schemas

### Phase 8: Observability and Telemetry (WAF)

- Add OpenTelemetry instrumentation for distributed tracing (span hierarchy per contracts/telemetry.md)
- Emit all metrics defined in contracts/telemetry.md (processing, escalation, quality, degradation, version)
- Emit custom events for key decision points
- Configure Application Insights alerting thresholds
- Write tests verifying metric emission

### Phase 9: Infrastructure (Deployment)

- Add/update Bicep modules for Cosmos DB containers (risk-assessments, risk-recommendations, risk-assessment-decisions), Service Bus queue, Container Apps scaling rules
- Configure auto-scaling rules based on queue depth
- Add managed identity for Cosmos DB and Service Bus access
- Configure port 8081 (avoiding monitoring agent's 8080)

## Identified Issues in Existing Code

1. **Hardcoded confidence in handoff** (`risk_assessment/agent.py:62`): `build_communication_handoff` uses hardcoded `confidence=0.9` instead of deriving from the recommendation's actual confidence score. Must use `recommendation.confidence_score` or the assessment's adjusted confidence.

2. **Missing numeric confidence** (`risk_assessment/agent.py:49`): `build_communication_handoff` checks `recommendation.confidence_level != "high"` (categorical) but FR-020 specifies a numeric threshold `≥ 0.7`. Must compare against the numeric `confidence_score` field.

3. **Incomplete recommendation fields** (`risk_assessment/agent.py:32–44`): `recommend_public_alert` doesn't set `assessment_id`, `confidence_score` (numeric), or `severity_level`. These are required by the extended Recommendation model.

4. **Single recommendation type only** (`risk_assessment/agent.py`): Only `recommend_public_alert` exists. Must add generators for `evacuation`, `resource_allocation`, `coordination`, and `infrastructure_action` types.

5. **No signal retrieval or correlation** (`risk_assessment/agent.py`): Current implementation receives signal_ids as parameters but doesn't retrieve actual Signal objects from the signal store, perform weighted correlation, or detect contradictions.

## Artifacts Generated

| Artifact | Path | Content |
|----------|------|---------|
| Research | `specs/012-risk-assessment-agent/research.md` | 9 research decisions resolving CHK unknowns |
| Data Model | `specs/012-risk-assessment-agent/data-model.md` | 7 entities, relationships, configurable parameters |
| Assessment Pipeline Contract | `specs/012-risk-assessment-agent/contracts/assessment-pipeline.md` | 8-stage pipeline with latency budget |
| Health Endpoint Contract | `specs/012-risk-assessment-agent/contracts/health-endpoint.md` | GET /health + POST /override schemas |
| Telemetry Contract | `specs/012-risk-assessment-agent/contracts/telemetry.md` | 20 metrics, traces, events, alert thresholds |
| Quickstart | `specs/012-risk-assessment-agent/quickstart.md` | Setup, run, verify instructions |
