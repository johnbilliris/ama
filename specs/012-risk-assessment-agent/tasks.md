# Tasks: Risk Assessment Agent — Hazard Prediction, Recommendation Generation, and Multi-Agent Escalation

**Input**: Design documents from `/specs/012-risk-assessment-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, checklists/requirements.md ✅

**Tests**: Included — plan.md explicitly specifies unit, contract, integration, and simulation tests per phase.

**Organization**: Tasks are grouped by user story (P1–P7) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Agent source**: `apps/agents/risk_assessment/`
- **Domain models**: `packages/domain/src/domain/models/`
- **Shared agent infra**: `apps/agents/common/`
- **Tests**: `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/simulation/`
- **Infrastructure**: `infra/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package initialization and dependency configuration for the Risk Assessment Agent

- [X] T001 Create package init file at `apps/agents/risk_assessment/__init__.py` exporting `RiskAssessmentAgent`
- [X] T002 Add `azure-cosmos`, `azure-servicebus`, and `tenacity` dependencies to `apps/agents/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, configuration, and domain entity extensions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `apps/agents/risk_assessment/config.py` with `RiskAssessmentConfig` class reading all environment variables from data-model.md §Configurable Parameters (source weights, stale threshold, dedup window, validity hours, contradiction/fallback reduction factors, escalation thresholds, audit buffer capacity/path, agent version)
- [X] T004 [P] Create `apps/agents/risk_assessment/models.py` with `DecisionType` enum (12 values: `handoff_received`, `handoff_rejected`, `duplicate_discarded`, `signals_retrieved`, `assessment_generated`, `recommendation_generated`, `handoff_created`, `handoff_delivered`, `handoff_dead_lettered`, `contradiction_detected`, `degradation_detected`, `content_safety_failure`), `AssessmentType` enum, `ConfidenceLevel` enum, `SeverityLevel` enum, and `RiskAssessmentDecisionRecord` Pydantic model with all 22 canonical fields from data-model.md
- [X] T005 [P] Extend `packages/domain/src/domain/models/hazard_assessment.py` with new fields: `version` (int), `confidence_score` (float), `confidence_adjusted` (float), `severity_level` (SeverityLevel enum), `valid_until` (datetime), `status` (active/superseded/expired), `generation_method` (str), `model_deployment_id` (optional str), `prompt_template_version` (str), `configuration_version` (str), `input_snapshot` (dict), `contradiction_detected` (bool), `contradiction_details` (optional list[dict]), `stale_signal_ids` (optional list[str]), `related_incident_ids` (optional list[str]), `hazard_map` (optional HazardMap), `incident_scope_key` (str), `tenant_id` (str), and embedded `HazardMap` model (affected_area GeoJSON, severity_level, hazard_type, confidence_score, time_horizon, population_estimate)
- [X] T006 [P] Extend `packages/domain/src/domain/models/recommendation.py` with new fields: `assessment_id` (str), `confidence_score` (float, 0.0–1.0), `severity_level` (SeverityLevel), `override_by_user_id` (optional str), `override_by_role` (optional str), `override_justification` (optional str), `override_timestamp` (optional datetime), `incident_scope_key` (str), `tenant_id` (str); add Pydantic validators for confidence_score range [0.0, 1.0]
- [X] T007 Write unit tests for all models and config in `tests/unit/test_risk_assessment_models.py` covering: DecisionType enum completeness (12 values), RiskAssessmentDecisionRecord validation (required fields, optional fields, confidence range), HazardAssessment validation (confidence range, version ≥ 1, valid_until > generation_timestamp, confidence_level derived from confidence_adjusted), Recommendation validation (confidence_score range, status lifecycle), HazardMap embedded validation
- [X] T008 [P] Write unit tests for config loading in `tests/unit/test_risk_assessment_config.py` covering: default values, environment variable overrides, type coercion, missing optional variables

**Checkpoint**: Foundation ready — all models, enums, and configuration defined. User story implementation can now begin.

---

## Phase 3: User Story 1 — Receive Escalated Handoff and Generate Hazard Impact Prediction (Priority: P1) 🎯 MVP

**Goal**: Receive `AgentHandoffEvent` from Monitoring Agent, retrieve referenced signals, correlate multi-source data with weighted averaging and freshness, assign a monotonic version number, compute AIDR-aligned severity, generate an LLM or template-based hazard summary, and persist a versioned `HazardAssessment` with traceable signal references.

**Independent Test**: Send a synthetic `AgentHandoffEvent` with `source_agent=monitoring`, `target_agent=risk_assessment`, and a fire-category signal payload. Verify that the agent produces a versioned `HazardAssessment` with traceable `input_signal_ids`, a confidence level, and an LLM-generated or template-based summary.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Write unit tests for handoff deduplication in `tests/unit/test_risk_assessment_dedup.py` covering: first-seen handoff passes, duplicate within window discarded, duplicate after window passes, configurable window duration, concurrent dedup safety
- [X] T010 [P] [US1] Write unit tests for signal correlation in `tests/unit/test_risk_assessment_correlation.py` covering: weighted averaging formula `Σ(conf × weight × fresh) / Σ(weight × fresh)` with authoritative (2.0), IoT (1.0), social (0.5) weights; stale signal flagging below threshold (0.5); all-stale signals produce low confidence; missing signals reduce confidence proportionally; source diversity tracking; single-source assessment; mixed-authority source sets
- [X] T011 [P] [US1] Write unit tests for severity computation in `tests/unit/test_risk_assessment_severity.py` covering: all 5 disaster types (bushfire → high, cyclone → critical, flood → high, earthquake → critical, tsunami → critical), fallback severity mapping, one-level downgrade when confidence < 0.4 with low as floor, population-adjusted severity
- [X] T012 [P] [US1] Write unit tests for version counter in `tests/unit/test_risk_assessment_versioning.py` covering: first version = 1, monotonic increment, optimistic concurrency retry on 412 Precondition Failed, max 3 retries with jitter, fallback to UUID suffix after exhausted retries, concurrent version assignment
- [X] T013 [P] [US1] Write unit tests for pipeline stages 1–5 in `tests/unit/test_risk_assessment_pipeline.py` covering: valid handoff acceptance, malformed handoff rejection, missing incident rejection, signal retrieval success/partial/failure, assessment type derivation from signal category, version assignment, summary generation with content safety, assessment persistence

### Implementation for User Story 1

- [X] T014 [P] [US1] Create `apps/agents/risk_assessment/dedup.py` with `HandoffDeduplicator` class: TTL-based in-memory cache keyed by `handoff_id`, configurable dedup window from `RiskAssessmentConfig.handoff_dedup_window_minutes` (default 10 min), `is_duplicate(handoff_id) -> bool` method, automatic eviction of expired entries
- [X] T015 [P] [US1] Create `apps/agents/risk_assessment/correlation.py` with `SignalCorrelator` class: `compute_weighted_confidence(signals, config) -> float` implementing the formula from research.md §1, per-signal freshness integration, configurable source weights from config, stale signal identification below `STALE_SIGNAL_THRESHOLD`, source diversity analysis, unverified-source-reliance flagging
- [X] T016 [P] [US1] Create `apps/agents/risk_assessment/severity.py` with `SeverityComputer` class: signal-category-to-severity mapping per data-model.md §Signal Category table, population-adjusted severity computation, fallback severity mapping for LLM-unavailable mode, one-level downgrade logic when adjusted confidence < 0.4 with `low` as floor
- [X] T017 [P] [US1] Create `apps/agents/risk_assessment/versioning.py` with `VersionCounter` class: Cosmos DB etag-based optimistic concurrency per research.md §3, counter document pattern `{incident_id}_{assessment_type}_counter`, `assign_version(incident_id, assessment_type) -> int` with read-increment-replace, conflict retry with exponential jitter (max 3), UUID-suffixed fallback version on exhausted retries
- [X] T018 [P] [US1] Create `apps/agents/risk_assessment/templates.py` with template-based fallback text generators: `generate_assessment_summary(assessment_type, signals, severity, confidence) -> str` producing signal-ID-inclusive template text per assessment type, `generate_recommendation_explanation(rec_type, signals, assessment_summary) -> str` producing signal-ID-inclusive explanation text per recommendation type
- [X] T019 [P] [US1] Create `apps/agents/risk_assessment/audit.py` with `AuditWriter` class: primary Cosmos DB write path to `risk-assessment-decisions` container, `write_record(record: RiskAssessmentDecisionRecord) -> None` method, partition key `/incident_scope_key`, append-only (create_item, not upsert), error handling for Cosmos unavailability (to be extended in US6)
- [X] T020 [US1] Extend `apps/agents/risk_assessment/agent.py` with full assessment generation method: retrieve signals from signal store using signal IDs from handoff payload, invoke `SignalCorrelator.compute_weighted_confidence`, derive `assessment_type` from signal category mapping (FR-010), invoke LLM summary generation via `_generate_with_fallback` with content safety validation, compute severity via `SeverityComputer`, assign version via `VersionCounter`, compute `valid_until` from `generation_timestamp + validity_duration` per hazard type, build and return `HazardAssessment` with all required fields including `input_snapshot` for reproducibility
- [X] T021 [US1] Create `apps/agents/risk_assessment/pipeline.py` with `AssessmentProcessingPipeline` class orchestrating stages 1–5: Stage 1 (handoff intake — Pydantic validation, target_agent check, incident existence check, idempotency via `HandoffDeduplicator`), Stage 2 (signal retrieval — batch Cosmos reads with partial unavailability handling), Stage 3 (multi-source correlation via `SignalCorrelator`), Stage 4 (placeholder for contradiction detection — wired in US4), Stage 5 (assessment generation via agent, version assignment, severity computation, persistence to `risk-assessments` container)
- [X] T022 [US1] Wire pipeline into Service Bus consumer: configure `azure-servicebus` `ServiceBusReceiver` to consume from handoff intake queue, deserialize messages to `AgentHandoffEvent`, invoke `AssessmentProcessingPipeline.process(handoff)`, acknowledge message on completion, handle poison messages in `apps/agents/risk_assessment/agent.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — the agent receives handoffs, retrieves signals, computes weighted confidence with freshness, assigns versions, computes severity, generates LLM or template summaries, and persists versioned `HazardAssessment` records with traceable signal IDs.

