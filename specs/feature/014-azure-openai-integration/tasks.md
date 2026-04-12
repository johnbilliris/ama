# Tasks: Azure OpenAI Integration Configuration

**Input**: Design documents from `/specs/014-azure-openai-integration/` and `/specs/feature/014-azure-openai-integration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — contract and integration tests explicitly requested in the feature specification (plan.md project structure, spec.md user stories US1–US8).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `apps/agents/common/`, `apps/agents/{agent}/`
- **Infrastructure**: `infra/`, `infra/modules/`
- **Tests**: `tests/contract/`, `tests/integration/`, `tests/simulation/`
- **Docs**: `docs/risk-register/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialisation — new modules, dependencies, shared configuration dataclass

- [x] T001 Add `azure-identity` dependency to project in `pyproject.toml` (verify `openai`, `tenacity`, `opentelemetry-api`, `opentelemetry-sdk` already present)
- [x] T002 Create shared LLM configuration dataclass `LLMClientConfig` in `apps/agents/common/llm_config.py` with all fields from data-model.md entity 1 (endpoint, deployments, model_tier, temperature, max_output_tokens, retry, circuit breaker, confidence, budget), frozen dataclass with env-var defaults via `field(default_factory=lambda: os.getenv(...))`, and `__post_init__` validation per contracts/llm-config.md
- [x] T003 [P] Create circuit breaker state machine `CircuitBreaker` with `CircuitState` enum in `apps/agents/common/circuit_breaker.py` — implement `can_execute()`, `record_success()`, `record_failure()`, `state` property with thread-safe `threading.Lock`, injectable clock for testing, per data-model.md entity 2

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core LLM client refactoring and mixin updates that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Refactor `LLMClient.__init__()` in `apps/agents/common/llm_client.py` — replace `AzureOpenAI(api_key=...)` with `AzureOpenAI(azure_ad_token_provider=get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"))`, accept optional `LLMClientConfig` parameter, add Australian endpoint validation (hostname must contain `australiaeast` or `australiasoutheast`), remove all `AZURE_OPENAI_API_KEY` references per contracts/llm-client.md and research.md R1
- [x] T005 Refactor `LLMClient.generate_response()` in `apps/agents/common/llm_client.py` — add `temperature` parameter (default 0.0), route `purpose` to correct deployment via `config.reasoning_deployment` / `config.drafting_deployment`, include `deployment_id`, `correlation_id`, `latency_ms`, `token_usage` in response dict, configure retry via `tenacity` with config-driven `retry_attempts`, `retry_min_wait`, `retry_max_wait` per contracts/llm-client.md
- [x] T006 Integrate circuit breaker into `LLMCallMixin._generate_with_fallback()` in `apps/agents/common/llm_mixin.py` — check `circuit_breaker.can_execute()` before LLM call, call `record_success()` / `record_failure()` on outcome, skip directly to template fallback when circuit is OPEN, add `circuit_breaker_state` and `confidence_adjustment` to fallback response dict per data-model.md entity 4
- [x] T007 Add confidence threshold gating to `LLMCallMixin` in `apps/agents/common/llm_mixin.py` — when `generation_method` is `template_fallback`, multiply confidence by `fallback_reduction_factor`; when confidence is below `confidence_threshold`, set `requires_human_review: true` and block automatic escalation per research.md R4
- [x] T007b Add structured output validation to `LLMCallMixin._generate_with_fallback()` in `apps/agents/common/llm_mixin.py` — after receiving LLM response, validate JSON output against the calling agent's Pydantic response model (e.g., `HazardPrediction`, `EvacuationRoute`, `SignalClassification`); on `ValidationError`, log the failure, trigger template fallback with `generation_method: "template_fallback"`, and apply `fallback_reduction_factor` to confidence per FR-018

**Checkpoint**: Foundation ready — managed identity auth, circuit breaker, confidence gating, structured output validation, and model routing are operational. User story implementation can now begin.

---

## Phase 3: User Story 1 — Azure OpenAI Resource Provisioned and Accessible (Priority: P1) 🎯 MVP

**Goal**: Provision Azure OpenAI resource in Australia East via Bicep IaC with model deployments, RBAC, diagnostics, and managed identity authentication — all agents can authenticate and call the endpoint.

