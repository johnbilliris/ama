"""Tests for FR-022a dev-only anonymous access on the eval role guard.

Scope (per Phase 10, T091):
  (a) anonymous accepted in dev when ``EVAL_ALLOW_ANONYMOUS=1``
  (b) anonymous rejected when ``ENVIRONMENT=staging`` even if env var is set
  (c) anonymous rejected in dev when env var is unset
  (d) bearer-token path still works in dev
  (e) dataset routes for non-synthetic datasets reject anonymous principals
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (
    _REPO_ROOT,
    _REPO_ROOT / "apps" / "eval-runner" / "src",
    _REPO_ROOT / "packages" / "eval-core" / "src",
):
    sys.path.insert(0, str(p))

# Dev tokens are needed for the bearer-token branch test (d).
os.environ["EVAL_ALLOW_DEV_TOKENS"] = "1"

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from apps.api.app.api.routes.eval import datasets as datasets_route  # noqa: E402
from apps.api.app.api.routes.eval import router as eval_router_module  # noqa: E402
from apps.api.app.middleware import eval_role_guard as guard  # noqa: E402
from apps.api.app.repositories.eval.repositories import DatasetRepository  # noqa: E402

# ---------------------------------------------------------------------------
# Direct unit tests against ``get_principal`` and helpers
# ---------------------------------------------------------------------------


def _call_principal(authorization: str | None = None) -> guard.EvalPrincipal:
    return asyncio.run(guard.get_principal(authorization=authorization))


def test_anonymous_accepted_in_dev_when_env_var_set(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")

    p = _call_principal(authorization=None)

    assert p.sub == "anonymous"
    assert p.is_anonymous is True
    assert p.is_dev_token is True
    assert p.environment == "dev"
    assert p.roles == frozenset({"Eval.Operator", "Eval.Viewer", "Eval.Auditor"})


def test_anonymous_rejected_in_staging_even_when_env_var_set(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")

    with pytest.raises(HTTPException) as exc:
        _call_principal(authorization=None)

    assert exc.value.status_code == 401


def test_anonymous_rejected_in_production_even_when_env_var_set(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")

    with pytest.raises(HTTPException) as exc:
        _call_principal(authorization=None)

    assert exc.value.status_code == 401


def test_anonymous_rejected_in_dev_when_env_var_unset(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.delenv("EVAL_ALLOW_ANONYMOUS", raising=False)

    with pytest.raises(HTTPException) as exc:
        _call_principal(authorization=None)

    assert exc.value.status_code == 401


def test_anonymous_rejected_in_dev_when_env_var_is_empty(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "")

    with pytest.raises(HTTPException) as exc:
        _call_principal(authorization=None)

    assert exc.value.status_code == 401


def test_bearer_dev_token_still_works_in_dev(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_DEV_TOKENS", "1")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")  # anonymous mode also on; bearer still wins

    p = _call_principal(authorization="Bearer dev:alice:Eval.Operator,Eval.Viewer")

    assert p.sub == "alice"
    assert p.is_anonymous is False
    assert p.is_dev_token is True
    assert p.roles == frozenset({"Eval.Operator", "Eval.Viewer"})


def test_audit_metadata_tags_anonymous_with_environment():
    p = guard.EvalPrincipal(
        sub="anonymous",
        roles=guard.ANONYMOUS_ROLES,
        is_dev_token=True,
        environment="dev",
        is_anonymous=True,
    )
    md = guard.audit_metadata(p, foo="bar")
    assert md == {"foo": "bar", "environment": "dev"}


def test_audit_metadata_does_not_tag_authenticated_principal():
    p = guard.EvalPrincipal(sub="alice", roles=frozenset({"Eval.Operator"}))
    md = guard.audit_metadata(p, foo="bar")
    assert md == {"foo": "bar"}


def test_enforce_anonymous_dataset_scope_allows_synthetic_dev_dataset():
    p = guard.EvalPrincipal(
        sub="anonymous",
        roles=guard.ANONYMOUS_ROLES,
        is_dev_token=True,
        environment="dev",
        is_anonymous=True,
    )
    # Should not raise.
    guard.enforce_anonymous_dataset_scope(p, "disaster-response-core")


def test_enforce_anonymous_dataset_scope_rejects_other_datasets():
    p = guard.EvalPrincipal(
        sub="anonymous",
        roles=guard.ANONYMOUS_ROLES,
        is_dev_token=True,
        environment="dev",
        is_anonymous=True,
    )
    with pytest.raises(HTTPException) as exc:
        guard.enforce_anonymous_dataset_scope(p, "real-derived-incidents")
    assert exc.value.status_code == 403


def test_enforce_anonymous_dataset_scope_no_op_for_authenticated_principal():
    p = guard.EvalPrincipal(sub="alice", roles=frozenset({"Eval.Operator"}))
    # Should not raise even for non-synthetic dataset ids.
    guard.enforce_anonymous_dataset_scope(p, "anything-goes")


# ---------------------------------------------------------------------------
# Integration: dataset route enforces anonymous scope (test e)
# ---------------------------------------------------------------------------


def _manifest(dataset_id: str = "disaster-response-core") -> dict:
    return {
        "datasetId": dataset_id,
        "version": "1.0.0",
        "state": "published",
        "contentHash": "sha256:" + "a" * 64,
        "caseCount": 5,
        "distribution": {"hazard:flood": {"count": 5, "percentage": 1.0}},
        "languageScope": ["en-AU"],
        "manifestBlobUri": "blob://test",
        "publishedAt": datetime.now(UTC).isoformat(),
        "publishedBy": "tester",
        "approvalChain": [],
    }


def _client(monkeypatch) -> TestClient:
    monkeypatch.setattr(datasets_route, "_repo", DatasetRepository())
    app = FastAPI()
    app.include_router(datasets_route.router, prefix="/api/eval")
    return TestClient(app)


def test_dataset_post_anonymous_allowed_for_synthetic_dev_dataset(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")
    client = _client(monkeypatch)

    resp = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=_manifest(),
    )
    assert resp.status_code == 201, resp.text


def test_dataset_post_anonymous_rejected_for_other_dataset(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")
    client = _client(monkeypatch)

    resp = client.post(
        "/api/eval/datasets/real-derived-incidents/versions",
        json=_manifest("real-derived-incidents"),
    )
    assert resp.status_code == 403, resp.text


def test_dataset_get_cases_anonymous_rejected_for_other_dataset(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")
    client = _client(monkeypatch)

    resp = client.get(
        "/api/eval/datasets/real-derived-incidents/versions/1.0.0/cases",
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Health endpoint advertises FR-022a anonymous mode
# ---------------------------------------------------------------------------


def _health_client() -> TestClient:
    app = FastAPI()
    app.include_router(eval_router_module.router, prefix="/api")
    return TestClient(app)


def test_health_reports_anonymous_access_true_in_dev_when_enabled(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")
    resp = _health_client().get("/api/eval/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["anonymousAccess"] is True
    assert body["environment"] == "dev"


def test_health_reports_anonymous_access_false_outside_dev(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("EVAL_ALLOW_ANONYMOUS", "1")
    resp = _health_client().get("/api/eval/health")
    assert resp.status_code == 200
    assert resp.json()["anonymousAccess"] is False


def test_health_reports_anonymous_access_false_when_flag_unset(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.delenv("EVAL_ALLOW_ANONYMOUS", raising=False)
    resp = _health_client().get("/api/eval/health")
    assert resp.status_code == 200
    assert resp.json()["anonymousAccess"] is False
