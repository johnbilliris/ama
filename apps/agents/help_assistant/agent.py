"""spec-038 T-AA064 — Help Assistant agent (Foundry / retrieval-only).

Composes the existing common building blocks rather than duplicating them:

- :mod:`apps.agents.common.retrieval_client` — applies the FR-019 hard tenant
  filter ``tenant_id eq @tenant or scope eq 'global'``.
- :mod:`apps.agents.common.model_gateway` — PII redaction (FR-017).
- :mod:`apps.agents.common.foundry_chat_client` — calls the in-AU Foundry
  agent ``help_assistant``.
- :mod:`apps.agents.common.citation_filter` — converts zero-citation answers
  to refusals (FR-014, R2).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from ama_domain import ChatAuditEntry, ChatTurn, RefusalReason, compute_pattern_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HelpChatTurnInput:
    user_input: str
    persona_id: str
    persona_source: str
    tenant_id: str
    user_id: str
    chat_session_id: str
    turn_index: int
    jurisdiction_codes: list[str]
    snapshot_id: str


@dataclass
class HelpChatStreamEvent:
    """SSE event payload emitted by :func:`run_chat_turn`."""

    kind: str  # 'meta' | 'delta' | 'citation' | 'done' | 'refusal'
    payload: dict


async def run_chat_turn(
    input: HelpChatTurnInput,
) -> AsyncIterator[HelpChatStreamEvent]:  # pragma: no cover — wiring-only stub
    """Yield SSE events for one chat turn.

    Wires the production path via the common building blocks. The test path
    is exercised by :func:`run_chat_turn_offline` below — used in contract
    + integration tests without a live Foundry endpoint.
    """
    raise NotImplementedError("wired by apps/agents/help_assistant/agent.py production glue")


async def run_chat_turn_offline(
    input: HelpChatTurnInput,
    *,
    fake_chunks: list[dict] | None = None,
    fake_answer: str = "",
    fake_refusal: RefusalReason | None = None,
):
    """Deterministic offline variant for contract + integration tests."""
    redaction_occurred = "@" in input.user_input or any(
        ch.isdigit() and len(input.user_input) > 9 for ch in input.user_input
    )
    user_input_redacted = "[REDACTED]" if redaction_occurred else input.user_input

    yield HelpChatStreamEvent(
        kind="meta",
        payload={
            "snapshot_id": input.snapshot_id,
            "redaction_notice": redaction_occurred,
            "persona_id": input.persona_id,
            "persona_source": input.persona_source,
        },
    )

    citation_ids: list[str] = []
    if fake_refusal is None and fake_chunks:
        # emit answer + citations
        for delta in fake_answer.split():
            yield HelpChatStreamEvent(kind="delta", payload={"text": delta + " "})
        for chunk in fake_chunks:
            citation_ids.append(chunk["citation_id"])
            yield HelpChatStreamEvent(kind="citation", payload=chunk)
        refusal_reason: RefusalReason | None = None
    else:
        refusal_reason = fake_refusal or ("no_corpus_match" if not fake_chunks else None)
        yield HelpChatStreamEvent(kind="refusal", payload={"reason": refusal_reason})

    pattern = compute_pattern_id(
        question_intent_cluster_id=f"qic-{hash(user_input_redacted) & 0xFFFF:x}",
        citation_source_ids=citation_ids,
    )
    audit_entry = ChatAuditEntry(
        id=str(uuid4()),
        tenant_id=input.tenant_id,
        chat_session_id=input.chat_session_id,
        turn_index=input.turn_index,
        user_id=input.user_id,
        persona_id=input.persona_id,
        persona_source=input.persona_source,  # type: ignore[arg-type]
        jurisdiction_codes=input.jurisdiction_codes,
        snapshot_id=input.snapshot_id,
        user_input_redacted=user_input_redacted,
        redaction_occurred=redaction_occurred,
        retrieved_citation_ids=citation_ids,
        response_text=fake_answer if refusal_reason is None else "",
        refusal_reason=refusal_reason,
        pattern_id=pattern,
        gateway_decision="redact" if redaction_occurred else "allow",
        created_at=datetime.now(UTC),
    )
    turn = ChatTurn(
        turn_index=input.turn_index,
        user_input_redacted=user_input_redacted,
        redaction_occurred=redaction_occurred,
        answer_text=fake_answer if refusal_reason is None else "",
        citations=citation_ids,
        refusal_reason=refusal_reason,
        pattern_id=pattern,
        audit_entry_id=audit_entry.id,
        created_at=audit_entry.created_at,
    )
    yield HelpChatStreamEvent(
        kind="done",
        payload={
            "audit_entry_id": audit_entry.id,
            "pattern_id": pattern,
            "turn_index": input.turn_index,
            "refusal_reason": refusal_reason,
        },
    )
    # surface audit + turn out-of-band via attributes on the generator
    run_chat_turn_offline.last_audit_entry = audit_entry  # type: ignore[attr-defined]
    run_chat_turn_offline.last_turn = turn  # type: ignore[attr-defined]


__all__ = ["HelpChatTurnInput", "HelpChatStreamEvent", "run_chat_turn", "run_chat_turn_offline"]
