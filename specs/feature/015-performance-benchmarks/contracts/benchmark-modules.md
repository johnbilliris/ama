# Contract: Benchmark Test Module Interface

**Feature**: 015-performance-benchmarks
**Date**: 2025-07-23
**Type**: pytest test module interfaces

---

## Overview

Four test modules comprise the benchmark suite. Each uses pytest-benchmark's `benchmark` fixture and follows consistent patterns for grouping, SLO metadata, and fixture scoping.

## Common Patterns (conftest.py)

### Shared Fixtures

```python
# Session-scoped TestClient fixtures (created once, reused across benchmarks)

@pytest.fixture(scope="session")
def monitoring_client() -> TestClient:
    """TestClient for monitoring agent (port 8080 equivalent)."""

@pytest.fixture(scope="session")
def risk_client() -> TestClient:
    """TestClient for risk assessment agent (port 8081 equivalent)."""

@pytest.fixture(scope="session")
def evacuation_client() -> TestClient:
    """TestClient for evacuation agent (port 8082 equivalent)."""

@pytest.fixture(scope="session")
def resource_client() -> TestClient:
    """TestClient for resource allocation agent (port 8083 equivalent)."""

@pytest.fixture(scope="session")
def communication_client() -> TestClient:
    """TestClient for communication agent (port 8084 equivalent)."""
```

### Async Wrapper

```python
def run_async(coro_fn, *args, **kwargs):
    """Execute an async function synchronously for pytest-benchmark compatibility."""
    return asyncio.run(coro_fn(*args, **kwargs))
```

### Benchmark Metadata Helper

```python
def set_benchmark_metadata(benchmark, *, agent: str, metric_type: str, slo_target_s: float):
    """Add SLO metadata to benchmark extra_info."""
    benchmark.extra_info["agent"] = agent
    benchmark.extra_info["metric_type"] = metric_type
    benchmark.extra_info["slo_target_s"] = slo_target_s
```

---

## Module 1: test_api_performance.py (Health Endpoints)

**Replaces**: Existing concurrent-batch load test
**Group**: `health`

### Test Functions

| Function | Agent | SLO | Description |
|----------|-------|-----|-------------|
| `test_health_monitoring` | monitoring | 100 ms | GET /health via TestClient |
| `test_health_risk` | risk | 75 ms | GET /health via TestClient |
| `test_health_evacuation` | evacuation | 75 ms | GET /health via TestClient |
| `test_health_resource` | resource | 100 ms | GET /health via TestClient |
| `test_health_communication` | communication | 100 ms | GET /health via TestClient |

### Pattern

```python
@pytest.mark.benchmark(group="health")
def test_health_monitoring(benchmark, monitoring_client):
    set_benchmark_metadata(benchmark, agent="monitoring", metric_type="health", slo_target_s=0.100)
    response = benchmark(monitoring_client.get, "/health")
    assert response.status_code == 200
```

---

## Module 2: test_pipeline_performance.py (Pipeline Processing)

**Group**: `pipeline`

### Test Functions

| Function | Agent | SLO | Entry Point | Async? |
|----------|-------|-----|-------------|--------|
| `test_pipeline_monitoring` | monitoring | 2 s | `process_signal()` | ✅ Yes |
| `test_pipeline_risk` | risk | 2 s | `process_handoff()` | ❌ No |
| `test_pipeline_evacuation` | evacuation | 2 s | `process_handoff()` | ❌ No |
| `test_pipeline_resource` | resource | 2 s | `process_handoff()` | ❌ No |
| `test_pipeline_communication` | communication | 2 s | `process_handoff()` | ❌ No |

### Pattern (sync)

```python
@pytest.mark.benchmark(group="pipeline")
def test_pipeline_risk(benchmark, risk_pipeline, risk_handoff):
    set_benchmark_metadata(benchmark, agent="risk", metric_type="pipeline", slo_target_s=2.0)
    result = benchmark(risk_pipeline.process_handoff, risk_handoff)
```

### Pattern (async — monitoring only)

```python
@pytest.mark.benchmark(group="pipeline")
def test_pipeline_monitoring(benchmark, monitoring_pipeline, sample_signal):
    set_benchmark_metadata(benchmark, agent="monitoring", metric_type="pipeline", slo_target_s=2.0)
    result = benchmark(
        lambda: asyncio.run(monitoring_pipeline.process_signal(sample_signal, signal_id="bench-001"))
    )
```

---

## Module 3: test_llm_performance.py (LLM Client)

**Group**: `llm`

### Test Functions

| Function | SLO | Description |
|----------|-----|-------------|
| `test_llm_client_overhead` | 500 ms | Full `generate_response()` with mocked `_client` |

### Pattern

```python
@pytest.mark.benchmark(group="llm")
def test_llm_client_overhead(benchmark, mock_llm_client):
    set_benchmark_metadata(benchmark, agent="shared", metric_type="llm", slo_target_s=0.500)
    result = benchmark(
        mock_llm_client.generate_response,
        purpose="reasoning",
        prompt="Assess wildfire risk for region XYZ",
    )
    assert "text" in result
```

---

## Module 4: test_circuit_breaker_performance.py (Circuit Breaker)

**Group**: `circuit-breaker`

### Test Functions

| Function | SLO | Description |
|----------|-----|-------------|
| `test_cb_closed_to_open` | N/A (timing only) | Measure time for 3 failures to trigger OPEN |
| `test_cb_open_to_half_open` | N/A (timing only) | Measure time for recovery timeout transition |
| `test_cb_full_recovery` | ≤ 2× recovery_timeout | Full cycle: CLOSED→OPEN→HALF_OPEN→CLOSED |

### Pattern

```python
@pytest.mark.benchmark(group="circuit-breaker")
def test_cb_full_recovery(benchmark):
    recovery_timeout = 0.1  # Use short timeout for benchmarking
    
    def full_cycle():
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=recovery_timeout)
        # Drive to OPEN
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # Wait for recovery
        time.sleep(recovery_timeout)
        # Probe triggers HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
        # Success returns to CLOSED
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
    
    set_benchmark_metadata(
        benchmark, agent="shared", metric_type="circuit_breaker",
        slo_target_s=recovery_timeout * 2,
    )
    benchmark(full_cycle)
```

**Note**: Circuit breaker benchmarks use a short `recovery_timeout` (100 ms instead of default 30 s) to keep the benchmark suite within the 60 s wall-clock budget. The SLO (≤ 2× timeout) is validated against this shorter value. An injectable `clock` can also be used to avoid `time.sleep()` entirely for the transition timing benchmarks.
