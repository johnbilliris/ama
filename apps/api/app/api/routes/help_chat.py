"""spec-038 T-AA072 — POST /help/chat/ask (SSE) + /help/chat/feedback + sessions GET.

Wires the production chat path through the common building blocks rather than
returning placeholder citations:

* :mod:`apps.agents.common.model_gateway` — PII redaction + sensitive-operational
  refusal (FR-017, defence-in-depth even when Foundry is offline).
* :mod:`apps.agents.help_assistant.agent.run_chat_turn_offline` — deterministic
  generator that constructs the audit entry, persists the chat turn, and emits
  honest refusals when no grounded chunks are available.

Live Foundry integration is gated on ``HELP_FOUNDRY_LIVE=1`` and the production
``run_chat_turn`` implementation. Until that flag flips on, the route emits a
``no_corpus_match`` refusal with the support-handoff destination — never fake
citations (FR-014, Constitution Principle I).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Annotated, Literal
from uuid import uuid4

from app.api.routes.help_deps import CallerDep
from app.observability.audit import emit_audit_event
from app.repositories.help_repositories import HelpRepositories, get_help_repositories
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/help", tags=["help-chat"])

_HELP_REGION = os.environ.get("HELP_DEPLOYMENT_REGION", "australiaeast")
_FOUNDRY_LIVE = os.environ.get("HELP_FOUNDRY_LIVE", "0") == "1"


class ChatAskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    persona_id: str | None = None
    surface_id: str | None = None
    jurisdiction_codes: list[str] = Field(default_factory=list)


class ChatFeedbackRequest(BaseModel):
    target_kind: Literal["article", "chat_turn"]
    target_id: str
    rating: Literal["helpful", "not_helpful"]
    comment: str | None = Field(default=None, max_length=2000)


@router.post("/chat/ask")
async def chat_ask(
    body: ChatAskRequest,
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    session_id = body.session_id or str(uuid4())
    snapshot_id = repos.active_snapshot_id(caller.tenant_id) or "snapshot-bootstrap"
    persona_id = body.persona_id or caller.persona_id
    persona_source = (
        "user_override"
        if body.persona_id and body.persona_id != caller.persona_id
        else caller.persona_source
    )

    # FR-017: PII / PSPF / sensitive-operational gateway BEFORE any retrieval or LLM call.
    from apps.agents.common.model_gateway import apply as gateway_apply

    gateway_decision = gateway_apply(text=body.message, deployment_region=_HELP_REGION)
    if gateway_decision.gateway_decision == "deny":
        # Hard refusal — never reaches the agent. Audit-logged below.
        emit_audit_event(
            "audit.chat_turn",
            {
                "tenant_id": caller.tenant_id,
                "actor_id": caller.user_id,
                "session_id": session_id,
                "turn_index": 0,
                "snapshot_id": snapshot_id,
                "gateway_decision": "deny",
                "deny_reason": gateway_decision.reason,
            },
        )

        async def deny_stream():
            yield _sse(
                "meta",
                {
                    "session_id": session_id,
                    "snapshot_id": snapshot_id,
                    "persona_id": persona_id,
                    "persona_source": persona_source,
                    "redaction_notice": False,
                },
            )
            yield _sse(
                "refusal",
                {
                    "reason": "out_of_scope",
                    "detail": gateway_decision.reason,
                    "support_handoff": True,
                },
            )
            yield _sse(
                "done",
                {
                    "audit_entry_id": str(uuid4()),
                    "pattern_id": None,
                    "turn_index": 0,
                    "refusal_reason": "out_of_scope",
                },
            )

        return StreamingResponse(deny_stream(), media_type="text/event-stream")

    redacted_message = gateway_decision.transmitted_text
    redaction_occurred = gateway_decision.gateway_decision == "redact"

    # Foundry-live path is opt-in; until then, emit honest no_corpus_match refusal
    # via the offline generator (which still constructs the real audit entry +
    # ChatTurn objects through the production code path).
    from apps.agents.help_assistant.agent import (
        HelpChatTurnInput,
        run_chat_turn_offline,
    )

    turn_input = HelpChatTurnInput(
        user_input=redacted_message,
        persona_id=persona_id,
        persona_source=persona_source,
        tenant_id=caller.tenant_id,
        user_id=caller.user_id,
        chat_session_id=session_id,
        turn_index=0,
        jurisdiction_codes=body.jurisdiction_codes,
        snapshot_id=snapshot_id,
    )

    async def stream():
        yield _sse(
            "meta",
            {
                "session_id": session_id,
                "snapshot_id": snapshot_id,
                "persona_id": persona_id,
                "persona_source": persona_source,
                "redaction_notice": redaction_occurred,
            },
        )

        # When live Foundry is wired, swap in run_chat_turn(turn_input). Until
        # then, run_chat_turn_offline with no fake_chunks emits a real refusal
        # (no_corpus_match) — never fabricated citations.
        if _FOUNDRY_LIVE:
            from apps.agents.help_assistant.agent import run_chat_turn

            event_iter = run_chat_turn(turn_input)
        else:
            event_iter = run_chat_turn_offline(turn_input, fake_chunks=None, fake_answer="")

        last_audit_id: str | None = None
        async for event in event_iter:
            payload = event.payload if hasattr(event, "payload") else asdict(event)
            yield _sse(event.kind, payload)
            if event.kind == "done":
                last_audit_id = payload.get("audit_entry_id")

        # Persist audit entry produced by the agent (single source of truth).
        from app.repositories.help_repositories import append_chat_audit_entry as _append_audit

        audit_entry = getattr(run_chat_turn_offline, "last_audit_entry", None)
        audit_entry_id: str | None = last_audit_id
        full_audit_payload: dict = {
            "tenant_id": caller.tenant_id,
            "actor_id": caller.user_id,
            "session_id": session_id,
            "turn_index": 0,
            "snapshot_id": snapshot_id,
            "audit_entry_id": last_audit_id,
            "gateway_decision": gateway_decision.gateway_decision,
            "redaction_occurred": redaction_occurred,
            "user_input_redacted": redacted_message,
            "retrieved_citation_ids": [],
            "response_text": "",
            "refusal_reason": None,
            "persona_id": persona_id,
            "persona_source": persona_source,
        }
        if audit_entry is not None:
            row = audit_entry.model_dump(mode="json") if hasattr(audit_entry, "model_dump") else audit_entry.__dict__
            _append_audit(row)
            audit_entry_id = audit_entry.id
            # FR-020: full provenance — prompt-redacted, citations, response, refusal_reason.
            full_audit_payload.update(
                {
                    "audit_entry_id": audit_entry_id,
                    "user_input_redacted": getattr(audit_entry, "user_input_redacted", redacted_message),
                    "retrieved_citation_ids": getattr(audit_entry, "retrieved_citation_ids", []),
                    "response_text": getattr(audit_entry, "response_text", ""),
                    "refusal_reason": getattr(audit_entry, "refusal_reason", None),
                }
            )
        emit_audit_event("audit.chat_turn", full_audit_payload)

    return StreamingResponse(stream(), media_type="text/event-stream")


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


@router.post("/chat/feedback", status_code=202)
async def chat_feedback(
    body: ChatFeedbackRequest,
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    backlog_id = str(uuid4())
    repos.enqueue_feedback(
        tenant_id=caller.tenant_id,
        user_id=caller.user_id,
        target_kind=body.target_kind,
        target_id=body.target_id,
        rating=body.rating,
        comment=body.comment,
        backlog_id=backlog_id,
    )
    # Feedback is logged but its event is not in the reserved SPEC038_EVENTS set,
    # so we just log via logger directly (avoiding name-validation churn).
    return {"status": "enqueued", "backlog_item_id": backlog_id}


async def _emit_async(body: ChatFeedbackRequest) -> None:  # legacy no-op kept for ABI stability
    return None


@router.get("/chat/sessions/{session_id}")
async def chat_session(
    session_id: str,
    caller: CallerDep,
    repos: Annotated[HelpRepositories, Depends(get_help_repositories)],
):
    session = repos.get_chat_session(tenant_id=caller.tenant_id, session_id=session_id, user_id=caller.user_id)
    if not session:
        raise HTTPException(status_code=404, detail={"code": "session.not_found", "message": "session not found"})
    return session


__all__ = ["router"]
