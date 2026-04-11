# Tasks: Monitoring Agent — Signal Triage, Misinformation Detection, and Escalation

**Input**: Design documents from `/specs/010-monitoring-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, checklists/requirements.md ✅, quickstart.md ✅

**Tests**: Included — the spec explicitly defines acceptance scenarios and test structure (unit, contract, integration, simulation).

**Organization**: Tasks follow the 8 implementation phases from plan.md, mapped to the 6 user stories from spec.md. Three existing code bugs are addressed inline.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Agent source**: `apps/agents/monitoring/` (new modules), `apps/agents/common/` (existing shared)
- **Domain models**: `packages/domain/src/domain/models/` (consumed)
- **API validators**: `apps/api/app/validators/` (consumed)
- **Tests**: `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/simulation/`
- **Infrastructure**: `infra/bicep/`, `infra/modules/`

---

## Phase 1: Core Models and Configuration (Foundation)

**Purpose**: Create the data types and configuration that every subsequent phase depends on. No user story can be implemented without these foundational models.

**⚠️ CRITICAL**: All phases 3–8 depend on this phase being complete.

- [X] T001 Create `MonitoringConfig` dataclass reading all 12 environment variables with defaults per data-model.md configurable parameters table in `apps/agents/monitoring/config.py`
- [X] T002 [P] Create `DecisionType` enum with all 9 values (summarised, escalated, blocked, handed_off, held_for_review, associated, degradation_detected, discarded, validation_failed) in `apps/agents/monitoring/models.py`
- [X] T003 [P] Create `FreshnessStatus` enum (healthy, degraded, offline) and `SourceType` enum (authoritative, iot, social) in `apps/agents/monitoring/models.py`
- [X] T004 Create `MonitoringDecisionRecord` Pydantic model with all fields from data-model.md (id, signal_id, decision, confidence, effective_confidence, freshness_score, inputs, output, agent_version, reasoning_summary, llm_classification, content_safety_result, incident_scope_key, tenant_id, timestamp, buffered_at, flush_source) in `apps/agents/monitoring/models.py`
- [X] T005 [P] Create `DataFreshnessIndicator` Pydantic model with per-source fields (data_source_id, source_type, last_signal_received_at, current_freshness_score, staleness_threshold_minutes, status, last_status_change_at) in `apps/agents/monitoring/models.py`
- [X] T006 [P] Create `AuditBufferEntry` Pydantic model (record, buffered_at, retry_count, last_retry_at) in `apps/agents/monitoring/models.py`
- [X] T007 Add `confidenceScore` and `freshnessScore` field validators (range [0.0, 1.0]) and `category` non-empty validator and `source.dataSourceId`/`source.kind` non-empty validators to `SignalEnvelope` in `apps/api/app/validators/signal_envelope.py`
- [X] T008 [P] Write unit tests for all models (DecisionType, MonitoringDecisionRecord, DataFreshnessIndicator, AuditBufferEntry) and config loading in `tests/unit/test_monitoring_models.py`

**Checkpoint**: All foundational data types and configuration exist. Model validation tests pass.

---

## Phase 2: Deduplication and Freshness Services

**Purpose**: Build the two stateless services that Phase 5 (pipeline) will orchestrate. These are independent of each other and can be built in parallel.

- [X] T009 Create `SignalDeduplicator` class with TTL-based in-memory cache (LRU with configurable `SIGNAL_DEDUP_WINDOW_MINUTES`), `is_duplicate(signal_id) -> bool` and `mark_seen(signal_id)` methods in `apps/agents/monitoring/dedup.py`
- [X] T010 [P] Create `DataFreshnessTracker` class managing per-source `DataFreshnessIndicator` instances with `update(data_source_id, source_type, freshness_score) -> StatusChange | None` and `get_status(data_source_id) -> DataFreshnessIndicator` methods implementing the 4 status transition rules from data-model.md in `apps/agents/monitoring/freshness.py`
- [X] T011 Write unit tests for `SignalDeduplicator` covering: first-seen signal returns False, duplicate within window returns True, signal after TTL expiry returns False, cache eviction behaviour in `tests/unit/test_monitoring_dedup.py`
- [X] T012 [P] Write unit tests for `DataFreshnessTracker` covering all 4 status transitions (healthy→degraded, degraded→offline, degraded→healthy, offline→healthy) and per-source-type threshold application in `tests/unit/test_monitoring_freshness.py`

**Checkpoint**: Dedup and freshness services work independently with full test coverage.

---

## Phase 3: Audit Writer with Three-Tier Degradation (Resilience)

**Purpose**: Implement the append-only audit trail with the three-tier degradation strategy (Cosmos → memory buffer → file spill → recovery flush) per research.md §3 and CHK040.

- [X] T013 Create `AuditWriter` class with `__init__(config: MonitoringConfig, cosmos_client=None)` and primary `write(record: MonitoringDecisionRecord) -> None` method that writes to Cosmos DB in `apps/agents/monitoring/audit.py`
- [X] T014 Implement secondary tier: in-memory ring buffer (bounded at `AUDIT_BUFFER_CAPACITY`, default 10K) activated on Cosmos DB write failure, with `_buffer_in_memory(record)` method in `apps/agents/monitoring/audit.py`
- [X] T015 Implement tertiary tier: local JSONL file spill at `AUDIT_BUFFER_FILE_PATH` when memory buffer is full, with `_spill_to_file(record)` method and critical alert emission in `apps/agents/monitoring/audit.py`
- [X] T016 Implement recovery flush: `flush() -> int` drains memory buffer then file buffer to Cosmos DB in chronological order, annotating each record with `buffered_at` and `flush_source` in `apps/agents/monitoring/audit.py`
- [X] T017 Implement `get_status() -> str` method returning "healthy" | "buffering" | "degraded" based on current tier, and `buffer_depth -> int` property in `apps/agents/monitoring/audit.py`
- [X] T018 Write unit tests for all three tiers: direct Cosmos write, memory buffer activation on Cosmos failure, file spill on buffer full, recovery flush ordering, and status reporting in `tests/unit/test_monitoring_audit.py`
- [X] T019 [P] Write integration test against Cosmos DB emulator verifying write, read-back, partition key routing, and recovery flush in `tests/integration/test_monitoring_cosmos_audit.py`

**Checkpoint**: Audit writer handles all degradation scenarios. Audit records are never lost.

---

## Phase 4: Misinformation Detection Enhancement (Safety) — User Story 2

**Purpose**: Fix the 3 existing code bugs and implement fail-safe-CLOSED misinformation detection per CHK066, CHK030, and CHK027.

**Goal**: Escalated signals undergo LLM credibility assessment with async timeout; misinformation is blocked, suspicious signals get a confidence penalty, and LLM failures result in hold-for-review (fail-safe-CLOSED).

**Independent Test**: Send a signal with `validationStatus=escalated` and a mock LLM returning "misinformation" → verify no handoff produced and blocking decision audit record created.

### Bug Fixes (3 existing bugs from plan.md §Identified Bugs)

- [X] T020 [US2] **BUG FIX**: Fix LLM client call signature mismatch in `_evaluate_escalated_signal()` — change `system_prompt=` / `user_prompt=` to `purpose="reasoning"` and `prompt=` with combined prompt text to match `LLMClient.generate_response()` signature in `apps/agents/monitoring/agent.py` (lines 78–83)
- [X] T021 [US1] **BUG FIX**: Add `earthquake` and `tsunami` to escalation category set — change `{"fire", "weather", "hydrology"}` to `{"fire", "weather", "hydrology", "earthquake", "tsunami"}` in `apps/agents/monitoring/agent.py` (line 48)
- [X] T022 [US1] **BUG FIX**: Implement `effectiveConfidence` computation — replace raw `envelope.confidenceScore >= 0.8` with `effective = envelope.confidenceScore * envelope.freshnessScore` and compare against `MonitoringConfig.escalation_confidence_threshold` in `apps/agents/monitoring/agent.py` (line 49)

### Misinformation Detection Implementation

- [X] T023 [US2] Implement async LLM evaluation with configurable timeout (`LLM_EVAL_TIMEOUT_SECONDS`, default 3s) using `asyncio.wait_for()` in `_evaluate_escalated_signal()` in `apps/agents/monitoring/agent.py`
- [X] T024 [US2] Implement fail-safe-CLOSED: on LLM timeout or unexpected response (not credible/suspicious/misinformation), return `held_for_review` instead of defaulting to credible in `apps/agents/monitoring/agent.py`
- [X] T025 [US2] Implement "suspicious" classification handling: apply `SUSPICIOUS_CONFIDENCE_PENALTY` (default 0.15) to `effectiveConfidence` when LLM returns "suspicious" in `apps/agents/monitoring/agent.py`
- [X] T026 [US2] Add audit record emission for every misinformation evaluation outcome (credible, suspicious, misinformation, llm_timeout, llm_unavailable, held_for_review) in `apps/agents/monitoring/agent.py`
- [X] T027 [P] [US2] Write contract tests for all 6 misinformation classification outcomes: credible (passes through), suspicious (penalty applied), misinformation (blocked), LLM timeout (held), LLM unavailable (held), unexpected response (held) in `tests/contract/test_monitoring_escalation.py`
- [X] T028 [P] [US2] Extend existing misinformation contract tests with fail-safe-CLOSED scenarios and suspicious-penalty verification in `tests/contract/test_misinformation_detector.py`

**Checkpoint**: All 3 bugs fixed. Misinformation detection uses fail-safe-CLOSED. Suspicious signals get confidence penalty. All contract tests pass.

---

## Phase 5: Signal Processing Pipeline (Integration) — User Stories 1, 3, 5, 6

**Purpose**: Create the 6-stage pipeline orchestrator per `contracts/signal-processing.md` that wires together all services from Phases 1–4, implementing the core triage and escalation flow.

**Goal (US1)**: High-risk signals (category in {fire, weather, hydrology, earthquake, tsunami}, effectiveConfidence ≥ 0.8, non-null incidentId) produce an `AgentHandoffEvent` to Risk Assessment within the 5-second SLA.

**Goal (US3)**: Every signal gets a structured summary (category, sourceKind, incidentId) with content safety validation. LLM summaries validated through `ContentSafetyValidator`; rule-based fallback when LLM unavailable.

**Goal (US5)**: Freshness tracked per source with status transitions emitted as audit records and metrics.

**Goal (US6)**: Every pipeline decision point produces a `MonitoringDecisionRecord` audit entry.

**Independent Test (US1)**: Send synthetic signal with `category=fire`, `confidenceScore=0.85`, `freshnessScore=1.0`, valid `incidentId` → verify handoff event produced with correct payload targeting `risk_assessment`.

### Pipeline Implementation

- [X] T029 [US1] Create `SignalProcessingPipeline` class with `__init__` accepting `MonitoringConfig`, `SignalDeduplicator`, `DataFreshnessTracker`, `AuditWriter`, `MonitoringAgent`, and `ContentSafetyValidator` dependencies in `apps/agents/monitoring/pipeline.py`
- [X] T030 [US6] Implement Stage 1 (Input Validation): validate `SignalEnvelope` via Pydantic, emit `validation_failed` audit record and `signal_validation_failures_total` metric on rejection in `apps/agents/monitoring/pipeline.py`
- [X] T031 [US6] Implement Stage 2 (Deduplication): check `SignalDeduplicator.is_duplicate()`, emit `discarded` audit record and `dedup_discards_total` metric on duplicate in `apps/agents/monitoring/pipeline.py`
- [X] T032 [US5] Implement Stage 3 (Freshness Assessment): call `DataFreshnessTracker.update()`, emit `degradation_detected` audit record and `DataSourceDegraded`/`DataSourceRecovered` custom events on status change in `apps/agents/monitoring/pipeline.py`
- [X] T033 [US2] Implement Stage 4 (Misinformation Evaluation): conditionally invoke `_evaluate_escalated_signal()` for `validationStatus=escalated` signals, wire fail-safe-CLOSED and suspicious-penalty logic in `apps/agents/monitoring/pipeline.py`
- [X] T034 [US3] Implement Stage 5 (Signal Summarisation): call `summarize_signal()` with LLM enrichment when available, validate output through `ContentSafetyValidator`, use rule-based fallback `{category, sourceKind, incidentId}` when LLM unavailable, emit `summarised` audit record in `apps/agents/monitoring/pipeline.py`
- [X] T035 [US1] Implement Stage 6 (Confidence-Based Triage): compute `effectiveConfidence = confidenceScore × freshnessScore`, apply suspicious penalty if set, check all 3 escalation conditions (category, threshold, incidentId), create `AgentHandoffEvent` via `build_handoff()`, deliver via `deliver_handoff_with_retry()`, emit `escalated` and `handed_off` audit records in `apps/agents/monitoring/pipeline.py`
- [X] T036 [US1] Implement top-level `process_signal(envelope: SignalEnvelope) -> MonitoringDecisionRecord` method orchestrating all 6 stages sequentially with error handling in `apps/agents/monitoring/pipeline.py`

### Pipeline Tests

- [X] T037 [P] [US1] Write unit tests for end-to-end pipeline: high-risk signal produces handoff, low-confidence signal skipped, missing incidentId skipped, non-escalation category skipped in `tests/unit/test_monitoring_pipeline.py`
- [X] T038 [P] [US3] Write unit tests for summarisation: LLM summary with content safety pass, content safety failure triggers fallback, LLM unavailable uses rule-based summary in `tests/unit/test_monitoring_pipeline.py`
- [X] T039 [P] [US6] Write unit tests for audit completeness: every pipeline path (validate, dedup, freshness, misinfo, summarise, triage) produces at least one audit record in `tests/unit/test_monitoring_pipeline.py`
- [X] T040 [P] [US1] Extend existing escalation contract tests with effectiveConfidence threshold verification and all 5 escalation categories in `tests/contract/test_monitoring_escalation.py`
- [X] T041 [P] [US5] Write unit tests for freshness degradation: source goes degraded after threshold, goes offline after 2× threshold, recovers on good signal in `tests/unit/test_monitoring_pipeline.py`

**Checkpoint**: Complete 6-stage pipeline processes signals end-to-end. US1 (triage), US3 (summarisation), US5 (freshness), and US6 (audit) are independently verifiable.

---

## Phase 6: Health Endpoint and Retrospective Association API — User Story 4

**Purpose**: Replace the simple `/health` handler with a FastAPI app returning structured health per `contracts/health-endpoint.md`, and add the `POST /associate` endpoint for retrospective incident association.

**Goal (US4)**: Retrospective association links unassociated signals to newly declared incidents within a configurable lookback window, respecting tenant isolation.

**Independent Test (US4)**: Create unassociated signals in a jurisdiction, invoke `POST /associate` with a new incident ID → verify signals linked and count returned.

### Health Endpoint

- [X] T042 [US5] Replace `http.server` health handler with a FastAPI app exposing `GET /health` returning the structured response schema from `contracts/health-endpoint.md` (status, agent_version, timestamp, checks object with llm_connectivity, data_source_freshness, processing_queue, audit_store) in `apps/agents/monitoring/agent.py`
- [X] T043 [US5] Wire health checks: LLM connectivity (ping Azure OpenAI), data source freshness (aggregate from `DataFreshnessTracker`), queue depth (from Service Bus client), audit store status (from `AuditWriter.get_status()`) in `apps/agents/monitoring/agent.py`
- [X] T044 [P] [US5] Write contract tests for health response schema validation (all fields present, correct types, status determination logic per contracts/health-endpoint.md table) in `tests/contract/test_monitoring_escalation.py`

### Retrospective Association

- [X] T045 [US4] Add `POST /associate` endpoint to FastAPI app accepting `{incident_id, jurisdiction_id, lookback_hours, tenant_id}`, calling `retrospective_associate()` with tenant isolation enforcement, returning `{incident_id, jurisdiction_id, signals_associated, lookback_hours, timestamp}` in `apps/agents/monitoring/agent.py`
- [X] T046 [US4] Add tenant isolation guard to `retrospective_associate()`: filter by `tenant_id` parameter, ensure simulation signals never associate with live incidents and vice versa in `apps/agents/monitoring/agent.py`
- [X] T047 [US4] Add audit record emission for each retrospective association (`decision=associated`) with signal_id, incident_id, lookback window, and tenant scope in `apps/agents/monitoring/agent.py`
- [X] T048 [P] [US4] Extend existing association contract tests with tenant isolation scenarios (simulation→live blocked, live→live allowed) and lookback window boundary tests in `tests/contract/test_incident_association.py`
- [X] T049 [P] [US4] Write integration test for `POST /associate` endpoint: create unassociated signals, call endpoint, verify response count and signal updates in `tests/integration/test_monitoring_service_bus.py`

**Checkpoint**: Health endpoint returns structured response per contract. Retrospective association works with tenant isolation. US4 and US5 health aspects independently testable.

---

## Phase 7: Observability and Telemetry (WAF)

**Purpose**: Add comprehensive observability per `contracts/telemetry.md` — all 13 metrics, distributed tracing, 8 custom events, and alerting threshold configuration.

- [X] T050 [US6] Add OpenTelemetry instrumentation with distributed tracing for the signal processing pipeline: root span `signal_processing` with child spans for each of the 6 stages per contracts/telemetry.md trace hierarchy in `apps/agents/monitoring/pipeline.py`
- [X] T051 [P] [US6] Implement all 13 metrics from contracts/telemetry.md: `signal_processing_latency`, `escalation_rate`, `misinformation_detection_rate`, `degradation_events`, `handoff_success_rate`, `signal_validation_failures_total`, `dedup_discards_total`, `llm_evaluation_latency`, `llm_timeout_count`, `audit_buffer_depth`, `audit_buffer_file_spills`, `health_check_latency`, `effective_confidence_distribution` with category/source_type/decision/tenant_id dimensions in `apps/agents/monitoring/pipeline.py`
- [X] T052 [P] [US6] Emit all 8 custom events from contracts/telemetry.md: `MisinformationBlocked`, `SignalHeldForReview`, `DataSourceDegraded`, `DataSourceRecovered`, `HandoffDeadLettered`, `AuditBufferActivated`, `AuditBufferFlushed`, `RetrospectiveAssociation` at appropriate decision points in `apps/agents/monitoring/pipeline.py` and `apps/agents/monitoring/audit.py`
- [X] T053 [P] [US6] Configure Application Insights alerting thresholds per contracts/telemetry.md: high misinformation rate (>10/min for 5 min), LLM unavailable (>5 timeouts/min), audit buffer activated (depth > 0), buffer near capacity (>8000), handoff dead letters (any), processing latency spike (p95 > 4000ms), queue depth critical (>5000) in `apps/agents/monitoring/config.py`
- [X] T054 [P] [US6] Add trace context propagation: use correlation ID from incoming Service Bus message as trace parent, set `signal_id` as span attribute on root span in `apps/agents/monitoring/pipeline.py`
- [X] T055 [US6] Write unit tests verifying metric emission: process a signal end-to-end and assert all expected metrics were emitted with correct dimensions in `tests/unit/test_monitoring_pipeline.py`

**Checkpoint**: Full observability stack. All 13 metrics, distributed traces, and custom events emitting correctly.

---

## Phase 8: Infrastructure (Deployment)

**Purpose**: Add/update Bicep modules for Cosmos DB container, Service Bus queue, Container Apps scaling rules, and managed identity access.

- [X] T056 [P] Add Cosmos DB container `monitoring-decisions` with partition key `/incident_scope_key`, no TTL, and serverless throughput in `infra/bicep/monitoring.bicep`
- [X] T057 [P] Add Service Bus queue configuration with session-based delivery (session ID = signal_id) for dedup affinity in `infra/bicep/monitoring.bicep`
- [X] T058 [P] Configure Container Apps auto-scaling rules based on Service Bus queue depth (scale-up at 100 messages, max replicas per NFR-002) in `infra/bicep/monitoring.bicep`
- [X] T059 Add managed identity role assignments: Cosmos DB Data Contributor for audit writes, Service Bus Data Receiver for signal intake, Azure OpenAI Cognitive Services User for LLM access in `infra/bicep/monitoring.bicep`
- [X] T060 Update `infra/bicep/main.bicep` to reference new monitoring agent resources (Cosmos container, Service Bus queue, scaling rules, MI assignments)
- [X] T061 [P] Add `azure-cosmos` and `tenacity` dependencies to `apps/agents/pyproject.toml`

**Checkpoint**: Infrastructure deployable via Bicep. All Azure resources configured with correct SKUs, regions (australiaeast), and security settings.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, simulation test extension, and documentation alignment.

- [X] T062 [P] Extend bushfire scenario simulation test with full pipeline flow: signal intake → dedup → freshness → misinformation check → summarise → triage → handoff → audit trail verification in `tests/simulation/test_bushfire_scenario.py`
- [X] T063 [P] Write Service Bus integration test: publish a SignalEnvelope to the intake queue, verify the pipeline consumes and processes it end-to-end in `tests/integration/test_monitoring_service_bus.py`
- [X] T064 Run all quickstart.md verification steps (signal summarisation, high-risk escalation, misinformation blocking) and validate they pass with updated code
- [X] T065 [P] Validate checklist coverage: verify that all 16 critical checklist items from plan.md §Checklist Resolution Summary (CHK001, CHK002, CHK003, CHK007, CHK008, CHK016, CHK024, CHK027, CHK030, CHK031, CHK040, CHK044, CHK060, CHK066, CHK070, CHK073) are addressed by implementation
- [X] T066 Code cleanup: ensure all new modules have docstrings, type hints, and follow existing codebase patterns (Pydantic BaseModel, logging via `logging.getLogger(__name__)`)
- [X] T067 [P] [US6] Write unit test verifying provenance metadata retention (FR-019): process a signal with provenance fields (source, collection method, time, location precision, validation status) through the full pipeline and assert provenance is preserved in audit records and handoff payloads in `tests/unit/test_monitoring_pipeline.py`
- [X] T068 [P] Write load test verifying NFR-001: generate 1,000 synthetic signals per minute sustained over 5 minutes, assert all signals processed within 5-second SLA for escalation path and no signal loss under load in `tests/simulation/test_monitoring_load.py`
- [X] T069 [P] [US2] Write prompt injection security test (FR-027): send signals with adversarial payloads (prompt injection attempts in signal content) through misinformation evaluation and summarisation, verify system prompts scope LLM role and prevent re-purposing in `tests/contract/test_monitoring_escalation.py`

**Checkpoint**: All tests pass. Quickstart verified. Checklist items validated. Code clean and documented. Coverage gaps for FR-019, FR-027, and NFR-001 addressed.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Core Models & Config ──────────────────────────────┐
                                                            │
Phase 2: Dedup & Freshness ─────┐                          │
                                ├── Phase 5: Pipeline ──────┤
Phase 3: Audit Writer ──────────┘        │                  │
                                         │                  │
Phase 4: Misinformation ────────────────-┘                  │
                                                            │
Phase 6: Health & Association API ──── depends on Phase 5 ──┤
                                                            │
Phase 7: Observability ────────────── depends on Phase 5 ──-┤
                                                            │
Phase 8: Infrastructure ───────────── independent ──────────┤
                                                            │
Phase 9: Polish ───────────────────── depends on ALL ───────┘
```

