"""FastAPI SSE chat route for the Simulation Controller."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.api.dependencies.rbac import require_simulation_role
from app.core.auth import extract_principal_from_claims
from app.core.tenant_context import TenantContext, set_current_tenant
from app.services.simulation.controller_service import SimulationControllerService
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["simulation", "chat"])

_controller = SimulationControllerService()


class ChatRequest(BaseModel):
    message: str
    correlation_id: str | None = None


@router.post("/{tenant_id}/chat")
async def post_chat(tenant_id: str, body: ChatRequest, request: Request) -> StreamingResponse:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    if not tenant_id.startswith("sim-"):
        raise HTTPException(status_code=400, detail="chat endpoint is simulation-scoped only")

    set_current_tenant(
        TenantContext(
            agency_id=principal.agency_id,
            jurisdiction_ids=principal.jurisdiction_ids,
            persona_id=principal.persona_id,
            tenant_id=tenant_id,
        )
    )

    async def _generator() -> AsyncIterator[bytes]:
        async for event in _controller.stream_turn(
            tenant_id=tenant_id,
            simulation_id=tenant_id,
            user_oid=principal.subject,
            user_message=body.message,
        ):
            yield event.to_sse().encode("utf-8")

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{tenant_id}/chat/health")
async def chat_health(tenant_id: str) -> dict:
    return {
        "tenant_id": tenant_id,
        "prompt_hash": _controller.prompt_hash,
        "backend": "azure-or-offline",
    }


@router.get("/{tenant_id}/chat/history")
async def get_chat_history(
    tenant_id: str,
    request: Request,
    limit: int = 100,
) -> dict:
    """Return prior chat turns for the simulation in ascending sequence.

    Used by the UI to hydrate the chat pane when a controller opens an
    existing simulation, and by the controller service internally to
    replay conversation context to the model.
    """
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    if not tenant_id.startswith("sim-"):
        raise HTTPException(status_code=400, detail="chat endpoint is simulation-scoped only")

    # Clamp to a sensible window — the UI only needs recent context.
    if limit < 1:
        limit = 1
    elif limit > 500:
        limit = 500

    turns = _controller.history.list_turns(tenant_id, limit=limit)
    return {
        "tenant_id": tenant_id,
        "turns": [t.model_dump(mode="json") for t in turns],
    }
