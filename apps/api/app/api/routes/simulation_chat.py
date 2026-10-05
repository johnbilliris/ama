"""FastAPI SSE chat route for the Simulation Controller."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx
from app.api.dependencies.rbac import require_simulation_participant, require_simulation_role
from app.api.routes.simulations import _clock, _recorder, _repo, _seeding
from app.core.async_io import run_blocking
from app.core.auth import extract_principal_from_claims
from app.services.simulation.controller_service import SimulationControllerService
from app.services.simulation.sub_agent_invoker import production_invoker
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["simulation", "chat"])

# Long-lived httpx client shared across all sub-agent calls. Created once
# at module import; the underlying connection pool survives the lifetime
# of the FastAPI process. Read timeout sits just above the SubAgentInvoker
# hard timeout (120 s) so the wrapper times out first and writes the
# canonical ``sub_agent.timeout`` audit row.
_sub_agent_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=5.0, read=125.0, write=5.0, pool=5.0),
)

# Wire the production sub-agent invoker into the Controller. Without this
# the constructor falls back to ``default_invoker()`` (empty registry),
# which causes every ``query_sub_agent`` tool call to return
# ``Unknown sub-agent '<role>'`` and the chat model to apologise that the
# sub-agent "is not available in this simulation".
#
# We also share the SimulationEventRecorder + clock + simulation repo
# singletons defined in :mod:`app.api.routes.simulations` so each chat
# turn (user prompt, assistant reply, tool invocation) is mirrored into
# the ``sim-events`` Cosmos container alongside lifecycle events. Without
# this wiring ``_maybe_record_chat_turn`` early-returns and the right-hand
# Event Log on the simulation dashboard never sees chat-issued commands
# (SITREP/Risk/Deploy/Alert/Escalate) after a refresh.
_controller = SimulationControllerService(
    sub_agents=production_invoker(_sub_agent_http_client),
    event_recorder=_recorder,
    clock_service=_clock,
    simulation_repository=_repo,
    scenario_seeding_service=_seeding,
)


class ChatRequest(BaseModel):
    message: str
    correlation_id: str | None = None


@router.post("/{tenant_id}/chat")
async def post_chat(tenant_id: str, body: ChatRequest, request: Request) -> StreamingResponse:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    if not tenant_id.startswith("sim-"):
        raise HTTPException(status_code=400, detail="chat endpoint is simulation-scoped only")
    await require_simulation_participant(principal, tenant_id, _repo)

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
async def chat_health(tenant_id: str) -> dict[str, str]:
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
) -> dict[str, object]:
    """Return prior chat turns for the simulation in ascending sequence.

    Used by the UI to hydrate the chat pane when a controller opens an
    existing simulation, and by the controller service internally to
    replay conversation context to the model.
    """
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    if not tenant_id.startswith("sim-"):
        raise HTTPException(status_code=400, detail="chat endpoint is simulation-scoped only")
    await require_simulation_participant(principal, tenant_id, _repo)

    # Clamp to a sensible window — the UI only needs recent context.
    if limit < 1:
        limit = 1
    elif limit > 500:
        limit = 500

    turns = await run_blocking(_controller.history.list_turns, tenant_id, limit=limit)
    return {
        "tenant_id": tenant_id,
        "turns": [t.model_dump(mode="json") for t in turns],
    }
