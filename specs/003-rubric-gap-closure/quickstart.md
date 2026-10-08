# Quickstart: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

## Purpose

Validate the feature 003 design through a test-first development flow that exercises LLM-integrated agents, event-driven handoff chaining, dead-letter handling, containerised builds, infrastructure provisioning, structured error handling, and performance validation. Each acceptance check maps to a success criterion from the spec.

## Prerequisites

- Python 3.12
- Node.js 22 and pnpm
- Docker (for container builds)
- Azure CLI and Bicep CLI (for IaC validation)
- Access to Microsoft Foundry model deployments in an approved Australian region (or approved carve-out)
- Locust (`pip install locust`) for load testing
- Existing feature 001 codebase fully passing tests

## Setup sequence

1. Install new Python dependencies for the API and agent runtime:
   - `openai` (Azure OpenAI SDK)
   - `tenacity` (retry with backoff)
   - `pytest-benchmark` (CI performance regression)
   - `locust` (load testing)
2. Configure environment variables for Foundry live rehearsal:
   - `AMA_LIVE_REHEARSAL=1` to opt in to live execution
   - `AZURE_AI_PROJECT_ENDPOINT`
   - `AZURE_AI_PROJECT_DEPLOYMENTS`
   - `AZURE_AI_REASONING_DEPLOYMENT`
   - `AZURE_AI_DRAFTING_DEPLOYMENT`
   - Authentication: Microsoft Entra ID / managed identity (no API key required)
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
3. Write a failing test that verifies handoff delivery is capped at 3 total attempts over 5 minutes (initial attempt + up to 2 retries), with `attempt_count` tracking total calls and `retry_count` tracking retries after the first call, then dead-letter on exhaustion.
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
3. Build each image locally from repository root context: `docker build -f apps/api/Dockerfile -t drh-api .` and `docker build -f apps/agents/Dockerfile -t drh-agents .`.
4. Run each container and verify `/api/health` responds (API readiness) and `/api/health/liveness` responds (API liveness), then verify the agent worker starts (agents).

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
2. Run Locust headless in an authorized staging environment: `locust --headless -u 1000 -r 100 --run-time 10m --host <approved-staging-url>`.
3. Verify the pass/fail report proves both thresholds in the same staged run: dashboard p95 <2s and sustained throughput >=50,000 signals/hour with read API p95 <500ms.

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
7. Verify exactly 2 logical handoff edges (Monitoring→Risk and Risk→Communication) are recorded as TimelineEvents; retries must not be counted as additional logical handoffs.
8. Simulate a model endpoint failure and verify template fallback is used, marked correctly, and the timeline records the fallback.
9. Approve and publish the alert; verify end-to-end completion in under 30 seconds.

## Acceptance checks (mapped to success criteria)

| QAC | Check | SC | Validation |
| --- | ----- | -- | ---------- |
| QAC-01 | Risk Assessment produces LLM explanation with signal citations | SC-001 | Contract test verifies ≥1 signal ID in output text |
| QAC-02 | Communication produces 6-language alert draft | SC-002 | Contract test verifies content_blocks keys match all 6 language codes |
| QAC-03 | Template fallback completes within 2s on model failure | SC-003 | Integration test with mocked unavailable endpoint |
| QAC-04 | CI pipeline runs all checks, completes <10 min, blocks on failure | SC-004 | GitHub Actions run log |
| QAC-05 | Full handoff chain completes automatically within 30s | SC-005 | Integration test with timing assertion and exactly two logical handoff edges |
| QAC-06 | Container images build, pass health check, run as non-root | SC-006 | Docker build + run + health check verification |
| QAC-07 | IaC what-if passes for all resources in Australian region | SC-007 | `az deployment group what-if` output |
| QAC-08 | Demo walkthrough and slide deck acceptance | SC-008 | Real resolved media/evidence package with linked annotated assets and reviewer acceptance record; file existence alone is insufficient |
| QAC-09 | All errors return structured JSON with correlation ID | SC-009 | Contract test on error responses |
| QAC-10 | Transient failures retried with exponential backoff, 90%+ recovery | SC-010 | Integration test with simulated transient failures and consistent `attempt_count`/`retry_count` results |
| QAC-11 | Alert notifications delivered within 5 min of threshold breach | SC-011 | Controlled breach-to-receipt evidence showing trigger time and confirmed receiver delivery time; static configuration alone is insufficient |
| QAC-12 | Load test validates performance targets; CI benchmark catches regression | SC-012 | Locust staged-run report + pytest-benchmark baseline comparison |
| QAC-13 | Overall rubric score reaches 60/60 | SC-013 | Independent post-implementation rubric re-evaluation |
