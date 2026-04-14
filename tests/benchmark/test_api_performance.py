"""Health endpoint latency benchmarks for all five agents.

Each agent's ``GET /health`` is benchmarked via an in-process
:class:`~fastapi.testclient.TestClient` (ASGI transport, no TCP sockets).
Safety-critical agents (risk, evacuation) have a tighter SLO (< 75 ms).
"""

from __future__ import annotations

import pytest
from benchmark_helpers import set_benchmark_metadata

# ── Monitoring (general) ─────────────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_monitoring(benchmark, monitoring_client) -> None:
    set_benchmark_metadata(
        benchmark, agent="monitoring", metric_type="health", slo_target_s=0.100
    )
    response = benchmark(monitoring_client.get, "/health")
    assert response.status_code == 200


# ── Risk Assessment (safety-critical) ────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_risk(benchmark, risk_client) -> None:
    set_benchmark_metadata(
        benchmark, agent="risk", metric_type="health", slo_target_s=0.075
    )
    response = benchmark(risk_client.get, "/health")
    assert response.status_code == 200


# ── Evacuation (safety-critical) ─────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_evacuation(benchmark, evacuation_client) -> None:
    set_benchmark_metadata(
        benchmark, agent="evacuation", metric_type="health", slo_target_s=0.075
    )
    response = benchmark(evacuation_client.get, "/health")
    assert response.status_code == 200


# ── Resource Allocation (general) ────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_resource(benchmark, resource_client) -> None:
    set_benchmark_metadata(
        benchmark, agent="resource", metric_type="health", slo_target_s=0.100
    )
    response = benchmark(resource_client.get, "/health")
    assert response.status_code == 200


# ── Communication (general) ──────────────────────────────────────────────────


@pytest.mark.benchmark(group="health")
def test_health_communication(benchmark, communication_client) -> None:
    set_benchmark_metadata(
        benchmark, agent="communication", metric_type="health", slo_target_s=0.100
    )
    response = benchmark(communication_client.get, "/health")
    assert response.status_code == 200
