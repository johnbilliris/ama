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

    Falls back to the in-memory store when the live Cosmos container is missing
    (e.g., ``azd provision`` has not yet created the spec-038 containers) so
    Help-Centre endpoints stay readable rather than 5xx-ing.
    """
    if "tenant_id" not in row:
        raise ValueError("row missing tenant_id — required as partition key")
    if row["tenant_id"] != tenant_id:
        raise ValueError("row.tenant_id ≠ partition tenant_id")
    if not _cosmos_enabled():
        return _STORE.upsert(container, tenant_id, row)
    try:
        c = _container(container)
        if container in APPEND_ONLY:
            c.create_item(body=row)
        else:
            c.upsert_item(body=row)
        return row
    except Exception as exc:  # noqa: BLE001
        from azure.cosmos.exceptions import CosmosResourceNotFoundError  # type: ignore[import-not-found]

        if isinstance(exc, CosmosResourceNotFoundError):
            return _STORE.upsert(container, tenant_id, row)
        raise


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
    """Query the live Cosmos container; return [] if the container does not yet
    exist (graceful degradation while ``azd provision`` has not created the
    spec-038 help containers — Constitution Principle I forbids hard-failing the
    Help Centre when a non-incident-critical resource is missing)."""
    try:
        c = _container(container)
        items = c.query_items(
            query="SELECT * FROM c WHERE c.tenant_id = @tid",
            parameters=[{"name": "@tid", "value": tenant_id}],
            partition_key=tenant_id,
        )
        return list(items)
    except Exception as exc:  # noqa: BLE001
        from azure.cosmos.exceptions import CosmosResourceNotFoundError  # type: ignore[import-not-found]

        if isinstance(exc, CosmosResourceNotFoundError):
            return []
        raise


# ---------- Append-only helpers (no update/delete) ----------


def append_chat_audit_entry(row: dict[str, Any]) -> dict[str, Any]:
    """Insert one immutable :class:`ChatAuditEntry`."""
    return upsert(CHAT_AUDIT_LOG, row["tenant_id"], row)


def append_snapshot_record(row: dict[str, Any]) -> dict[str, Any]:
    return upsert(SNAPSHOT_RECORDS, row.get("tenant_id", "__global__"), row)


# ---------- Cross-tenant guard helpers ----------


CrossTenantPolicy = Literal["deny", "allow_global"]


def assert_tenant_scope(
    rows: Iterable[dict[str, Any]],
    tenant_id: str,
    policy: CrossTenantPolicy = "allow_global",
) -> None:
    """Defence-in-depth: every returned row must match ``tenant_id`` or be global."""
    for r in rows:
        rt = r.get("tenant_id")
        if rt == tenant_id:
            continue
        if policy == "allow_global" and rt == "__global__":
            continue
        raise PermissionError(f"cross-tenant leak detected: row tenant {rt!r} ≠ {tenant_id!r}")


# ---------- High-level facade used by FastAPI routes ----------


class HelpRepositories:
    """Tenant-aware facade over the Cosmos containers used by Phase 3 routes."""

    def active_snapshot_id(self, tenant_id: str) -> str | None:
        rows = query(SNAPSHOT_RECORDS, tenant_id, where={"status": "active"})
        if rows:
            return rows[0].get("id")
        # fallback: any global active snapshot
        global_rows = query(SNAPSHOT_RECORDS, "__global__", where={"status": "active"})
        return global_rows[0]["id"] if global_rows else None

    def list_snapshots(self, tenant_id: str) -> list[dict[str, Any]]:
        return query(SNAPSHOT_RECORDS, tenant_id) + query(SNAPSHOT_RECORDS, "__global__")

    def get_chat_session(self, *, tenant_id: str, session_id: str, user_id: str) -> dict[str, Any] | None:
        row = get(CHAT_SESSIONS, tenant_id, session_id)
        if not row:
            return None
        if row.get("user_id") != user_id:
            return None
        return row

    def upsert_chat_session(self, row: dict[str, Any]) -> dict[str, Any]:
        return upsert(CHAT_SESSIONS, row["tenant_id"], row)

    def enqueue_feedback(
        self,
        *,
        tenant_id: str,
        user_id: str,
        target_kind: str,
        target_id: str,
        rating: str,
        comment: str | None,
        backlog_id: str,
    ) -> dict[str, Any]:
        row = {
            "id": backlog_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "target_kind": target_kind,
            "target_id": target_id,
            "rating": rating,
            "comment": comment,
            "status": "pending",
        }
        return upsert(CONTENT_REVIEW_BACKLOG, tenant_id, row)

    def list_articles(
        self,
        *,
        tenant_id: str,
        persona: str | None = None,
        surface: str | None = None,
        kind: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = query(HELP_ARTICLES, tenant_id) + query(HELP_ARTICLES, "__global__")
        if persona:
            # Honour both legacy ``personas`` and current ``persona_tags``
            # front-matter spellings; ``all-personas`` matches any persona.
            def _matches(r: dict[str, Any]) -> bool:
                tags = r.get("personas") or r.get("persona_tags") or []
                return persona in tags or "all-personas" in tags
            rows = [r for r in rows if _matches(r)]
        if surface:
            rows = [r for r in rows if surface in (r.get("surfaces") or r.get("surface_tags") or [])]
        if kind:
            rows = [r for r in rows if r.get("kind") == kind]
        return rows[:limit]

    def get_article(self, *, tenant_id: str, slug: str) -> dict[str, Any] | None:
        for src in (tenant_id, "__global__"):
            rows = query(HELP_ARTICLES, src, where={"slug": slug})
            if rows:
                return rows[0]
        return None

    def list_staleness_flags(self, tenant_id: str) -> list[dict[str, Any]]:
        return query("staleness_flags", tenant_id, where={"status": "open"})

    def upsert_staleness_flag(self, row: dict[str, Any]) -> dict[str, Any]:
        return upsert("staleness_flags", row["tenant_id"], row)

    def get_support_handoff(self, tenant_id: str) -> dict[str, Any] | None:
        rows = query(SUPPORT_HANDOFF_CONFIG, tenant_id)
        return rows[0] if rows else None

    def put_support_handoff(self, row: dict[str, Any]) -> dict[str, Any]:
        return upsert(SUPPORT_HANDOFF_CONFIG, row["tenant_id"], row)


_REPOS = HelpRepositories()


def get_help_repositories() -> HelpRepositories:
    return _REPOS


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
    "HelpRepositories",
    "SCREENSHOT_REGISTRY",
    "SNAPSHOT_RECORDS",
    "SUPPORT_HANDOFF_CONFIG",
    "append_chat_audit_entry",
    "append_snapshot_record",
    "assert_tenant_scope",
    "get",
    "get_help_repositories",
    "query",
    "reset_in_memory_store",
    "upsert",
]
