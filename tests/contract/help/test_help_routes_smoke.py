"""spec-038 T-AA092 — Phase 3 route smoke tests.

Exercises every help router via FastAPI TestClient without requiring
Cosmos / Foundry / AI Search.
"""

from __future__ import annotations

import pytest
from app.api.routes.help_articles import router as articles_router
from app.api.routes.help_chat import router as chat_router
from app.api.routes.help_screenshots import router as screenshots_router
from app.api.routes.help_search import router as search_router
from app.api.routes.help_snapshots import router as snapshots_router
from app.api.routes.help_support_handoff import router as handoff_router
from app.repositories import help_repositories
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    help_repositories.reset_in_memory_store()
    app = FastAPI()
    for r in (chat_router, articles_router, snapshots_router, screenshots_router, search_router, handoff_router):
        app.include_router(r)
    return TestClient(app)


HDR = {"X-Tenant-Id": "tenant-aaa", "X-User-Id": "user-1", "X-Persona-Id": "operational-default"}


def test_articles_list_empty(client: TestClient) -> None:
    r = client.get("/help/articles", headers=HDR)
    assert r.status_code == 200
    assert r.json() == {"items": [], "continuation": None}


def test_articles_get_404(client: TestClient) -> None:
    r = client.get("/help/articles/missing", headers=HDR)
    assert r.status_code == 404


def test_articles_etag(client: TestClient) -> None:
    help_repositories.upsert(
        "help_articles",
        "tenant-aaa",
        {"id": "a1", "tenant_id": "tenant-aaa", "slug": "foo", "title": "Foo", "updated_at": "2025-01-01T00:00:00Z"},
    )
    r1 = client.get("/help/articles/foo", headers=HDR)
    assert r1.status_code == 200
    etag = r1.headers["ETag"]
    r2 = client.get("/help/articles/foo", headers={**HDR, "If-None-Match": etag})
    assert r2.status_code == 304


def test_articles_get_nested_slug(client: TestClient) -> None:
    slug = "screen-by-screen/multi-jurisdiction-filter"
    help_repositories.upsert(
        "help_articles",
        "tenant-aaa",
        {
            "id": "a2",
            "tenant_id": "tenant-aaa",
            "slug": slug,
            "title": "Multi-jurisdiction filter",
            "updated_at": "2025-01-01T00:00:00Z",
        },
    )

    response = client.get(f"/help/articles/{slug}", headers=HDR)

    assert response.status_code == 200
    assert response.json()["slug"] == slug


def test_chat_sse_stream(client: TestClient) -> None:
    """Without live Foundry (HELP_FOUNDRY_LIVE!=1), the route MUST emit an honest
    refusal stream — never fake citations (FR-014, Constitution Principle I).
    Contract: meta is first, done is last, refusal appears between when no
    grounded chunks are available."""
    with client.stream("POST", "/help/chat/ask", json={"message": "hello"}, headers=HDR) as r:
        body = b"".join(r.iter_bytes()).decode("utf-8")
    assert r.status_code == 200
    assert "event: meta" in body
    assert "event: refusal" in body
    assert "event: done" in body
    # Honest behaviour — never fabricated citations when corpus support is missing.
    assert "event: citation" not in body


def test_chat_feedback(client: TestClient) -> None:
    r = client.post(
        "/help/chat/feedback",
        json={"target_kind": "chat_turn", "target_id": "t1", "rating": "helpful"},
        headers=HDR,
    )
    assert r.status_code == 202
    assert r.json()["status"] == "enqueued"


def test_chat_session_isolation(client: TestClient) -> None:
    help_repositories.upsert(
        "chat_sessions",
        "tenant-aaa",
        {"id": "s1", "tenant_id": "tenant-aaa", "user_id": "user-1", "turns": []},
    )
    r = client.get("/help/chat/sessions/s1", headers=HDR)
    assert r.status_code == 200
    # cross-user must 404
    r2 = client.get("/help/chat/sessions/s1", headers={**HDR, "X-User-Id": "user-2"})
    assert r2.status_code == 404


def test_snapshot_publish_dual_approval(client: TestClient) -> None:
    bad = client.post(
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
    assert bad.status_code == 422
    ok = client.post(
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
    assert ok.status_code == 201
    sid = ok.json()["id"]
    rb = client.post(f"/help/snapshots/{sid}/rollback", headers=HDR)
    assert rb.status_code == 200


def test_staleness_lifecycle(client: TestClient) -> None:
    raise_ = client.post(
        "/help/screenshots/staleness",
        json={"screen_id": "screen-1", "reason": "ui-changed", "action": "raise"},
        headers=HDR,
    )
    assert raise_.status_code == 202
    fid = raise_.json()["flag_id"]
    listed = client.get("/help/screenshots/staleness", headers=HDR)
    assert listed.status_code == 200 and len(listed.json()) == 1
    cleared = client.post(f"/help/screenshots/staleness/{fid}/clear", headers=HDR)
    assert cleared.status_code == 202


def test_screenshot_signed_url(client: TestClient) -> None:
    r = client.get("/help/screenshots/sc-1/url?theme=light", headers=HDR)
    assert r.status_code == 200
    body = r.json()
    assert body["theme"] == "light" and body["url"].startswith("https://")


def test_search_glossary_first(client: TestClient) -> None:
    help_repositories.upsert(
        "help_articles",
        "tenant-aaa",
        {
            "id": "g1",
            "tenant_id": "tenant-aaa",
            "slug": "term-foo",
            "kind": "glossary",
            "term": "Foo",
            "title": "Foo glossary",
            "summary": "what is foo",
            "personas": ["operational-default"],
        },
    )
    help_repositories.upsert(
        "help_articles",
        "tenant-aaa",
        {
            "id": "a1",
            "tenant_id": "tenant-aaa",
            "slug": "foo-article",
            "kind": "article",
            "title": "Foo article",
            "summary": "talks about foo",
            "personas": ["operational-default"],
        },
    )
    r = client.get("/help/search?q=foo", headers=HDR)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and items[0]["kind"] == "glossary"


def test_handoff_put_then_get(client: TestClient) -> None:
    put = client.put(
        "/help/support-handoff",
        json={"label": "AMA helpdesk", "email": "help@ama.gov.au"},
        headers=HDR,
    )
    assert put.status_code == 200
    g = client.get("/help/support-handoff", headers=HDR)
    assert g.status_code == 200 and g.json()["label"] == "AMA helpdesk"


def test_auth_missing_tenant_returns_401(client: TestClient) -> None:
    r = client.get("/help/articles")
    assert r.status_code == 401
