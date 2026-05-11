"""spec-038 — typed Cosmos repository helpers for Help containers.

Every helper enforces the ``/tenant_id`` partition key requirement (FR-019,
R3) and exposes append-only semantics for the immutable containers
(``chat_audit_log``, ``snapshot_records``).

When ``COSMOS_ENDPOINT`` is unset the helpers fall back to an in-memory store
so unit + contract tests run without infrastructure (mirrors the pattern in
``apps/api/app/repositories/audit_repository.py``).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Container names — mirror infra/bicep/modules/cosmos-help-containers.bicep
HELP_ARTICLES = "help_articles"
SCREENSHOT_REGISTRY = "screenshot_registry"
CHAT_SESSIONS = "chat_sessions"
CHAT_AUDIT_LOG = "chat_audit_log"
SNAPSHOT_RECORDS = "snapshot_records"
SUPPORT_HANDOFF_CONFIG = "support_handoff_config"
CONTENT_REVIEW_BACKLOG = "content_review_backlog"

# Containers that disallow UPDATE / DELETE at the application layer.
APPEND_ONLY: frozenset[str] = frozenset({CHAT_AUDIT_LOG, SNAPSHOT_RECORDS})


class _InMemoryStore:
    """Tenant-keyed in-memory fallback used in tests."""

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def upsert(self, container: str, tenant_id: str, row: dict[str, Any]) -> dict[str, Any]:
        key = (container, tenant_id)
        rows = self._rows.setdefault(key, [])
        # immutable containers refuse overwrite
        if container in APPEND_ONLY and any(r["id"] == row["id"] for r in rows):
            raise PermissionError(f"{container} is append-only; id={row['id']} already present")
        rows = [r for r in rows if r["id"] != row["id"]]
        rows.append(row)
        self._rows[key] = rows
        return row

    def query(self, container: str, tenant_id: str) -> list[dict[str, Any]]:
        return list(self._rows.get((container, tenant_id), []))

    def get(self, container: str, tenant_id: str, item_id: str) -> dict[str, Any] | None:
        for r in self._rows.get((container, tenant_id), []):
            if r["id"] == item_id:
                return r
        return None


_STORE = _InMemoryStore()


def _cosmos_enabled() -> bool:
    return bool(os.environ.get("COSMOS_ENDPOINT"))


def _container(container: str) -> Any:
    """Return the live Cosmos container client (only when configured)."""
    from azure.cosmos import CosmosClient  # type: ignore[import-not-found]
    from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]

    endpoint = os.environ["COSMOS_ENDPOINT"]
    database = os.environ.get("COSMOS_DATABASE", "ama")
    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    return client.get_database_client(database).get_container_client(container)


def upsert(container: str, tenant_id: str, row: dict[str, Any]) -> dict[str, Any]:
    """Upsert ``row`` into ``container`` partitioned by ``/tenant_id``.

    Append-only containers (``chat_audit_log``, ``snapshot_records``) reject
    overwrites at the application layer; Cosmos RBAC custom-role denies
    UPDATE/DELETE at the platform layer (T-AA020).
    """
    if "tenant_id" not in row:
        raise ValueError("row missing tenant_id — required as partition key")
    if row["tenant_id"] != tenant_id:
        raise ValueError("row.tenant_id ≠ partition tenant_id")
    if not _cosmos_enabled():
        return _STORE.upsert(container, tenant_id, row)
    c = _container(container)
    if container in APPEND_ONLY:
        c.create_item(body=row)  # 409 on duplicate id
    else:
        c.upsert_item(body=row)
    return row


def get(container: str, tenant_id: str, item_id: str) -> dict[str, Any] | None:
    if not _cosmos_enabled():
        return _STORE.get(container, tenant_id, item_id)
    try:
        return _container(container).read_item(item=item_id, partition_key=tenant_id)
    except Exception:  # noqa: BLE001 — Cosmos raises CosmosResourceNotFoundError
        return None


def query(
    container: str,
    tenant_id: str,
    *,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows = _STORE.query(container, tenant_id) if not _cosmos_enabled() else _live_query(container, tenant_id)
    if where:
        return [r for r in rows if all(r.get(k) == v for k, v in where.items())]
    return rows


def _live_query(container: str, tenant_id: str) -> list[dict[str, Any]]:
    c = _container(container)
    items = c.query_items(
        query="SELECT * FROM c WHERE c.tenant_id = @tid",
        parameters=[{"name": "@tid", "value": tenant_id}],
        partition_key=tenant_id,
    )
    return list(items)


# ---------- Append-only helpers (no update/delete) ----------


def append_chat_audit_entry(row: dict[str, Any]) -> dict[str, Any]:
    """Insert one immutable :class:`ChatAuditEntry`."""
    return upsert(CHAT_AUDIT_LOG, row["tenant_id"], row)


def append_snapshot_record(row: dict[str, Any]) -> dict[str, Any]:
    return upsert(SNAPSHOT_RECORDS, row.get("tenant_id", "__global__"), row)


# ---------- Cross-tenant guard helpers ----------


CrossTenantPolicy = Literal["deny", "allow_global"]


def assert_tenant_scope(rows: Iterable[dict[str, Any]], tenant_id: str, policy: CrossTenantPolicy = "allow_global") -> None:
    """Defence-in-depth: every returned row must match ``tenant_id`` or be global."""
    for r in rows:
        rt = r.get("tenant_id")
        if rt == tenant_id:
            continue
        if policy == "allow_global" and rt == "__global__":
            continue
        raise PermissionError(f"cross-tenant leak detected: row tenant {rt!r} ≠ {tenant_id!r}")


def reset_in_memory_store() -> None:
    """Test-only — wipe the in-memory fallback."""
    global _STORE
    _STORE = _InMemoryStore()


__all__ = [
    "APPEND_ONLY",
    "CHAT_AUDIT_LOG",
    "CHAT_SESSIONS",
    "CONTENT_REVIEW_BACKLOG",
    "HELP_ARTICLES",
    "SCREENSHOT_REGISTRY",
    "SNAPSHOT_RECORDS",
    "SUPPORT_HANDOFF_CONFIG",
    "append_chat_audit_entry",
    "append_snapshot_record",
    "assert_tenant_scope",
    "get",
    "query",
    "reset_in_memory_store",
    "upsert",
]
