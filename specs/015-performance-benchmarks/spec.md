# Feature Specification: Performance Benchmarks

**Feature Branch**: `015-performance-benchmarks`  
**Created**: 2025-07-23  
**Status**: Draft  
**Input**: User description: "Expand the existing single-endpoint benchmark into a comprehensive performance benchmark suite that covers all 5 agent endpoints, pipeline processing latency, LLM client response times, and circuit breaker recovery. Store benchmark results as CI artifacts with regression detection thresholds. Provide SLO-aligned latency targets per agent."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Multi-Endpoint Latency Benchmarks (Priority: P1)

As an **SRE**, I want automated latency benchmarks for every agent health endpoint so that I can establish baselines, detect regressions in CI, and ensure each agent meets its latency SLO before changes are merged.

**Why this priority**: Health endpoint latency is the most fundamental observable signal for all five agents. Without per-agent baselines, regressions ship silently and degrade the overall system. This story also replaces the current single-endpoint benchmark, closing the most visible gap in benchmark coverage.

**Independent Test**: Can be fully tested by running `pytest tests/benchmark/` against the five agent health endpoints (monitoring, risk, evacuation, resource, communication) and verifying each result is below its SLO target. Delivers immediate regression detection for every agent.

**Acceptance Scenarios**:

1. **Given** the benchmark suite is executed in CI, **When** all five agent health endpoints are benchmarked, **Then** each endpoint's median latency is recorded and compared against its SLO target (general agents < 100 ms; safety-critical agents — risk and evacuation — < 75 ms).
2. **Given** a code change increases an agent's health endpoint latency by 25%, **When** the benchmark suite runs, **Then** a regression warning is reported in the CI output.
3. **Given** a code change increases an agent's health endpoint latency by 55%, **When** the benchmark suite runs, **Then** the benchmark step fails the CI build.

---

### User Story 2 — Pipeline Processing Benchmarks (Priority: P2)

As an **SRE**, I want to benchmark the pipeline processing path of each agent so that I can verify end-to-end processing latency stays within SLO and identify stages that regress over time.

**Why this priority**: Pipeline processing is the core workload of each agent. Benchmarking it ensures the critical orchestration path — from request receipt through multi-stage processing to response — is monitored for latency regressions independent of external service calls.

**Independent Test**: Can be fully tested by invoking each agent's pipeline with mocked dependencies and verifying the processing completes within the pipeline SLO (< 2 s). Delivers value even without LLM or circuit breaker benchmarks.

**Acceptance Scenarios**:

1. **Given** the benchmark suite runs with mocked external dependencies, **When** the pipeline benchmark executes for each agent, **Then** the median end-to-end pipeline latency is recorded and is below 2 s.
2. **Given** a regression increases pipeline latency for the evacuation agent by 30%, **When** the suite runs, **Then** a regression warning is emitted and the specific agent is identified.

---

### User Story 3 — LLM Client Response Time Benchmarks (Priority: P2)

As a **QA engineer**, I want benchmarks that measure the LLM client response path (with mocked responses) so that I can verify the application-side overhead stays within the LLM SLO budget and CI runs are fast and deterministic.

**Why this priority**: The LLM client is a shared component used by all agents. Benchmarking the application-side overhead (serialization, retry logic, response parsing) ensures changes to the client do not silently add latency. Mocked responses keep CI execution fast and repeatable.

**Independent Test**: Can be fully tested by calling `LLMClient.generate_response()` with mocked external responses and measuring the application-side latency against the LLM SLO (< 500 ms mocked round-trip). Delivers value independently of endpoint or pipeline benchmarks.

**Acceptance Scenarios**:

1. **Given** the LLM client benchmark uses mocked responses, **When** the benchmark runs, **Then** the median round-trip time (including application overhead) is below 500 ms.
2. **Given** a change adds overhead to the LLM client's retry or parsing logic, **When** the benchmark runs, **Then** a regression warning is reported if latency increases by ≥ 20%.

