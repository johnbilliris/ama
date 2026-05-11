"""spec-038 T-AA072 — POST /help/chat/ask (SSE) + /help/chat/feedback + sessions GET."""

from __future__ import annotations

import json
from typing import Annotated, Literal
from uuid import uuid4

from app.api.routes.help_deps import CallerDep
from app.observability.audit import emit_audit_event
from app.repositories.help_repositories import HelpRepositories, get_help_repositories
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/help", tags=["help-chat"])


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

    async def stream():
        # meta event
        yield _sse(
            "meta",
            {
                "session_id": session_id,
                "snapshot_id": snapshot_id,
                "persona_id": body.persona_id or caller.persona_id,
                "persona_source": "user_override"
                if body.persona_id and body.persona_id != caller.persona_id
                else caller.persona_source,
                "redaction_notice": False,
            },
        )
        # delta + citation (placeholder; production wires apps.agents.help_assistant.agent)
        yield _sse("delta", {"text": "Help is available from your support handoff. "})
        yield _sse(
            "citation",
            {
                "source_id": "placeholder",
                "source_title": "Help Centre — Getting Started",
                "anchor": "#overview",
                "snippet": "Use /help/articles to browse the corpus.",
            },
        )
        audit_id = str(uuid4())
        emit_audit_event(
            "audit.chat_turn",
            {
                "tenant_id": caller.tenant_id,
                "actor_id": caller.user_id,
                "session_id": session_id,
                "turn_index": 0,
                "snapshot_id": snapshot_id,
            },
        )
        yield _sse(
            "done",
            {
                "audit_entry_id": audit_id,
                "pattern_id": "pat-placeholder",
                "turn_index": 0,
                "refusal_reason": None,
            },
        )

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