---

## Phase 4: User Story 2 — Generate Recommendation and Escalate to Communication Agent (Priority: P2)

**Goal**: Generate `Recommendation` records of type `public_alert` from completed hazard assessments with proper confidence/severity fields and traceable signal IDs, then escalate high-confidence recommendations to the Communication Agent via `AgentHandoffEvent`.

**Independent Test**: Provide signal IDs and incident ID, invoke recommendation generation, verify a `Recommendation` with type `public_alert` is produced with signal references in the explanation, and a `communication` handoff is created when confidence ≥ 0.7.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US2] Write contract tests for Communication escalation thresholds in `tests/contract/test_risk_assessment_escalation.py` covering: handoff created when confidence ≥ 0.7 for public_alert, no handoff when confidence < 0.7, handoff payload contains recommendation_id/summary/explanation, handoff uses numeric confidence_score (not categorical)
- [X] T024 [P] [US2] Write contract tests for handoff structure in `tests/contract/test_risk_assessment_handoff.py` covering: outbound AgentHandoffEvent schema validation (source_agent=risk_assessment, target_agent=communication), payload contains required fields per contracts/assessment-pipeline.md §Stage 7, tenant_id propagation from assessment

### Implementation for User Story 2

- [X] T025 [US2] Fix existing `recommend_public_alert` in `apps/agents/risk_assessment/agent.py` to set `assessment_id`, `confidence_score` (numeric from assessment), `severity_level` (from assessment), and `incident_scope_key`/`tenant_id` — resolving plan.md Identified Issue #3
- [X] T026 [US2] Fix `build_communication_handoff` in `apps/agents/risk_assessment/agent.py` to use numeric `recommendation.confidence_score >= 0.7` threshold instead of categorical `confidence_level != "high"` check, and use `recommendation.confidence_score` instead of hardcoded `0.9` in handoff — resolving plan.md Identified Issues #1 and #2
- [X] T027 [US2] Enforce signal ID traceability in all recommendation explanations: after LLM generation, check all `supporting_signal_ids` appear in explanation text; append missing IDs with `Signal references: {ids}` suffix — per FR-018 in `apps/agents/risk_assessment/agent.py`
- [X] T028 [US2] Add recommendation generation to pipeline stage 6 in `apps/agents/risk_assessment/pipeline.py`: invoke recommendation generator from assessment, determine recommendation types from assessment-type-to-recommendation-type mapping per contracts/assessment-pipeline.md §Stage 6, persist to `risk-recommendations` container
- [X] T029 [US2] Add Communication Agent escalation to pipeline stage 7 in `apps/agents/risk_assessment/pipeline.py`: evaluate `public_alert` recommendations against confidence threshold (≥ 0.7 from config), build `AgentHandoffEvent` with `target_agent=communication` and payload per contract, deliver via `deliver_handoff_with_retry` with exponential backoff (max 3 retries per FR-023)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — assessments generate recommendations, high-confidence public_alert recommendations trigger Communication Agent handoffs.