---

### User Story 4 — Circuit Breaker Recovery Benchmarks (Priority: P3)

As a **Chaos Engineer**, I want benchmarks that measure circuit breaker state transitions and recovery timing so that I can compare benchmark baselines with chaos experiment results and prove the system degrades gracefully.

**Why this priority**: Circuit breaker behavior directly impacts system resilience. Benchmarking state transitions (closed → open → half-open → closed) and recovery timing provides the baseline that chaos experiments can compare against. Lower priority because it depends on the LLM client benchmarks for context.

**Independent Test**: Can be fully tested by driving the circuit breaker through its state machine with simulated failures and measuring transition times and recovery duration. Delivers value independently.

**Acceptance Scenarios**:

1. **Given** the circuit breaker is in CLOSED state, **When** enough simulated failures are injected to trigger the OPEN state, **Then** the transition happens within the configured failure threshold (3 failures) and the benchmark records the transition time.
2. **Given** the circuit breaker is in OPEN state, **When** the recovery timeout elapses and a success is recorded, **Then** the circuit transitions through HALF_OPEN to CLOSED and the total recovery time is recorded and is within 2× the configured recovery timeout.

---

### User Story 5 — Benchmark Result Storage and Regression Detection (Priority: P1)

As an **SRE**, I want benchmark results stored as structured artifacts with automated regression detection so that I can trend performance over time and receive clear pass/fail signals in CI.

**Why this priority**: Without persistent, structured results, benchmarks are ephemeral and cannot be trended. This story enables all other stories to deliver long-term value by making results queryable and by providing the regression detection logic that gates CI.

**Independent Test**: Can be fully tested by running any benchmark, verifying a JSON result file is produced in `.benchmarks/`, and confirming the regression detection logic correctly flags a synthetic 25% increase as a warning and a 55% increase as a failure.

**Acceptance Scenarios**:

1. **Given** a benchmark run completes, **When** the results are written, **Then** a JSON file containing timestamps, agent name, metric type, median value, min, max, iterations, and SLO target is saved to the `.benchmarks/` directory. P95 and P99 are derivable from the raw `stats.data` array in pytest-benchmark's native JSON output but are not explicitly stored as top-level fields.
2. **Given** a previous baseline exists, **When** a new run's median latency exceeds the baseline by ≥ 20%, **Then** the regression detection logic emits a warning.
3. **Given** a previous baseline exists, **When** a new run's median latency exceeds the baseline by ≥ 50%, **Then** the regression detection logic causes the benchmark CI step to fail.
4. **Given** benchmark results are stored as CI artifacts, **When** an SRE reviews a pull request, **Then** they can download the artifact and compare it to previous baselines.

---

### Edge Cases

- What happens when no previous baseline exists? The first run establishes the baseline; regression detection is skipped and a notice is logged.
- What happens when an agent fails to start during benchmarking? The benchmark for that agent is marked as an error (not a regression), the failure is logged, and remaining benchmarks continue.
- What happens when a mocked dependency introduces unexpected latency (e.g., mock server delay)? Benchmarks use in-process mocks (not network mocks) to eliminate external timing variability.
- What happens when the `.benchmarks/` directory is missing? It is created automatically on first write.
- How does benchmark timing interact with CI runner variability? Regression thresholds (20% warning / 50% failure) are set high enough to absorb typical CI runner noise. Benchmarks use relative comparisons, not absolute values, for regression detection.
- What happens when the current run produces new metrics absent from the stored baseline? New metrics are treated as first-run for that metric — regression detection is skipped and a notice is logged.
- What happens when the stored baseline contains metrics the current run no longer produces (e.g., agent removed)? The missing metrics are logged as a notice but are NOT treated as a regression or failure.
- How do regression warnings propagate in CI vs failures? Warnings (≥ 20% but < 50%) are emitted via `logging.warning()` — visible in CI output but non-blocking (zero exit code). Only ≥ 50% regressions cause assertion failures and non-zero exit code.

