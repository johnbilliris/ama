# Tasks: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

**Input**: Design documents from `/specs/003-rubric-gap-closure/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — the project constitution mandates TDD and the quickstart defines a test-first validation flow (Phases A–H).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install new dependencies and configure environment for feature 003.

- [X] T001 Add openai, tenacity, pytest-benchmark, and locust dependencies to apps/api/pyproject.toml and apps/agents/pyproject.toml
- [X] T002 Update apps/agents/.env.example with AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_REASONING_DEPLOYMENT, and AZURE_OPENAI_DRAFTING_DEPLOYMENT variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared domain models and services required by multiple user stories. MUST complete before any user story work begins.

**⚠️ CRITICAL**: US1 needs the LLM client infrastructure, US3 and US7 both depend on the dead-letter service and extended event bus.

- [X] T003 [P] Create DeadLetterEntry Pydantic model with entryId, entryType, correlationId, originalPayload, failureReason, failureCode, retryCount, sourceService, targetService, incidentId, tenantScopeKey, resolution, and timestamps in packages/domain/src/domain/models/dead_letter_entry.py per data-model.md
- [X] T004 [P] Add dead_letter_entry import to apps/api/app/services/state_store.py and create DEAD_LETTERS store
- [X] T005 Create dead-letter service with store, query (by entryType, resolution, incidentId with pagination), and resolve (replayed, discarded, escalated) operations in apps/api/app/services/dead_letter_service.py per contracts/openapi-addendum.yaml
- [X] T006 Extend EventBus with subscriber registration (`subscribe(channel, handler)`), dispatch to handlers (`publish()` invokes handlers), delivery status tracking (success/failure per subscriber), and dead-letter routing on permanent delivery failure via dead_letter_service in apps/api/app/services/event_bus.py per data-model.md EventBus modifications

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Agents produce AI-generated outputs (Priority: P1) 🎯 MVP

**Goal**: Integrate Azure OpenAI into Risk Assessment and Communication agents with template fallback and content safety validation.

**Independent Test**: Ingest mixed-provenance signals for a simulated bushfire incident and verify Risk Assessment returns LLM-generated explanation with cited signal IDs, and Communication returns 6-language alert draft, both within acceptable latency and token budgets.

**Covers**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006 · SC-001, SC-002, SC-003

### Models for User Story 1

- [X] T007 [P] [US1] Create ModelDeployment Pydantic model with deploymentId, endpointUrl, modelName, modelVersion, apiVersion, tokenBudgetInput, tokenBudgetOutput, contentSafetyPolicy, fallbackMode, timeoutSeconds, purpose (reasoning/drafting), and status in packages/domain/src/domain/models/model_deployment.py per data-model.md
- [X] T008 [P] [US1] Add generationMethod (llm/template/template_fallback/safety_fallback), modelDeploymentId, and tokenUsage ({input_tokens, output_tokens}) fields to Recommendation model in packages/domain/src/domain/models/recommendation.py per data-model.md modifications
- [X] T009 [P] [US1] Add generationMethod, modelDeploymentId, and contentSafetyResult (passed/failed_with_fallback/not_checked) fields to PublicAlert model in packages/domain/src/domain/models/public_alert.py per data-model.md modifications

### Services for User Story 1

- [X] T010 [US1] Create Azure OpenAI LLM client wrapper with AzureOpenAI SDK, dual-model config (reasoning deployment for Risk Assessment, drafting deployment for Communication), correlation ID propagation via request headers, and token usage logging (input_tokens, output_tokens, latency, deploymentId) in apps/agents/common/llm_client.py per research.md decision 1
- [X] T011 [P] [US1] Create rule-based content safety validator with keyword filtering (profanity/harm dictionary), length validation, and language detection confirming output matches requested language codes in apps/agents/common/content_safety.py per research.md decision 3
- [X] T012 [US1] Create LLMCallMixin with configurable token budget enforcement (truncation or re-request on overage), template fallback on model failure (marks generationMethod=template_fallback), content safety validation on outputs (marks generationMethod=safety_fallback on failure), and latency/token logging with correlation ID in apps/agents/common/llm_mixin.py per research.md decision 2

### Implementation for User Story 1

- [X] T013 [US1] Update Risk Assessment agent to use LLMCallMixin for LLM-generated recommendation explanations that cite specific signal IDs, state confidence level, and populate generationMethod + modelDeploymentId + tokenUsage on the Recommendation model in apps/agents/risk_assessment/agent.py
- [X] T014 [US1] Update Communication agent to use LLMCallMixin for generating public alert content_blocks in all 6 languages (en-AU, zh-Hans, ar, vi, el, it) with contentSafetyResult tracking in apps/agents/communication/agent.py

### Tests for User Story 1

- [X] T015 [P] [US1] Write contract test verifying Risk Assessment produces LLM explanation citing ≥1 signal ID with generationMethod=llm when model endpoint is available in tests/contract/test_risk_assessment_llm.py (validates SC-001)
- [X] T016 [P] [US1] Write contract test verifying Communication produces content_blocks keyed by all 6 language codes with generationMethod=llm within 30s latency budget in tests/contract/test_communication_llm.py (validates SC-002)
- [X] T017 [P] [US1] Write contract test verifying template fallback on mocked unavailable endpoint (generationMethod=template_fallback, completes <2s) and content safety fallback on flagged content (generationMethod=safety_fallback, logs flagged content with correlation ID) in tests/contract/test_llm_fallback.py (validates SC-003)
- [X] T018 [P] [US1] Write contract test verifying token budget enforcement handles overage with truncation or re-request and logs the overage event in tests/contract/test_token_budget.py (validates FR-003)
- [X] T019 [P] [US1] Write contract test verifying LLM call logs contain correlation ID, token usage (input_tokens + output_tokens), latency, and model deployment identifier in tests/contract/test_llm_logging.py (validates FR-005)

**Checkpoint**: User Story 1 complete — Risk Assessment and Communication agents produce LLM-generated outputs with fallback and safety validation

---

## Phase 4: User Story 2 — Every code change is automatically validated (Priority: P2)

**Goal**: Complete CI/CD pipeline with full test execution, linting, type-checking, web build, and performance regression check.

**Independent Test**: Create a PR with a failing test and verify the pipeline blocks merge, then fix it and verify the pipeline passes.

**Covers**: FR-007, FR-008, FR-009, FR-010, FR-030 · SC-004, SC-012 (CI benchmark portion)

### Implementation for User Story 2

- [X] T020 [US2] Update ci.yml with Python test execution (pytest), Python lint (ruff check), TypeScript type-check (tsc --noEmit), and web build (pnpm build) stages, adding 003-rubric-gap-closure to branch triggers in .github/workflows/ci.yml. Use stage names matching PipelineStage.stageName values (python-test, python-lint, ts-typecheck, web-build, perf-benchmark) to satisfy FR-010 stage-by-stage summary via GitHub Actions step naming.
- [X] T021 [US2] Add lightweight performance benchmark stage (<60s, ~50 concurrent requests) using pytest-benchmark to ci.yml, checking key endpoint p95 latency against configured thresholds and blocking merge on regression in .github/workflows/ci.yml (validates FR-030)
- [X] T022 [US2] Create pytest-benchmark fixture that starts the FastAPI app, sends ~50 concurrent requests to dashboard and signal endpoints, and compares p95 latency against stored baselines in tests/benchmark/test_api_performance.py

**Checkpoint**: User Story 2 complete — CI pipeline runs all quality gates on every PR and blocks merge on failure

---

## Phase 5: User Story 3 — Agents coordinate through event-driven handoffs (Priority: P3)

**Goal**: Implement automatic handoff chaining (Monitoring → Risk Assessment → Communication) with retry, dead-letter, and audit timeline recording.

**Independent Test**: Ingest a high-risk authoritative signal and verify the full chain completes automatically without manual intervention, with each handoff recorded as a timeline event.

**Covers**: FR-011, FR-012, FR-013, FR-014 · SC-005

### Models for User Story 3

- [X] T023 [P] [US3] Extend AgentHandoff to AgentHandoffEvent Pydantic model with handoffId, incidentId, status (pending/delivered/retrying/failed/dead_lettered), retryCount, maxRetries, retryWindowSeconds, nextRetryAt, timelineEventId, deadLetterEntryId, createdAt, deliveredAt, failedAt, and failureReason in apps/agents/common/handoffs.py per data-model.md AgentHandoffEvent
- [X] T024 [P] [US3] Add handoff, dead_letter, and llm_call to TimelineEvent event_type enum and add handoff payload fields (source_agent, target_agent, scope_key, confidence, handoff_status, payload_summary) in packages/domain/src/domain/models/timeline_event.py per data-model.md TimelineEvent modifications

### Implementation for User Story 3

- [X] T025 [US3] Update Monitoring agent to publish a typed AgentHandoffEvent to the Risk Assessment agent via event bus when a signal is classified as high-risk, scoped to the incident tenant in apps/agents/monitoring/agent.py (implements FR-011)
- [X] T026 [US3] Update Risk Assessment agent to publish a typed AgentHandoffEvent to the Communication agent when a recommendation of type public_alert with high confidence is produced in apps/agents/risk_assessment/agent.py (implements FR-012)
- [X] T027 [US3] Implement handoff delivery retry with exponential backoff (3 attempts over 5 minutes) respecting circuit breaker state, and dead-letter routing on exhaustion via dead_letter_service in apps/agents/common/handoffs.py (implements FR-014)
- [X] T028 [US3] Record a TimelineEvent for every agent-to-agent handoff capturing source agent, target agent, scope key, confidence, and payload summary in apps/api/app/services/event_bus.py (implements FR-013)
- [X] T029 [US3] Create handoff status API route: GET /incidents/{incidentId}/handoffs listing AgentHandoffEvents with status filtering in apps/api/app/api/handoffs.py and register in apps/api/app/main.py per contracts/openapi-addendum.yaml

### Tests for User Story 3

- [X] T030 [US3] Write integration test verifying full Monitoring → Risk Assessment → Communication handoff chain completes automatically within 30s with each handoff recorded as a TimelineEvent in tests/integration/test_handoff_chain.py (validates SC-005)
- [X] T031 [US3] Write integration test verifying handoff retry on open circuit breaker (3 retries over 5 min) and dead-letter on exhaustion with correct DeadLetterEntry fields in tests/integration/test_handoff_retry.py (validates FR-014)

**Checkpoint**: User Story 3 complete — agents chain automatically through event-driven handoffs with audit trail

---

## Phase 6: User Story 4 — Application containers are deployable from source (Priority: P4)

**Goal**: Create Dockerfiles for API and agent runtime that build reproducible, secure container images.

**Independent Test**: Build each Dockerfile locally, run the container, and verify the health endpoint responds.

**Covers**: FR-015, FR-016, FR-017 · SC-006

### Implementation for User Story 4

- [X] T032 [P] [US4] Create multi-stage Dockerfile for API service with python:3.12-slim base, builder stage for dependency installation, runtime stage copying only installed packages + app code, non-root user, health check command (`curl -f http://localhost:8000/health`), and exposed port 8000 in apps/api/Dockerfile. Verify a second build after a code-only change reuses the dependency layer (faster than clean build). No embedded secrets. (implements FR-015, FR-017)
- [X] T033 [P] [US4] Create multi-stage Dockerfile for agent runtime with python:3.12-slim base, builder stage for dependency installation, runtime stage with non-root user in apps/agents/Dockerfile. Verify a second build after a code-only change reuses the dependency layer. No embedded secrets. (implements FR-016, FR-017)
- [X] T034 [US4] Create /health endpoint returning JSON {status: healthy|degraded, version: string, dependencies: {cosmos: status, redis: status, openai: status}} in apps/api/app/api/health.py and register route in apps/api/app/main.py. Return dependency status `stub` for in-memory backends when no real connection string is configured. Matches contracts/openapi-addendum.yaml /health schema.

