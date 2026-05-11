"""spec-038 T-AA191 — publish + rollback flow."""

from __future__ import annotations

import time

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


def test_publish_then_list_then_rollback_under_budget(client: TestClient) -> None:
    t0 = time.perf_counter()
    pub = client.post(
        "/help/snapshots/publish",
        json={
            "source_set": ["a", "b"],
            "approvers": [
                {"identity": "alice", "role": "help_content_owner"},
                {"identity": "bob", "role": "safety_lead"},
            ],
        },
        headers=HDR,
    )
    assert pub.status_code == 201
    snapshot_id = pub.json()["id"]

    listed = client.get("/help/snapshots", headers=HDR)
    assert listed.status_code == 200
    assert any(s["id"] == snapshot_id for s in listed.json())

    rb = client.post(f"/help/snapshots/{snapshot_id}/rollback", headers=HDR)
    elapsed = time.perf_counter() - t0
    assert rb.status_code == 200
    assert elapsed < 300, f"FR-011c 5-min rollback budget breached: {elapsed:.2f}s"
