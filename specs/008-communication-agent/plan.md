# Implementation Plan: Communication Agent — Multilingual Alert Generation, Content Safety, AIIMS Approval, and Multi-Channel Public Dissemination

**Branch**: `008-communication-agent` | **Date**: 2026-04-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-communication-agent/spec.md`
**Checklist**: [checklists/communication-agent.md](checklists/communication-agent.md) (72 items, 7 critical resolutions)

## Summary

The Communication Agent is the fifth and final agent in the disaster response pipeline. It receives `AgentHandoffEvent` messages from the Risk Assessment Agent containing `public_alert` recommendations, and performs:

1. **Handoff intake and validation** — Pydantic v2 boundary validation with TTL-based idempotency checking (30-minute window), incident existence verification, and dual deduplication (handoff ID + incident/hazard combination)
2. **Multilingual alert drafting** — LLM-enhanced text generation in six languages (en-AU, zh-Hans, ar, vi, el, it) with template-based fallback; en-AU generated first as reference; back-translation quality validation (cosine similarity ≥ 0.85); content safety validation on all LLM-generated text
3. **Content safety validation** — All LLM-generated content passes through `ContentSafetyValidator` before approval queue; pre-approved static templates exempt from runtime validation; per-language fallback to templates on failure; blocked keywords, language detection, length enforcement (1,200 chars)
4. **AIIMS-aligned approval workflow** — All alerts enter `pending_review`; commander approves/rejects/modifies via POST endpoints; auto-escalation at 15 minutes (configurable); max 3 escalation levels; NEVER auto-approve; approval notification via Service Bus `commander-approval-queue`
5. **Audience segmentation** — Three-dimensional: geographic zone (from evacuation agent polygons), vulnerability (aged care, hospitals, schools), language preference (from demographic data); vulnerable populations delivered first with `priority=critical`; overlapping segments deduplicated at delivery (highest-priority wins)
6. **Multi-channel delivery** — SMS (Azure Communication Services, multi-part up to 612 chars/4 segments), push (Azure Notification Hubs), emergency broadcast (EAS webhook, en-AU only); per-channel independent retry (3×, exponential backoff 1s/2s/4s); delivery receipts per channel per segment
7. **Alert versioning** — Format `ca-{incident_id}-v{N}` with optimistic concurrency (Cosmos DB etag); immutable versions; change types: initial, update, correction, all_clear; `superseded` vs `expired` as independent states (expired = 24h TTL configurable)
8. **Append-only audit trail** — Every processing step persisted with three-tier degradation (Cosmos → memory buffer → JSONL file spill); 100% reconcilable via handoff-to-audit correlation

**Critical checklist resolutions** incorporated from `checklists/communication-agent.md`:
- **CHK034**: SMS 612 chars = multi-part concatenated SMS (4 segments). Log segment count in delivery record
- **CHK031**: Compound confidence penalties stack multiplicatively in order: freshness → back-translation (0.9×) → LLM fallback (0.8×)
- **CHK019**: Max 3 escalation levels. If no commander after 3 levels, hold alert with CRITICAL priority flag for next available commander. NEVER auto-approve
- **CHK014/CHK068**: Templates version-controlled in git at `data/alert-templates/`. Changes require PR review. No runtime governance
- **CHK008**: Missing template file for a language → fall back to en-AU with "[Translation unavailable]" note
- **CHK024**: `superseded` = replaced by newer version. `expired` = time-based TTL (24h default, configurable). Independent states
- **CHK035**: SLA arithmetic: 20s draft + 5s approval notification + 10s delivery = 35s pipeline. 60s end-to-end includes 25s buffer for queue/processing overhead
- **CHK041**: Overlapping segments deduplicated at delivery — each recipient gets ONE alert per channel (highest-priority segment wins)
- **CHK051**: Embedding service outage → skip back-translation check, use template translation, log degradation decision
- **CHK059**: Commander identity validated via JWT claims (role=commander). RBAC deferred to v2
- **CHK062**: Auto-scaling: scale out on queue depth > 10, scale in when < 3 for 5 minutes

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, Pydantic v2, openai (Azure OpenAI SDK), azure-identity, azure-monitor-opentelemetry, azure-cosmos, azure-servicebus, azure-communication-sms, azure-notificationhubs, tenacity, numpy (cosine similarity for back-translation)
**Storage**: Azure Cosmos DB (public-alerts, communication-decisions, delivery-records containers, append-only audit), Azure Service Bus (communication-handoffs intake queue, commander-approval-queue)
**Testing**: pytest (unit, contract, integration, simulation tests — existing test structure)
**Target Platform**: Linux containers on Azure Container Apps (australiaeast primary, australiasoutheast DR)
**Project Type**: Agent worker (message-driven microservice with health HTTP endpoint + approval API endpoints)
**Performance Goals**: 50 concurrent alert drafting operations during peak; 20-second SLA for alert drafting (6 languages + back-translation); 5-second approval notification; 10-second delivery initiation; 60-second end-to-end (excluding approval wait)
**Constraints**: ≤20s p95 drafting latency; ≤60s p95 end-to-end (excl. approval); ≤1s health endpoint; Australian data residency; append-only audit with infinite retention; SMS multi-part ≤ 612 chars (4 segments)
**Scale/Scope**: Multi-instance auto-scaling on queue depth (scale-out > 10, scale-in < 3 for 5 min); single upstream consumer (Risk Assessment Agent); downstream: incident commander dashboard, public via SMS/push/broadcast

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (passed)

| # | Constitution Principle | Requirement | Status | Notes |
|---|----------------------|-------------|--------|-------|
| 1 | **I. Life Safety First** — Safety-critical outputs prioritised | Alerts drafted within 20s SLA; vulnerable populations delivered first with `priority=critical`; structured actionable format (what/where/when/do/help) | ✅ PASS | FR-007, FR-024, SC-001 |
| 2 | **I. Life Safety First** — Human override and emergency stop | All alerts require commander approval before delivery; commanders can approve, reject, or modify; no auto-approve even after escalation chain exhausted (CHK019) | ✅ PASS | FR-019, FR-020, FR-042 |
| 3 | **I. Life Safety First** — Explanations for incident commanders | Alert previews include all language variants, audience segments, delivery channels, and traceability to originating risk assessment | ✅ PASS | FR-020, US-2 |
| 4 | **I. Life Safety First** — Safe degradation on low confidence/stale data | Template fallback when LLM unavailable (20% confidence reduction, 0.8×); embedding outage skips back-translation (CHK051); never halt for single dependency failure | ✅ PASS | FR-036, FR-039 |
| 5 | **II. Multi-Agent Coordination** — Explicit handoffs with confidence/timestamps | Consumes `AgentHandoffEvent` from Risk Assessment with full payload validation; confidence and timestamps carried through pipeline | ✅ PASS | FR-001, FR-002 |
| 6 | **II. Multi-Agent Coordination** — No silent shared state changes | All alert versions immutable once persisted; status transitions are the only mutation; every state change produces audit records | ✅ PASS | FR-016, FR-032 |
| 7 | **II. Multi-Agent Coordination** — AIIMS alignment | Agent proposes alerts but does not publish autonomously; all alerts remain `pending_review` until commander approval; `approval_mode=human_approved` | ✅ PASS | FR-019, FR-021 |
| 8 | **III. Data Trust & Provenance** — Provenance metadata carried | Every alert traces back to recommendation ID and assessment ID; audit trail captures full lineage from handoff to delivery | ✅ PASS | FR-002, FR-033 |
| 9 | **III. Data Trust & Provenance** — Data freshness indicator | Freshness penalty factor (0.9×) applied to stale input data; compound confidence penalties stack multiplicatively in deterministic order (CHK031: freshness → back-translation → fallback); `effectiveConfidence = confidenceScore × freshnessScore × backTranslationPenalty × fallbackPenalty` per FR-006a | ✅ PASS | FR-006, FR-006a, SC-001 |
| 10 | **III. Data Trust & Provenance** — Versioned, reproducible outputs | Alert versions `ca-{incident_id}-v{N}` with optimistic concurrency via Cosmos DB etag; change types tracked (initial/update/correction/all_clear) | ✅ PASS | FR-015, FR-017 |
| 11 | **IV. Privacy & Security** — Data minimisation | Only alert content and segment metadata persisted; no individual recipient PII stored; segment-level delivery tracking (CHK069) | ✅ PASS | Out of Scope §3 |
| 12 | **IV. Privacy & Security** — Australian data residency | All Azure resources in australiaeast/australiasoutheast; no cross-region data leakage | ✅ PASS | NFR-003, Constitution §VI |
| 13 | **IV. Privacy & Security** — Tenant isolation | Simulation/live boundaries enforced at all stages; simulation alerts MUST NOT trigger real public delivery | ✅ PASS | FR-040, FR-041 |
| 14 | **IV. Privacy & Security** — Prompt injection protection | System prompts scope LLM role to emergency alert drafting; ContentSafetyValidator on all LLM outputs; input sanitisation for placeholder interpolation | ✅ PASS | FR-013, FR-010 |
| 15 | **V. Communication** — Multilingual, accessible, actionable alerts | Six languages; plain-language accessible format; structured content (what/where/when/do/help); channel-specific formatting | ✅ PASS | FR-005, FR-007, FR-028 |
| 16 | **V. Communication** — Content safety for all public-facing outputs | All LLM-generated content through ContentSafetyValidator; pre-approved templates exempt; per-language fallback on failure | ✅ PASS | FR-010, FR-011, FR-014 |
| 17 | **V. Communication** — Delivery channels (SMS, push, broadcast) | Three channels with independent retry; channel-specific formatting; multi-part SMS for 612 chars (CHK034) | ✅ PASS | FR-026, FR-028, FR-029 |
| 18 | **V. Communication** — Outbound alert logging | All outbound alerts logged with audience, content, time, channel, and approval mode | ✅ PASS | FR-035 |
| 19 | **VI. Cloud Platform** — Azure, Australian regions only | ACA, Cosmos DB, Azure OpenAI, Azure Communication Services, Notification Hubs, Service Bus — all australiaeast | ✅ PASS | Constitution §VI |
| 20 | **NFR** — Resilience to partial outages | Three-tier audit degradation; LLM template fallback; per-channel independent delivery; embedding outage handling (CHK051); never halt for single failure | ✅ PASS | FR-034, FR-036, FR-037, FR-039 |
| 21 | **NFR** — Append-only audit trail | `CommunicationDecisionRecord` in Cosmos DB, no TTL, no updates/deletes | ✅ PASS | FR-032, FR-033 |
| 22 | **NFR** — WAF compliance | Observability via Application Insights + OpenTelemetry; auto-scaling via ACA (CHK062: depth > 10 scale out, < 3 scale in); security via MI + JWT + content safety | ✅ PASS | NFR-001, NFR-002 |
| 23 | **NFR** — Scenario-based testing | Simulation mode via tenant isolation; bushfire, cyclone, flood scenarios; reproducibility tests | ✅ PASS | FR-040, FR-041 |

### Post-Design Re-check (passed)

All 23 gates re-evaluated after Phase 1 design — no regressions. Key design decisions that strengthened compliance:
- **Multi-part SMS** (CHK034) ensures 612-char messages reach recipients as 4-segment concatenated SMS without truncation loss (gates 1, 15, 17)
- **3-level escalation cap** (CHK019) with CRITICAL hold ensures no alert is auto-approved, maintaining absolute commander authority (gate 2)
- **Multiplicative confidence stacking** (CHK031) in deterministic order (freshness → back-translation → fallback) provides traceable quality degradation (gates 4, 9)
- **Delivery-time deduplication** (CHK041) prevents alert fatigue from overlapping segments while preserving highest-priority delivery (gates 1, 15)
- **JWT-based commander auth** (CHK059) on approval endpoints secures the approval workflow without premature RBAC complexity (gate 14)
- **Template governance via git PR** (CHK014/CHK068) avoids runtime governance overhead while maintaining template quality (gate 16)

## Project Structure

### Documentation (this feature)

```text
specs/008-communication-agent/
├── plan.md                            # This file
├── research.md                        # Phase 0 output — 14 research decisions
├── data-model.md                      # Phase 1 output — 6 entities, configurable parameters
├── quickstart.md                      # Phase 1 output — setup, run, verify
├── contracts/                         # Phase 1 output
│   ├── communication-pipeline.md      # 11-stage pipeline contract with latency budget
│   ├── health-endpoint.md             # GET /health + approval API contracts
│   └── telemetry.md                   # 23 metrics, traces, 17 custom events, alerting thresholds
├── checklists/
│   └── communication-agent.md         # 72-item requirements quality checklist
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
├── communication/                             # Communication Agent (this feature)
│   ├── __init__.py                            # Package init (NEW)
│   ├── agent.py                               # CommunicationAgent class + FastAPI app (existing stub, to be replaced)
│   ├── models.py                              # All Pydantic v2 models, enums, embedded models (NEW)
│   ├── config.py                              # CommunicationConfig from environment variables (NEW)
│   ├── audit.py                               # AuditWriter with three-tier degradation (NEW)
│   ├── dedup.py                               # HandoffDeduplicator with TTL cache (NEW)
│   ├── translator.py                          # Multilingual translation engine, back-translation validation (NEW)
│   ├── segmentation.py                        # Audience segmentation — zone, vulnerability, language (NEW)
│   ├── delivery.py                            # Multi-channel delivery — SMS, push, broadcast with retry (NEW)
│   ├── approval.py                            # AIIMS approval workflow — escalation chain, timeout (NEW)
│   ├── versioning.py                          # Optimistic concurrency version counter (NEW)
│   ├── templates.py                           # Template loader and fallback text generators (NEW)
│   ├── telemetry.py                           # OpenTelemetry metrics, traces, events (NEW)
│   └── pipeline.py                            # CommunicationProcessingPipeline orchestrator — 11 stages (NEW)
└── pyproject.toml                             # Agent workspace deps (existing, add azure-communication-sms, azure-notificationhubs, numpy)

