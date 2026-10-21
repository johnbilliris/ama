"""Shared helper utilities for benchmark test modules.

Kept in a separate module (not conftest) so that test files can import
with an unambiguous name that won't shadow the root-level conftest.py.
"""

from __future__ import annotations

import asyncio


def run_async(coro_fn, *args, **kwargs):
    """Execute an async function synchronously for pytest-benchmark compatibility."""
    return asyncio.run(coro_fn(*args, **kwargs))


def set_benchmark_metadata(
    benchmark,
    *,
    agent: str,
    metric_type: str,
    slo_target_s: float,
    evidence_scope: str = "local-mocked",
) -> None:
    """Add SLO metadata to benchmark ``extra_info``."""
    benchmark.extra_info["agent"] = agent
    benchmark.extra_info["metric_type"] = metric_type
    benchmark.extra_info["slo_target_s"] = slo_target_s
    benchmark.extra_info["evidence_scope"] = evidence_scope
