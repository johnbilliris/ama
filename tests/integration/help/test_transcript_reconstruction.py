"""spec-038 T-AA197 — Observer-Auditor transcript reconstruction emits audit."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.repositories import help_repositories as repo
from app.services.help.transcript_reconstructor import reconstruct_session


@pytest.fixture(autouse=True)
def _reset() -> None:
    repo.reset_in_memory_store()


def test_reconstruct_returns_ordered_rows() -> None:
    tenant = "t-1"
    sid = "chat-123"
    base = datetime.now(UTC).isoformat()
    for i in (2, 0, 1):
        repo.upsert(
            repo.CHAT_AUDIT_LOG,
            tenant,
            {
                "id": f"ce-{i}",
                "tenant_id": tenant,
                "chat_session_id": sid,
                "turn_index": i,
                "created_at": base,
            },
        )
    rows = reconstruct_session(chat_session_id=sid, tenant_id=tenant, auditor_user_id="u-aud", reason="legal-hold")
    assert [r["turn_index"] for r in rows] == [0, 1, 2]


def test_reconstruct_empty_returns_empty_list() -> None:
    rows = reconstruct_session(chat_session_id="missing", tenant_id="t-1", auditor_user_id="u-aud", reason="audit")
    assert rows == []
