# Data Model: Performance Benchmarks

**Feature**: 015-performance-benchmarks
**Date**: 2025-07-23

---

## Entities

### 1. BenchmarkResult

A single measurement record produced by pytest-benchmark, augmented with SLO metadata.

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `name` | `str` | pytest-benchmark | Fully qualified test function name (e.g., `test_health_monitoring`) |
| `group` | `str` | pytest-benchmark | Benchmark category: `"health"`, `"pipeline"`, `"llm"`, `"circuit-breaker"` |
| `fullname` | `str` | pytest-benchmark | Module path + test name |
| `stats.median` | `float` | pytest-benchmark | Median execution time in seconds — **primary regression metric** |
| `stats.mean` | `float` | pytest-benchmark | Mean execution time in seconds |
| `stats.stddev` | `float` | pytest-benchmark | Standard deviation |
| `stats.min` | `float` | pytest-benchmark | Minimum observed time |
| `stats.max` | `float` | pytest-benchmark | Maximum observed time |
| `stats.rounds` | `int` | pytest-benchmark | Number of rounds executed |
| `stats.iterations` | `int` | pytest-benchmark | Iterations per round |
| `extra_info.slo_target_s` | `float` | wrapper | SLO target in seconds for this benchmark |
| `extra_info.agent` | `str` | wrapper | Agent name (monitoring, risk, evacuation, resource, communication) |
| `extra_info.metric_type` | `str` | wrapper | Category: health, pipeline, llm, circuit_breaker |

**Notes**:
- The native pytest-benchmark JSON schema is preserved unchanged. SLO metadata is added via `benchmark.extra_info` dict (a pytest-benchmark feature).
- `stats.median` is the primary value used for SLO validation and regression detection.
- P95 and P99 are not natively provided by pytest-benchmark but can be derived from `stats.data` (raw timings) when `--benchmark-json` includes data.

### 2. Baseline

A stored set of benchmark results used as the reference for regression detection.

| Field | Type | Description |
|-------|------|-------------|
| `machine_info` | `dict` | pytest-benchmark machine metadata (cpu, hostname, etc.) |
| `commit_info` | `dict` | Git commit metadata (auto-populated by pytest-benchmark) |
| `datetime` | `str` | ISO timestamp of the baseline run |
| `version` | `str` | pytest-benchmark version |
| `benchmarks` | `list[BenchmarkResult]` | Array of all benchmark results in the baseline |

**Storage**: `.benchmarks/baseline.json` (committed to repo)

**Update procedure**:
1. Run benchmarks locally or in CI to produce `.benchmarks/current.json`.
2. Review results for reasonableness.
3. Copy: `cp .benchmarks/current.json .benchmarks/baseline.json`
4. Commit: `git add .benchmarks/baseline.json && git commit -m "Update benchmark baseline"`

**Constraints**:
- NOT auto-updated by CI runs.
- Old baselines are preserved in git history.
- `.benchmarks/current.json` is in `.gitignore`.

### 3. ComparisonReport

Output of the comparison wrapper function — a structured report of per-benchmark regression status.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `str` | ISO timestamp of the comparison |
| `commit_sha` | `str` | Current git commit SHA (`git rev-parse HEAD`; `"unknown"` if unavailable) |
| `baseline_file` | `str` | Path to baseline file used |
| `current_file` | `str` | Path to current results file |
| `overall_status` | `str` | `"PASS"`, `"WARNING"`, or `"FAILURE"` (worst status across all metrics) |
| `has_failures` | `bool` | True if any metric has ≥ 50% regression |
| `results` | `list[MetricComparison]` | Per-benchmark comparison details |
| `summary` | `str` | Human-readable summary for CI output |

### 4. MetricComparison

A single benchmark's comparison result within the ComparisonReport.

| Field | Type | Description |
|-------|------|-------------|
| `benchmark_name` | `str` | Test function name matching between current and baseline |
| `group` | `str` | Benchmark group (health, pipeline, llm, circuit-breaker) |
| `agent` | `str \| None` | Agent name (None for non-agent-specific benchmarks like LLM/CB) |
| `baseline_median_s` | `float \| None` | Baseline median in seconds (None if first run) |
| `current_median_s` | `float` | Current median in seconds |
| `slo_target_s` | `float \| None` | SLO target in seconds (None if not applicable) |
| `slo_pass` | `bool` | Whether current median is below SLO target |
| `pct_change` | `float \| None` | Percentage change vs baseline (None if first run) |
| `status` | `str` | One of: `PASS`, `WARNING`, `FAILURE`, `FIRST_RUN`, `BASELINE_ONLY`, `ERROR` |
| `message` | `str` | Human-readable status message |

### 5. SLOTarget

Configuration mapping benchmark names to SLO targets. Defined as constants in the comparison module.

| Agent | Metric Type | SLO Target | Source |
|-------|------------|------------|--------|
| monitoring | health | 100 ms | FR-005: general agent |
| risk | health | 75 ms | FR-005: safety-critical |
| evacuation | health | 75 ms | FR-005: safety-critical |
| resource | health | 100 ms | FR-005: general agent |
| communication | health | 100 ms | FR-005: general agent |
| all agents | pipeline | 2,000 ms | FR-005: uniform |
| — | llm (mocked) | 500 ms | FR-005 |
| — | circuit_breaker_recovery | 2× recovery_timeout | FR-005: ≤ 2× configured timeout |

---

## Relationships

```
BenchmarkResult ──(many)──> Baseline (stored as JSON array)
BenchmarkResult ──(many)──> ComparisonReport.results (as MetricComparison)
MetricComparison ──(ref)──> SLOTarget (lookup by benchmark name/group)
ComparisonReport ──(derived)──> overall_status (worst of all MetricComparison statuses)
```

---

## State Transitions

### Regression Detection State Machine

```
                    ┌──────────────┐
                    │  FIRST_RUN   │ ← no baseline exists for this metric
                    └──────────────┘
                           │
                     (next run with baseline)
                           ▼
    ┌──────────┐    pct_change < 20%    ┌──────────┐
    │   PASS   │◄───────────────────────│ Compare  │
    └──────────┘                        │  median  │
                                        │  values  │
    ┌──────────┐   20% ≤ pct < 50%     │          │
    │ WARNING  │◄───────────────────────│          │
    └──────────┘                        │          │
                                        │          │
    ┌──────────┐    pct_change ≥ 50%   │          │
    │ FAILURE  │◄───────────────────────┘──────────┘
    └──────────┘
```

### Circuit Breaker State Machine (benchmarked, not owned by this feature)

```
  CLOSED ──(3 failures)──> OPEN ──(timeout)──> HALF_OPEN ──(success)──> CLOSED
                              ▲                     │
                              └──(failure)──────────┘
```

The circuit breaker benchmark measures the time for each transition.

---

## Validation Rules

1. **BenchmarkResult**: `stats.median > 0` (zero or negative values logged as warning, excluded from percentage comparison).
2. **Baseline**: Must be valid JSON with `benchmarks` array. If corrupted → skip comparison, log warning, pass.
3. **ComparisonReport**: `overall_status` MUST be the worst status across all `results`.
4. **SLOTarget**: All targets are positive values in seconds. Missing SLO → skip SLO check for that metric.
5. **MetricComparison**: `pct_change` is calculated as `(current - baseline) / baseline`. Negative values (improvements) are valid and always PASS.
