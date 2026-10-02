"""Bounded dependency health checks for the Communication Agent."""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeResult:
    status: str
    latency_ms: float
    last_checked: str
    critical: bool


Probe = Callable[[], object | Awaitable[object]]


class DependencyHealthReporter:
    def __init__(
        self,
        probes: dict[str, tuple[Probe | None, bool]],
        *,
        timeout_seconds: float = 2.0,
        cache_seconds: float = 10.0,
    ) -> None:
        self._probes = probes
        self._timeout_seconds = timeout_seconds
        self._cache_seconds = cache_seconds
        self._cache: dict[str, tuple[float, ProbeResult]] = {}

    async def check_all(self) -> dict[str, ProbeResult]:
        results = await asyncio.gather(
            *(self._check(name, probe, critical) for name, (probe, critical) in self._probes.items())
        )
        return dict(results)

    async def _check(self, name: str, probe: Probe | None, critical: bool) -> tuple[str, ProbeResult]:
        cached = self._cache.get(name)
        now = time.monotonic()
        if cached is not None and now - cached[0] < self._cache_seconds:
            return name, cached[1]
        started = time.perf_counter()
        status = "not_configured" if probe is None else "healthy"
        if probe is not None:
            try:
                if inspect.iscoroutinefunction(probe):
                    await asyncio.wait_for(probe(), timeout=self._timeout_seconds)
                else:
                    result = await asyncio.wait_for(asyncio.to_thread(probe), timeout=self._timeout_seconds)
                    if inspect.isawaitable(result):
                        await asyncio.wait_for(result, timeout=self._timeout_seconds)
            except Exception:
                status = "unhealthy"
        checked_at = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
        probe_result = ProbeResult(
            status=status,
            latency_ms=(time.perf_counter() - started) * 1000,
            last_checked=checked_at,
            critical=critical,
        )
        self._cache[name] = (now, probe_result)
        return name, probe_result


__all__ = ["DependencyHealthReporter", "ProbeResult"]