**Checkpoint**: User Story 4 complete — both images build in <5min clean / <2min incremental, pass health checks, run as non-root

---

## Phase 7: User Story 5 — Infrastructure is defined as code (Priority: P5)

**Goal**: Provision all application resources (Container Apps, Cosmos DB, Redis, Blob Storage, Azure OpenAI) via Bicep with Australian data residency and managed identity.

**Independent Test**: Run `az deployment group what-if` and verify all resources are planned in an Australian region with correct configurations.

**Covers**: FR-018, FR-019, FR-020, FR-026, FR-027 · SC-007, SC-011

### Implementation for User Story 5

- [X] T035 [US5] Create main.bicep provisioning Container Apps Environment, Container Apps (API + agents), Cosmos DB account, Redis Cache, Blob Storage, and Azure OpenAI resource with managed identity for inter-service auth, Australian region enforcement (australiaeast), and monitoring integration via diagnostic settings referencing monitoring.bicep outputs in infra/bicep/main.bicep (implements FR-018, FR-019, FR-020)
- [X] T036 [US5] Add AlertActionGroup resource (Microsoft.Insights/actionGroups) with email and webhook notification targets (shortName ≤12 chars, ≥1 enabled target) and link to existing error-rate and latency alert rules in infra/bicep/monitoring.bicep per data-model.md AlertActionGroup (implements FR-026)
- [X] T037 [US5] Complete the latency alert rule threshold configuration (currently has incomplete criterionType for p99 threshold) and validate alongside the existing error-rate alert in infra/bicep/monitoring.bicep (implements FR-027)