- **Phase 1**: No dependencies — start immediately. BLOCKS all subsequent phases.
- **Phase 2**: Depends on Phase 1 (models). Dedup and freshness can be built in parallel.
- **Phase 3**: Depends on Phase 1 (models). Can run in parallel with Phase 2.
- **Phase 4**: Depends on Phase 1 (models, config). Can run in parallel with Phases 2–3.
- **Phase 5**: Depends on Phases 1–4 (all services must exist to orchestrate).
- **Phase 6**: Depends on Phase 5 (pipeline must exist for health status and association).
- **Phase 7**: Depends on Phase 5 (pipeline must exist to instrument).
- **Phase 8**: Can run in parallel with Phases 2–7 (infrastructure is independent of application code).
- **Phase 9**: Depends on all phases — final validation.

### User Story Dependencies

- **US1 (Triage & Escalation, P1)**: Requires Phase 1 + Phase 5 (Stage 6). Bug fixes T021, T022 in Phase 4.
- **US2 (Misinformation, P2)**: Requires Phase 1 + Phase 4 + Phase 5 (Stage 4). Bug fix T020 in Phase 4.
- **US3 (Summarisation, P3)**: Requires Phase 1 + Phase 5 (Stage 5). No dependencies on other stories.
- **US4 (Retrospective Association, P4)**: Requires Phase 6. Independent of US1–US3.
- **US5 (Freshness & Degradation, P5)**: Requires Phase 2 + Phase 5 (Stage 3) + Phase 6 (health endpoint).
- **US6 (Audit Trail, P6)**: Requires Phase 3 + Phase 5 (all stages emit audit) + Phase 7 (telemetry).