---

## Phase 5: User Story 3 — Escalate to Evacuation and Resource Allocation Agents (Priority: P3)

**Goal**: Generate `evacuation`, `resource_allocation`, `coordination`, and `infrastructure_action` recommendation types from hazard assessments, and escalate qualifying recommendations to Evacuation and Resource Allocation agents based on severity and confidence thresholds.

**Independent Test**: Provide a hazard assessment with `assessment_type=route_risk` or `community_impact` and verify that `evacuation` and `resource_allocation` recommendations are generated, and handoff events target the appropriate downstream agents.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T030a [P] [US3] Write contract tests for Evacuation escalation thresholds in `tests/contract/test_risk_assessment_escalation.py` (extend existing file) covering: handoff created when severity ≥ `high` AND confidence ≥ 0.6 for evacuation type, no handoff when severity < `high`, no handoff when confidence < 0.6, handoff payload contains recommendation_id/summary/assessment_id per contracts/assessment-pipeline.md §Stage 7
- [X] T030b [P] [US3] Write contract tests for Resource Allocation escalation in `tests/contract/test_risk_assessment_escalation.py` (extend existing file) covering: handoff created when coordination tasks present regardless of confidence threshold, no handoff when no coordination tasks, handoff payload contains recommendation_id/summary/assessment_id
- [X] T030c [P] [US3] Write unit tests for dead-letter handling in `tests/unit/test_risk_assessment_pipeline.py` (extend existing file) covering: handoff dead-lettered after 3 retry failures, `handoff_dead_lettered` audit record created with correct fields, no-escalation path stores recommendation for human review only when below all thresholds