data/
└── alert-templates/                           # Pre-approved multilingual alert templates (NEW)
    ├── en-AU.json                             # English (Australian) templates
    ├── zh-Hans.json                           # Simplified Chinese templates
    ├── ar.json                                # Arabic templates
    ├── vi.json                                # Vietnamese templates
    ├── el.json                                # Greek templates
    └── it.json                                # Italian templates

tests/
├── unit/
│   ├── test_communication_models.py           # Model validation tests (NEW)
│   ├── test_communication_config.py           # Config loading tests (NEW)
│   ├── test_communication_translator.py       # Translation, back-translation, fallback (NEW)
│   ├── test_communication_segmentation.py     # Audience segmentation, dedup, priority (NEW)
│   ├── test_communication_delivery.py         # Multi-channel delivery, retry, multi-part SMS (NEW)
│   ├── test_communication_approval.py         # Approval workflow, escalation, timeout (NEW)
│   ├── test_communication_versioning.py       # Optimistic concurrency (NEW)
│   ├── test_communication_dedup.py            # Handoff deduplication (NEW)
│   ├── test_communication_audit.py            # Audit writer degradation (NEW)
│   ├── test_communication_pipeline.py         # Pipeline stage unit tests (NEW)
│   └── test_communication_endpoints.py        # Health, approval endpoint tests (NEW)
├── contract/
│   ├── test_communication_handoff.py          # Handoff structure contract tests (NEW)
│   ├── test_communication_alert_schema.py     # Alert output schema contract tests (NEW)
│   └── test_communication_reproducibility.py  # Reproducibility contract tests (NEW)
├── integration/
│   ├── test_communication_cosmos.py           # Cosmos DB persistence integration (NEW)
│   └── test_communication_service_bus.py      # Service Bus handoff intake integration (NEW)
└── simulation/
    ├── test_cyclone_alert_scenario.py         # Cyclone alert scenario — Far North QLD (NEW)
    ├── test_bushfire_alert_scenario.py        # Bushfire alert scenario — NSW/VIC (NEW)
    └── test_flood_alert_scenario.py           # Flood alert scenario — multilingual metro area (NEW)
```

**Structure Decision**: Follows the established agent pattern used by risk_assessment, evacuation, and resource_allocation agents. Each agent is a self-contained package under `apps/agents/` with consistent module naming (config.py, models.py, pipeline.py, audit.py, dedup.py, agent.py). Domain-specific modules (translator.py, segmentation.py, delivery.py, approval.py) replace the domain-specific modules of other agents (e.g., scorer.py, matcher.py, router.py). Alert templates live under `data/alert-templates/` alongside existing data directories.

## Complexity Tracking

> No Constitution Check violations. All 23 gates passed without justification needed.