### Within Each Phase

- Models/enums before services
- Services before pipeline orchestrator
- Bug fixes before new feature implementation
- Core implementation before tests (tests written alongside but validated after)
- Unit tests before contract tests before integration tests

### Parallel Opportunities

- **Phase 1**: T002, T003, T005, T006 can all run in parallel (different models in same file, but independent sections)
- **Phase 2**: T009 and T010 can run in parallel (dedup.py and freshness.py are independent files)
- **Phase 3**: T019 can run in parallel with T013–T018 (integration test vs unit implementation)
- **Phase 4**: T027 and T028 can run in parallel (different test files)
- **Phase 5**: T037, T038, T039, T040, T041 can all run in parallel (test writing)
- **Phase 7**: T051, T052, T053, T054 can all run in parallel (independent metric/event/trace concerns)
- **Phase 8**: T056, T057, T058, T061 can all run in parallel (independent Bicep resources)
- **Phase 9**: T062, T063, T065 can all run in parallel (independent validation tasks)

---

## Parallel Example: Phase 2 (Dedup & Freshness)

```bash
# Launch both service implementations together (different files):
Task T009: "Create SignalDeduplicator in apps/agents/monitoring/dedup.py"
Task T010: "Create DataFreshnessTracker in apps/agents/monitoring/freshness.py"

# Launch both test files together (different files):
Task T011: "Unit tests for dedup in tests/unit/test_monitoring_dedup.py"
Task T012: "Unit tests for freshness in tests/unit/test_monitoring_freshness.py"
```