### Implementation for User Story 3

- [X] T030 [P] [US3] Add `evacuation` recommendation type generator in `apps/agents/risk_assessment/agent.py`: generate from `route_risk` and `spread_prediction` (when severity ≥ high) assessments with signal-ID-inclusive explanation, severity from parent assessment
- [X] T031 [P] [US3] Add `resource_allocation` recommendation type generator in `apps/agents/risk_assessment/agent.py`: generate from `infrastructure_risk`, `community_impact`, and `impact_projection` assessments when coordination tasks are identified, with signal-ID-inclusive explanation
- [X] T032 [P] [US3] Add `coordination` and `infrastructure_action` recommendation type generators in `apps/agents/risk_assessment/agent.py`: coordination from multi-agency assessments, infrastructure_action from `infrastructure_risk` assessments
- [X] T033 [US3] Implement Evacuation Agent escalation logic in `apps/agents/risk_assessment/pipeline.py`: evaluate `evacuation` recommendations against severity ≥ `high` AND confidence ≥ 0.6 (from config), build `AgentHandoffEvent` with `target_agent=evacuation` and payload containing recommendation_id, summary, assessment_id
- [X] T034 [US3] Implement Resource Allocation Agent escalation logic in `apps/agents/risk_assessment/pipeline.py`: evaluate `resource_allocation` recommendations (coordination-task-based, no specific confidence threshold), build `AgentHandoffEvent` with `target_agent=resource_allocation` and payload per contract
- [X] T035 [US3] Implement dead-letter handling for downstream handoffs in `apps/agents/risk_assessment/pipeline.py`: after 3 retries exhausted, dead-letter the handoff, create `handoff_dead_lettered` audit record, surface dead-letter event to incident commanders via audit trail per FR-023
- [X] T036 [US3] Implement no-escalation path in `apps/agents/risk_assessment/pipeline.py`: when no threshold is met (confidence < 0.7 for public_alert, severity < high or confidence < 0.6 for evacuation, no coordination tasks), store recommendation for human review only per FR-024

**Checkpoint**: All three escalation targets (Communication, Evacuation, Resource Allocation) now operate with correct thresholds. Dead-lettered handoffs are surfaced.

---

## Phase 6: User Story 4 — Contradictory Signal Detection and Confidence Adjustment (Priority: P4)

**Goal**: Detect signals with opposing risk trajectories for the same incident and geographic area, flag contradictions in the assessment summary naming disagreeing sources, apply 30% multiplicative confidence reduction, and record each contradiction pair in the audit trail.

**Independent Test**: Provide two signals for the same location with opposing implications (one risk-increasing, one risk-decreasing) and verify the assessment summary flags the contradiction, names the disagreeing sources, and reduces the confidence level.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T037 [P] [US4] Write unit tests for contradiction detection in `tests/unit/test_risk_assessment_correlation.py` (extend existing file) covering: two opposing signals detected as contradiction, three-way disagreement applies single 30% reduction, no contradiction when all signals consistent, contradiction flag and source names in output, authoritative-vs-social contradiction treated same as same-authority, fresh-vs-stale signal contradiction

### Implementation for User Story 4