## Clarifications

### Session 2026-04-12

- Q: Should benchmark results use pytest-benchmark's native `--benchmark-json` output with a thin SLO/regression wrapper, or a fully custom JSON schema? → A: pytest-benchmark native JSON + thin comparison wrapper
- Q: Spec body says `.benchmarks/` but A-007 says `apps/agents/.benchmarks/`. Both directories exist (empty). Which is canonical? → A: Repo root `.benchmarks/`; A-007 corrected
- Q: Should `tests/benchmark/test_api_performance.py` be replaced/refactored in-place or kept alongside new files? → A: Replace in-place; existing concurrent-batch pattern is load testing (out of scope)
- Q: What constitutes "pipeline processing" for benchmarking — pipeline class `process_handoff()` calls or full HTTP request paths? → A: Direct `process_handoff()` / `process_signal()` calls with mocked deps
- Q: Should risk/evacuation agents have tighter pipeline SLOs than the uniform < 2 s? → A: Uniform < 2 s for all; health-endpoint differentiation (75 ms vs 100 ms) is sufficient for current scope

### Session 2026-04-12 (Pass 2)

- Q: How should regression warnings (≥ 20%) surface in CI — log output, pytest warning, or non-zero exit code? → A: Warnings via `logging.warning()` to CI output (visible, non-blocking). Only ≥ 50% regressions cause non-zero exit code via assertion failure.
- Q: SC-007 says "within 60 seconds (excluding agent startup)" but user decision says unqualified "under 60 seconds." What does the 60 s budget measure? → A: 60 s wall-clock for the entire `pytest tests/benchmark/` command; "(excluding agent startup)" removed since benchmarks use in-process TestClient. CI step gets `timeout-minutes: 2` safeguard.
- Q: SC-008 requires comparison against chaos experiment baselines, but no FR supports this capability. In scope? → A: Softened to data-format concern — result schema includes sufficient structure for future chaos comparison; actual comparison tooling is out of scope.
- Q: What happens when the current run produces metrics absent from the stored baseline (new agent/metric), or vice versa (removed agent)? → A: New metrics not in baseline → first-run semantics (skip regression, log notice). Baseline metrics absent from current run → logged as notice, not treated as regression.
- Q: FR-002 doesn't mention that monitoring's `process_signal()` is async, and Benchmark Result entity lacks git commit SHA. Do these need spec updates? → A: Yes. FR-002 amended to note async entry point; wrapper metadata gets `commit_sha` field.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The benchmark suite MUST measure and record the latency of the health endpoint (GET /health) for each of the five agents: monitoring, risk, evacuation, resource, and communication. Agent port numbers (8080–8084) are runtime identifiers only; benchmarks use in-process TestClient via ASGI transport.
- **FR-002**: The benchmark suite MUST measure and record the end-to-end pipeline processing latency for each agent by calling the pipeline class entry point directly (`process_handoff()` for risk, evacuation, resource, and communication agents; `process_signal()` for the monitoring agent) with mocked external dependencies. Note: `process_signal()` is async and MUST be benchmarked using an event loop wrapper (e.g., `asyncio.run()` or equivalent) compatible with pytest-benchmark.
- **FR-003**: The benchmark suite MUST measure and record the LLM client round-trip time using mocked LLM responses, isolating application-side overhead.
- **FR-004**: The benchmark suite MUST measure and record circuit breaker state transition times (CLOSED → OPEN, OPEN → HALF_OPEN, HALF_OPEN → CLOSED) and total recovery duration.
- **FR-005**: The benchmark suite MUST apply SLO-aligned latency targets per agent:
  - Health endpoint: < 100 ms (general), < 75 ms (safety-critical: risk, evacuation)
  - Pipeline processing: < 2 s (uniform for all agents; safety-critical differentiation deferred to future iteration)
  - LLM client (mocked): < 500 ms
  - Circuit breaker recovery: ≤ 2× configured recovery timeout