**Checkpoint**: User Story 5 complete — `az deployment group what-if` validates all resources in Australian region with managed identity

---

## Phase 8: User Story 6 — Executive-ready demo walkthrough (Priority: P6)

**Goal**: Produce a version-controlled demo screenplay and executive slide deck demonstrating the full incident workflow.

**Independent Test**: A non-technical reviewer reads the walkthrough and can describe the hub's purpose, core workflow, and measurable impact.

**Covers**: FR-021, FR-022 · SC-008

### Implementation for User Story 6

- [X] T038 [P] [US6] Create annotated demo walkthrough screenplay covering: incident activation → signal ingestion → dashboard → persona workspace → recommendation approval → multilingual alert publishing → scenario replay, with embedded screenshot/GIF placeholders for every major UI surface, in under 5 minutes reading time in docs/disaster-response-hub/demo/walkthrough.md per research.md decision 10 (implements FR-021)
- [X] T039 [P] [US6] Create executive slide deck with value proposition narrative, core architecture diagram, before/after KPI comparisons (response time 50% reduction, evacuation 24h earlier, resource efficiency 30% improvement, operator UX), and annotated screenshots of every major UI surface in docs/disaster-response-hub/demo/executive-deck.md (implements FR-022)

**Checkpoint**: User Story 6 complete — demo materials exist in repository for evaluator review