**Independent Test**: Deploy the Bicep module, then run a health check from each agent verifying: (a) endpoint is reachable, (b) managed identity authentication succeeds, (c) configured deployment name resolves to a valid model.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T008 [P] [US1] Contract test for managed identity auth in `tests/contract/test_llm_managed_identity.py` — verify `LLMClient` constructs with `azure_ad_token_provider` (not `api_key`), verify `AZURE_OPENAI_API_KEY` env var is never read, verify Australian endpoint validation rejects non-AU endpoints, verify missing endpoint results in `None` client (graceful degradation)
- [x] T009 [P] [US1] Contract test for Bicep region restriction in `tests/contract/test_llm_managed_identity.py` — verify `@allowed` decorator on location parameter rejects non-Australian regions (can be a Bicep linting/what-if assertion)

### Implementation for User Story 1

- [x] T010 [P] [US1] Create Bicep module `infra/modules/azure-openai.bicep` — parameters per contracts/bicep-module.md (openAiAccountName, location with `@allowed(['australiaeast','australiasoutheast'])`, envPrefix, tags, model names/versions, TPM quotas, agentPrincipalIds, logAnalyticsWorkspaceId); resources: reasoning deployment `gpt-4o-{envPrefix}`, drafting deployment `gpt-4o-mini-{envPrefix}` (serial with `dependsOn`), RBAC `Cognitive Services OpenAI User` role for each principal, diagnostic settings (RequestResponse + Audit logs, AllMetrics); outputs: reasoningDeploymentName, draftingDeploymentName, openAiEndpoint
- [x] T011 [US1] Modify `infra/main.bicep` — set `disableLocalAuth: true` on existing `openAi` resource (line ~389), add module reference to `azure-openai.bicep` passing openAi.name, location, environmentName, tags, agent principal IDs, monitoring workspace ID; add `AZURE_OPENAI_REASONING_DEPLOYMENT` and `AZURE_OPENAI_DRAFTING_DEPLOYMENT` env vars to Container App env arrays; remove any `AZURE_OPENAI_API_KEY` env var entries

**Checkpoint**: At this point, the Azure OpenAI resource is provisioned with both model deployments, RBAC is assigned, diagnostics are flowing, and agents authenticate via managed identity. US1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Model Selection Routes Agents to Appropriate Deployments (Priority: P1)

**Goal**: Each agent's config specifies its model tier (reasoning or drafting), and the LLM client routes requests to the correct Azure OpenAI deployment accordingly.

**Independent Test**: Invoke the LLM client from each agent's context with its configured purpose and verify the request is routed to the expected deployment name in response metadata.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US2] Contract test for model routing in `tests/contract/test_llm_model_routing.py` — verify `purpose="reasoning"` routes to `config.reasoning_deployment`, verify `purpose="drafting"` routes to `config.drafting_deployment`, verify unknown purpose raises descriptive error, verify temperature defaults (0.0 for reasoning, 0.3 for drafting)

### Implementation for User Story 2

- [x] T013 [P] [US2] Add LLM config fields to `apps/agents/risk_assessment/config.py` — add `llm_model_tier` (default `"reasoning"`), `llm_temperature` (default `0.0`), `llm_max_output_tokens` (default `4000`), `llm_confidence_threshold` (default `0.7`), `llm_fallback_reduction_factor` (default `0.5`), `llm_monthly_budget_usd` (default `50.0`) as frozen dataclass fields with env-var overrides; update `__post_init__` validation; update `compute_config_hash()` per contracts/llm-config.md
- [x] T014 [P] [US2] Add LLM config fields to `apps/agents/evacuation/config.py` — same fields as T013 with defaults: model_tier=`"reasoning"`, temperature=`0.0`, max_output_tokens=`4000`
- [x] T015 [P] [US2] Add LLM config fields to `apps/agents/monitoring/config.py` — same fields with defaults: model_tier=`"drafting"`, temperature=`0.3`, max_output_tokens=`2000`
- [x] T016 [P] [US2] Add LLM config fields to `apps/agents/communication/config.py` — same fields with defaults: model_tier=`"drafting"`, temperature=`0.3`, max_output_tokens=`2000`
- [x] T017 [P] [US2] Add LLM config fields to `apps/agents/resource_allocation/config.py` — same fields with defaults: model_tier=`"drafting"`, temperature=`0.3`, max_output_tokens=`2000`

