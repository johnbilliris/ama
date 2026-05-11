"""spec-038 T-AA059 — append-only chat audit writer (FR-020 / FR-029)."""

from __future__ import annotations

from ama_domain import ChatAuditEntry
from app.repositories import help_repositories as repo


def append_audit_entry(entry: ChatAuditEntry) -> ChatAuditEntry:
    """Append ``entry`` to ``chat_audit_log``. Refuses overwrites."""
    repo.append_chat_audit_entry(entry.model_dump(mode="json"))
    return entry


__all__ = ["append_audit_entry"]