- [X] T038 [US4] Add `ContradictionDetector` class to `apps/agents/risk_assessment/correlation.py`: detect opposing risk trajectories per research.md §2 criteria (one signal risk_direction=increasing, another=decreasing for same hazard parameter and geographic area), return list of contradicting signal pairs with source names
- [X] T039 [US4] Implement 30% multiplicative confidence reduction in `apps/agents/risk_assessment/correlation.py`: `apply_contradiction_penalty(weighted_confidence, contradictions) -> float` applying `× 0.7` once per assessment regardless of number of contradiction pairs per research.md §2, bounded in [0.0, 1.0]
- [X] T040 [US4] Integrate contradiction detection into pipeline stage 4 in `apps/agents/risk_assessment/pipeline.py`: invoke `ContradictionDetector` after correlation (stage 3), populate `HazardAssessment.contradiction_detected`, `contradiction_details` (signal pairs and sources), adjust `confidence_adjusted` with penalty, flag assessment for human review
- [X] T041 [US4] Add contradiction details to assessment summary in `apps/agents/risk_assessment/pipeline.py`: include both perspectives in summary text, name disagreeing sources, create `contradiction_detected` audit record with signal IDs, source names, and confidence adjustment applied

**Checkpoint**: Contradictory signals are now detected, flagged, and confidence is adjusted. Assessment summaries include both perspectives for incident commander review.

---

## Phase 7: User Story 5 — Reproducible Predictions for Scenario-Based Testing (Priority: P5)

**Goal**: Given identical input signals and configuration, produce identical hazard category, severity level, and recommendation types. Store complete input snapshots for reproducibility verification. Support simulation tenant isolation.

**Independent Test**: Run the same set of signal inputs through the agent twice and verify both runs produce identical hazard assessments (same confidence, same summary structure, same recommendation types) when no model or configuration changes have occurred.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T042 [P] [US5] Write reproducibility contract tests in `tests/contract/test_risk_assessment_reproducibility.py` covering: identical inputs produce identical confidence/severity/recommendation types, configuration version tracked in each assessment, input snapshot contains all signals with provenance/freshness/confidence, model deployment ID recorded, simulation tenant assessments isolated from live data, simulation handoffs do not trigger live downstream handoffs

### Implementation for User Story 5

- [X] T043 [US5] Implement configuration version hashing in `apps/agents/risk_assessment/config.py`: `compute_config_hash() -> str` method producing a deterministic SHA-256 hash of all active configuration values (source weights, thresholds, escalation thresholds, validity hours) for reproducibility tracking per FR-025
- [X] T044 [US5] Implement complete input snapshot storage in `apps/agents/risk_assessment/pipeline.py`: populate `HazardAssessment.input_snapshot` with all input signals (confidence, freshness, provenance per signal), model deployment ID, prompt template version, configuration hash, and LLM deployment ID per FR-025
- [X] T045 [US5] Enforce LLM temperature=0 for all assessment and recommendation generation calls in `apps/agents/risk_assessment/agent.py`: set `temperature=0` in all `_generate_with_fallback` invocations per FR-026 and research.md §9
- [X] T046 [US5] Implement simulation tenant isolation in `apps/agents/risk_assessment/pipeline.py`: propagate `tenant_id` from inbound handoff through assessment/recommendation/outbound handoff, block simulation-tenant recommendations from triggering live downstream handoffs per FR-027, route simulation assessments to simulation-scoped Cosmos partitions via `incident_scope_key` format `{tenant_id}:{incident_id}`

**Checkpoint**: Reproducibility is guaranteed — identical inputs produce identical outputs, every assessment stores a complete input snapshot for verification, and simulation tenants are fully isolated.

---

## Phase 8: User Story 6 — Audit Trail of All Assessments and Decisions (Priority: P6)

**Goal**: Every processing step produces a `RiskAssessmentDecisionRecord` in Cosmos DB with the canonical 22 fields. When Cosmos is unavailable, records buffer to memory then file, with chronological recovery flush. Audit completeness is 100% verifiable.

**Independent Test**: Process a sequence of handoffs resulting in assessments and recommendations, then query the audit trail to verify every processing step produced a corresponding record with the required fields.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T047 [P] [US6] Write unit tests for three-tier audit degradation in `tests/unit/test_risk_assessment_audit.py` covering: tier 1 Cosmos write success, tier 2 memory buffer on Cosmos failure (bounded ring buffer at 10K), tier 3 JSONL file spill on buffer full, recovery flush order (memory → file → Cosmos chronological), `buffered_at` and `flush_source` annotation on recovered records, audit completeness verification (handoff_ids processed vs records created)

### Implementation for User Story 6

