"""spec-038 T-AA060 — Observer-Auditor transcript reconstructor (FR-029a/b).

Past the 30-day FR-029 transcript window, only an Observer-Auditor may
reconstruct a chat session from append-only ChatAuditEntry rows. Every
reconstruction emits ``audit.transcript_reconstructed``.
"""

from __future__ import annotations

from typing import Any

from app.observability.audit import emit_audit_event
from app.repositories import help_repositories as repo


def reconstruct_session(
    *,
    chat_session_id: str,
    tenant_id: str,
    auditor_user_id: str,
    reason: str,
) -> list[dict[str, Any]]:
    """Return the ordered list of audit-entry rows for ``chat_session_id``."""
    rows = repo.query(repo.CHAT_AUDIT_LOG, tenant_id, where={"chat_session_id": chat_session_id})
    rows.sort(key=lambda r: r.get("turn_index", 0))
    emit_audit_event(
        "audit.transcript_reconstructed",
        {
            "chat_session_id": chat_session_id,
            "tenant_id": tenant_id,
            "auditor_user_id": auditor_user_id,
            "reason": reason,
            "turn_count": len(rows),
        },
    )
    return rows


__all__ = ["reconstruct_session"]
