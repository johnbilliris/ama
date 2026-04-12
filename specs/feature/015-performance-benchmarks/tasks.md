# Tasks: Performance Benchmarks

**Input**: Design documents from `/specs/015-performance-benchmarks/` and `/specs/feature/015-performance-benchmarks/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested — test tasks are NOT included. The benchmarks themselves ARE the tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and shared configuration

- [ ] T001 Create `.benchmarks/` directory at repo root with empty `.gitkeep` file
- [ ] T002 Add `.benchmarks/current.json` to `.gitignore` (keep `baseline.json` tracked)
- [ ] T003 Create shared benchmark fixtures and configuration in `tests/benchmark/conftest.py` with session-scoped TestClient fixtures for all 5 agents (monitoring, risk, evacuation, resource, communication), `run_async()` helper, `set_benchmark_metadata()` helper, and `pytest_sessionfinish` hook for regression comparison invocation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Comparison wrapper module — the regression detection engine used by ALL user stories

**⚠️ CRITICAL**: No user story benchmark can deliver regression detection value until this phase is complete

- [ ] T004 Implement `ComparisonReport` and `MetricComparison` dataclasses in `tests/benchmark/compare_benchmarks.py` per data-model.md schema (timestamp, commit_sha, overall_status, has_failures, results list)
- [ ] T005 Implement `DEFAULT_SLO_TARGETS` constant dict in `tests/benchmark/compare_benchmarks.py` mapping all benchmark function names to SLO thresholds (health: 0.100/0.075 s, pipeline: 2.0 s, LLM: 0.500 s) per contracts/comparison-wrapper.md
- [ ] T006 Implement `load_benchmark_json()` helper in `tests/benchmark/compare_benchmarks.py` that loads and validates pytest-benchmark JSON from a Path, returns None on corrupted/malformed input with `logging.warning()`
- [ ] T007 Implement `get_commit_sha()` helper in `tests/benchmark/compare_benchmarks.py` that returns current git SHA via `git rev-parse HEAD` subprocess call, or `"unknown"` if unavailable
- [ ] T008 Implement `compare_benchmarks()` function in `tests/benchmark/compare_benchmarks.py` with full regression detection logic: ≥ 50% → FAILURE, ≥ 20% → WARNING, < 20% → PASS, missing baseline → FIRST_RUN, baseline-only metric → BASELINE_ONLY, zero baseline median → skip with warning
- [ ] T009 Implement `format_report()` function in `tests/benchmark/compare_benchmarks.py` that renders `ComparisonReport` as human-readable CI output with status emoji (✅/⚠️/❌/🆕), metric names, SLO values, and percentage changes per contracts/comparison-wrapper.md output format

**Checkpoint**: Comparison wrapper ready — all regression detection logic is testable independently with synthetic JSON inputs

---

## Phase 3: User Story 1 — Multi-Endpoint Latency Benchmarks (Priority: P1) 🎯 MVP

**Goal**: Replace existing `tests/benchmark/test_api_performance.py` with comprehensive health endpoint benchmarks for all 5 agents with SLO-aligned latency targets and per-agent regression detection

**Independent Test**: Run `pytest tests/benchmark/test_api_performance.py --benchmark-json=.benchmarks/current.json -q` and verify all 5 agents produce latency results below their SLO targets (< 100 ms general, < 75 ms safety-critical)

### Implementation for User Story 1

- [ ] T010 [US1] Replace `tests/benchmark/test_api_performance.py` — remove existing concurrent-batch load test and implement `test_health_monitoring()` function benchmarking `GET /health` via monitoring TestClient with `@pytest.mark.benchmark(group="health")`, `set_benchmark_metadata(agent="monitoring", metric_type="health", slo_target_s=0.100)`, and `assert response.status_code == 200`
- [ ] T011 [P] [US1] Add `test_health_risk()` function in `tests/benchmark/test_api_performance.py` benchmarking risk agent `GET /health` with SLO target 0.075 s (safety-critical)
- [ ] T012 [P] [US1] Add `test_health_evacuation()` function in `tests/benchmark/test_api_performance.py` benchmarking evacuation agent `GET /health` with SLO target 0.075 s (safety-critical)
- [ ] T013 [P] [US1] Add `test_health_resource()` function in `tests/benchmark/test_api_performance.py` benchmarking resource agent `GET /health` with SLO target 0.100 s (general)
- [ ] T014 [P] [US1] Add `test_health_communication()` function in `tests/benchmark/test_api_performance.py` benchmarking communication agent `GET /health` with SLO target 0.100 s (general)

**Checkpoint**: All 5 agent health endpoints are benchmarked with SLO targets. Running the suite produces regression detection for every agent. This is the MVP — delivers immediate regression detection.

---

## Phase 4: User Story 5 — Benchmark Result Storage and Regression Detection (Priority: P1) 🎯 MVP

**Goal**: Wire the comparison wrapper (Phase 2) into the pytest session so benchmark results are stored as structured JSON artifacts with automated regression detection on every run

**Independent Test**: Run `pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q` and verify: (1) `.benchmarks/current.json` is produced with correct schema including `extra_info` SLO metadata; (2) comparison report is printed to stdout; (3) synthetic 25% baseline inflation triggers WARNING; (4) synthetic 55% inflation triggers FAILURE with non-zero exit

### Implementation for User Story 5

- [ ] T015 [US5] Wire `pytest_sessionfinish` hook in `tests/benchmark/conftest.py` to call `compare_benchmarks()` from `compare_benchmarks.py`, print `format_report()` output, and set `session.exitstatus = 1` when `report.has_failures` is True
- [ ] T016 [US5] Create initial `.benchmarks/baseline.json` placeholder file (empty JSON structure `{"benchmarks": []}`) so first CI run treats all metrics as FIRST_RUN per FR-012

**Checkpoint**: End-to-end regression detection pipeline works — benchmark results are stored, compared, and produce clear pass/fail signals in CI

---

## Phase 5: User Story 2 — Pipeline Processing Benchmarks (Priority: P2)

**Goal**: Benchmark the pipeline processing path of each agent by calling `process_handoff()` / `process_signal()` directly with mocked dependencies, verifying processing latency stays within the 2 s SLO

**Independent Test**: Run `pytest tests/benchmark/test_pipeline_performance.py -q` and verify all 5 agents complete pipeline processing within 2 s median

### Implementation for User Story 2

- [ ] T017 [US2] Create `tests/benchmark/test_pipeline_performance.py` with pipeline fixture factories — instantiate each agent's pipeline class with mocked dependencies (LLMClient=MagicMock, Cosmos containers=None, AuditWriter with cosmos_client=None) per research.md R-008
- [ ] T018 [US2] Implement `test_pipeline_monitoring()` in `tests/benchmark/test_pipeline_performance.py` using `asyncio.run()` wrapper to benchmark async `process_signal()` with `@pytest.mark.benchmark(group="pipeline")` and SLO target 2.0 s per research.md R-005
- [ ] T019 [P] [US2] Implement `test_pipeline_risk()` in `tests/benchmark/test_pipeline_performance.py` benchmarking sync `process_handoff()` on `AssessmentProcessingPipeline` with SLO target 2.0 s
- [ ] T020 [P] [US2] Implement `test_pipeline_evacuation()` in `tests/benchmark/test_pipeline_performance.py` benchmarking sync `process_handoff()` on `EvacuationProcessingPipeline` with SLO target 2.0 s
- [ ] T021 [P] [US2] Implement `test_pipeline_resource()` in `tests/benchmark/test_pipeline_performance.py` benchmarking sync `process_handoff()` on `AllocationProcessingPipeline` with SLO target 2.0 s
- [ ] T022 [P] [US2] Implement `test_pipeline_communication()` in `tests/benchmark/test_pipeline_performance.py` benchmarking sync `process_handoff()` on `CommunicationProcessingPipeline` with SLO target 2.0 s

**Checkpoint**: All 5 agent pipelines are benchmarked with mocked dependencies. Processing latency is tracked independently of external service calls.

---

## Phase 6: User Story 3 — LLM Client Response Time Benchmarks (Priority: P2)

**Goal**: Benchmark the LLM client's application-side overhead (serialization, retry logic, response parsing) with mocked responses, verifying it stays within the 500 ms SLO budget

**Independent Test**: Run `pytest tests/benchmark/test_llm_performance.py -q` and verify mocked round-trip time is below 500 ms median

### Implementation for User Story 3

- [ ] T023 [US3] Create `tests/benchmark/test_llm_performance.py` with `mock_llm_client` fixture that instantiates `LLMClient` from `apps/agents/common/llm_client.py` and patches `_client.chat.completions.create` to return a pre-built MagicMock response instantly (choices with message content, usage with token counts) per research.md R-012
- [ ] T024 [US3] Implement `test_llm_client_overhead()` in `tests/benchmark/test_llm_performance.py` with `@pytest.mark.benchmark(group="llm")`, `set_benchmark_metadata(agent="shared", metric_type="llm", slo_target_s=0.500)`, calling `generate_response(purpose="reasoning", prompt="...")` and asserting `"text" in result`

**Checkpoint**: LLM client overhead is benchmarked independently. Changes to retry/parsing logic will be caught by regression detection.

---

## Phase 7: User Story 4 — Circuit Breaker Recovery Benchmarks (Priority: P3)

**Goal**: Benchmark circuit breaker state transitions (CLOSED→OPEN→HALF_OPEN→CLOSED) and recovery timing to provide baselines for future chaos experiment comparison

**Independent Test**: Run `pytest tests/benchmark/test_circuit_breaker_performance.py -q` and verify full recovery completes within 2× the configured recovery timeout

### Implementation for User Story 4

- [ ] T025 [US4] Create `tests/benchmark/test_circuit_breaker_performance.py` with imports from `apps/agents/common/circuit_breaker.py` (CircuitBreaker, CircuitState) and a short `recovery_timeout` constant (0.1 s) for fast benchmarking per contracts/benchmark-modules.md
- [ ] T026 [P] [US4] Implement `test_cb_closed_to_open()` in `tests/benchmark/test_circuit_breaker_performance.py` with `@pytest.mark.benchmark(group="circuit-breaker")` — drive 3 `record_failure()` calls, assert `state == CircuitState.OPEN`, record transition time
- [ ] T027 [P] [US4] Implement `test_cb_open_to_half_open()` in `tests/benchmark/test_circuit_breaker_performance.py` — after triggering OPEN state, sleep for `recovery_timeout`, assert `state == CircuitState.HALF_OPEN`, record timing
- [ ] T028 [US4] Implement `test_cb_full_recovery()` in `tests/benchmark/test_circuit_breaker_performance.py` — full cycle CLOSED→OPEN→HALF_OPEN→CLOSED with `set_benchmark_metadata(agent="shared", metric_type="circuit_breaker", slo_target_s=recovery_timeout * 2)`, assert complete recovery within 2× timeout

**Checkpoint**: Circuit breaker state machine is benchmarked with timing data. Result schema supports future chaos experiment comparison (SC-008).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: CI integration, gitignore update, and documentation

- [ ] T029 Update `.github/workflows/ci.yml` — replace existing `perf-benchmark` step: change command to `pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q`, add `timeout-minutes: 2` per SC-007
- [ ] T030 Add `upload-benchmark-results` step in `.github/workflows/ci.yml` after `perf-benchmark` using `actions/upload-artifact@v4` with `if: always()`, `name: benchmark-results`, `path: .benchmarks/current.json`, `retention-days: 30` per contracts/ci-workflow.md
- [ ] T031 Add feature branch `"015-performance-benchmarks"` to `on.push.branches` list in `.github/workflows/ci.yml` for feature development CI triggers
- [ ] T032 Run full benchmark suite locally (`pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -v --benchmark-group-by=group`) and verify: all benchmarks pass, JSON output is valid, comparison report renders correctly, exit code is 0
- [ ] T033 Generate initial baseline by copying verified `current.json` to `.benchmarks/baseline.json` and commit as initial benchmark baseline
- [ ] T034 Run quickstart.md validation — execute all commands from `specs/feature/015-performance-benchmarks/quickstart.md` and verify they work as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (conftest.py must exist for imports) — BLOCKS regression detection in all user stories
- **US1 Health Benchmarks (Phase 3)**: Depends on Phase 1 (conftest.py fixtures) — can start after Phase 1 even before Phase 2 (benchmarks work without comparison)
- **US5 Result Storage (Phase 4)**: Depends on Phase 2 (comparison wrapper) + Phase 1 (conftest.py)
- **US2 Pipeline Benchmarks (Phase 5)**: Depends on Phase 1 (conftest.py) — independent of US1 and US5
- **US3 LLM Benchmarks (Phase 6)**: Depends on Phase 1 (conftest.py) — independent of other stories
- **US4 Circuit Breaker Benchmarks (Phase 7)**: No fixture dependencies — independent of all other stories
- **Polish (Phase 8)**: Depends on Phase 3 at minimum (need benchmarks to exist before CI update)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **User Story 5 (P1)**: Can start after Phase 2 — Needs comparison wrapper but no other stories
- **User Story 2 (P2)**: Can start after Phase 1 — Independent of US1 and US5
- **User Story 3 (P2)**: Can start after Phase 1 — Independent of all other stories
- **User Story 4 (P3)**: Can start immediately (no shared fixtures needed) — Independent of all other stories

### Within Each User Story

- Fixtures/setup before benchmark functions
- All benchmark functions within a module can be parallelized (marked [P]) when they affect the same file ONLY if they are independent additions
- Core implementation before integration

### Parallel Opportunities

- T011, T012, T013, T014 (health benchmarks for risk/evacuation/resource/communication) can all be written in parallel — same file but independent functions
- T019, T020, T021, T022 (pipeline benchmarks for risk/evacuation/resource/communication) can all be written in parallel
- T026, T027 (CB closed→open and open→half_open) can be written in parallel
- Phase 5 (US2), Phase 6 (US3), and Phase 7 (US4) can proceed in parallel after Phase 1 is complete
- T029, T030, T031 (CI workflow updates) should be done together as a single logical commit

---

## Parallel Example: User Story 1 (Health Benchmarks)

```
# After T010 (first benchmark establishing the file pattern):
Task T011: "Add test_health_risk() in tests/benchmark/test_api_performance.py"
Task T012: "Add test_health_evacuation() in tests/benchmark/test_api_performance.py"
Task T013: "Add test_health_resource() in tests/benchmark/test_api_performance.py"
Task T014: "Add test_health_communication() in tests/benchmark/test_api_performance.py"
```

## Parallel Example: User Stories 2, 3, 4 (After Phase 1)

```
# These three user stories are fully independent — different files, no shared state:
Phase 5 (US2): "tests/benchmark/test_pipeline_performance.py"
Phase 6 (US3): "tests/benchmark/test_llm_performance.py"
Phase 7 (US4): "tests/benchmark/test_circuit_breaker_performance.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 5)