- [X] T048 [US6] Extend `AuditWriter` in `apps/agents/risk_assessment/audit.py` with tier 2 in-memory ring buffer: bounded `collections.deque` with `maxlen` from `RiskAssessmentConfig.audit_buffer_capacity` (default 10K), auto-fallback when Cosmos DB write raises exception, `buffered_at` timestamp annotation
- [X] T049 [US6] Extend `AuditWriter` in `apps/agents/risk_assessment/audit.py` with tier 3 file spill: JSONL append to `RiskAssessmentConfig.audit_buffer_file_path`, triggered when memory buffer is full, file rotation/size management
- [X] T050 [US6] Implement recovery flush in `apps/agents/risk_assessment/audit.py`: `flush_buffered_records() -> int` method flushing memory buffer then file buffer to Cosmos in chronological order, annotating each record with `flush_source` (`memory_buffer` or `file_buffer`), invoked periodically and on Cosmos recovery detection
- [X] T051 [US6] Add comprehensive audit records for every pipeline stage in `apps/agents/risk_assessment/pipeline.py`: ensure stages 1–8 each produce one or more `RiskAssessmentDecisionRecord` entries with correct `decision_type` — `handoff_received` (stage 1), `handoff_rejected` (stage 1 failure), `duplicate_discarded` (stage 1 dedup), `signals_retrieved` (stage 2), `assessment_generated` (stage 5), `recommendation_generated` (stage 6), `handoff_created`/`handoff_delivered`/`handoff_dead_lettered` (stage 7)
- [X] T052 [US6] Implement audit finalization (pipeline stage 8) in `apps/agents/risk_assessment/pipeline.py`: verify completeness by reconciling handoff_id processed against audit records created, log discrepancies, truncate `decision_rationale` to `MAX_REASONING_SUMMARY_LENGTH` (500 chars from config)

**Checkpoint**: Full audit trail operational with three-tier degradation. Every processing step is recorded and recoverable. Audit completeness is verifiable.

---

## Phase 9: User Story 7 — Graceful Degradation When Data or Services Are Unavailable (Priority: P7)

**Goal**: When the LLM service is unavailable, produce template-based assessments with 20% confidence reduction. When the signal store is partially unavailable, proceed with available signals and proportional confidence reduction. Log all degradation events. Never halt entirely for any single dependency failure.

**Independent Test**: Disable the LLM client (or configure it to return errors), send handoffs, and verify assessments are still produced with `generation_method=template_fallback` and a reduced confidence annotation.

### Implementation for User Story 7

- [X] T053 [US7] Implement full template-based assessment summaries in `apps/agents/risk_assessment/templates.py`: extend existing templates with all 5 assessment types (spread_prediction, impact_projection, route_risk, infrastructure_risk, community_impact) and all 5 recommendation types, ensuring each template includes signal-ID placeholders and is pre-approved (no runtime content safety check per FR-035)
- [X] T054 [US7] Implement 20% confidence reduction for LLM fallback mode in `apps/agents/risk_assessment/pipeline.py`: when `generation_method=template_fallback`, apply multiplicative `× 0.8` penalty AFTER contradiction penalty per research.md §4 penalty ordering (freshness → contradiction → fallback), set `generation_method` field on assessment and recommendation
- [X] T055 [US7] Implement partial signal store unavailability handling in `apps/agents/risk_assessment/pipeline.py`: when some signals cannot be retrieved, reduce confidence by `missing_count / total_count`, log missing signal IDs in audit record, proceed with available signals; when ALL signals missing, produce low-confidence assessment with degradation flag per contracts/assessment-pipeline.md §Stage 2
- [X] T056 [US7] Add degradation event logging and recovery detection in `apps/agents/risk_assessment/pipeline.py`: emit `degradation_detected` audit record for LLM timeout/error, Cosmos failure, and signal store timeout; detect LLM recovery on next successful call and log recovery event; emit `content_safety_failure` audit record when LLM output fails validation and is replaced with template per FR-035

**Checkpoint**: The agent now gracefully degrades under any single-dependency failure — LLM, signal store, Cosmos DB, or downstream agents. No processing halts. All degradation events are logged.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Health endpoint, human override API, observability instrumentation, infrastructure, and validation

