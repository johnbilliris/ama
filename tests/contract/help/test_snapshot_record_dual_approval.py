"""spec-038 T-AA184 — dual-approval enforcement at the publish endpoint."""

from __future__ import annotations

import pytest
from app.api.routes.help_snapshots import router as snapshots_router
from app.repositories import help_repositories
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    help_repositories.reset_in_memory_store()
    app = FastAPI()
    app.include_router(snapshots_router)
    return TestClient(app)


HDR = {"X-Tenant-Id": "tenant-aaa", "X-User-Id": "user-1"}


def test_rejects_single_identity_twice(client: TestClient) -> None:
    r = client.post(
        "/help/snapshots/publish",
        json={
            "source_set": ["a"],
            "approvers": [
                {"identity": "alice", "role": "help_content_owner"},
                {"identity": "alice", "role": "safety_lead"},
            ],
        },
        headers=HDR,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "snapshot.dual_approval_required"


def test_rejects_missing_content_owner(client: TestClient) -> None:
    r = client.post(
        "/help/snapshots/publish",
        json={
            "source_set": ["a"],
            "approvers": [
                {"identity": "alice", "role": "safety_lead"},
                {"identity": "bob", "role": "governance_lead"},
            ],
        },
        headers=HDR,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "snapshot.missing_content_owner"


def test_rejects_missing_safety_or_governance(client: TestClient) -> None:
    r = client.post(
        "/help/snapshots/publish",
        json={
            "source_set": ["a"],
            "approvers": [
                {"identity": "alice", "role": "help_content_owner"},
                {"identity": "bob", "role": "help_content_owner"},
            ],
        },
        headers=HDR,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "snapshot.missing_safety_governance"


def test_accepts_valid_dual_approval(client: TestClient) -> None:
    r = client.post(
        "/help/snapshots/publish",
        json={
            "source_set": ["a"],
            "approvers": [
                {"identity": "alice", "role": "help_content_owner"},
                {"identity": "bob", "role": "safety_lead"},
            ],
        },
        headers=HDR,
    )
    assert r.status_code == 201
    body = r.json()
    assert len(body["approvers"]) == 2
    identities = {a["identity"] for a in body["approvers"]}
    assert identities == {"alice", "bob"}