- **FR-006**: The benchmark suite MUST store results as structured JSON files in the repo-root `.benchmarks/` directory, using pytest-benchmark's native `--benchmark-json` output format supplemented by a thin comparison wrapper that adds SLO target and regression status metadata.
- **FR-007**: The benchmark suite MUST compare current results against a stored baseline and emit a warning (via `logging.warning()` to CI output — visible but non-blocking, no non-zero exit code) when any metric's median increases by ≥ 20%.
- **FR-008**: The benchmark suite MUST fail the CI step when any metric's median increases by ≥ 50% over the stored baseline.
- **FR-009**: The benchmark suite MUST execute without live Azure services; all external dependencies (LLM, Azure endpoints) MUST be mocked.
- **FR-010**: The benchmark suite MUST use pytest-benchmark for all timing measurements to ensure consistent, statistically sound results.
- **FR-011**: The benchmark suite MUST produce results that are uploadable as CI artifacts for historical trending and pull request review.
- **FR-012**: When no previous baseline exists for a given metric (including new metrics not present in the stored baseline), the benchmark suite MUST treat the current run as the first baseline for that metric, skip regression detection, and log a notice. Baseline metrics absent from the current run MUST be logged as a notice but NOT treated as a regression or failure.
- **FR-013**: The benchmark suite MUST continue executing remaining benchmarks when an individual agent benchmark fails or errors, reporting all results at the end.

### Key Entities

- **Benchmark Result**: A single measurement record containing the agent name, metric type (health, pipeline, LLM, circuit breaker), statistical summary (median, min, max, iterations), SLO target, pass/fail status, timestamp, and `commit_sha` (from `git rev-parse HEAD`) for CI artifact correlation. P95 and P99 percentiles are derivable from the raw `stats.data` array in pytest-benchmark's native JSON output.
- **Baseline**: A stored set of benchmark results used as the reference for regression detection. Updated explicitly (not overwritten on every run).
- **Regression Report**: A comparison output identifying which metrics regressed, by how much, and whether the regression exceeds the warning (20%) or failure (50%) threshold.
- **SLO Target**: A latency ceiling associated with a specific agent and metric type, derived from operational requirements and the project's Life Safety First principle.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five agent health endpoints are benchmarked on every CI run, with per-agent latency results recorded and compared against SLO targets.
- **SC-002**: Safety-critical agents (risk and evacuation) are held to tighter health endpoint latency targets (< 75 ms vs < 100 ms for general agents), reflecting the Life Safety First constitutional principle. Pipeline SLOs remain uniform at < 2 s (per clarification session 1).
- **SC-003**: Pipeline processing benchmarks for all agents complete within the 2 s SLO on every CI run.
- **SC-004**: Latency regressions of ≥ 20% are automatically detected and surfaced as warnings in CI output.
- **SC-005**: Latency regressions of ≥ 50% automatically fail the CI build, preventing performance-degrading changes from merging.
- **SC-006**: Benchmark results are stored as structured JSON artifacts, enabling historical comparison across at least 30 days of CI runs.
- **SC-007**: The full benchmark suite completes within 60 seconds wall-clock time in CI (the entire `pytest tests/benchmark/` command, including setup/teardown), keeping the feedback loop fast for developers. The CI step SHOULD include a `timeout-minutes: 2` safeguard to hard-kill runaway benchmarks.
- **SC-008**: Benchmark result schema includes sufficient structure (metric type, state transitions, timing, commit SHA) to enable future comparison with chaos experiment outputs. Actual chaos comparison tooling is out of scope for this feature.
- **SC-009**: The Performance & Reliability rubric score improves from 3 (Satisfactory) to 4+ (Good/Excellent) as assessed by the AMA rubric.

## Assumptions