1. Complete Phase 1: Setup (conftest.py, .benchmarks/ directory, .gitignore)
2. Complete Phase 2: Foundational (comparison wrapper)
3. Complete Phase 3: User Story 1 — Health endpoint benchmarks for all 5 agents
4. Complete Phase 4: User Story 5 — Wire regression detection into pytest session
5. **STOP and VALIDATE**: Run full suite, verify JSON output, regression detection, and SLO checks
6. This MVP replaces the existing single-endpoint benchmark with comprehensive 5-agent coverage + regression detection

### Incremental Delivery

1. Setup + Foundational + US1 + US5 → MVP with health benchmarks and regression detection ✅
2. Add US2 (Pipeline) → Pipeline latency tracking for all agents ✅
3. Add US3 (LLM) → LLM client overhead monitoring ✅
4. Add US4 (Circuit Breaker) → Resilience baseline data ✅
5. Polish → CI integration, artifact upload, baseline generation ✅
6. Each story adds a new benchmark category without breaking existing benchmarks

### Parallel Team Strategy

With multiple developers:

1. All complete Phase 1 (Setup) together
2. One developer handles Phase 2 (comparison wrapper) — blocking
3. Once Phase 1 is done:
   - Developer A: US1 (health benchmarks) — Phase 3
   - Developer B: US2 (pipeline benchmarks) — Phase 5
   - Developer C: US3 + US4 (LLM + circuit breaker) — Phases 6 & 7
4. Once Phase 2 is done: Developer A wires US5 (Phase 4)
5. Final: Anyone handles Phase 8 (CI integration)

---

## Notes

- [P] tasks = different files or independent additions to same file, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story produces a separate test module (except US1/US5 which share conftest.py integration)
- The existing `test_api_performance.py` is replaced in-place (T010) — the concurrent-batch pattern is load testing and out of scope
- All benchmarks use in-process mocks (not network mocks) to eliminate external timing variability
- Circuit breaker benchmarks use short recovery_timeout (0.1 s) to stay within 60 s wall-clock budget
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
