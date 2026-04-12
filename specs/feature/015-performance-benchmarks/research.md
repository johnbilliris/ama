# Research: Performance Benchmarks

**Feature**: 015-performance-benchmarks
**Date**: 2025-07-23
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R-001: Checklist Priority — Report-All vs Fail-Fast (CHK023, CHK037)

**Question**: Does FR-013's "continue executing remaining benchmarks" conflict with FR-008's "fail the CI step"? When multiple agents regress simultaneously, are all regressions reported?

**Decision**: Report-all (fail-at-end), not fail-fast. Every agent is always benchmarked; failures are aggregated at the end.

**Rationale**: FR-013 explicitly requires "continue executing remaining benchmarks when an individual agent benchmark fails or errors, reporting all results at the end." This means:
- A ≥ 50% regression in one agent does NOT block remaining agents from being benchmarked.
- All benchmarks run to completion.
- The comparison wrapper (run as a separate step after all benchmarks) evaluates all results and emits a single aggregated pass/fail.
- The CI step exit code is non-zero only after all agents have been benchmarked and all regressions have been reported.

**Alternatives considered**:
- Fail-fast on first ≥ 50% regression — rejected because FR-013 explicitly requires continued execution and it would mask regressions in other agents.
- Separate CI steps per agent — rejected because it adds CI complexity without benefit (pytest-benchmark's grouping handles categorization).

---

## R-002: Checklist Priority — Comparison Wrapper Interface (CHK005, CHK011)

**Question**: What is the "thin comparison wrapper"? What are its inputs, outputs, invocation method, and error handling?

**Decision**: The comparison wrapper is a simple Python function (`compare_benchmarks()`) that loads the baseline JSON and current run JSON, compares median values per benchmark, and returns a structured report.

**Rationale**: FR-006 prescribes "pytest-benchmark's native `--benchmark-json` output format supplemented by a thin comparison wrapper that adds SLO target and regression status metadata." The wrapper is intentionally minimal:

**Interface**:
```python
def compare_benchmarks(
    current_path: Path,     # Path to current run JSON (pytest-benchmark output)
    baseline_path: Path,    # Path to baseline JSON (stored in .benchmarks/)
    slo_targets: dict[str, float],  # benchmark_name → SLO ceiling in seconds
) -> ComparisonReport:
    """Compare current benchmark results against baseline.
    
    Returns ComparisonReport with per-benchmark status:
    - PASS: within SLO and < 20% regression
    - WARNING: ≥ 20% regression (logged, non-blocking)
    - FAILURE: ≥ 50% regression (causes non-zero exit)
    - FIRST_RUN: no baseline for this metric (logged, non-blocking)
    - BASELINE_ONLY: metric in baseline but not current run (logged, non-blocking)
    """
```

**Error handling**:
- Baseline file missing → all metrics treated as FIRST_RUN, log notice, pass.
- Baseline file corrupted/malformed JSON → skip comparison entirely, log warning, pass. (CHK035)
- Current run file missing → ERROR, fail step (indicates benchmark execution failure).
- Division by zero (baseline median = 0) → skip percentage comparison for that metric, log warning, pass.

**Invocation**: Called by a pytest session-scoped fixture (`conftest.py`) using `pytest_sessionfinish` hook, or as a post-benchmark conftest step. NOT a separate CI step — it runs within the same `pytest tests/benchmark/` command.

**Alternatives considered**:
- Full custom JSON schema replacing pytest-benchmark output — rejected per clarification session decision.
- External CLI tool — rejected; a Python function is simpler, testable, and avoids another dependency.
- pytest plugin — rejected; too heavy for a simple comparison function.

---

## R-003: Checklist Priority — Corrupted Baselines (CHK035)

**Question**: What happens when the baseline JSON file is corrupted, malformed, or schema-incompatible?

**Decision**: Skip comparison entirely, log a warning, and pass the test. Do not fail the CI step.

**Rationale**: A corrupted baseline is an infrastructure issue, not a code regression. Failing the CI step would block all PRs until someone fixes the baseline, creating a class of non-code failures that harms developer velocity. The safer behavior is:
1. Attempt to load and parse baseline JSON.
2. If JSON parsing fails → `logging.warning("Baseline corrupted, skipping comparison")`, treat all metrics as FIRST_RUN.
3. If JSON parses but schema is incompatible (missing expected keys) → same behavior.
4. The current run still produces a valid result file that can become the new baseline.

**Alternatives considered**:
- Fail on corrupted baseline — rejected because it blocks PRs for infrastructure issues.
- Silently ignore — rejected because the warning is important for operators to notice.

---

## R-004: Checklist Priority — Acceptance Scenario Values vs Thresholds (CHK019, CHK022)

**Question**: Are the acceptance scenario threshold examples (25% and 55% in US1, 30% in US2) separate thresholds from FR-007/FR-008 (≥ 20% / ≥ 50%)?

**Decision**: No. The acceptance scenario values (25%, 55%, 30%) are **illustrative examples** showing the thresholds in action, not separate thresholds. The only operative thresholds are ≥ 20% (warning) and ≥ 50% (failure) from FR-007/FR-008.

**Rationale**: 
- US1 scenario 2 says "25% increase" → this exceeds the 20% warning threshold, demonstrating a warning.
- US1 scenario 3 says "55% increase" → this exceeds the 50% failure threshold, demonstrating a failure.
- US2 scenario 2 says "30% increase" → this exceeds the 20% warning threshold.
- US3 scenario 2 says "≥ 20% increase" → directly mirrors FR-007.
- All scenarios use values that would trigger the FR-007/FR-008 gates, confirming they're examples of the same gates in action.

**Implementation**: Only two comparison thresholds exist in code:
```python
WARNING_THRESHOLD = 0.20  # ≥ 20% regression → logging.warning()
FAILURE_THRESHOLD = 0.50  # ≥ 50% regression → assertion failure
```

**Alternatives considered**:
- Per-story thresholds (25%, 30%, etc.) — rejected; would create confusing, inconsistent behavior.

---

## R-005: Async Benchmarking with pytest-benchmark

**Question**: How to benchmark the async `process_signal()` method using pytest-benchmark (which is sync-only)?

**Decision**: Use `asyncio.run()` wrapper inside the benchmark callable.

**Rationale**: pytest-benchmark's `benchmark()` fixture is synchronous. The monitoring pipeline's `process_signal()` is the only async entry point (all other pipelines use sync `process_handoff()`). The standard pattern is:

```python
def test_monitoring_pipeline(benchmark, monitoring_pipeline, sample_signal):
    result = benchmark(lambda: asyncio.run(
        monitoring_pipeline.process_signal(sample_signal, signal_id="bench-001")
    ))
```

This is:
- Compatible with pytest-benchmark's timing infrastructure.
- Consistent with FR-002's note: "MUST be benchmarked using an event loop wrapper."
- The event loop overhead is negligible compared to the 2 s SLO.
- `asyncio.run()` creates a fresh loop per call, which is correct for benchmark isolation.

**Alternatives considered**:
- `benchmark.pedantic()` with custom runner — adds complexity without benefit.
- `pytest-benchmark-async` third-party plugin — doesn't exist as a maintained package.
- `loop.run_until_complete()` with shared loop — creates state leakage between iterations.

---

## R-006: Benchmark Execution Strategy

**Question**: How should benchmarks be structured across files and executed in CI?

**Decision**: One test file per benchmark category, shared conftest.py, single CI command.

**Rationale**:
- **File structure**: 4 test files (health, pipeline, LLM, circuit breaker) + 1 conftest + 1 comparison module.
- **Grouping**: Use `@pytest.mark.benchmark(group="health")` etc. for categorization in output.
- **Execution**: Single `pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json` command.
- **Serial execution**: pytest-benchmark runs benchmarks serially by default (no xdist). This avoids resource contention.
- **Warm-up/iterations**: Delegate to pytest-benchmark defaults (auto-calibration). FR-001 does not specify iteration counts, and the defaults produce statistically sound results.

**CI step**:
```yaml
- name: perf-benchmark
  timeout-minutes: 2
  run: |
    pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q
    python tests/benchmark/compare_benchmarks.py
```

Wait — per R-002, comparison runs inside pytest via session hooks. So CI is just:
```yaml
- name: perf-benchmark
  timeout-minutes: 2
  run: pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q
```

**Alternatives considered**:
- Separate CI step per benchmark category — rejected; adds 4 CI steps for no benefit.
- `--benchmark-compare` built-in — rejected; it compares against previous pytest-benchmark save files, not our custom baseline format with SLO metadata.

---

## R-007: TestClient Instantiation for Health Benchmarks

**Question**: How should agent TestClients be created for health endpoint benchmarks?

**Decision**: Use `create_app()` factory per agent with `fastapi.testclient.TestClient`. Create once per agent in session-scoped fixtures.

**Rationale**: The existing test pattern (used in `tests/unit/test_evacuation_endpoints.py`, `tests/unit/test_resource_allocation_endpoints.py`) creates TestClient from `create_app()`:

```python
from monitoring.agent import create_app as create_monitoring_app
app = create_monitoring_app()
client = TestClient(app)
```

Key design decisions:
- **Fixture scope**: `session` scope for TestClient creation (expensive, done once). The `benchmark` fixture handles timing only the HTTP call.
- **No network ports**: TestClient uses ASGI transport, not actual TCP sockets. No port conflicts.
- **No mocking needed for health endpoints**: `create_app()` works without live Azure services for health checks (health endpoints check internal state, not external services).
- **All 5 agents**: monitoring, risk_assessment, evacuation, resource_allocation, communication — each gets its own TestClient fixture.

**Alternatives considered**:
- `httpx.AsyncClient` — rejected; adds async complexity for simple GET /health.
- Shared TestClient — rejected; each agent has its own FastAPI app.

---

## R-008: Pipeline Benchmark Dependency Mocking

**Question**: How should pipeline dependencies be mocked for benchmarks?

**Decision**: Follow existing unit test patterns — instantiate pipeline classes directly with mocked/None dependencies.

**Rationale**: Each pipeline has a different dependency signature. Based on existing test patterns:

| Agent | Pipeline Class | Key Mocked Dependencies |
|-------|---------------|------------------------|
| Monitoring | `SignalProcessingPipeline` | `audit_writer=AuditWriter(config, cosmos_client=None)`, `llm_client=MagicMock()` |
| Risk | `AssessmentProcessingPipeline` | `audit_writer=AuditWriter(config, cosmos_client=None)` |
| Evacuation | `EvacuationProcessingPipeline` | `road_network=RoadNetworkLoader.load(sample)`, all Cosmos containers=`None` |
| Resource | `AllocationProcessingPipeline` | Full constructor with `None` audit writer's cosmos_client |
| Communication | `CommunicationProcessingPipeline` | `translator=MagicMock(spec=MultilingualTranslator)` |

- `LLMClient` is mocked with `MagicMock()` where needed, with `generate_response.return_value` returning a valid dict.
- All Cosmos/Azure dependencies are `None` — pipelines handle this gracefully.
- `AgentHandoffEvent` constructed with minimal valid fields per existing test patterns.

---

## R-009: Baseline Management Workflow

**Question**: How are baselines stored, updated, and versioned?

**Decision**: Baseline is a committed JSON file at `.benchmarks/baseline.json`. Updated explicitly by running a script or copying `current.json`. Not auto-updated.

**Rationale**:
- FR-006: "structured JSON files in `.benchmarks/`"
- Out of Scope: "Automatic baseline updates (baselines are updated explicitly by a team member)"
- The baseline file is checked into the repo so all branches and CI runs use the same reference.
- Updating is a manual step: `cp .benchmarks/current.json .benchmarks/baseline.json && git commit`.
- The `.benchmarks/current.json` is a CI artifact, uploaded via `actions/upload-artifact`.
- `.gitignore` should include `.benchmarks/current.json` but NOT `.benchmarks/baseline.json`.

**Alternatives considered**:
- Store baseline as CI artifact only — rejected; not accessible to local runs or other branches.
- Auto-update on main branch — explicitly out of scope per spec.

---

## R-010: Regression Detection Boundary Behavior (CHK026)

**Question**: How does regression detection handle boundary values (exactly 20.0%, exactly 50.0%)?

**Decision**: The spec uses "≥" (greater than or equal to), so exactly 20.0% triggers a warning and exactly 50.0% triggers a failure.

**Rationale**: FR-007 says "≥ 20%" and FR-008 says "≥ 50%". Implementation uses `>=` comparisons:

```python
pct_change = (current_median - baseline_median) / baseline_median
if pct_change >= 0.50:
    status = "FAILURE"
elif pct_change >= 0.20:
    status = "WARNING"
else:
    status = "PASS"
```

Note: Check failure first (≥ 50%) to correctly classify the most severe category.

---

## R-011: CI Artifact Upload and Retention (CHK008, CHK043, CHK053)

**Question**: How do benchmark results flow from `.benchmarks/` to CI artifacts? What's the retention policy?

**Decision**: pytest-benchmark writes to `.benchmarks/current.json` via `--benchmark-json`. CI uploads the entire `.benchmarks/` directory as an artifact.

**Rationale**:
- FR-006 and FR-011 refer to the same files — `.benchmarks/current.json` is both the local output and the CI artifact source.
- SC-006 requires "at least 30 days" — this maps to the `retention-days: 30` setting on the artifact upload action.
- The CI step:
  ```yaml
  - uses: actions/upload-artifact@v4
    if: always()
    with:
      name: benchmark-results
      path: .benchmarks/current.json
      retention-days: 30
  ```
- `if: always()` ensures artifacts are uploaded even when benchmarks fail (important for investigating regressions).

---

## R-012: LLM Client Benchmark Design (CHK017, CHK034)

**Question**: What exactly constitutes "application-side overhead" in the LLM client benchmark?

**Decision**: Benchmark the full `generate_response()` call path with a mocked `_client.chat.completions.create()` that returns instantly. This measures serialization, retry logic setup (tenacity decorator overhead), response parsing, and logging.

**Rationale**: FR-003 says "isolating application-side overhead." The LLM client's `generate_response()` method does:
1. Validate configuration (deployment lookup)
2. Set up correlation ID
3. Call `_call_llm_with_retry()` (tenacity-wrapped)
4. Parse response (choices, usage)
5. Log the call
6. Return structured dict

By mocking only `self._client.chat.completions.create()` to return a pre-built response object instantly, we measure everything except the actual HTTP call to Azure OpenAI. This is the correct boundary for "application-side overhead."

Mock construction:
```python
mock_response = MagicMock()
mock_response.choices = [MagicMock(message=MagicMock(content="test response"))]
mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20)
client._client.chat.completions.create = MagicMock(return_value=mock_response)
```

The mock returns instantly (no simulated delay), so the benchmark purely measures Python code path overhead. Variable mock latency (CHK034) is avoided entirely.