**Checkpoint**: All 5 agents have LLM config fields with correct tier-specific defaults. Reasoning agents (Risk Assessment, Evacuation) route to GPT-4o; drafting agents (Monitoring, Communication, Resource Allocation) route to GPT-4o-mini.

---

## Phase 5: User Story 3 — Template Fallback When Azure OpenAI Is Unavailable (Priority: P1)

**Goal**: When the LLM endpoint is unreachable or returns transient errors, agents fall back to template-based outputs within the timeout window, with clear `generation_method: template_fallback` marking and audit trail.

**Independent Test**: Configure LLM client with an unreachable endpoint, trigger a generation request, and verify template output is returned with correct `generation_method` marker within 15 seconds.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T018 [P] [US3] Contract test for fallback in `tests/contract/test_llm_fallback.py` — extend existing tests to verify: circuit breaker integration (CLOSED→OPEN after 3 failures, OPEN skips LLM directly, HALF_OPEN probe), `generation_method: template_fallback` in response, fallback within 15s timeout, audit trail includes error reason + correlation ID + retry count
- [x] T019 [P] [US3] Contract test for circuit breaker state transitions in `tests/contract/test_llm_circuit_breaker.py` — verify CLOSED→OPEN after `failure_threshold` consecutive failures, OPEN→HALF_OPEN after `recovery_timeout`, HALF_OPEN→CLOSED on probe success, HALF_OPEN→OPEN on probe failure, thread safety under concurrent access, injectable clock for deterministic testing

### Implementation for User Story 3

- [x] T020 [US3] Verify and extend fallback audit trail in `apps/agents/common/llm_mixin.py` — ensure fallback events include error reason, timestamp, correlation ID, retry count, and `circuit_breaker_state` in response; log at WARNING level per contracts/llm-client.md logging contract

**Checkpoint**: Template fallback works end-to-end with circuit breaker recovery. Agents produce structured output within 15s during LLM outages. Circuit breaker prevents retry storms.

---

## Phase 6: User Story 4 — Content Safety Validation on All LLM Outputs (Priority: P2)

**Goal**: All LLM outputs pass through the existing `ContentSafetyValidator` before reaching users or downstream agents. Failed validation triggers `safety_fallback` with template text substitution.

**Independent Test**: Provide the content safety validator with outputs containing blocked keywords, excessive length, and empty output, then verify each produces the correct rejection and template substitution.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US4] Contract test for content safety integration in `tests/contract/test_llm_fallback.py` — verify blocked keyword → `generation_method: safety_fallback`, verify length exceeded → rejection, verify empty output → rejection, verify passed output → original LLM text used with `content_safety_result: passed`

### Implementation for User Story 4

- [x] T022 [US4] Verify content safety integration in `apps/agents/common/llm_mixin.py` — confirm `ContentSafetyValidator.validate()` is called on every LLM output before return, confirm validation failure triggers template substitution with `generation_method: safety_fallback`, confirm `content_safety_result` field is set in response dict for both pass and fail cases (existing flow — verify no gaps)

**Checkpoint**: Content safety gate is verified end-to-end. No LLM text reaches users without validation.

---

## Phase 7: User Story 5 — Token Budget Management and Cost Tracking (Priority: P2)

**Goal**: Each agent tracks token consumption per LLM call, reports usage via telemetry, enforces per-call max output token limits with trimming, and emits budget warning metrics when monthly thresholds are exceeded.

**Independent Test**: Make LLM calls with known prompts, capture token usage metadata, verify telemetry records include per-call counts, and verify responses exceeding max output tokens are trimmed.

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T023 [P] [US5] Contract test for token budget tracking in `tests/contract/test_llm_telemetry.py` — verify `token_usage` dict in response with `input_tokens` and `output_tokens` as non-negative ints, verify trim when output exceeds `max_output_tokens`, verify `llm.budget.exceeded` counter emitted when monthly cumulative exceeds threshold

### Implementation for User Story 5

