from __future__ import annotations

import asyncio

import pytest
from communication.health import DependencyHealthReporter


@pytest.mark.asyncio
async def test_health_reporter_distinguishes_healthy_unhealthy_and_unconfigured() -> None:
    def failed_probe():
        raise RuntimeError("down")

    reporter = DependencyHealthReporter(
        {
            "healthy": (lambda: True, True),
            "unhealthy": (failed_probe, True),
            "optional": (None, False),
        },
        cache_seconds=0,
    )

    results = await reporter.check_all()

    assert results["healthy"].status == "healthy"
    assert results["unhealthy"].status == "unhealthy"
    assert results["optional"].status == "not_configured"


@pytest.mark.asyncio
async def test_health_probe_timeout_is_bounded() -> None:
    async def blocked():
        await asyncio.Event().wait()

    reporter = DependencyHealthReporter({"blocked": (blocked, True)}, timeout_seconds=0.01)

    result = (await reporter.check_all())["blocked"]

    assert result.status == "unhealthy"