---

## Phase 9: User Story 7 — Errors are handled robustly with actionable alerts (Priority: P7)

**Goal**: Implement structured error responses, exponential-backoff retries for transient failures, and dead-letter API routes for operator inspection.

**Independent Test**: Simulate a Cosmos DB transient failure and verify retry succeeds, then simulate a permanent failure and verify the alert fires and the failed operation lands in the dead-letter store.

**Covers**: FR-023, FR-024, FR-025 · SC-009, SC-010

### Implementation for User Story 7

- [X] T040 [US7] Create structured error handler middleware returning ErrorResponse (correlationId as UUID, statusCode, errorCategory from enum [validation_error, dependency_failure, authorization_error, not_found, internal_error, rate_limited], non-leaking message) for all API failure modes in apps/api/app/middleware/error_handler.py and register in apps/api/app/main.py per contracts/openapi-addendum.yaml ErrorResponse schema (implements FR-023)
- [X] T041 [US7] Add tenacity retry decorators with exponential backoff (3 attempts, jitter, configurable stop/wait) for transient Cosmos DB and Redis failures on state_store and cache service methods in apps/api/app/middleware/resilience.py per research.md decision 4 (implements FR-024)
- [X] T042 [US7] Create dead-letter API routes: GET /dead-letters (list with entryType, resolution, incidentId, limit, offset filtering) and POST /dead-letters/{entryId}/resolve (resolution + resolvedByPersonaId + optional notes) in apps/api/app/api/dead_letters.py and register in apps/api/app/main.py per contracts/openapi-addendum.yaml (implements FR-025 API surface)

### Tests for User Story 7

- [X] T043 [P] [US7] Write contract test verifying all error responses return structured JSON matching ErrorResponse schema (correlationId, statusCode, errorCategory, non-leaking message; no stack traces) in tests/contract/test_error_responses.py (validates SC-009)
- [X] T044 [P] [US7] Write integration test verifying exponential-backoff retry on simulated transient storage failure (recovers within 3 attempts, 90%+ success rate) and dead-letter on permanent failure (correct DeadLetterEntry with correlationId and failureReason) in tests/integration/test_retry_dead_letter.py (validates SC-010)

**Checkpoint**: User Story 7 complete — errors return structured responses, transient failures are retried, and failed operations are dead-lettered

---

## Phase 10: User Story 8 — Performance targets are validated under load (Priority: P8)

**Goal**: Create a load test suite that validates documented performance targets and a pass/fail report comparing measured values.

**Independent Test**: Run the load test suite against the local API and verify results meet or fail documented thresholds.