## Parallel Example: Phase 8 (Infrastructure)

```bash
# Launch all independent Bicep resources together:
Task T056: "Cosmos DB container in infra/bicep/monitoring.bicep"
Task T057: "Service Bus queue in infra/bicep/monitoring.bicep"
Task T058: "Container Apps scaling rules in infra/bicep/monitoring.bicep"
Task T061: "Dependencies in apps/agents/pyproject.toml"
```

---

## Implementation Strategy

### MVP First (User Story 1 — Signal Triage & Escalation)

1. Complete Phase 1: Core Models & Config (T001–T008)
2. Complete Phase 4 bug fixes only: T020, T021, T022 (fix existing code)
3. Complete Phase 5 Stage 6: T035, T036 (triage logic)
4. **STOP and VALIDATE**: Send a synthetic fire signal with confidence 0.85, freshness 1.0, valid incidentId → verify handoff produced
5. Deploy/demo if ready — core pipeline works

### Incremental Delivery

1. Phase 1 → Foundation ready
2. Phase 2 + 3 → Services ready (dedup, freshness, audit)
3. Phase 4 → Bug fixes + misinformation detection (US2 testable)
4. Phase 5 → Full pipeline (US1, US3, US5, US6 testable)
5. Phase 6 → Health endpoint + retrospective association (US4 testable)
6. Phase 7 → Full observability
7. Phase 8 → Infrastructure deployable
8. Phase 9 → Polish and validate

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 together
2. Once Phase 1 is done:
   - Developer A: Phase 2 (dedup + freshness) + Phase 5 (pipeline)
   - Developer B: Phase 3 (audit writer) + Phase 7 (observability)
   - Developer C: Phase 4 (bug fixes + misinformation) + Phase 6 (health + association API)
   - Developer D: Phase 8 (infrastructure — fully independent)
