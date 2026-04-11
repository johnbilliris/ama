# Implementation Plan: Monitoring Agent — Signal Triage, Misinformation Detection, and Escalation

**Branch**: `010-monitoring-agent` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/010-monitoring-agent/spec.md`  
**Checklist**: [checklists/requirements.md](checklists/requirements.md) (74 items)

## Summary

The Monitoring Agent is the first agent in the disaster response pipeline. It receives normalised `SignalEnvelope` messages from ingestion pipelines via Azure Service Bus and performs:

1. **Input validation and deduplication** — Pydantic v2 boundary validation with time-bounded idempotency checking
2. **LLM-powered misinformation detection** — Tier 2 evaluation on escalated signals with async timeout (3s) and fail-safe-CLOSED policy
3. **Signal summarisation with content safety** — LLM-enriched summaries validated through `ContentSafetyValidator`, with rule-based fallback
4. **Confidence-based triage and escalation** — Using `effectiveConfidence = confidenceScore × freshnessScore` with configurable threshold (default 0.8), producing `AgentHandoffEvent` handoffs to Risk Assessment
5. **Retrospective incident association** — Linking unassociated signals to newly declared incidents within a configurable lookback window
6. **Data freshness tracking** — Per-source health monitoring with healthy/degraded/offline status transitions
7. **Append-only audit trail** — Every decision persisted to Cosmos DB with three-tier degradation (Cosmos → memory buffer → file spill)

**Critical checklist resolutions** incorporated from `checklists/requirements.md`:
- **CHK030**: 5-second SLA uses async LLM with 3-second timeout; held for review on timeout
- **CHK070**: `effectiveConfidence = confidenceScore × freshnessScore` replaces raw confidence in escalation gate
- **CHK040**: Three-tier audit degradation: Cosmos → in-memory buffer (10K) → local file spill
- **CHK066**: Fail-safe-CLOSED for misinformation (hold for review, not auto-escalate)

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, tenacity  
**Storage**: Azure Cosmos DB (monitoring-decisions container, append-only audit), Azure Service Bus (signal intake queue)  
**Testing**: pytest (unit, contract, integration, simulation tests — existing test structure)  
**Target Platform**: Linux containers on Azure Container Apps (australiaeast primary, australiasoutheast DR)  
**Project Type**: Agent worker (message-driven microservice with health HTTP endpoint)  
**Performance Goals**: 1,000 signals/minute sustained throughput; 5-second SLA for high-risk escalation path  
**Constraints**: ≤5s p95 escalation latency; ≤1s health endpoint response; Australian data residency; append-only audit with infinite retention  
**Scale/Scope**: Multi-instance auto-scaling on queue depth; single downstream consumer (Risk Assessment Agent)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (passed)

| # | Constitution Principle | Requirement | Status | Notes |
|---|----------------------|-------------|--------|-------|
| 1 | **I. Life Safety First** — Safety-critical outputs prioritised | High-risk signals escalate within 5s SLA; fail-safe-CLOSED blocks uncertain signals | ✅ PASS | CHK066 resolved: fail-safe-closed for misinformation |
| 2 | **I. Life Safety First** — Human override and emergency stop | Escalated signals held for human review when LLM unavailable/timeout | ✅ PASS | FR-006 satisfied |
| 3 | **I. Life Safety First** — Explanations for incident commanders | Audit records include reasoning_summary, inputs, outputs, confidence | ✅ PASS | FR-021 |
| 4 | **I. Life Safety First** — Safe degradation on low confidence/stale data | effectiveConfidence incorporates freshness; rule-based fallback when LLM down | ✅ PASS | CHK070 resolved |
| 5 | **II. Multi-Agent Coordination** — Explicit handoffs with confidence/timestamps | AgentHandoffEvent includes all required fields per common/handoffs.py | ✅ PASS | FR-010, FR-011 |
| 6 | **II. Multi-Agent Coordination** — No silent shared state changes | All state changes produce audit records | ✅ PASS | FR-020 |
| 7 | **II. Multi-Agent Coordination** — AIIMS alignment | Agent does not replace incident management governance; recommendations only | ✅ PASS | Read-only triage |
| 8 | **III. Data Trust & Provenance** — Provenance metadata carried | Every signal retains provenance from ingestion pipeline | ✅ PASS | FR-019 |
| 9 | **III. Data Trust & Provenance** — Authoritative source preference | Escalation categories include BoM (weather) and Geoscience Australia (earthquake, tsunami) | ✅ PASS | FR-009 |
| 10 | **III. Data Trust & Provenance** — Data freshness indicator | DataFreshnessIndicator with per-source thresholds and status transitions | ✅ PASS | FR-017, FR-018 |
| 11 | **III. Data Trust & Provenance** — Misinformation detection | Tier 2 LLM evaluation on escalated signals with fail-safe-closed | ✅ PASS | FR-004–FR-008 |
| 12 | **IV. Privacy & Security** — Data minimisation | Only structured classification fields in summaries; no raw user content | ✅ PASS | FR-003, FR-026 |
| 13 | **IV. Privacy & Security** — Australian data residency | All Azure resources in australiaeast/australiasoutheast | ✅ PASS | NFR-004 |
| 14 | **IV. Privacy & Security** — Tenant isolation | Simulation/live boundaries enforced at all stages | ✅ PASS | FR-015 |
| 15 | **IV. Privacy & Security** — Prompt injection protection | System prompts scope LLM role; ContentSafetyValidator on outputs | ✅ PASS | FR-027, FR-028 |
| 16 | **V. Communication** — Content safety | All LLM outputs validated through ContentSafetyValidator before propagation | ✅ PASS | FR-028 |
| 17 | **VI. Cloud Platform** — Azure, Australian regions only | ACA, Cosmos DB, Azure OpenAI, App Insights, Service Bus — all australiaeast | ✅ PASS | NFR-004 |
| 18 | **NFR** — Resilience to partial outages | Three-tier audit degradation; rule-based LLM fallback; source-level degradation | ✅ PASS | CHK040 resolved |
| 19 | **NFR** — Append-only audit trail | MonitoringDecisionRecord in Cosmos DB, no TTL, no updates/deletes | ✅ PASS | FR-022 |
| 20 | **NFR** — WAF compliance | Observability via Application Insights; auto-scaling via ACA; security via MI + content safety | ✅ PASS | NFR-001–003 |

### Post-Design Re-check (passed)

All 20 gates re-evaluated after Phase 1 design — no regressions. Key design decisions that strengthened compliance:
- **effectiveConfidence** formula ensures freshness is mathematically incorporated (gate 4, 10)
- **Fail-safe-CLOSED** ensures suspicious signals don't bypass human review (gate 1, 11)
- **Three-tier audit degradation** ensures audit continuity during infrastructure failures (gate 18, 19)

## Project Structure

### Documentation (this feature)

```text
specs/010-monitoring-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output — 9 research decisions
├── data-model.md        # Phase 1 output — 5 entities, configurable parameters
├── quickstart.md        # Phase 1 output — setup, run, verify
├── contracts/           # Phase 1 output
│   ├── signal-processing.md   # 6-stage pipeline contract with latency budget
│   ├── health-endpoint.md     # GET /health + POST /associate contracts
│   └── telemetry.md           # Metrics, traces, events, alerting thresholds
├── checklists/
│   └── requirements.md        # 74-item requirements quality checklist
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/agents/
├── common/                           # Shared agent infrastructure (existing)
│   ├── content_safety.py             # ContentSafetyValidator (existing)
│   ├── handoffs.py                   # AgentHandoffEvent, build_handoff, deliver_with_retry (existing)
│   ├── llm_client.py                 # LLMClient wrapping Azure OpenAI (existing)
│   ├── llm_mixin.py                  # LLMCallMixin with fallback (existing)
│   └── dependency_notifier.py        # Dependency health notification (existing)
├── monitoring/                       # Monitoring Agent (this feature)
│   ├── __init__.py                   # Package init (existing)
│   ├── agent.py                      # MonitoringAgent class (existing, to be extended)
│   ├── models.py                     # MonitoringDecisionRecord, DataFreshnessIndicator, DecisionType (NEW)
│   ├── audit.py                      # AuditWriter with three-tier degradation (NEW)
│   ├── freshness.py                  # DataFreshnessTracker service (NEW)
│   ├── dedup.py                      # SignalDeduplicator with TTL cache (NEW)
│   ├── pipeline.py                   # SignalProcessingPipeline orchestrator (NEW)
│   └── config.py                     # MonitoringConfig from environment variables (NEW)
└── pyproject.toml                    # Agent workspace deps (existing, add azure-cosmos)

