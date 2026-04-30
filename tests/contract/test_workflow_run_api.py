"""Workflow runs API contract test (T051)."""

from __future__ import annotations

import os
import sys

# Ensure agents pkg is importable BEFORE the FastAPI app is imported.
_AGENTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agents"))
if _AGENTS not in sys.path:
    sys.path.insert(0, _AGENTS)

from app.main import create_app  # noqa: E402 — sys.path adjustment must precede this import.
from fastapi.testclient import TestClient  # noqa: E402


def _client() -> TestClient:
    return TestClient(create_app())


def test_list_runs_returns_200_and_envelope_shape() -> None:
    r = _client().get("/api/workflow_runs")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert isinstance(body["items"], list)


def test_get_unknown_run_returns_404() -> None:
    r = _client().get("/api/workflow_runs/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    # AMA's existing exception middleware wraps HTTPException details into a
    # canonical envelope with `errorCategory`/`message`/`correlationId`.
    assert body.get("errorCategory") == "not_found" or body.get("detail", {}).get("error") == "not_found"


def test_approval_gate_metrics_invalid_window_400() -> None:
    r = _client().get("/api/workflow_runs/metrics/approval-gate?window=99h")
    assert r.status_code == 400
    body = r.json()
    # AMA's exception middleware serialises HTTPException details into a
    # `message` string; treat membership of the canonical token as the contract.
    assert "invalid_window" in body.get("message", "") or body.get("detail", {}).get("error") == "invalid_window"


def test_approval_gate_metrics_default_window() -> None:
    r = _client().get("/api/workflow_runs/metrics/approval-gate")
    assert r.status_code == 200
    body = r.json()
    assert body["window"] == "24h"
    for k in ("mtta_seconds", "approvals", "modifications", "rejections", "escalations", "timeouts"):
        assert k in body
