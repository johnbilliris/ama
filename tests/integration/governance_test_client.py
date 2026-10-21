from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

# Guard against accidental live backends during import-time test setup.
os.environ.pop("COSMOS_ENDPOINT", None)
os.environ.pop("REDIS_HOST", None)

import pytest
from app.api.dependencies.governance_composition import GovernanceComposition
from app.main import create_app
from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_cache import GovernanceCacheService
from app.services.governance_registry import GovernanceRegistryService
from app.services.state_store import reset_state
from fastapi.testclient import TestClient


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def monotonic(self) -> float:
        return self.current.timestamp()

    def advance(self, seconds: float) -> None:
        self.current = self.current + timedelta(seconds=seconds)


def _claims_header(role: str, subject: str = "integration-user") -> str:
    claims = {
        "sub": subject,
        "agency_id": "nsw-ses",
        "jurisdiction_ids": ["nsw"],
        "roles": [role],
        "persona_id": role,
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("ascii")
    return encoded


@pytest.fixture
def governance_client_factory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "0")
    monkeypatch.setenv("AMA_GOVERNANCE_BACKEND_MODE", "in_memory")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    monkeypatch.delenv("REDIS_HOST", raising=False)
    reset_state()

    def _build() -> tuple[TestClient, FakeClock]:
        clock = FakeClock(current=datetime(2026, 1, 1, tzinfo=UTC))
        app = create_app()
        repo = GovernanceRepository()
        cache = GovernanceCacheService(ttl_seconds=5, retention_seconds=30, now=clock.monotonic)
        registry = GovernanceRegistryService(repo=repo, now_provider=clock.now)
        registry.set_cache_invalidator(
            lambda data_source_id, tenant_id: cache.invalidate(data_source_id, tenant_id=tenant_id)
        )

        composition = GovernanceComposition(
            repository=repo,
            registry=registry,
            cache=cache,
            backend_mode="in_memory",
        )
        app.state.governance_composition = composition
        app.state.governance_repository = repo
        app.state.governance_registry = registry
        app.state.governance_cache = cache

        return TestClient(app), clock

    return _build


@pytest.fixture
def governance_client(governance_client_factory):
    return governance_client_factory()


@pytest.fixture
def governance_write_headers() -> dict[str, str]:
    return {
        "X-MS-CLIENT-PRINCIPAL": _claims_header("governance_lead"),
        "X-Tenant-Id": "live",
    }


@pytest.fixture
def governance_read_headers() -> dict[str, str]:
    return {
        "X-MS-CLIENT-PRINCIPAL": _claims_header("observer_auditor", subject="auditor"),
        "X-Tenant-Id": "live",
    }


@pytest.fixture
def governance_forbidden_headers() -> dict[str, str]:
    return {
        "X-MS-CLIENT-PRINCIPAL": _claims_header("simulation_user", subject="blocked-user"),
        "X-Tenant-Id": "live",
    }
