"""Tests for the AMA API ↔ eval-runner integration we added for full-fix dev.

Covers:
- POST /api/eval/datasets/{id}/versions registers a manifest and returns 201.
- POST then PATCH/POST again with same content hash returns the same version (idempotent).
- POST then POST again with different content hash returns 409 Conflict.
- eval_job_trigger.is_configured() reflects required env vars.
- runner.py reads run args from AMA_EVAL_* env vars when CLI args are missing.
"""

from __future__ import annotations

import importlib
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (
    _REPO_ROOT,
    _REPO_ROOT / "apps" / "eval-runner" / "src",
    _REPO_ROOT / "packages" / "eval-core" / "src",
):
    sys.path.insert(0, str(p))

os.environ.pop("COSMOS_ENDPOINT", None)
os.environ["EVAL_ALLOW_DEV_TOKENS"] = "1"

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from apps.api.app.api.routes.eval import datasets as datasets_route  # noqa: E402
from apps.api.app.repositories.eval.repositories import DatasetRepository  # noqa: E402


def _manifest(content_hash: str = "sha256:" + "a" * 64) -> dict:
    return {
        "datasetId": "disaster-response-core",
        "version": "1.0.0",
        "state": "published",
        "contentHash": content_hash,
        "caseCount": 5,
        "distribution": {"hazard:flood": {"count": 5, "percentage": 1.0}},
        "languageScope": ["en-AU"],
        "manifestBlobUri": "blob://test",
        "publishedAt": datetime.now(UTC).isoformat(),
        "publishedBy": "tester",
        "approvalChain": [],
    }


def _client_with_fresh_repo(monkeypatch) -> TestClient:
    repo = DatasetRepository()
    monkeypatch.setattr(datasets_route, "_repo", repo)
    app = FastAPI()
    app.include_router(datasets_route.router, prefix="/api/eval")
    return TestClient(app)


def _auth() -> dict:
    return {"Authorization": "Bearer dev:tester:Eval.Operator"}


def test_post_dataset_version_creates_record(monkeypatch):
    client = _client_with_fresh_repo(monkeypatch)

    resp = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=_manifest(),
        headers=_auth(),
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["datasetId"] == "disaster-response-core"
    assert body["version"] == "1.0.0"


def test_post_dataset_version_is_idempotent_same_hash(monkeypatch):
    client = _client_with_fresh_repo(monkeypatch)
    payload = _manifest()

    first = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=payload,
        headers=_auth(),
    )
    assert first.status_code == 201, first.text

    second = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=payload,
        headers=_auth(),
    )
    assert second.status_code == 201
    assert second.json()["contentHash"] == payload["contentHash"]


def test_post_dataset_version_rejects_hash_change(monkeypatch):
    client = _client_with_fresh_repo(monkeypatch)

    first = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=_manifest("sha256:" + "a" * 64),
        headers=_auth(),
    )
    assert first.status_code == 201

    second = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=_manifest("sha256:" + "b" * 64),
        headers=_auth(),
    )
    assert second.status_code == 409


def test_post_dataset_version_rejects_path_id_mismatch(monkeypatch):
    client = _client_with_fresh_repo(monkeypatch)

    resp = client.post(
        "/api/eval/datasets/some-other-dataset/versions",
        json=_manifest(),
        headers=_auth(),
    )

    assert resp.status_code == 400


def test_post_dataset_version_requires_operator_role(monkeypatch):
    client = _client_with_fresh_repo(monkeypatch)

    resp = client.post(
        "/api/eval/datasets/disaster-response-core/versions",
        json=_manifest(),
        headers={"Authorization": "Bearer dev:viewer:Eval.Viewer"},
    )

    assert resp.status_code == 403


def test_eval_job_trigger_not_configured_by_default(monkeypatch):
    for var in ("EVAL_RUNNER_JOB_IMAGE", "EVAL_RUNNER_JOB_NAME", "EVAL_RUNNER_JOB_RESOURCE_GROUP"):
        monkeypatch.delenv(var, raising=False)

    from apps.api.app.services import eval_job_trigger

    importlib.reload(eval_job_trigger)
    assert eval_job_trigger.is_configured() is False
    assert (
        eval_job_trigger.start_run_execution(
            run_id="r1",
            dataset_id="d1",
            dataset_version="1.0.0",
            mode="ad-hoc",
        )
        is None
    )


def test_eval_job_trigger_is_configured_when_env_set(monkeypatch):
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "sub1")
    monkeypatch.setenv("EVAL_RUNNER_JOB_RESOURCE_GROUP", "rg-eval")
    monkeypatch.setenv("EVAL_RUNNER_JOB_NAME", "caj-eval-runner-dev")
    monkeypatch.setenv("EVAL_RUNNER_JOB_IMAGE", "registry.example/eval-runner:dev")

    from apps.api.app.services import eval_job_trigger

    importlib.reload(eval_job_trigger)
    assert eval_job_trigger.is_configured() is True


def test_runner_main_falls_back_to_env_vars(monkeypatch):
    monkeypatch.setenv("AMA_EVAL_RUN_ID", "r-env")
    monkeypatch.setenv("AMA_EVAL_DATASET_ID", "disaster-response-core")
    monkeypatch.setenv("AMA_EVAL_DATASET_VERSION", "1.0.0")

    from ama_eval import runner

    rc = runner.main(["--dry-run"])
    assert rc == 0


def test_runner_main_errors_when_args_missing(monkeypatch, capsys):
    for var in ("AMA_EVAL_RUN_ID", "AMA_EVAL_DATASET_ID", "AMA_EVAL_DATASET_VERSION"):
        monkeypatch.delenv(var, raising=False)

    from ama_eval import runner

    try:
        runner.main([])
    except SystemExit as exc:
        assert exc.code == 2
    captured = capsys.readouterr()
    assert "AMA_EVAL_RUN_ID" in captured.err
