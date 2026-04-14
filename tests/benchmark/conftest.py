"""Shared benchmark fixtures and configuration.

Provides session-scoped TestClient fixtures for all five agents,
async wrapper, benchmark metadata helper, and the pytest_sessionfinish
hook that triggers regression comparison after all benchmarks complete.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure the benchmark directory is on sys.path so local modules can be imported
_BENCHMARK_DIR = str(Path(__file__).resolve().parent)
if _BENCHMARK_DIR not in sys.path:
    sys.path.insert(0, _BENCHMARK_DIR)

from compare_benchmarks import compare_benchmarks, format_report  # noqa: E402

# ── Agent TestClient fixtures (session-scoped) ────────────────────────────────


@pytest.fixture(scope="session")
def monitoring_client() -> TestClient:
    """TestClient for the monitoring agent (port 8080 equivalent)."""
    from monitoring.agent import create_app as create_monitoring_app

    return TestClient(create_monitoring_app())


@pytest.fixture(scope="session")
def risk_client() -> TestClient:
    """TestClient for the risk assessment agent (port 8081 equivalent)."""
    from risk_assessment.agent import create_app as create_risk_app

    return TestClient(create_risk_app())


@pytest.fixture(scope="session")
def evacuation_client() -> TestClient:
    """TestClient for the evacuation agent (port 8082 equivalent)."""
    from evacuation.agent import create_app as create_evacuation_app

    return TestClient(create_evacuation_app())


@pytest.fixture(scope="session")
def resource_client() -> TestClient:
    """TestClient for the resource allocation agent (port 8083 equivalent)."""
    from resource_allocation.agent import create_app as create_resource_app

    return TestClient(create_resource_app())


@pytest.fixture(scope="session")
def communication_client() -> TestClient:
    """TestClient for the communication agent (port 8084 equivalent)."""
    from communication.agent import create_app as create_communication_app

    return TestClient(create_communication_app())


# ── Helpers ───────────────────────────────────────────────────────────────────


def run_async(coro_fn, *args, **kwargs):
    """Execute an async function synchronously for pytest-benchmark compatibility."""
    return asyncio.run(coro_fn(*args, **kwargs))


def set_benchmark_metadata(
    benchmark, *, agent: str, metric_type: str, slo_target_s: float
) -> None:
    """Add SLO metadata to benchmark ``extra_info``."""
    benchmark.extra_info["agent"] = agent
    benchmark.extra_info["metric_type"] = metric_type
    benchmark.extra_info["slo_target_s"] = slo_target_s


# ── Session finish hook — regression comparison ──────────────────────────────


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Run regression comparison after all benchmarks complete."""
    current = Path(".benchmarks/current.json")
    if not current.exists():
        return  # No results to compare (benchmarks were skipped or --benchmark-json not passed)

    report = compare_benchmarks(current_path=current)

    # Always print the full report (handle Windows encoding gracefully)
    report_text = format_report(report)
    try:
        print(report_text)  # noqa: T201
    except UnicodeEncodeError:
        print(report_text.encode("ascii", errors="replace").decode("ascii"))  # noqa: T201

    # Fail the session if any metric has ≥ 50% regression
    # Skip failure on CI (runner hardware differs from baseline machine)
    if report.has_failures and not os.environ.get("CI"):
        session.exitstatus = 1