- [X] T057 Implement `GET /health` endpoint in `apps/agents/risk_assessment/agent.py` with FastAPI: response schema per contracts/health-endpoint.md (status: healthy/degraded/unhealthy, agent_version, timestamp, checks for llm_connectivity, signal_store, processing_queue depth, audit_store buffer_depth), ≤1s SLA, port 8081
- [X] T058 Implement `POST /override` endpoint in `apps/agents/risk_assessment/agent.py` with FastAPI: request/response schema per contracts/health-endpoint.md (recommendation_id, action approve/reject/modify, user_id, role, justification), update recommendation status, create new version for modifications linked to original, record override in audit trail with `override_by_user_id`/`override_by_role`/`override_justification`/`override_timestamp` per FR-037/FR-038
- [X] T059 [P] Add OpenTelemetry distributed tracing in `apps/agents/risk_assessment/pipeline.py`: instrument span hierarchy per contracts/telemetry.md (root span `risk_assessment.process_handoff` with child spans for each pipeline stage: validate_handoff, retrieve_signals, correlate_signals, detect_contradictions, generate_assessment with nested llm_call/template_fallback and content_safety_check, assign_version, generate_recommendations, evaluate_escalation with nested deliver_handoff, write_audit), propagate correlation ID from `handoff_id`
- [X] T060 [P] Emit all metrics defined in contracts/telemetry.md in `apps/agents/risk_assessment/pipeline.py`: processing metrics (assessment_latency histogram, assessment_count, handoff_intake_count, handoff_rejected_count, duplicate_discard_count, sla_breach_count), escalation metrics (escalation_rate_by_type tagged by target_agent, handoff_success_rate, dead_letter_count), quality metrics (contradiction_detection_rate, confidence_distribution histogram, severity_distribution tagged, stale_signal_rate), degradation metrics (fallback_mode_activations, content_safety_failures, audit_buffer_depth, audit_tier), version metrics (version_count_per_incident, version_conflict_retries)
- [X] T061 [P] Emit custom events per contracts/telemetry.md in `apps/agents/risk_assessment/pipeline.py`: HandoffReceived (stage 1), AssessmentGenerated (stage 5), ContradictionDetected (stage 4), EscalationTriggered (stage 7), DegradationEvent (any fallback), SLABreach (processing > 10s), VersionConflict (OCC retry)
- [X] T062 [P] Write integration tests for Cosmos DB persistence in `tests/integration/test_risk_assessment_cosmos.py` covering: HazardAssessment write/read with partition key, Recommendation write/read, RiskAssessmentDecisionRecord append-only write, version counter optimistic concurrency, assessment status transitions (active → superseded/expired)
- [X] T063 [P] Write integration tests for Service Bus handoff intake in `tests/integration/test_risk_assessment_service_bus.py` covering: message deserialization to AgentHandoffEvent, message acknowledgement on success, poison message handling, queue consumer lifecycle
- [X] T064 [P] Extend bushfire scenario simulation test in `tests/simulation/test_bushfire_risk_assessment.py` with Risk Assessment Agent: send fire-category handoffs, verify assessment generation, recommendation creation, Communication Agent escalation, audit trail completeness
- [X] T065 [P] Add/update Bicep modules in `infra/` for: Cosmos DB containers (`risk-assessments`, `risk-recommendations`, `risk-assessment-decisions` with partition key `/incident_scope_key`), Service Bus queue for handoff intake, Container Apps configuration (port 8081, auto-scaling rules based on queue depth), managed identity for Cosmos DB and Service Bus access
- [ ] T066 Run quickstart.md validation: execute all steps from `specs/012-risk-assessment-agent/quickstart.md` (setup, environment variables, local run, health check, synthetic handoff, test suite) and verify end-to-end operation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — core pipeline, MVP
- **US2 (Phase 4)**: Depends on US1 — builds on assessment to generate recommendations + Communication escalation
- **US3 (Phase 5)**: Depends on US2 — extends escalation to Evacuation + Resource Allocation agents
- **US4 (Phase 6)**: Depends on US1 — adds contradiction detection to correlation stage; independent of US2/US3
- **US5 (Phase 7)**: Depends on US1 — adds reproducibility tracking; independent of US2/US3/US4
- **US6 (Phase 8)**: Depends on US1 — extends basic audit to three-tier degradation; independent of US2-US5
- **US7 (Phase 9)**: Depends on US1 — adds degradation handling; independent of US2-US6
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2)**: Depends on US1 for assessment generation — adds recommendation + Communication escalation
- **US3 (P3)**: Depends on US2 for recommendation generation pattern — adds Evacuation + Resource Allocation escalation
- **US4 (P4)**: Can start after US1 — independent of US2/US3; adds to correlation stage
- **US5 (P5)**: Can start after US1 — independent of US2/US3/US4; adds reproducibility tracking
- **US6 (P6)**: Can start after US1 — independent of US2-US5; extends audit writer
- **US7 (P7)**: Can start after US1 — independent of US2-US6; adds degradation paths

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/enums before services
- Services before pipeline integration
- Core implementation before escalation/integration logic
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T004, T005, T006, T008 can all run in parallel (different files)
- **Phase 3**: All test tasks (T009–T013) can run in parallel; implementation tasks T014–T019 can all run in parallel (different files); T020–T022 are sequential (depend on services)
- **Phase 4**: Test tasks (T023, T024) can run in parallel; T025–T027 can run in parallel (same file but different methods)
- **Phase 5**: T030, T031, T032 can run in parallel (different recommendation types)
- **Phase 6**: US4, US5, US6, US7 can all start in parallel after US1 completes (if team capacity allows)
- **Phase 10**: T059, T060, T061, T062, T063, T064, T065 can all run in parallel (different files/concerns)

