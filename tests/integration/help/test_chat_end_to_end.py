"""spec-038 T-AA190 — chat end-to-end SSE shape + audit trail."""

from __future__ import annotations

import pytest
from app.api.routes.help_chat import router as chat_router
from app.repositories import help_repositories
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    help_repositories.reset_in_memory_store()
    app = FastAPI()
    app.include_router(chat_router)
    return TestClient(app)


HDR = {"X-Tenant-Id": "tenant-aaa", "X-User-Id": "user-1"}


def test_chat_streams_meta_refusal_done_when_no_corpus(client: TestClient) -> None:
    """End-to-end SSE shape (no live Foundry path): meta → refusal → done.
    Verifies FR-014 / SC-003 — never fabricated citations when corpus support
    is unavailable."""
    with client.stream("POST", "/help/chat/ask", json={"message": "how do I escalate?"}, headers=HDR) as r:
        body = b"".join(r.iter_bytes()).decode("utf-8")
    for event in ("event: meta", "event: refusal", "event: done"):
        assert event in body, f"missing {event} in SSE stream"
    assert "event: citation" not in body, "must not fabricate citations without corpus"


def test_chat_streams_meta_delta_citation_done_with_grounded_chunks(
    client: TestClient,
) -> None:
    """When the in-memory help corpus contains a matching article, the
    Cosmos-grounded retrieval path MUST emit meta → delta(s) → citation(s) → done.

    Verifies FR-014 (citation grounding) end-to-end against the production
    retrieval seam, not an injected fake; the article is upserted via the
    real ``upsert`` API so the test exercises the genuine list_articles
    code path."""
    help_repositories.upsert(
        help_repositories.HELP_ARTICLES,
        "__global__",
        {
            "id": "art-001",
            "tenant_id": "__global__",
            "slug": "art-001",
            "title": "Escalation guide",
            "kind": "article",
            "domain": "troubleshooting",
            "persona_tags": ["all-personas"],
            "sector_tags": [],
            "surface_tags": [],
            "jurisdiction_tags": [],
            "body_uri": "synthetic://test",
            "body_md": (
                "# Escalation guide\n\n"
                "## How to escalate\n\n"
                "Use the support handoff button to escalate when you cannot proceed. "
                "The escalation captures your correlation ID and the redacted transcript."
            ),
            "snapshot_id": "snap-test",
        },
    )
    with client.stream("POST", "/help/chat/ask", json={"message": "how do I escalate?"}, headers=HDR) as r:
        body = b"".join(r.iter_bytes()).decode("utf-8")
    for event in ("event: meta", "event: delta", "event: citation", "event: done"):
        assert event in body, f"missing {event} in grounded SSE stream"


def test_chat_feedback_enqueues_backlog(client: TestClient) -> None:
    r = client.post(
        "/help/chat/feedback",
        json={"target_kind": "chat_turn", "target_id": "t1", "rating": "not_helpful", "comment": "wrong jurisdiction"},
        headers=HDR,
    )
    assert r.status_code == 202
    assert r.json()["status"] == "enqueued"
    backlog = help_repositories.query("content_review_backlog", "tenant-aaa")
    assert any(b["target_id"] == "t1" for b in backlog)
