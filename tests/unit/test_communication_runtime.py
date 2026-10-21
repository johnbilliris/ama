from __future__ import annotations

import sys
from types import SimpleNamespace

from communication.config import CommunicationConfig
from communication.runtime import build_application, main
from fastapi.testclient import TestClient


def test_build_application_composes_pipeline_and_services() -> None:
    app = build_application(CommunicationConfig(environment="test", cosmos_endpoint=""))

    assert app.state.pipeline is not None
    assert app.state.approval_workflow is not None
    assert app.state.audit_writer is not None
    assert TestClient(app).get("/health").status_code == 200


def test_deployed_runtime_requires_cosmos_persistence() -> None:
    config = CommunicationConfig(environment="production", cosmos_endpoint="")

    try:
        build_application(config)
    except RuntimeError as exc:
        assert "COSMOS_ENDPOINT" in str(exc)
    else:
        raise AssertionError("Production runtime accepted missing persistence")


def test_main_runs_composed_application_on_configured_port(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(app, **kwargs) -> None:
        captured.update({"app": app, **kwargs})

    monkeypatch.setenv("PORT", "8184")
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_run))

    main()

    assert captured["app"].state.pipeline is not None
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8184


def test_compatibility_entrypoint_delegates_to_runtime(monkeypatch) -> None:
    called = []
    monkeypatch.setattr("communication.runtime.main", lambda: called.append(True))

    from communication.agent import main as compatibility_main

    compatibility_main()

    assert called == [True]