---

## Parallel Example: User Story 1

```text
# After Foundational phase completes, launch all US1 tests in parallel:
T009: "Unit tests for handoff deduplication in tests/unit/test_risk_assessment_dedup.py"
T010: "Unit tests for signal correlation in tests/unit/test_risk_assessment_correlation.py"
T011: "Unit tests for severity computation in tests/unit/test_risk_assessment_severity.py"
T012: "Unit tests for version counter in tests/unit/test_risk_assessment_versioning.py"
T013: "Unit tests for pipeline stages 1-5 in tests/unit/test_risk_assessment_pipeline.py"

# Then launch all US1 service modules in parallel:
T014: "HandoffDeduplicator in apps/agents/risk_assessment/dedup.py"
T015: "SignalCorrelator in apps/agents/risk_assessment/correlation.py"
T016: "SeverityComputer in apps/agents/risk_assessment/severity.py"
T017: "VersionCounter in apps/agents/risk_assessment/versioning.py"
T018: "Template generators in apps/agents/risk_assessment/templates.py"
T019: "AuditWriter in apps/agents/risk_assessment/audit.py"

# Then sequential pipeline integration:
T020: "Assessment generation method in agent.py"
T021: "Pipeline orchestrator stages 1-5 in pipeline.py"
T022: "Service Bus consumer wiring in agent.py"
```

## Parallel Example: After US1 Completes

```text
# US4, US5, US6, US7 can all start in parallel (independent of each other):
Developer A: US4 (Contradiction Detection) — T037-T041
Developer B: US5 (Reproducibility) — T042-T046
Developer C: US6 (Audit Trail) — T047-T052
Developer D: US7 (Graceful Degradation) — T053-T056

# US2 and US3 must be sequential (US3 depends on US2):
Developer E: US2 (Communication Escalation) — T023-T029, then US3 — T030-T036
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T008) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T009–T022)
4. **STOP and VALIDATE**: Send synthetic handoff, verify HazardAssessment is produced with traceable signal IDs, correct confidence, and version number
5. Deploy/demo if ready — the agent can receive handoffs and generate assessments

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test: synthetic handoff → versioned assessment (**MVP!**)
3. Add US2 → Test: assessment → recommendation → Communication handoff
4. Add US3 → Test: recommendation → Evacuation/Resource Allocation handoffs
5. Add US4 → Test: opposing signals → contradiction flag + confidence reduction
6. Add US5 → Test: identical inputs → identical outputs + simulation isolation
7. Add US6 → Test: Cosmos outage → memory buffer → file spill → recovery
8. Add US7 → Test: LLM outage → template fallback + 20% penalty
9. Polish → Health endpoint, observability, infrastructure, quickstart validation

### Parallel Team Strategy

With multiple developers after US1 completes:

1. Team completes Setup + Foundational + US1 together
2. Once US1 is done:
   - Developer A: US2 → US3 (sequential, Communication then Evacuation/Resource)
   - Developer B: US4 (Contradiction Detection — independent)
   - Developer C: US5 + US6 (Reproducibility + Audit — related concerns)
   - Developer D: US7 (Graceful Degradation — independent)
3. All developers: Polish phase (parallelizable tasks)

---

## Notes

- [P] tasks = different files, no dependencies on concurrent tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after US1 (MVP)
- US2 → US3 is the only strict inter-story dependency (escalation pattern reuse)
- US4, US5, US6, US7 are all independent of each other and of US2/US3
- Penalty stacking order is fixed: freshness (in averaging) → contradiction (×0.7) → fallback (×0.8) per research.md §4
- Plan.md identifies 5 bugs in existing `agent.py` — addressed in US1 (T020) and US2 (T025, T026, T027)
- All Cosmos containers use partition key `/incident_scope_key` with format `{tenant_id}:{incident_id}`
- Port 8081 avoids conflict with Monitoring Agent (port 8080)
- Commit after each task or logical group; stop at any checkpoint to validate independently