- **A-001**: All five agents can be instantiated in-process (via test clients) during CI without requiring network ports or container orchestration.
- **A-002**: Pipeline processing can be exercised via direct function calls with mocked dependencies, without requiring full agent startup.
- **A-003**: The LLM client's `generate_response()` method can be exercised with injected/mocked HTTP responses to avoid Azure OpenAI calls in CI.
- **A-004**: The circuit breaker's `record_failure()` / `record_success()` methods can be called directly to drive state transitions without requiring actual network failures.
- **A-005**: CI runners provide sufficiently consistent timing that a 20% regression threshold reliably distinguishes real regressions from runner noise.
- **A-006**: The existing `pytest-benchmark` dependency is sufficient for all timing measurements; no additional benchmarking tooling is required.
- **A-007**: The `.benchmarks/` directory at the repository root is the canonical location for benchmark result storage. (Note: `apps/agents/.benchmarks/` also exists but is not used; repo root is simpler for CI artifact paths.)

## Dependencies

- **D-001**: Existing `pytest-benchmark` package (already installed in CI).
- **D-002**: Existing agent health endpoints (GET /health on ports 8080–8084).
- **D-003**: Existing `LLMClient` at `apps/agents/common/llm_client.py`.
- **D-004**: Existing `CircuitBreaker` at `apps/agents/common/circuit_breaker.py`.
- **D-005**: CI workflow at `.github/workflows/ci.yml` (to be updated with expanded benchmark step and artifact upload).
- **D-006**: Existing `tests/benchmark/test_api_performance.py` — to be replaced in-place by the new comprehensive benchmark suite. The current 50-concurrent-worker pattern is load testing (out of scope) and will not be preserved.

## Out of Scope

- Load testing or stress testing with high concurrency (hundreds/thousands of concurrent users).
- Benchmarking against live Azure services or real LLM endpoints.
- Automated performance dashboards or visualization tooling (results are JSON files; visualization is a future enhancement).
- Benchmarking the web frontend (`apps/web`).
- Benchmarking database or data layer operations.
- Automatic baseline updates (baselines are updated explicitly by a team member, not overwritten by every CI run).


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-037**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-038**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-039** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-013**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-013.md` (created in feature 028 polish).


## Capstone-Aligned Success Criteria (Feature 028 / FR-012)

The five capstone success metrics MUST each map to at least one benchmark scenario in this spec; AU-v1 baselines are recorded today, capstone-country baselines are deferred. Cited by `specs/shared/capstone-metric-trace.md` SC-Owner cells (see feature 028 / US2 / T039..T043).

- **SC-CAP-015-001** **`LIVES_SAVED`** - AU-v1 baseline scenario: lives at risk per major-flood exercise (BoM-driven); measurement method: pre/post intervention exercise outcomes; capstone target: >= 1,000 lives/yr saved at solution-of-whole level. Capstone-country baselines: deferred.
- **SC-CAP-015-002** **`RESPONSE_SPEED`** - AU-v1 baseline scenario: alert-to-acknowledgement median latency; measurement method: end-to-end timing in benchmark exercises; capstone target: 50 % faster than the unaided reference. Capstone-country baselines: deferred.
- **SC-CAP-015-003** **`EVAC_LEAD_TIME`** - AU-v1 baseline scenario: warning-issuance to recommended-evacuation-start delta; measurement method: timeline reconstruction in benchmark scenarios; capstone target: 24 h earlier evacuation than unaided reference. Capstone-country baselines: deferred.
- **SC-CAP-015-004** **`LOGISTICS_EFFICIENCY`** - AU-v1 baseline scenario: resource utilisation rate (allocated vs idle) during exercise; measurement method: telemetry from `specs/011-resource-allocation-agent`; capstone target: 30 % efficiency uplift. Capstone-country baselines: deferred.
- **SC-CAP-015-005** **`ECONOMIC_LOSS_REDUCTION`** - AU-v1 baseline scenario: estimated avoided economic loss in exercise (Sendai indicator alignment); measurement method: scenario-modelled counterfactual; capstone target: 30 % loss-reduction. Capstone-country baselines: deferred.
