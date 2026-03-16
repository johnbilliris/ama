# Quickstart: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

## Purpose

Validate the feature 003 design through a test-first development flow that exercises LLM-integrated agents, event-driven handoff chaining, dead-letter handling, containerised builds, infrastructure provisioning, structured error handling, and performance validation. Each acceptance check maps to a success criterion from the spec.

## Prerequisites

- Python 3.12
- Node.js 22 and pnpm
- Docker (for container builds)
- Azure CLI and Bicep CLI (for IaC validation)
- Access to an Azure OpenAI resource with a deployed model in an Australian-accessible region
- Locust (`pip install locust`) for load testing
- Existing feature 001 codebase fully passing tests

## Setup sequence

1. Install new Python dependencies for the API and agent runtime:
   - `openai` (Azure OpenAI SDK)
   - `tenacity` (retry with backoff)
   - `pytest-benchmark` (CI performance regression)
   - `locust` (load testing)
2. Configure environment variables for Azure OpenAI:
   - `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
   - `AZURE_OPENAI_API_KEY` or managed identity configuration
   - `AZURE_OPENAI_REASONING_DEPLOYMENT`: deployment name for risk assessment (e.g., `gpt-4o`)
   - `AZURE_OPENAI_DRAFTING_DEPLOYMENT`: deployment name for communication (e.g., `gpt-4o-mini`)
3. No changes to the web application setup from feature 001.

## Test-first validation flow

### Phase A: AI Integration (FR-001–006, SC-001–003)

1. Write a failing contract test that verifies the Risk Assessment agent produces an LLM-generated explanation citing signal IDs when the model endpoint is available.
2. Write a failing contract test that verifies the Communication agent produces alert content blocks in all 6 languages (en-AU, zh-Hans, ar, vi, el, it).
3. Write a failing test that verifies template fallback is triggered when the model endpoint is mocked as unavailable, and the output is marked as `template_fallback`.
4. Write a failing test that verifies content safety validation catches flagged content and falls back to template with `safety_fallback` marking.
5. Write a failing test that verifies token budget enforcement (truncation or re-request on overage).
6. Implement `llm_mixin.py`, update `risk_assessment/agent.py` and `communication/agent.py` to pass all tests.

### Phase B: Agent Orchestration (FR-011–014, SC-005)

1. Write a failing integration test that ingests a high-risk signal and verifies the Monitoring → Risk Assessment → Communication handoff chain completes automatically.
2. Write a failing test that verifies each handoff is recorded as a TimelineEvent with source agent, target agent, scope key, confidence, and payload summary.
3. Write a failing test that verifies handoff retry (3 attempts over 5 minutes) when target circuit is open, then dead-letter on exhaustion.
4. Extend the event bus with subscriber registration, dispatch, and dead-letter routing.
5. Update agent `process()` methods to publish typed handoffs on completion.

### Phase C: CI/CD Pipeline (FR-007–010, FR-030, SC-004)

1. Update `.github/workflows/ci.yml` with stages for Python test execution, Python linting (ruff), TypeScript type-checking, web build, and lightweight performance benchmark.
2. Add the `003-rubric-gap-closure` branch to the CI trigger list.
3. Verify the pipeline blocks a PR with a deliberately failing test.
4. Verify the performance benchmark stage completes in <60 seconds and flags a regression when an endpoint exceeds the configured threshold.

### Phase D: Container Definitions (FR-015–017, SC-006)

1. Create `apps/api/Dockerfile` with multi-stage build, non-root user, health check.
2. Create `apps/agents/Dockerfile` with multi-stage build, non-root user.
3. Build each image locally: `docker build -t drh-api apps/api` and `docker build -t drh-agents apps/agents`.
4. Run each container and verify the health endpoint responds (API) and the agent worker starts (agents).

### Phase E: Infrastructure as Code (FR-018–020, FR-026–027, SC-007, SC-011)

1. Create `infra/bicep/main.bicep` provisioning Container Apps Environment, Cosmos DB, Redis, Blob Storage, and Azure OpenAI.
2. Add action groups to `infra/bicep/monitoring.bicep` with email and webhook targets.
3. Complete the latency alert rule (currently has incomplete threshold configuration).
4. Run `az deployment group what-if` and verify all resources are planned in an Australian region with managed identity and monitoring integration.

### Phase F: Error Handling (FR-023–025, SC-009–010)

1. Write a failing test that verifies structured JSON error responses include correlation ID, status code, error category, and non-leaking message.
2. Write a failing test that verifies exponential backoff retry (3 attempts) on transient Cosmos DB/Redis failure.
3. Write a failing test that verifies failed payloads are stored in the dead-letter store with correlation ID and failure reason.
4. Implement the dead-letter service, structured error handler, and retry decorators to pass all tests.

### Phase G: Performance Validation (FR-028–029, SC-012)

1. Create `tests/load/locustfile.py` with scenarios for concurrent dashboard load and burst signal ingestion.
2. Run Locust headless: `locust --headless -u 100 -r 10 --run-time 2m` against the local API.
3. Verify the pass/fail report for dashboard p95 <2s, read API p95 <500ms, and ingestion throughput.

### Phase H: Demo Artifacts (FR-021–022, SC-008)

1. Create `docs/disaster-response-hub/demo/walkthrough.md` with a screenplay of the full incident workflow: activation → signal ingestion → dashboard → persona workspace → recommendation approval → multilingual alert publishing → scenario replay.
2. Capture annotated screenshots or GIF recordings for each major UI surface.
3. Create `docs/disaster-response-hub/demo/executive-deck.md` with before/after KPI comparisons and value proposition narrative.

## Scenario rehearsal: LLM-augmented incident flow

1. Seed a multi-jurisdiction bushfire incident with two Australian jurisdictions.
2. Ingest 3 signals: one authoritative BoM weather warning (high confidence), one community report (medium confidence), one IoT sensor reading (high confidence).
3. Verify the Monitoring agent classifies the BoM signal as high-risk and automatically triggers the Risk Assessment agent via event bus handoff.
4. Verify the Risk Assessment agent produces an LLM-generated explanation that cites the signal IDs and states the confidence level.
5. Verify the Risk Assessment agent automatically triggers the Communication agent via a second handoff (recommendation type: public_alert, confidence: high).
6. Verify the Communication agent produces multilingual alert drafts in all 6 languages.
7. Verify all 3 handoffs (Monitoring→Risk, Risk→Communication) are recorded as TimelineEvents.
8. Simulate a model endpoint failure and verify template fallback is used, marked correctly, and the timeline records the fallback.
9. Approve and publish the alert; verify end-to-end completion in under 30 seconds.

## Acceptance checks (mapped to success criteria)

| Check | SC | Validation |
|-------|------|------------|
| Risk Assessment produces LLM explanation with signal citations | SC-001 | Contract test verifies ≥1 signal ID in output text |
| Communication produces 6-language alert draft | SC-002 | Contract test verifies content_blocks keys match all 6 language codes |
| Template fallback completes within 2s on model failure | SC-003 | Integration test with mocked unavailable endpoint |
| CI pipeline runs all checks, completes <10 min, blocks on failure | SC-004 | GitHub Actions run log |
| Full handoff chain completes automatically within 30s | SC-005 | Integration test with timing assertion |
| Container images build, pass health check, run as non-root | SC-006 | Docker build + run + health check verification |
| IaC what-if passes for all resources in Australian region | SC-007 | `az deployment group what-if` output |
| Demo walkthrough and slide deck exist in repo | SC-008 | File existence check |
| All errors return structured JSON with correlation ID | SC-009 | Contract test on error responses |
| Transient failures retried with exponential backoff, 90%+ recovery | SC-010 | Integration test with simulated transient failures |
| Alert notifications delivered within 5 min of threshold breach | SC-011 | Verified via action group configuration in Bicep |
| Load test validates performance targets; CI benchmark catches regression | SC-012 | Locust results report + pytest-benchmark baseline comparison |
| Overall rubric score reaches 60/60 | SC-013 | Post-implementation rubric re-evaluation |