**Covers**: FR-028, FR-029 · SC-012 (load test portion)

### Models for User Story 8

- [X] T045 [US8] Create LoadTestResult Pydantic model with resultId, scenarioName, executedAt, durationSeconds, concurrentUsers, totalRequests, successfulRequests, failedRequests, errorRate, p50/p95/p99 latency, throughputPerSecond, targetName, targetThreshold, targetUnit, passed, environment, and notes in packages/domain/src/domain/models/load_test_result.py per data-model.md

### Implementation for User Story 8

- [X] T046 [US8] Create Locust load test suite with dashboard concurrent load scenario (1,000 users, target p95 <2s) and signal burst ingestion scenario (50,000 signals/hour, target <1% error rate) using headless mode in tests/load/locustfile.py per research.md decision 6 (implements FR-028)
- [X] T047 [US8] Create load test report generator that parses Locust stats CSV/JSON output and produces a pass/fail report per documented performance target (dashboard_p95_lt_2s, read_api_p95_lt_500ms, signal_throughput_50k_hr) in tests/load/report.py (implements FR-029)

**Checkpoint**: User Story 8 complete — load test validates dashboard p95 <2s, read API p95 <500ms, signal throughput 50k/hour

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Schema updates, final integration validation, and full acceptance check.

- [X] T048 Update packages/schemas/openapi.yaml with new endpoints (/health, /dead-letters, /dead-letters/{entryId}/resolve, /incidents/{incidentId}/handoffs) and all new schemas (DeadLetterEntry, AgentHandoffEvent, ModelDeployment, ErrorResponse) and modified schemas (Recommendation, PublicAlert, TimelineEvent) from contracts/openapi-addendum.yaml
- [X] T049 Run full test suite (pytest + Playwright) and verify all 13 success criteria (SC-001 through SC-013) from spec.md pass
- [X] T050 Run quickstart.md scenario rehearsal (LLM-augmented incident flow, steps 1–9) end-to-end and record results
- [X] T051 Install/enable pnpm in CI-like local environment and run Playwright suite (`pnpm --filter ./apps/web exec playwright test`) to complete T049 web validation portion
- [ ] T052 Provision test Azure OpenAI configuration and execute quickstart scenario rehearsal with real model calls to complete T050
- [X] T053 Add live Azure OpenAI rehearsal runbook and gated simulation test for credentialed execution in docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md and tests/simulation/test_quickstart_live_llm_rehearsal.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–10)**: All depend on Foundational phase completion
  - US1 (P1): Can start after Phase 2 — no dependencies on other stories
  - US2 (P2): Can start after Phase 2 — no dependencies on other stories
  - US3 (P3): Can start after Phase 2 — independent, but US1 enriches the chain with LLM outputs
  - US4 (P4): Can start after Phase 2 — no dependencies on other stories
  - US5 (P5): Can start after Phase 2 — no dependencies on other stories
  - US6 (P6): Can start after Phase 2 — benefits from US1+US3 being complete for screenshots
  - US7 (P7): Can start after Phase 2 — uses shared dead-letter foundation from Phase 2
  - US8 (P8): Can start after Phase 2 — benefits from US1+US3 for realistic load scenarios
- **Polish (Phase 11)**: Depends on all user stories being complete

### Within Each User Story

- Models before services
- Services before implementation
- Core implementation before integration
- Tests verify each story independently
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 2** (after Setup):
- T003 and T004 can run in parallel (different files)

**Phase 3 — US1** (after Foundational):
- T007, T008, T009 can run in parallel (different model files)
- T010 and T011 can run in parallel (different service files)
- T015, T016, T017, T018, T019 can run in parallel (different test files)

**Phases 3–10** (after Foundational):
- US1, US2, US3, US4, US5, US6, US7, US8 can all be worked on in parallel by different team members

**Phase 5 — US3** (after Foundational):
- T023 and T024 can run in parallel (different model files)

**Phase 6 — US4**:
- T032 and T033 can run in parallel (different Dockerfiles)

**Phase 8 — US6**:
- T038 and T039 can run in parallel (different doc files)

**Phase 9 — US7**:
- T043 and T044 can run in parallel (different test files)

---

## Parallel Example: User Story 1