3. All converge on Phase 9 for end-to-end validation

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 66 |
| **Phase 1 (Models & Config)** | 8 tasks |
| **Phase 2 (Dedup & Freshness)** | 4 tasks |
| **Phase 3 (Audit Writer)** | 7 tasks |
| **Phase 4 (Misinformation / US2)** | 9 tasks (incl. 3 bug fixes) |
| **Phase 5 (Pipeline / US1,3,5,6)** | 13 tasks |
| **Phase 6 (Health & Association / US4,5)** | 8 tasks |
| **Phase 7 (Observability / US6)** | 6 tasks |
| **Phase 8 (Infrastructure)** | 6 tasks |
| **Phase 9 (Polish)** | 5 tasks |
| **Bug fixes addressed** | 3 (LLM signature, missing categories, effectiveConfidence) |
| **Parallel opportunities** | 8 groups across phases |
| **User stories covered** | 6/6 |
| **Checklist items addressed** | 16 critical items per plan.md resolution table |
| **New source files** | 6 (config.py, models.py, audit.py, freshness.py, dedup.py, pipeline.py) |
| **New test files** | 8 (5 unit, 1 contract, 2 integration) |
| **Extended test files** | 3 (misinformation, association, bushfire simulation) |
| **MVP scope** | Phase 1 + bug fixes + Phase 5 Stage 6 (US1 triage & escalation) |

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] labels map tasks to user stories: US1 (Triage), US2 (Misinformation), US3 (Summarisation), US4 (Association), US5 (Freshness/Degradation), US6 (Audit)
- Three bugs in existing `agent.py` are fixed in Phase 4 (T020–T022) before new feature work builds on them
- `effectiveConfidence = confidenceScore × freshnessScore` is the key formula from CHK070 — used throughout triage
- Fail-safe-CLOSED (CHK066) means uncertain signals are HELD, not passed through
- Three-tier audit degradation (CHK040) ensures no audit records are lost during infrastructure failures
- All configurable parameters read from environment variables at startup only (CHK044)
- Commit after each task or logical group; stop at any checkpoint to validate independently