- [x] T024 [US5] Implement in-memory monthly budget tracker in `apps/agents/common/llm_mixin.py` — track cumulative token-to-dollar conversion using pricing constants (GPT-4o: ~$2.50/1M input, ~$10.00/1M output; GPT-4o-mini: ~$0.15/1M input, ~$0.60/1M output), emit `llm.budget.exceeded` counter when threshold breached, reset counter monthly, per research.md R10
- [x] T025 [US5] Verify token trimming in `apps/agents/common/llm_mixin.py` — confirm existing `text[:max(80, int(len(text) * 0.8))]` trim logic fires when output tokens exceed `max_output_tokens`, confirm warning logged with actual vs. maximum token counts per research.md R5

**Checkpoint**: Token usage tracked per call, budget warnings emitted via telemetry, responses trimmed when exceeding limits.

---

## Phase 8: User Story 6 — Confidence Thresholds and Human Review Gates (Priority: P2)

**Goal**: Safety-critical outputs below the confidence threshold are flagged `requires_human_review: true` and blocked from automatic escalation. Template fallback outputs have confidence automatically reduced by the fallback reduction factor.

**Independent Test**: Generate a recommendation with confidence below threshold and verify no automatic escalation occurs and output is marked for human review.

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T026 [P] [US6] Contract test for confidence gating in `tests/contract/test_llm_confidence.py` — verify confidence below threshold → `requires_human_review: true` + no automatic handoff, verify confidence at/above threshold → normal escalation, verify template fallback → confidence multiplied by `fallback_reduction_factor` (0.5 default), verify review output includes confidence score + data sources + reasoning summary

### Implementation for User Story 6

- [x] T027 [US6] Wire confidence threshold gating into agent pipeline in `apps/agents/common/llm_mixin.py` — ensure `_generate_with_fallback()` output includes `confidence_adjustment` field (None for LLM, factor value for template), downstream agents check `requires_human_review` before escalation (verify existing pattern handles this)

**Checkpoint**: Confidence gating works. Low-confidence and template-fallback outputs are blocked from automatic escalation.

---

## Phase 9: User Story 7 — Azure OpenAI Infrastructure as Code (Priority: P3)

**Goal**: The Bicep IaC module supports extensible provisioning — operators can add deployments, change TPM quotas, and redeploy without manual portal steps.

**Independent Test**: Deploy the Bicep module to a test subscription and verify resource, deployments, RBAC, and diagnostics match parameter values.

### Implementation for User Story 7

- [x] T028 [US7] Add environment-aware TPM quota parameters to `infra/modules/azure-openai.bicep` — verify `reasoningTpmQuota` and `draftingTpmQuota` params with `@minValue(1)` decorator accept operator overrides, verify dev defaults (30/60) and prod overrides (120/240) work via parameter files, verify quota change redeploys without resource recreation per FR-022
- [x] T029 [US7] Create parameter files for dev and prod environments — `infra/parameters/dev.bicepparam` and `infra/parameters/prod.bicepparam` with environment-specific TPM quotas and budget values (if parameter files pattern exists; otherwise document in quickstart.md)

**Checkpoint**: IaC module is extensible. Operators can modify deployments and quotas via parameters.

---

## Phase 10: User Story 8 — Model Performance Monitoring and Token Usage Metrics (Priority: P3)

**Goal**: LLM-specific telemetry metrics (call count, latency histogram, token counters, fallback frequency, error rate, circuit breaker transitions, budget warnings) are emitted via OpenTelemetry and available in the monitoring pipeline.

**Independent Test**: Make a series of LLM calls, then query the telemetry backend for expected metrics and verify counters, histograms, and labels are correctly recorded.

### Tests for User Story 8

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T030 [P] [US8] Contract test for LLM telemetry in `tests/contract/test_llm_telemetry.py` — verify all 9 metric instruments from contracts/telemetry.md are created: `llm.call.count` (counter), `llm.call.duration_ms` (histogram with correct buckets), `llm.tokens.input` (counter), `llm.tokens.output` (counter), `llm.fallback.count` (counter), `llm.error.count` (counter), `llm.circuit_breaker.state_change` (counter), `llm.budget.exceeded` (counter), `llm.confidence.below_threshold` (counter); verify label schema (`agent`, `deployment`, `outcome`, `fallback_type`, `error_category`, `from_state`, `to_state`)

