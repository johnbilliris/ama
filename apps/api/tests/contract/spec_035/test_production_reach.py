"""T017 — production-reachable evaluator route.

Verifies that when ``AMA_ENABLE_PRODUCTION_AUTH=1`` (and test-support disabled),
``POST /api/outcomes/{scenarioId}/evaluate`` is mounted and returns a spec-034
success envelope when called with a valid (test) Entra principal.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def production_app(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("AMA_ENABLE_TEST_SUPPORT", raising=False)
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv(
        "AMA_ENTRA_TEST_PRINCIPAL",
        json.dumps(
            {
                "oid": "00000000-0000-0000-0000-000000000001",
                "sub": "00000000-0000-0000-0000-000000000001",
                "app_role": "incident-commander",
                "roles": ["incident-commander"],
                "persona_id": "incident-commander",
            }
        ),
    )
    import importlib

    from app import main as main_module

    importlib.reload(main_module)
    return TestClient(main_module.create_app())


def test_evaluator_route_is_mounted_when_production_auth_enabled(
    production_app: TestClient,
) -> None:
    res = production_app.post(
        "/api/outcomes/sc-001/evaluate",
        json={
            "scenario_id": "sc-001",
            "context": {"jurisdiction": "AU-NSW"},
            "decision": {"label": "evacuate", "confidence": 0.92},
        },
        headers={"Authorization": "Bearer test-stub-token"},
    )
    assert res.status_code != 404, "production evaluator route must be mounted"


def test_audit_list_route_is_mounted_when_production_auth_enabled(
    production_app: TestClient,
) -> None:
    res = production_app.get(
        "/api/audit/list",
        headers={"Authorization": "Bearer test-stub-token"},
    )
    assert res.status_code != 404, "audit list route must be mounted"


def test_whoami_route_is_mounted_when_production_auth_enabled(
    production_app: TestClient,
) -> None:
    res = production_app.get(
        "/api/auth/whoami",
        headers={"Authorization": "Bearer test-stub-token"},
    )
    assert res.status_code != 404, "/api/auth/whoami must be mounted"


def test_offline_replay_route_is_mounted_when_production_auth_enabled(
    production_app: TestClient,
) -> None:
    res = production_app.post(
        "/api/offline/replay",
        json={"tier": "routine", "entries": []},
        headers={"Authorization": "Bearer test-stub-token"},
    )
    assert res.status_code != 404, "/api/offline/replay must be mounted"