packages/domain/src/domain/models/
└── signal.py                         # Signal domain model (existing, consumed)

apps/api/app/validators/
└── signal_envelope.py                # SignalEnvelope Pydantic model (existing, consumed)

tests/
├── unit/
│   ├── test_monitoring_pipeline.py           # Pipeline stage unit tests (NEW)
│   ├── test_monitoring_models.py             # Model validation tests (NEW)
│   ├── test_monitoring_dedup.py              # Deduplication tests (NEW)
│   ├── test_monitoring_freshness.py          # Freshness tracker tests (NEW)
│   └── test_monitoring_audit.py              # Audit writer degradation tests (NEW)
├── contract/
│   ├── test_misinformation_detector.py       # Misinformation contract tests (existing, extend)
│   ├── test_incident_association.py          # Association contract tests (existing, extend)
│   └── test_monitoring_escalation.py         # Escalation contract tests (NEW)
├── integration/
│   ├── test_handoff_retry.py                 # Handoff retry integration (existing)
│   ├── test_monitoring_cosmos_audit.py       # Cosmos DB audit write integration (NEW)
│   └── test_monitoring_service_bus.py        # Service Bus signal intake integration (NEW)
└── simulation/
    └── test_bushfire_scenario.py              # Bushfire scenario simulation (existing, extend)
