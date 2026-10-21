from __future__ import annotations

from unittest.mock import Mock

import pytest
from app.api import health as health_api
from app.main import create_app
from dispatcher import agent as dispatcher
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.agents.common.bootstrap import bootstrap_hold_requested


def test_api_held_startup_does_not_initialize_business_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_BOOTSTRAP_HOLD", "true")
    startup = Mock(side_effect=AssertionError("Business initialization must not run while held"))
    monkeypatch.setattr("app.main.validate_runtime_environment", startup)
    monkeypatch.setattr("app.services.evidence._clients.initialize_registry", startup)
    monkeypatch.setattr("app.api.dependencies.governance_composition.initialize_governance_composition", startup)
    monkeypatch.setattr("app.middleware.activation_mutex._seed_workspace_tasks_safely", startup)
    application = create_app()
    with TestClient(application) as client:
        assert client.get("/api/health/liveness").status_code == 200
        assert client.get("/api/health/startup").json() == {"status": "held", "initialized": True}
        response = client.get("/api/health/readiness")
        assert response.status_code == 503
        assert response.json()["ready"] is False
        for path in ("/api/health", "/api/docs", "/api/simulations"):
            assert client.get(path).status_code == 503
        assert client.post("/api/health/startup").status_code == 503
    startup.assert_not_called()
    assert application.state.startup_complete is False


def test_dispatcher_hold_never_constructs_a_client_or_invokes_business(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_BOOTSTRAP_HOLD", "true")
    constructor = Mock(side_effect=AssertionError("Client construction must not occur while held"))
    monkeypatch.setattr(dispatcher, "_build_foundry_client", constructor)
    with TestClient(dispatcher.create_app()) as client:
        assert client.get("/health/liveness").status_code == 200
        assert client.get("/health/startup").json() == {"status": "held", "initialized": True}
        assert client.get("/health/readiness").status_code == 503
        assert (
            client.post("/monitoring/invoke", json={"tenant_id": "synthetic", "question": "blocked"}).status_code == 503
        )
        assert client.get("/docs").status_code == 503
    constructor.assert_not_called()


def test_dispatcher_invalid_configuration_is_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    from common.llm_config import FoundryConfigurationError

    monkeypatch.delenv("AMA_BOOTSTRAP_HOLD", raising=False)
    monkeypatch.setattr(
        dispatcher, "_build_foundry_client", Mock(side_effect=FoundryConfigurationError("synthetic invalid routing"))
    )
    with TestClient(dispatcher.create_app()) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/health/readiness")
        assert response.status_code == 503
        assert response.json()["dependency_authorization_verified"] is False
        assert response.json()["inference_attempted"] is False


def test_api_readiness_rejects_missing_dependencies_after_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    from common.llm_config import DeploymentResolver

    monkeypatch.setattr(DeploymentResolver, "from_environment", Mock(return_value=Mock()))
    for name in health_api._DEPENDENCY_ENV_KEYS.values():
        monkeypatch.delenv(name, raising=False)
    application = FastAPI()
    application.state.startup_complete = True
    application.state.bootstrap_held = False
    application.include_router(health_api.router, prefix="/api")
    with TestClient(application) as client:
        response = client.get("/api/health/readiness")
        assert response.status_code == 503
        assert response.json()["ready"] is False
        assert response.json()["dependencies"] == {"cosmos": "stub", "redis": "stub", "foundry": "stub"}


def test_api_readiness_does_not_treat_a_listening_process_as_started() -> None:
    application = FastAPI()
    application.include_router(health_api.router, prefix="/api")
    with TestClient(application) as client:
        assert client.get("/api/health/liveness").status_code == 200
        assert client.get("/api/health/startup").status_code == 503
        assert client.get("/api/health/readiness").status_code == 503


def test_bootstrap_hold_rejects_unknown_flag_instead_of_unholding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_BOOTSTRAP_HOLD", "tru")
    with pytest.raises(ValueError, match="AMA_BOOTSTRAP_HOLD"):
        bootstrap_hold_requested()
