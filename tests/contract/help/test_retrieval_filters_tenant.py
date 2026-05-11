"""spec-038 T-AA187 — retrieval filter forces tenant scope; cannot be overridden."""

from __future__ import annotations

import pytest
from app.repositories import help_repositories


def test_cross_tenant_read_returns_empty() -> None:
    help_repositories.reset_in_memory_store()
    help_repositories.upsert(
        "help_articles",
        "tenant-A",
        {
            "id": "a1",
            "tenant_id": "tenant-A",
            "slug": "secret-a",
            "title": "Tenant A secret",
        },
    )
    # tenant B query: nothing comes back
    rows = help_repositories.query("help_articles", "tenant-B")
    assert rows == []


def test_assert_tenant_scope_raises_on_leak() -> None:
    with pytest.raises(PermissionError):
        help_repositories.assert_tenant_scope(
            [{"tenant_id": "tenant-X"}],
            tenant_id="tenant-Y",
            policy="deny",
        )


def test_tenant_partition_required_on_write() -> None:
    help_repositories.reset_in_memory_store()
    with pytest.raises(ValueError):
        help_repositories.upsert("help_articles", "tenant-A", {"id": "x", "tenant_id": "tenant-B"})
