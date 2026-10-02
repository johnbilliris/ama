"""Health endpoint latency benchmarks for all five agents.

Each agent's ``GET /health`` is benchmarked via an in-process
:class:`~fastapi.testclient.TestClient` (ASGI transport, no TCP sockets).
Safety-critical agents (risk, evacuation) have a tighter SLO (< 75 ms).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence

import httpx
import pytest
from app.main import create_app
from app.services.state_store import INCIDENTS, reset_state
from benchmark_helpers import run_async, set_benchmark_metadata

from packages.domain.src.domain.models.incident import Incident

# ── Monitoring (general) ─────────────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_monitoring(benchmark, monitoring_client) -> None:
    set_benchmark_metadata(benchmark, agent="monitoring", metric_type="health", slo_target_s=0.100)
    response = benchmark(monitoring_client.get, "/health")
    assert response.status_code == 200


# ── Risk Assessment (safety-critical) ────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_risk(benchmark, risk_client) -> None:
    set_benchmark_metadata(benchmark, agent="risk", metric_type="health", slo_target_s=0.075)
    response = benchmark(risk_client.get, "/health")
    assert response.status_code == 200


# ── Evacuation (safety-critical) ─────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_evacuation(benchmark, evacuation_client) -> None:
    set_benchmark_metadata(benchmark, agent="evacuation", metric_type="health", slo_target_s=0.075)
    response = benchmark(evacuation_client.get, "/health")
    assert response.status_code == 200


# ── Resource Allocation (general) ────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_resource(benchmark, resource_client) -> None:
    set_benchmark_metadata(benchmark, agent="resource", metric_type="health", slo_target_s=0.100)
    response = benchmark(resource_client.get, "/health")
    assert response.status_code == 200


# ── Communication (general) ──────────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_communication(benchmark, communication_client) -> None:
    set_benchmark_metadata(benchmark, agent="communication", metric_type="health", slo_target_s=0.100)
    response = benchmark(communication_client.get, "/health")
    assert response.status_code == 200


@pytest.fixture(scope="module")
def api_perf_app():
    reset_state()
    INCIDENTS["inc-bench-001"] = Incident(
        incident_id="inc-bench-001",
        title="Benchmark Incident",
        incident_type="bushfire",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["nsw-01"],
    )
    app = create_app()
    yield app
    reset_state()


def _p95(values: Sequence[float]) -> float:
    ordered = sorted(values)
    index = int(round(0.95 * (len(ordered) - 1)))
    return ordered[max(0, min(index, len(ordered) - 1))]


async def _concurrent_get_p95(app, path: str, concurrency: int) -> float:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

        async def _timed_get() -> tuple[int, float]:
            started = time.perf_counter()
            response = await client.get(path)
            return response.status_code, time.perf_counter() - started

        status_and_latencies = await asyncio.gather(*[_timed_get() for _ in range(concurrency)])

    status_codes = [status_code for status_code, _ in status_and_latencies]
    assert all(status_code == 200 for status_code in status_codes)
    latencies = [latency_s for _, latency_s in status_and_latencies]
    return _p95(latencies)


def _dashboard_burst_p95(app, concurrency: int) -> float:
    return run_async(
        _concurrent_get_p95,
        app,
        "/api/incidents/inc-bench-001/dashboard",
        concurrency,
    )


def _signals_list_burst_p95(app, concurrency: int) -> float:
    return run_async(
        _concurrent_get_p95,
        app,
        "/api/signals?incidentId=inc-bench-001",
        concurrency,
    )


@pytest.mark.benchmark(group="api-lightweight")
@pytest.mark.benchmark(min_rounds=5, max_time=0.6, warmup=False)
def test_api_dashboard_p95_concurrent(benchmark, api_perf_app) -> None:
    concurrency = 50
    set_benchmark_metadata(benchmark, agent="api", metric_type="dashboard", slo_target_s=2.0)
    benchmark.extra_info["required_metric"] = True
    benchmark.extra_info["concurrency"] = concurrency
    p95_s = benchmark(_dashboard_burst_p95, api_perf_app, concurrency)
    benchmark.extra_info["p95_s"] = p95_s
    assert p95_s <= 2.0


@pytest.mark.benchmark(group="api-lightweight")
@pytest.mark.benchmark(min_rounds=5, max_time=0.6, warmup=False)
def test_api_signals_list_p95_concurrent(benchmark, api_perf_app) -> None:
    concurrency = 50
    set_benchmark_metadata(benchmark, agent="api", metric_type="signals-list", slo_target_s=0.5)
    benchmark.extra_info["required_metric"] = True
    benchmark.extra_info["concurrency"] = concurrency
    p95_s = benchmark(_signals_list_burst_p95, api_perf_app, concurrency)
    benchmark.extra_info["p95_s"] = p95_s
    assert p95_s <= 0.5