```

**Structure Decision**: Follows the existing multi-agent workspace pattern under `apps/agents/`. New modules are added within `apps/agents/monitoring/` following the separation of concerns already established in the codebase (agent logic, models, services). The Monitoring Agent does not introduce a new top-level package — it extends the existing `monitoring/` package. Test files follow the existing test directory structure (`tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/simulation/`).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Three-tier audit degradation (memory + file + Cosmos) | Constitution mandates unbroken audit trail even during infrastructure failures; CHK040 explicitly identifies this gap | Single-tier (Cosmos-only) would silently lose audit records during Cosmos outages, violating constitutional NFRs |
| effectiveConfidence formula (multiplicative) | CHK070 identifies misalignment between FR-009 (checks raw confidence) and FR-017/FR-023 (mandate freshness consideration) | Separate freshness gate would not capture the interaction between confidence and freshness in a single testable threshold |
| Fail-safe-CLOSED for LLM misinformation | CHK066 identifies conflict between fail-safe-open (spec) and life-safety-first (constitution) | Fail-safe-open is simpler but violates Constitution Principle I — potential misinformation reaching downstream agents could endanger lives |

## Checklist Resolution Summary

The following table maps critical checklist items to their resolution in this plan:

| Checklist Item | Category | Resolution | Reference |
|----------------|----------|------------|-----------|
| CHK001 | Completeness | Pydantic validation at agent boundary; reject invalid signals with audit record | research.md §7, data-model.md |
| CHK002 | Completeness | Deferred — v1 uses FIFO ordering; priority queuing is a future enhancement | — |
| CHK003 | Completeness | LLM timeout (3s) with async evaluation; no separate concurrency limit for v1 | research.md §1 |
| CHK007 | Completeness | Composite partition key `{tenant_id}:{incident_id}` with synthetic suffix for hot partition mitigation | research.md §6 |
| CHK008 | Completeness | No TTL per spec; archival strategy deferred to future iteration | — |
| CHK016 | Clarity | Proportional reduction resolved via multiplicative formula: `effectiveConfidence = confidenceScore × freshnessScore` | research.md §2 |
| CHK024 | Clarity | In-memory TTL set per instance + Service Bus session affinity | research.md §8 |
| CHK027 | Consistency | "Suspicious" classification applies 0.15 confidence penalty (differential from "credible") | research.md §4 |
| CHK030 | Conflict | Async LLM with 3-second timeout; hold for review on timeout | research.md §1 |
| CHK031 | Conflict | Fail-safe-CLOSED resolves the conflict — uncertain signals do not bypass content safety | research.md §4 |
| CHK040 | Coverage | Three-tier degradation: Cosmos → 10K memory buffer → local file spill → recovery flush | research.md §3 |
| CHK044 | Coverage | Startup-only config via environment variables; hot-reload deferred to v2 | research.md §9 |
| CHK060 | Assumption | Azure OpenAI confirmed available in australiaeast; DR uses rule-based fallback | research.md §5 |
| CHK066 | Conflict | Fail-safe-CLOSED for misinformation detection (hold, not pass-through) | research.md §4 |
| CHK070 | Conflict | effectiveConfidence formula aligns FR-009 with FR-017/FR-023 | research.md §2 |
| CHK073 | Hygiene | Consolidated configurable parameters table in data-model.md | data-model.md §Parameters |

## Azure Resources

| Resource | SKU/Tier | Region | Purpose |
|----------|----------|--------|---------|
| Azure Container Apps | Consumption | australiaeast | Agent hosting with auto-scaling |
| Azure Cosmos DB | Serverless | australiaeast | Audit trail (monitoring-decisions container) |
| Azure OpenAI | Standard (GPT-4o) | australiaeast | Misinformation detection + signal summarisation |
| Azure Application Insights | Standard | australiaeast | Telemetry, metrics, distributed tracing |
| Azure Service Bus | Standard | australiaeast | Signal intake queue + session-based delivery |
| Azure Container Apps (DR) | Consumption | australiasoutheast | DR deployment |
| Azure Cosmos DB (DR) | Multi-region write | australiasoutheast | DR replication |

## Implementation Phases

### Phase 1: Core Models and Configuration (Foundation)

- Create `monitoring/config.py` with `MonitoringConfig` class reading all environment variables
- Create `monitoring/models.py` with `MonitoringDecisionRecord`, `DataFreshnessIndicator`, `DecisionType` enum
- Add `signal_id` field to `SignalEnvelope` (or wrap in a processing context)
- Extend Pydantic validation on `SignalEnvelope` at agent boundary
- Write unit tests for all models and config

### Phase 2: Deduplication and Freshness (Services)

- Create `monitoring/dedup.py` with `SignalDeduplicator` (TTL cache, configurable window)
- Create `monitoring/freshness.py` with `DataFreshnessTracker` (per-source status, transitions)
- Write unit tests for dedup edge cases (window boundary, cache eviction)
- Write unit tests for freshness transitions (healthy→degraded→offline→healthy)

### Phase 3: Audit Writer with Degradation (Resilience)

- Create `monitoring/audit.py` with `AuditWriter` class
- Implement primary Cosmos DB write path
- Implement secondary in-memory ring buffer (10K capacity)
- Implement tertiary file spill (JSONL)
- Implement recovery flush (memory → Cosmos, file → Cosmos)
- Write unit tests for all three tiers and recovery
- Write integration test against Cosmos DB emulator

### Phase 4: Misinformation Detection Enhancement (Safety)

- Update `_evaluate_escalated_signal()` with async timeout (3s)
- Implement fail-safe-CLOSED: hold on timeout/unexpected response
- Implement "suspicious" confidence penalty
- Fix LLM client call signature (currently mismatched: `system_prompt`/`user_prompt` vs `purpose`/`prompt`)
- Write contract tests for all classification outcomes

### Phase 5: Pipeline Orchestrator (Integration)

- Create `monitoring/pipeline.py` with `SignalProcessingPipeline` orchestrating all 6 stages
- Wire up effectiveConfidence computation in triage stage
- Add `earthquake` and `tsunami` to escalation categories (currently missing)
- Wire up audit recording at each decision point
- Wire up telemetry emission (metrics + traces)
- Write integration tests for end-to-end signal flow

### Phase 6: Health Endpoint and API Enhancement (Operations)

- Replace simple `/health` handler with FastAPI app returning structured health response
- Add `POST /associate` endpoint for retrospective association
- Wire health checks to LLM connectivity, freshness status, queue depth, audit store status
- Write contract tests for health response schema

### Phase 7: Observability and Telemetry (WAF)

- Add OpenTelemetry instrumentation for distributed tracing
- Emit all metrics defined in contracts/telemetry.md
- Emit custom events for key decision points
- Configure Application Insights alerting thresholds
- Write tests verifying metric emission

### Phase 8: Infrastructure (Deployment)

- Add/update Bicep modules for Cosmos DB container, Service Bus queue, Container Apps scaling rules
- Configure auto-scaling rules based on queue depth
- Add managed identity for Cosmos DB and Service Bus access
- Update `infra/bicep/monitoring.bicep` with new resources

## Identified Bugs in Existing Code

1. **LLM client signature mismatch** (`agent.py:82–85`): `_evaluate_escalated_signal()` calls `self._llm_client.generate_response(system_prompt=..., user_prompt=...)` but `LLMClient.generate_response()` expects `purpose` and `prompt` parameters. Must fix to use `purpose="reasoning"` and `prompt=` with the combined prompt text.

2. **Missing escalation categories** (`agent.py:52`): Only checks `{fire, weather, hydrology}` but spec requires `{fire, weather, hydrology, earthquake, tsunami}`. Must add `earthquake` and `tsunami` to the category set.

3. **No effectiveConfidence computation** (`agent.py:53`): Uses raw `confidenceScore` without incorporating `freshnessScore`. Must multiply by `freshnessScore` per the effectiveConfidence formula.

## Artifacts Generated

| Artifact | Path | Content |
|----------|------|---------|
| Research | `specs/010-monitoring-agent/research.md` | 9 research decisions resolving CHK unknowns |
| Data Model | `specs/010-monitoring-agent/data-model.md` | 5 entities, relationships, configurable parameters |
| Signal Processing Contract | `specs/010-monitoring-agent/contracts/signal-processing.md` | 6-stage pipeline with latency budget |
| Health Endpoint Contract | `specs/010-monitoring-agent/contracts/health-endpoint.md` | GET /health + POST /associate schemas |
| Telemetry Contract | `specs/010-monitoring-agent/contracts/telemetry.md` | 13 metrics, traces, events, alert thresholds |
| Quickstart | `specs/010-monitoring-agent/quickstart.md` | Setup, run, verify instructions |
