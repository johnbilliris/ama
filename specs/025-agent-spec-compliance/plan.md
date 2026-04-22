# Implementation Plan: Agent Specification Compliance Audit

**Branch**: `025-agent-spec-compliance` | **Date**: 2026-04-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-agent-spec-compliance/spec.md`

## Summary

Remediate 8 verified compliance audit findings across the 5 operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication). The technical approach is: (1) convert synchronous blocking retries to async with dead-letter persistence and auto-redelivery, (2) add GeoJSON polygon generation to Risk Assessment using Shapely + Cosmos DB-backed radius lookup, (3) integrate Azure AI Content Safety with circuit breaker fallback, factual consistency, and tone-level alignment, (4) wire missing inter-agent handoffs (Evacuation→Resource Allocation, Resource Allocation→Communication, Monitoring→Evacuation), (5) add Azure IoT Hub ingestion adapter with in-memory dedup, (6) replace bag-of-words translation quality with embedding-based semantic similarity. All infrastructure runs on Azure Australia East.

## Technical Context

**Language/Version**: Python 3.11+ (agents, API), TypeScript 5.x (Next.js dashboard)
**Primary Dependencies**: FastAPI, Pydantic, Shapely, azure-ai-contentsafety, azure-iot-device, azure-cosmos, httpx, numpy, Next.js 14
**Storage**: Azure Cosmos DB (dead-letters, radius lookup table, assessments), Azure Blob Storage (signal archives), Azure IoT Hub (device telemetry)
**Testing**: pytest (unit, contract, integration, simulation, benchmark), Playwright (e2e)
**Target Platform**: Azure Container Apps (Australia East), Linux containers
**Project Type**: Multi-service web application (3 runtimes: Next.js dashboard, FastAPI API, Python autonomous agents)
**Performance Goals**: P95 pipeline latency ≤ 5s under single-agent failure (SC-001), ≤ 2s max blocking per retry (SC-002), 10K IoT msg/s ingestion (FR-018)
**Constraints**: Data sovereignty — Azure Australia East/Southeast only. Managed identity in production. Human-in-the-loop for public alerts.
**Scale/Scope**: 1,000 concurrent signals, 10,000 IoT msg/s, 50 concurrent dead-letter redeliveries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Primacy of Life (I) | PASS | Content safety (FR-007–009) protects life-safety comms; human-in-the-loop preserved |
| 2 | National EM Principles (II) | PASS | Comprehensive hazard coverage (5 types in FR-006); coordinated multi-agent handoffs |
| 3 | AIIMS Functional Alignment (II-A) | PASS | Agents map to AIIMS functions: Intelligence (Monitoring), Planning (Risk Assessment), Operations (Evacuation), Logistics (Resource Allocation), Public Information (Communication) |
| 4 | Multi-Hazard Design (III) | PASS | FR-006 covers flood, bushfire, earthquake, cyclone, chemical_spill with admin-editable radius table |
| 5 | Transparency & Auditability (IV) | PASS | FR-003/003a structured telemetry for all retries and dead-letters; FR-009 circuit breaker telemetry; FR-015 road network audit log; FR-021 security audit events |
| 6 | Australian Warning System (V-A) | PASS | FR-007(c) tone check enforces AWS tier compliance (Advice/Watch and Act/Emergency Warning) |
| 7 | Ten Warning Principles (V-B) | PASS | Content safety + multilingual support + human review preserves warning quality |
| 8 | Total Warning System (V-C) | PASS | IoT adapter (monitoring/prediction), content safety (message construction), multilingual (communication) |
| 9 | Evacuation Framework (VI) | PASS | FR-010/011 transport handoffs with priority for vulnerable populations; FR-014 dynamic road network |
| 10 | Cloud Platform Azure (VIII) | PASS | All new services Azure-native: AI Content Safety, IoT Hub, Cosmos DB, Azure OpenAI embeddings |
| 11 | Data Sovereignty (NON-NEG 2) | PASS | Australia East/Southeast regions; managed identity in production (FR-007) |
| 12 | Human-in-the-loop (NON-NEG 1) | PASS | Dismissed finding F07 preserves human approval gate; FR-009 delivers during fallback but flags for review |
| 13 | Interoperability (NON-NEG 4) | PASS | GeoJSON output (FR-004/005), OpenAPI endpoints (contracts), SignalEnvelope normalisation |
| 14 | Graceful Degradation (NON-NEG 5) | PASS | Circuit breaker fallback (FR-009), non-blocking retries (FR-001), dead-letter persistence (FR-003a) |
| 15 | Privacy by Design (NON-NEG 3) | PASS | No new PII collection; IoT signals are sensor readings, not personal data |

**Result: 15/15 PASS** — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/025-agent-spec-compliance/
├── plan.md              # This file
├── research.md          # Phase 0 output — 8 research decisions
├── data-model.md        # Phase 1 output — entity schemas
├── quickstart.md        # Phase 1 output — dev setup guide
├── contracts/
│   └── openapi-delta.md # Phase 1 output — API contract changes
├── checklists/
│   └── requirements.md  # Checklist — 16/16 pass
└── tasks.md             # Phase 2 output — task breakdown
```

### Source Code (repository root)