### Implementation for User Story 8

- [x] T031 [P] [US8] Add LLM telemetry instruments to `apps/agents/risk_assessment/telemetry.py` — add all 9 metric instruments per contracts/telemetry.md, follow existing OTel pattern (`_OTEL_AVAILABLE` guard, `_NoOpMeter` fallback, module-level singletons)
- [x] T032 [P] [US8] Add LLM telemetry instruments to `apps/agents/evacuation/telemetry.py` — create new file if it does not exist; add all 9 metric instruments following same pattern as T031
- [x] T033 [P] [US8] Add LLM telemetry instruments to `apps/agents/monitoring/telemetry.py` — create new file if it does not exist; add all 9 metric instruments following same pattern as T031
- [x] T034 [P] [US8] Add LLM telemetry instruments to `apps/agents/communication/telemetry.py` — add all 9 metric instruments following same pattern as T031
- [x] T035 [P] [US8] Add LLM telemetry instruments to `apps/agents/resource_allocation/telemetry.py` — add all 9 metric instruments following same pattern as T031
- [x] T036 [US8] Wire telemetry recording into `apps/agents/common/llm_mixin.py` — after each LLM call record: `llm.call.count` (success/failure/timeout), `llm.call.duration_ms`, `llm.tokens.input`, `llm.tokens.output`; on fallback: `llm.fallback.count`; on error: `llm.error.count`; on circuit breaker transition: `llm.circuit_breaker.state_change`; on confidence below threshold: `llm.confidence.below_threshold`; all with correct label values per contracts/telemetry.md usage examples

**Checkpoint**: All LLM telemetry metrics are emitted. Operators can view per-agent call counts, latency, token usage, error rates, and fallback frequency within 60s (SC-006).

---

## Phase 11: Integration Testing & End-to-End Validation

**Purpose**: Cross-cutting integration tests that exercise the full LLM call chain

- [x] T037 [P] Create integration test for full LLM call chain in `tests/integration/test_llm_integration.py` — test end-to-end: agent config → LLMClient (with mocked Azure OpenAI) → content safety → response with metadata; test fallback chain: LLM failure → circuit breaker opens → template fallback → circuit breaker recovers; test token tracking across multiple calls; test confidence gating blocks escalation
- [x] T038 Update simulation test `tests/simulation/test_quickstart_live_llm_rehearsal.py` — update for managed identity auth (remove API key references), add `DefaultAzureCredential` path, conditionally skip when `AZURE_OPENAI_ENDPOINT` is not set

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, risk register, final validation

- [x] T039 [P] Create risk register entry `docs/risk-register/RISK-AOAI-001.md` — document AI Model Unavailability risk per data-model.md entity 7: Risk ID `RISK-AOAI-001`, Probability Medium (20–50%), Impact High, Mitigation (template fallback, circuit breaker, manual failover to AU Southeast, confidence threshold gating), Residual Risk Low, Owner Platform Operations Lead, Review Cadence quarterly + post-incident; add additional entries for `RISK-AOAI-002` (token quota exhaustion) and `RISK-AOAI-003` (credential propagation delays) per FR-019
- [x] T040 [P] Update quickstart documentation — verify `specs/feature/014-azure-openai-integration/quickstart.md` matches final implementation (env vars, test commands, troubleshooting), update if any details changed during implementation
- [x] T041 Run full test suite validation — execute `pytest tests/contract/ tests/integration/ -v` and confirm all new and existing tests pass; run `az bicep build -f infra/modules/azure-openai.bicep` to validate Bicep syntax
- [x] T042 Run quickstart.md validation — follow the quickstart guide end-to-end on a clean checkout to verify developer experience

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phases 3–10)**: All depend on Phase 2 (Foundational) completion
  - US1 (Phase 3) + US2 (Phase 4) can proceed in parallel once Phase 2 is done
  - US3 (Phase 5) depends on Phase 2 (circuit breaker integrated in foundational)
  - US4 (Phase 6) can proceed after Phase 2
  - US5 (Phase 7) can proceed after Phase 2
  - US6 (Phase 8) depends on Phase 2 (confidence gating integrated in foundational)
  - US7 (Phase 9) depends on US1 (Bicep module exists)
  - US8 (Phase 10) can proceed after Phase 2