```text
# Launch all models in parallel:
T007: Create ModelDeployment model in packages/domain/src/domain/models/model_deployment.py
T008: Add fields to Recommendation in packages/domain/src/domain/models/recommendation.py
T009: Add fields to PublicAlert in packages/domain/src/domain/models/public_alert.py

# Then launch independent services in parallel:
T010: Create LLM client wrapper in apps/agents/common/llm_client.py
T011: Create content safety validator in apps/agents/common/content_safety.py

# Sequential: LLM mixin depends on client + safety:
T012: Create LLMCallMixin in apps/agents/common/llm_mixin.py

# Sequential: agents depend on mixin:
T013: Update Risk Assessment agent in apps/agents/risk_assessment/agent.py
T014: Update Communication agent in apps/agents/communication/agent.py

# Launch all tests in parallel:
T015: Contract test for Risk Assessment LLM in tests/contract/test_risk_assessment_llm.py
T016: Contract test for Communication LLM in tests/contract/test_communication_llm.py
T017: Contract test for fallback behavior in tests/contract/test_llm_fallback.py
T018: Contract test for token budget in tests/contract/test_token_budget.py
T019: Contract test for LLM call logging (FR-005) in tests/contract/test_llm_logging.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (AI Integration)
4. **STOP and VALIDATE**: Verify LLM explanations cite signal IDs, 6-language drafts are produced, fallback works
5. Demo-ready: agents produce real AI-generated content

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (AI Integration) → Agents produce LLM outputs → **MVP!**
3. US2 (CI/CD) → Every PR is validated automatically
4. US3 (Orchestration) → Agents chain dynamically
5. US4 (Containers) → Images deployable from source
6. US5 (IaC) → Full environment provisionable
7. US6 (Demo) → Executive-ready walkthrough exists
8. US7 (Error Handling) → Robust retry + dead-letter + alerts
9. US8 (Performance) → Load test validates targets
10. Polish → Schema sync, full validation, rubric re-evaluation

### Suggested MVP Scope

**User Story 1 (AI Integration)** is the MVP — it closes the highest-impact rubric gap (AI model selection/deployment: 3/5 → 5/5) with the fewest dependencies.

---

## Coverage Matrix

### Functional Requirements → Tasks

| FR | Task(s) | User Story |
|----|---------|------------|
| FR-001 | T013, T015 | US1 |
| FR-002 | T014, T016 | US1 |
| FR-003 | T012, T018 | US1 |
| FR-004 | T012, T017 | US1 |
| FR-005 | T010, T019 | US1 |
| FR-006 | T011, T012, T017 | US1 |
| FR-007 | T020 | US2 |
| FR-008 | T020 | US2 |
| FR-009 | T020 | US2 |
| FR-010 | T020 | US2 |
| FR-011 | T025 | US3 |
| FR-012 | T026 | US3 |
| FR-013 | T028, T029 | US3 |
| FR-014 | T027, T031 | US3 |
| FR-015 | T032, T034 | US4 |
| FR-016 | T033 | US4 |
| FR-017 | T032, T033 | US4 |
| FR-018 | T035 | US5 |
| FR-019 | T035 | US5 |
| FR-020 | T035 | US5 |
| FR-021 | T038 | US6 |
| FR-022 | T039 | US6 |
| FR-023 | T040, T043 | US7 |
| FR-024 | T041 | US7 |
| FR-025 | T005, T042, T044 | Foundation + US7 |
| FR-026 | T036 | US5 |
| FR-027 | T037 | US5 |
| FR-028 | T046 | US8 |
| FR-029 | T047 | US8 |
| FR-030 | T021, T022 | US2 |

### Success Criteria → Validation

| SC | Validates Via | Task(s) |
|----|-------------|---------|
| SC-001 | Contract test: ≥1 signal ID citation | T015 |
| SC-002 | Contract test: 6 language codes, <30s | T016 |
| SC-003 | Contract test: fallback <2s, zero lost | T017 |
| SC-004 | CI pipeline run log | T020, T021 |
| SC-005 | Integration test: chain <30s + timeline | T030 |
| SC-006 | Docker build + run + health check | T032, T033, T034 |
| SC-007 | az deployment group what-if | T035 |
| SC-008 | File existence check | T038, T039 |
| SC-009 | Contract test: structured JSON | T043 |
| SC-010 | Integration test: retry 90%+ recovery | T044 |
| SC-011 | Action group config in Bicep | T036 |
| SC-012 | Locust report + pytest-benchmark | T021, T022, T046, T047 |
| SC-013 | Post-implementation rubric evaluation | T049, T050 |
