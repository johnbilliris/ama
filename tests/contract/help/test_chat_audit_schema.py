"""spec-038 T-AA183 — ChatAuditEntry round-trip through Pydantic v2."""

from __future__ import annotations

from datetime import UTC, datetime

from ama_domain import ChatAuditEntry, compute_pattern_id


def test_chat_audit_round_trip() -> None:
    p = compute_pattern_id(question_intent_cluster_id="qic-abc", citation_source_ids=["a", "b", "c"])
    entry = ChatAuditEntry(
        id="aud-1",
        tenant_id="tenant-a",
        chat_session_id="ses-1",
        turn_index=0,
        user_id="user-1",
        persona_id="operational-default",
        persona_source="idp_default",
        jurisdiction_codes=["AU-NSW"],
        snapshot_id="snap-x",
        user_input_redacted="hello",
        redaction_occurred=False,
        retrieved_citation_ids=["a", "b", "c"],
        response_text="hi",
        refusal_reason=None,
        pattern_id=p,
        gateway_decision="allow",
        created_at=datetime.now(UTC),
    )
    j = entry.model_dump()
    again = ChatAuditEntry(**j)
    assert again.pattern_id == p
    assert again.tenant_id == "tenant-a"


def test_chat_audit_refusal_path() -> None:
    p = compute_pattern_id(question_intent_cluster_id="qic-xyz", citation_source_ids=[])
    entry = ChatAuditEntry(
        id="aud-2",
        tenant_id="tenant-a",
        chat_session_id="ses-2",
        turn_index=1,
        user_id="user-1",
        persona_id="observer-auditor",
        persona_source="user_override",
        jurisdiction_codes=[],
        snapshot_id="snap-x",
        user_input_redacted="show me other tenant",
        redaction_occurred=False,
        retrieved_citation_ids=[],
        response_text="",
        refusal_reason="cross_tenant",
        pattern_id=p,
        gateway_decision="allow",
        created_at=datetime.now(UTC),
    )
    assert entry.refusal_reason == "cross_tenant"
    assert entry.response_text == ""
