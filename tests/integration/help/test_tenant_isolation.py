"""spec-038 T-AA193 — multi-tenant probe: tenant A queries never return tenant B docs."""

from __future__ import annotations

import pytest
from app.api.routes.help_articles import router as articles_router
from app.repositories import help_repositories
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    help_repositories.reset_in_memory_store()
    help_repositories.upsert(
        "help_articles",
        "tenant-A",
        {
            "id": "a",
            "tenant_id": "tenant-A",
            "slug": "tenant-a-internal",
            "title": "A only",
            "personas": ["operational-default"],
        },
    )
    help_repositories.upsert(
        "help_articles",
        "tenant-B",
        {
            "id": "b",
            "tenant_id": "tenant-B",
            "slug": "tenant-b-internal",
            "title": "B only",
            "personas": ["operational-default"],
        },
    )
    app = FastAPI()
    app.include_router(articles_router)
    return TestClient(app)


def test_tenant_a_does_not_see_tenant_b(client: TestClient) -> None:
    r = client.get("/help/articles", headers={"X-Tenant-Id": "tenant-A", "X-User-Id": "u1"})
    items = r.json()["items"]
    slugs = {a["slug"] for a in items}
    assert "tenant-a-internal" in slugs
    assert "tenant-b-internal" not in slugs


def test_tenant_b_does_not_see_tenant_a(client: TestClient) -> None:
    r = client.get("/help/articles", headers={"X-Tenant-Id": "tenant-B", "X-User-Id": "u1"})
    slugs = {a["slug"] for a in r.json()["items"]}
    assert "tenant-b-internal" in slugs
    assert "tenant-a-internal" not in slugs


def test_direct_slug_lookup_does_not_cross_tenant(client: TestClient) -> None:
    r = client.get("/help/articles/tenant-b-internal", headers={"X-Tenant-Id": "tenant-A", "X-User-Id": "u1"})
    assert r.status_code == 404
