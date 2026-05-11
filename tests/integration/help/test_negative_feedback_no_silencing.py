"""spec-038 T-AA199 — negative feedback never auto-disables content (FR-022a)."""

from __future__ import annotations

import pytest
from app.api.routes.help_chat import router as chat_router
from app.repositories import help_repositories
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    help_repositories.reset_in_memory_store()
    help_repositories.upsert(
        "help_articles",
        "tenant-A",
        {"id": "art-1", "tenant_id": "tenant-A", "slug": "important", "title": "Important", "status": "active"},
    )
    app = FastAPI()
    app.include_router(chat_router)
    return TestClient(app)


def test_four_negatives_do_not_disable(client: TestClient) -> None:
    hdr = {"X-Tenant-Id": "tenant-A", "X-User-Id": "u1"}
    for _ in range(4):
        r = client.post(
            "/help/chat/feedback",
            json={"target_kind": "article", "target_id": "art-1", "rating": "not_helpful"},
            headers=hdr,
        )
        assert r.status_code == 202
    # article still listed / still in store
    article = next(
        (a for a in help_repositories.query("help_articles", "tenant-A") if a["id"] == "art-1"),
        None,
    )
    assert article is not None
    assert article.get("status", "active") == "active", "FR-022a: feedback must never auto-disable"


def test_backlog_promotes_to_needs_review_after_threshold(client: TestClient) -> None:
    hdr = {"X-Tenant-Id": "tenant-A", "X-User-Id": "u1"}
    for _ in range(3):
        client.post(
            "/help/chat/feedback",
            json={"target_kind": "article", "target_id": "art-1", "rating": "not_helpful"},
            headers=hdr,
        )
    backlog = help_repositories.query("content_review_backlog", "tenant-A")
    matching = [b for b in backlog if b["target_id"] == "art-1"]
    assert len(matching) >= 3
