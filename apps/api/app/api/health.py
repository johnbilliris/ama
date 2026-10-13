import asyncio
import logging
import os
import socket
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from inspect import iscoroutinefunction
from urllib.parse import urlparse

from app.observability.tenant_telemetry import telemetry_status
from fastapi import APIRouter

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


_DEPENDENCY_ENV_KEYS: dict[str, str] = {
    "cosmos": "COSMOS_ENDPOINT",
    "redis": "REDIS_HOST",
    "foundry": "AZURE_AI_PROJECT_ENDPOINT",
}


ProbeResult = str
ProbeFunc = Callable[[], ProbeResult | Awaitable[ProbeResult]]


@dataclass(frozen=True)
class _ProbeCacheEntry:
    status: ProbeResult
    expires_at: float


_PROBE_CACHE: dict[str, _ProbeCacheEntry] = {}
_PROBE_OVERRIDES: dict[str, ProbeFunc] = {}


def _health_probe_timeout_seconds() -> float:
    raw = os.getenv("AMA_HEALTH_PROBE_TIMEOUT_SECONDS", "0.35")
    try:
        timeout = float(raw)
    except ValueError:
        timeout = 0.35
    return max(0.05, min(2.0, timeout))


def _health_probe_ttl_seconds() -> float:
    raw = os.getenv("AMA_HEALTH_PROBE_TTL_SECONDS", "5")
    try:
        ttl = float(raw)
    except ValueError:
        ttl = 5.0
    return max(0.0, min(30.0, ttl))


def _extract_host(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"tcp://{value}")
    host = (parsed.hostname or "").strip()
    return host


def _tcp_reachable(host: str, port: int, timeout_seconds: float) -> bool:
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except Exception:
        return False


def _probe_cosmos() -> ProbeResult:
    endpoint = os.getenv("COSMOS_ENDPOINT", "")
    host = _extract_host(endpoint)
    if not host:
        return "unavailable"
    try:
        parsed = urlparse(endpoint if "://" in endpoint else f"tcp://{endpoint}")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError:
        return "unavailable"
    return "healthy" if _tcp_reachable(host, port, _health_probe_timeout_seconds()) else "unavailable"


def _probe_redis() -> ProbeResult:
    host = _extract_host(os.getenv("REDIS_HOST", ""))
    port_raw = os.getenv("REDIS_PORT", "6379")
    try:
        port = int(port_raw)
    except ValueError:
        port = 6379
    return "healthy" if _tcp_reachable(host, port, _health_probe_timeout_seconds()) else "unavailable"


def _probe_foundry() -> ProbeResult:
    endpoint = (os.getenv("AZURE_AI_PROJECT_ENDPOINT", "") or "").strip()
    deployments = (os.getenv("AZURE_AI_PROJECT_DEPLOYMENTS", "") or "").strip()
    if not endpoint or not deployments:
        return "unavailable"
    host = _extract_host(endpoint)
    return "healthy" if _tcp_reachable(host, 443, _health_probe_timeout_seconds()) else "unavailable"


_DEFAULT_PROBES: dict[str, ProbeFunc] = {
    "cosmos": _probe_cosmos,
    "redis": _probe_redis,
    "foundry": _probe_foundry,
}


def _set_dependency_probe_for_test(name: str, probe: ProbeFunc | None) -> None:
    if probe is None:
        _PROBE_OVERRIDES.pop(name, None)
        return
    _PROBE_OVERRIDES[name] = probe


def _clear_probe_cache_for_test() -> None:
    _PROBE_CACHE.clear()


async def _run_probe_with_timeout(probe: ProbeFunc, timeout_seconds: float) -> ProbeResult:
    if iscoroutinefunction(probe):
        status = await asyncio.wait_for(probe(), timeout=timeout_seconds)
    else:
        status = await asyncio.wait_for(asyncio.to_thread(probe), timeout=timeout_seconds)
    return status if status in {"healthy", "unavailable"} else "unavailable"


async def _dependency_status(name: str, env_name: str) -> str:
    value = os.getenv(env_name)
    if not value:
        return "stub"

    now = time.monotonic()
    cached = _PROBE_CACHE.get(name)
    if cached and cached.expires_at > now:
        return cached.status

    timeout_seconds = _health_probe_timeout_seconds()
    ttl_seconds = _health_probe_ttl_seconds()
    probe = _PROBE_OVERRIDES.get(name) or _DEFAULT_PROBES[name]
    try:
        status = await _run_probe_with_timeout(probe, timeout_seconds)
    except Exception:
        status = "unavailable"

    _PROBE_CACHE[name] = _ProbeCacheEntry(status=status, expires_at=now + ttl_seconds)
    return status


@router.get("/health/liveness")
async def liveness() -> dict[str, object]:
    return {
        "status": "healthy",
        "version": "0.2.0",
    }


@router.get("/health")
async def healthcheck() -> dict[str, object]:
    dependencies = {
        "cosmos": await _dependency_status("cosmos", _DEPENDENCY_ENV_KEYS["cosmos"]),
        "redis": await _dependency_status("redis", _DEPENDENCY_ENV_KEYS["redis"]),
        # Spec 036 / ADR-20 — Foundry is the canonical chat plane post-cutover.
        "foundry": await _dependency_status("foundry", _DEPENDENCY_ENV_KEYS["foundry"]),
    }

    configured_unavailable = any(
        dependencies[name] == "unavailable" and bool(os.getenv(env_name))
        for name, env_name in _DEPENDENCY_ENV_KEYS.items()
    )
    status = "degraded" if configured_unavailable else "healthy"

    return {
        "status": status,
        "version": "0.2.0",
        "dependencies": dependencies,
        "telemetry": telemetry_status(),
    }