- **Integration Testing (Phase 11)**: Depends on Phases 3–10
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no user story dependencies
- **US2 (P1)**: Can start after Phase 2 — no user story dependencies (parallel with US1)
- **US3 (P1)**: Can start after Phase 2 — no user story dependencies (parallel with US1, US2)
- **US4 (P2)**: Can start after Phase 2 — no user story dependencies
- **US5 (P2)**: Can start after Phase 2 — no user story dependencies
- **US6 (P2)**: Can start after Phase 2 — no user story dependencies
- **US7 (P3)**: Depends on US1 completion (extends the Bicep module created in US1)
- **US8 (P3)**: Can start after Phase 2 — no user story dependencies (parallel with US1–US6)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Config/models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (different files)
- **Phase 2**: T004/T005 sequential (same file); T006/T007/T007b sequential (same file); but Phase 2 group 1 (T004-T005) and group 2 (T006-T007-T007b) can be parallelised across developers
- **Phase 3**: T008, T009, T010 can all run in parallel (different files)
- **Phase 4**: T013, T014, T015, T016, T017 can all run in parallel (5 different agent config files)
- **Phase 5**: T018, T019 can run in parallel (different test files)
- **Phase 10**: T031, T032, T033, T034, T035 can all run in parallel (5 different telemetry files)
- **Cross-phase**: US1 (Bicep), US2 (configs), US3 (fallback tests), US4 (safety), US5 (budget), US6 (confidence), US8 (telemetry) can all proceed in parallel after Phase 2

---

## Parallel Example: User Story 2 (Model Routing Config)

```bash
# Launch all 5 agent config updates in parallel (different files):
Task: T013 "Add LLM config fields to apps/agents/risk_assessment/config.py"
Task: T014 "Add LLM config fields to apps/agents/evacuation/config.py"
Task: T015 "Add LLM config fields to apps/agents/monitoring/config.py"
Task: T016 "Add LLM config fields to apps/agents/communication/config.py"
Task: T017 "Add LLM config fields to apps/agents/resource_allocation/config.py"
```

## Parallel Example: User Story 8 (Telemetry)

```bash
# Launch all 5 agent telemetry updates in parallel (different files):
Task: T031 "Add LLM telemetry to apps/agents/risk_assessment/telemetry.py"
Task: T032 "Add LLM telemetry to apps/agents/evacuation/telemetry.py"
Task: T033 "Add LLM telemetry to apps/agents/monitoring/telemetry.py"
Task: T034 "Add LLM telemetry to apps/agents/communication/telemetry.py"
Task: T035 "Add LLM telemetry to apps/agents/resource_allocation/telemetry.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T007)
3. Complete Phase 3: US1 — Azure OpenAI Resource Provisioned (T008–T011)
4. Complete Phase 4: US2 — Model Routing Config (T012–T017)
5. Complete Phase 5: US3 — Template Fallback Verified (T018–T020)
6. **STOP and VALIDATE**: Test US1 + US2 + US3 independently — agents can authenticate, route to correct models, and fall back safely
7. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US2 + US3 → Test independently → Deploy/Demo (**MVP!**)
3. Add US4 (Content Safety) → Test independently → Deploy/Demo
4. Add US5 (Token Budget) + US6 (Confidence) → Test independently → Deploy/Demo
5. Add US7 (IaC Extensibility) + US8 (Telemetry) → Test independently → Deploy/Demo
6. Integration Testing + Polish → Final validation

### Parallel Team Strategy

With multiple developers after Phase 2 completion:

1. **Developer A**: US1 (Bicep module) + US7 (IaC extensibility)
2. **Developer B**: US2 (agent configs — 5 files) + US3 (fallback verification)
3. **Developer C**: US4 (content safety) + US5 (token budget) + US6 (confidence)
4. **Developer D**: US8 (telemetry — 5 agent files + mixin wiring)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are included — explicitly required by spec and plan
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Python 3.12, frozen dataclasses, env-var-at-construction pattern throughout
- All agents reuse the shared `LLMClientConfig` from `apps/agents/common/llm_config.py`
- Bicep module follows existing `infra/modules/` conventions (location, envPrefix, tags params)
