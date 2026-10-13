from __future__ import annotations

import asyncio
import json

import pytest
from app.api import health as health_api
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_probes(monkeypatch: pytest.MonkeyPatch) -> None:
    health_api._clear_probe_cache_for_test()
    for name in ("cosmos", "redis", "foundry"):
        health_api._set_dependency_probe_for_test(name, None)
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    monkeypatch.delenv("REDIS_HOST", raising=False)
    monkeypatch.delenv("REDIS_PORT", raising=False)
    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_PROJECT_DEPLOYMENTS", raising=False)
    monkeypatch.delenv("AMA_HEALTH_PROBE_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("AMA_HEALTH_PROBE_TTL_SECONDS", raising=False)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    return TestClient(create_app())


def test_health_returns_stub_when_dependencies_unset(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["dependencies"] == {
        "cosmos": "stub",
        "redis": "stub",
        "foundry": "stub",
    }


def test_health_returns_healthy_for_reachable_configured_dependencies(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://cosmos.local")
    monkeypatch.setenv("REDIS_HOST", "redis.local")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://foundry.local")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-4o@2024-01-01=dep-reasoning")

    health_api._set_dependency_probe_for_test("cosmos", lambda: "healthy")
    health_api._set_dependency_probe_for_test("redis", lambda: "healthy")
    health_api._set_dependency_probe_for_test("foundry", lambda: "healthy")

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["dependencies"] == {
        "cosmos": "healthy",
        "redis": "healthy",
        "foundry": "healthy",
    }


def test_cosmos_probe_uses_http_endpoint_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSMOS_ENDPOINT", "http://cosmos:8081")
    reached: list[tuple[str, int]] = []

    def _reachable(host: str, port: int, timeout_seconds: float) -> bool:  # noqa: ARG001
        reached.append((host, port))
        return True

    monkeypatch.setattr(health_api, "_tcp_reachable", _reachable)

    assert health_api._probe_cosmos() == "healthy"
    assert reached == [("cosmos", 8081)]


def test_health_marks_configured_probe_exception_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://cosmos.local")

    def _boom() -> str:
        raise RuntimeError("probe failed")

    health_api._set_dependency_probe_for_test("cosmos", _boom)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["cosmos"] == "unavailable"


def test_health_marks_timeout_unavailable(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REDIS_HOST", "redis.local")
    monkeypatch.setenv("AMA_HEALTH_PROBE_TIMEOUT_SECONDS", "0.05")

    async def _slow_probe() -> str:
        await asyncio.sleep(0.2)
        return "healthy"

    health_api._set_dependency_probe_for_test("redis", _slow_probe)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["redis"] == "unavailable"


def test_health_marks_foundry_unavailable_when_endpoint_set_but_deployments_missing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://foundry.local")
    monkeypatch.delenv("AZURE_AI_PROJECT_DEPLOYMENTS", raising=False)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["foundry"] == "unavailable"


def test_health_caches_probe_results_within_ttl(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://cosmos.local")
    monkeypatch.setenv("AMA_HEALTH_PROBE_TTL_SECONDS", "10")
    calls = {"count": 0}

    def _cached_probe() -> str:
        calls["count"] += 1
        return "healthy"

    health_api._set_dependency_probe_for_test("cosmos", _cached_probe)

    first = client.get("/api/health")
    second = client.get("/api/health")

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] == 1


def test_health_mixed_dependency_statuses_report_degraded(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://cosmos.local")
    monkeypatch.setenv("REDIS_HOST", "redis.local")

    health_api._set_dependency_probe_for_test("cosmos", lambda: "healthy")
    health_api._set_dependency_probe_for_test("redis", lambda: "unavailable")

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"] == {
        "cosmos": "healthy",
        "redis": "unavailable",
        "foundry": "stub",
    }


def test_health_does_not_leak_secret_material_on_failures(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "SUPER_SECRET_MARKER"
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", f"https://{secret}.foundry.local")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-4o@2024-01-01=dep-reasoning")

    def _fail() -> str:
        raise RuntimeError(f"failed while probing {secret}")

    health_api._set_dependency_probe_for_test("foundry", _fail)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    blob = json.dumps(body)
    assert secret not in blob
    assert "AZURE_AI_PROJECT_ENDPOINT" not in blob


def test_liveness_endpoint_remains_dependency_free(client: TestClient) -> None:
    response = client.get("/api/health/liveness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "dependencies" not in body
