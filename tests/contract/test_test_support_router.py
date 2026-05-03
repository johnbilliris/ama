"""Contract tests for the spec 034 test-support router (T010).

Asserts the dual-guard contract from
``specs/034-webapp-capstone-coverage/contracts/persona-fixture.contract.md``:

(a) 404 when ``AMA_TEST_SUPPORT`` is unset.
(b) 404 when ``settings.environment == "production"`` regardless of env var.
(c) 200 + correct shape when both guards green.
(d) Refuses to mutate seed data on any verb.
"""

from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient


def _build_client(monkeypatch, *, environment: str, test_support_flag: str | None) -> TestClient:
    """Rebuild the FastAPI app under specific guard conditions."""

    if test_support_flag is None:
        monkeypatch.delenv("AMA_TEST_SUPPORT", raising=False)
    else:
        monkeypatch.setenv("AMA_TEST_SUPPORT", test_support_flag)
    monkeypatch.setenv("AMA_ENVIRONMENT", environment)

    # Force reload of settings + router so the dual-guard sees current env.
    import app.core.settings as settings_module

    importlib.reload(settings_module)
    settings_module.get_settings.cache_clear()

    import app.middleware.test_support_guard as guard_module

    importlib.reload(guard_module)

    import app.api.router as router_module

    importlib.reload(router_module)

    import app.main as main_module

    importlib.reload(main_module)

    return TestClient(main_module.create_app())


# ----------------------------------------------------------------------
# (a) Guard refuses when AMA_TEST_SUPPORT is unset
# ----------------------------------------------------------------------
def test_router_404_when_env_var_unset(monkeypatch):
    client = _build_client(monkeypatch, environment="dev", test_support_flag=None)
    assert client.get("/api/test-support/personas").status_code == 404
    assert client.get("/api/test-support/personas/incident-commander").status_code == 404


# ----------------------------------------------------------------------
# (b) Guard refuses in production regardless of env var
# ----------------------------------------------------------------------
def test_router_404_in_production(monkeypatch):
    client = _build_client(monkeypatch, environment="production", test_support_flag="1")
    assert client.get("/api/test-support/personas").status_code == 404


# ----------------------------------------------------------------------
# (c) 200 + correct shape when both guards green
# ----------------------------------------------------------------------
def test_router_returns_personas_when_enabled(monkeypatch):
    client = _build_client(monkeypatch, environment="dev", test_support_flag="1")
    res = client.get("/api/test-support/personas")
    assert res.status_code == 200, res.text
    body = res.json()
    assert "items" in body and "count" in body
    assert body["count"] == len(body["items"])
    # 68 personas per spec 034 (10 operational + 58 sector, no asia)
    assert body["count"] == 68
    sample = body["items"][0]
    for key in (
        "persona_id",
        "display_name",
        "organisation_id",
        "jurisdiction_id",
        "role",
        "permissions",
        "aiims_function",
        "direct_reports",
    ):
        assert key in sample, f"missing key {key} in persona fixture shape"


def test_router_returns_404_for_unknown_persona(monkeypatch):
    client = _build_client(monkeypatch, environment="dev", test_support_flag="1")
    res = client.get("/api/test-support/personas/no-such-persona")
    assert res.status_code == 404


def test_router_returns_known_operational_persona(monkeypatch):
    client = _build_client(monkeypatch, environment="dev", test_support_flag="1")
    res = client.get("/api/test-support/personas/incident-commander")
    assert res.status_code == 200, res.text
    assert res.json()["aiims_function"] == "control"


# ----------------------------------------------------------------------
# (d) Refuses to mutate seed data on any verb
# ----------------------------------------------------------------------
def test_router_does_not_mutate_seed(monkeypatch):
    client = _build_client(monkeypatch, environment="dev", test_support_flag="1")
    before = client.get("/api/test-support/personas").json()["count"]

    # Try various mutating-verb attempts; all must NOT change the seed count.
    client.post("/api/test-support/personas", json={"persona_id": "x", "display_name": "X"})
    client.put("/api/test-support/personas/incident-commander", json={"display_name": "Hacked"})
    client.delete("/api/test-support/personas/incident-commander")
    client.patch("/api/test-support/personas/incident-commander", json={"display_name": "Hacked"})

    after = client.get("/api/test-support/personas").json()["count"]
    sample = client.get("/api/test-support/personas/incident-commander").json()
    assert before == after
    assert sample["display_name"] != "Hacked"


def test_seed_scenario_is_read_only(monkeypatch):
    client = _build_client(monkeypatch, environment="dev", test_support_flag="1")
    res = client.post(
        "/api/test-support/seed/scenario",
        json={"scenario_id": "outcome-1-bushfire-extreme-heat"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["scenario"]["outcome"] == 1
    assert "bushfire" in body["scenario"]["hazards"]
    assert "extreme-heat" in body["scenario"]["hazards"]


@pytest.fixture(autouse=True)
def _restore_env():
    """Belt-and-braces: never leak AMA_TEST_SUPPORT between tests."""
    original = os.environ.get("AMA_TEST_SUPPORT")
    yield
    if original is None:
        os.environ.pop("AMA_TEST_SUPPORT", None)
    else:
        os.environ["AMA_TEST_SUPPORT"] = original