```text
apps/
├── agents/
│   ├── common/
│   │   ├── handoffs.py          # F10: async retry + dead-letter persistence
│   │   ├── dead_letters.py      # F10: DeadLetterRedeliveryPoller (NEW)
│   │   ├── startup.py           # Dead-letter poller startup registration (NEW)
│   │   ├── content_safety.py    # F08: Azure AI + factual + tone + circuit breaker
│   │   └── circuit_breaker.py   # F08: ContentSafetyCircuitBreaker (NEW)
│   ├── monitoring/
│   │   ├── pipeline.py          # F04: road closure signal classification + handoff
│   │   └── iot_adapter.py       # F01: IoT Hub → SignalEnvelope normaliser (NEW)
│   ├── risk_assessment/
│   │   ├── pipeline.py          # F03: HazardMapGenerator stage integration
│   │   ├── hazard_map.py        # F03: GeoJSON polygon generation (NEW)
│   │   ├── hazard_radius.py     # F03: Cosmos DB-backed radius lookup (NEW)
│   │   └── versioning.py        # F10: async OCC retry
│   ├── evacuation/
│   │   ├── pipeline.py          # F05: transport handoff + F04: road closure handler
│   │   └── versioning.py        # F10: async OCC retry
│   ├── resource_allocation/
│   │   ├── pipeline.py          # F06: dispatch notification handoff
│   │   └── versioning.py        # F10: async OCC retry
│   └── communication/
│       ├── pipeline.py          # F08: content safety integration point
│       ├── versioning.py        # F10: async OCC retry
│       └── delivery.py          # F10: async channel delivery retry
├── api/
│   └── app/
│       ├── main.py              # Existing API entrypoint (no poller registration)
│       └── routes/
│           ├── dead_letters.py  # FR-003a: dead-letter inspection + redelivery (NEW)
│           └── radius_lookup.py # FR-006: radius table CRUD (NEW)
└── web/
    └── src/                     # No changes in this feature

infra/
├── main.bicep                   # Updated: references new modules
├── bicep/
│   ├── content-safety.bicep     # F08: Azure AI Content Safety (NEW)
│   └── iot-hub.bicep            # F01: Azure IoT Hub + Event Grid (NEW)

tests/
├── unit/
│   ├── test_async_handoff_retry.py
│   ├── test_hazard_map_generation.py
│   ├── test_content_safety_azure.py
│   ├── test_content_safety_factual.py
│   ├── test_content_safety_tone.py
│   ├── test_circuit_breaker.py
│   ├── test_evacuation_transport_handoff.py
│   ├── test_resource_dispatch_handoff.py
│   ├── test_road_network_dynamic.py
│   ├── test_iot_adapter.py
│   ├── test_translation_embedding.py
│   ├── test_dead_letter_redelivery.py
│   └── test_named_location_lookup.py
├── contract/
│   ├── test_evacuation_resource_handoff.py
│   └── test_resource_communication_handoff.py
├── integration/
│   └── test_content_safety_integration.py
└── benchmark/
    └── test_pipeline_latency.py
```

**Structure Decision**: Existing multi-app monorepo structure (apps/agents, apps/api, apps/web) with shared packages (packages/domain, packages/schemas). All changes are additive within existing directories.

## Constitution Check — Post-Design Re-evaluation

*GATE: Re-checked after Phase 1 design artifacts (research.md R1–R16, data-model.md, contracts/openapi-delta.md).*

New additions validated against 15 constitutional gates:

| Addition | Constitutional Principles Verified | Status |
|----------|-----------------------------------|--------|
| Cosmos DB radius lookup (R12) | IV Transparency (change audit), VIII Azure Cloud, NON-NEG 2 Data Sovereignty (AU) | PASS |
| Named-location lookup (R11) | IV Transparency (resolution logged), VIII Azure Cloud | PASS |
| Circuit breaker + telemetry (R9) | IV Transparency (5 telemetry events), NON-NEG 5 Graceful Degradation | PASS |
| Management API RBAC (R10) | NON-NEG 1 Human-in-the-loop (admin-only writes), NON-NEG 3 Privacy (no PII exposed) | PASS |
| Permanently failed state (R14) | IV Transparency (full audit trail), Quality Gates (explicit lifecycle) | PASS |
| Normalized confidence (R13) | IV Transparency (unified scoring across validators) | PASS |
| Test corpora requirements (R15) | Quality Gates (measurable, repeatable test coverage) | PASS |
| Priority in transport handoff (R16) | VI-C Vulnerable Populations (triage ordering for scarce transport) | PASS |

**Result: 15/15 PASS post-design** — no violations introduced by Phase 1 artifacts.

## Generated Artifacts Summary

| Artifact | Path | Status |
|----------|------|--------|
| Implementation Plan | [plan.md](plan.md) | Complete |
| Research Decisions | [research.md](research.md) | R1–R16 (16 decisions, 0 NEEDS CLARIFICATION) |
| Data Model | [data-model.md](data-model.md) | 4 modified + 8 new entities |
| API Contracts | [contracts/openapi-delta.md](contracts/openapi-delta.md) | 3 internal + 2 infra + 7 REST endpoints |
| Quickstart | [quickstart.md](quickstart.md) | Dev setup + 13 test commands |
| Requirements Checklist | [checklists/requirements.md](checklists/requirements.md) | 16/16 pass |
