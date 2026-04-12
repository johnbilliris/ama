# Contract: Comparison Wrapper Interface

**Feature**: 015-performance-benchmarks
**Date**: 2025-07-23
**Type**: Internal Python module interface

---

## Overview

The comparison wrapper (`tests/benchmark/compare_benchmarks.py`) is a Python module that compares pytest-benchmark JSON output against a stored baseline. It is the single point of regression detection logic, invoked after all benchmarks complete.

## Module Interface

### Constants

```python
WARNING_THRESHOLD: float = 0.20   # ≥ 20% median increase → warning
FAILURE_THRESHOLD: float = 0.50   # ≥ 50% median increase → failure

BASELINE_PATH: Path = Path(".benchmarks/baseline.json")
CURRENT_PATH: Path = Path(".benchmarks/current.json")
```

### Primary Function

```python
def compare_benchmarks(
    current_path: Path = CURRENT_PATH,
    baseline_path: Path = BASELINE_PATH,
    slo_targets: dict[str, float] | None = None,
) -> ComparisonReport:
    """Compare current benchmark results against stored baseline.

    Args:
        current_path: Path to current run JSON (pytest-benchmark --benchmark-json output).
        baseline_path: Path to baseline JSON file.
        slo_targets: Optional override for SLO targets. If None, uses DEFAULT_SLO_TARGETS.

    Returns:
        ComparisonReport with per-benchmark status and overall pass/fail.

    Behavior:
        - Baseline missing → all metrics FIRST_RUN, overall PASS.
        - Baseline corrupted/malformed → skip comparison, log warning, overall PASS.
        - Current file missing → raises FileNotFoundError (indicates benchmark execution failure).
        - Metric in current but not baseline → FIRST_RUN for that metric.
        - Metric in baseline but not current → BASELINE_ONLY (logged, not a failure).
        - Baseline median is zero → skip percentage comparison for that metric, log warning.
        - Negative percentage change (improvement) → always PASS for regression check.
    """
```

### Data Classes

```python
@dataclass
class MetricComparison:
    benchmark_name: str
    group: str
    agent: str | None
    baseline_median_s: float | None
    current_median_s: float
    slo_target_s: float | None
    slo_pass: bool
    pct_change: float | None
    status: str           # PASS | WARNING | FAILURE | FIRST_RUN | BASELINE_ONLY | ERROR
    message: str

@dataclass
class ComparisonReport:
    timestamp: str
    commit_sha: str
    baseline_file: str
    current_file: str
    overall_status: str   # PASS | WARNING | FAILURE
    has_failures: bool
    results: list[MetricComparison]
    summary: str
```

### Helper Functions

```python
def load_benchmark_json(path: Path) -> dict | None:
    """Load and validate pytest-benchmark JSON. Returns None if corrupted."""

def get_commit_sha() -> str:
    """Return current git commit SHA, or 'unknown' if unavailable."""

def format_report(report: ComparisonReport) -> str:
    """Format report as human-readable text for CI output."""
```

### SLO Target Registry

```python
DEFAULT_SLO_TARGETS: dict[str, float] = {
    # Health endpoints (seconds)
    "test_health_monitoring": 0.100,
    "test_health_risk": 0.075,
    "test_health_evacuation": 0.075,
    "test_health_resource": 0.100,
    "test_health_communication": 0.100,
    # Pipeline processing (seconds)
    "test_pipeline_monitoring": 2.0,
    "test_pipeline_risk": 2.0,
    "test_pipeline_evacuation": 2.0,
    "test_pipeline_resource": 2.0,
    "test_pipeline_communication": 2.0,
    # LLM client (seconds)
    "test_llm_client_overhead": 0.500,
    # Circuit breaker — SLO is dynamic (2× recovery_timeout),
    # validated inside the test, not in the wrapper
}
```

## Invocation Pattern

The wrapper is invoked within the pytest session, not as a separate CI command:

```python
# In tests/benchmark/conftest.py
import pytest
from compare_benchmarks import compare_benchmarks, format_report

def pytest_sessionfinish(session, exitstatus):
    """Run regression comparison after all benchmarks complete."""
    current = Path(".benchmarks/current.json")
    if not current.exists():
        return  # No results to compare (benchmarks were skipped/disabled)
    
    report = compare_benchmarks(current_path=current)
    
    # Log the full report (always, regardless of status)
    print(format_report(report))
    
    # Fail the session if any metric has ≥ 50% regression
    if report.has_failures:
        session.exitstatus = 1
```

## Output Format

### CI Log Output (human-readable)

```
═══════════════════════════════════════════════════
 Benchmark Regression Report — commit abc1234
═══════════════════════════════════════════════════
 ✅ PASS  test_health_monitoring       12.3 ms (SLO: 100 ms)  +3.2%
 ✅ PASS  test_health_risk              8.1 ms (SLO:  75 ms)  +1.1%
 ⚠️ WARN  test_health_evacuation       62.4 ms (SLO:  75 ms) +24.5%
 ✅ PASS  test_health_resource         15.0 ms (SLO: 100 ms)  -2.0%
 ✅ PASS  test_health_communication    18.2 ms (SLO: 100 ms)  +5.3%
 ✅ PASS  test_pipeline_monitoring    450.0 ms (SLO:   2 s)   +8.0%
 ❌ FAIL  test_pipeline_risk         3200.0 ms (SLO:   2 s)  +55.0%
 🆕 NEW   test_pipeline_evacuation   800.0 ms (SLO:   2 s)   first run
───────────────────────────────────────────────────
 Overall: FAILURE (1 failure, 1 warning, 1 new)
═══════════════════════════════════════════════════
```

### JSON Output (in current.json, via pytest-benchmark)

The native pytest-benchmark JSON format is used unchanged. SLO metadata is embedded via `extra_info`:

```json
{
  "benchmarks": [
    {
      "name": "test_health_monitoring",
      "group": "health",
      "extra_info": {
        "slo_target_s": 0.100,
        "agent": "monitoring",
        "metric_type": "health"
      },
      "stats": {
        "median": 0.0123,
        "mean": 0.0130,
        "stddev": 0.0015,
        "min": 0.0110,
        "max": 0.0200,
        "rounds": 100,
        "iterations": 1
      }
    }
  ]
}
```

## Error Handling Summary

| Condition | Behavior | Exit Code Impact |
|-----------|----------|-----------------|
| Baseline file missing | All metrics → FIRST_RUN, log notice | No impact (pass) |
| Baseline file corrupted | Skip comparison, log warning | No impact (pass) |
| Current file missing | Skip comparison entirely | No impact (pytest handles) |
| Metric not in baseline | That metric → FIRST_RUN | No impact |
| Metric not in current | That metric → BASELINE_ONLY, log notice | No impact |
| Baseline median = 0 | Skip % comparison, log warning | No impact |
| ≥ 20% regression | Log warning | No impact (exit 0) |
| ≥ 50% regression | Log failure | Sets exit code 1 |
| Agent fails to start | Benchmark marked ERROR, others continue | Depends on other results |
