"""Spec-036 Wave 4 — Lifecycle state guard dependency (T-P02 / T-P03).

Provides ``require_active_state`` — a FastAPI dependency that gates
``/inject-telemetry`` and chat/sub-agent dispatch routes on the
:class:`SimulationStateRepository` so requests against a paused or
aborted simulation are refused with HTTP 409
``application/problem+json lifecycle-state-conflict`` and a
``lifecycle.refused_while_paused`` audit envelope (audit-envelope.md
§3.13a).

Per pass 2 Q7 the 409 refusal itself is **NOT** cached in the FR-066
idempotency cache so a fresh request body is serviced cleanly on
resume.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from app.api.dependencies.simulation_rbac import (
    CoordinatorPrincipal,
    require_simulation_coordinator,
)
from fastapi import HTTPException, Path, Request

logger = logging.getLogger(__name__)


def _problem_detail(*, status: int, type_id: str, title: str, **extra: Any) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "type": f"https://aidr.gov.au/problems/{type_id}",
        "title": title,
        "status": status,
    }
    detail.update(extra)
    return detail


async def _read_state_safely(simulation_id: str) -> str:
    """Look up the simulation's lifecycle state via the repository.

    Returns the state string. Falls back to ``"active"`` when the
    repository has no record (a sim implicitly starts active).
    """

    try:
        from app.services.simulation.repositories.simulation_state import (
            UnknownSimulationError,
            get_simulation_state_repository,
        )
    except ImportError:  # pragma: no cover - defensive
        return "active"

    repo = get_simulation_state_repository()
    try:
        state = await repo.read(simulation_id)
    except UnknownSimulationError:
        return "active"
    return state.state


async def _emit_refusal_audit(
    *,
    simulation_id: str,
    principal: CoordinatorPrincipal,
    attempted_action: str,
    idempotency_key: str | None,
    request_correlation_id: str,
) -> None:
    from app.services.simulation.audit_writer import get_audit_writer

    audit = get_audit_writer()
    try:
        await audit.write(
            "lifecycle.refused_while_paused",
            simulation_id=simulation_id,
            actor="lifecycle_guard",
            request_correlation_id=request_correlation_id,
            idempotency_key=idempotency_key,
            details={
                "attempted_action": attempted_action,
                "coordinator_user_id": principal.user_id,
                "idempotency_key": idempotency_key,
                "request_correlation_id": request_correlation_id,
                "refusal_response_status": 409,
            },
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "lifecycle_guard.audit_emit_failed sim=%s user=%s",
            simulation_id,
            principal.user_id,
        )


def make_lifecycle_guard(attempted_action: str) -> Any:
    """Factory returning a FastAPI dependency for the given action.

    Each call returns a fresh coroutine so the FastAPI dependency
    resolver can introspect signatures correctly.
    """

    async def _guard(
        request: Request,
        sim_id: str = Path(..., min_length=1, description="Simulation ID"),
        principal: CoordinatorPrincipal = None,  # type: ignore[assignment]
    ) -> CoordinatorPrincipal:
        # The principal is supplied by ``require_simulation_coordinator``
        # via FastAPI's dependency injection (route-level wiring).
        if principal is None:
            principal = await require_simulation_coordinator(request=request, sim_id=sim_id)

        state = await _read_state_safely(sim_id)
        if state in ("active",):
            return principal

        idempotency_key = request.headers.get("Idempotency-Key") if request else None
        request_correlation_id = (request.headers.get("X-Request-Correlation-Id") if request else None) or str(uuid4())

        await _emit_refusal_audit(
            simulation_id=sim_id,
            principal=principal,
            attempted_action=attempted_action,
            idempotency_key=idempotency_key,
            request_correlation_id=request_correlation_id,
        )
        raise HTTPException(
            status_code=409,
            detail=_problem_detail(
                status=409,
                type_id="lifecycle-state-conflict",
                title="Simulation not active",
                detail=(
                    f"Cannot {attempted_action!r} while simulation is in state {state!r}; resume the simulation first."
                ),
                current_state=state,
                attempted_action=attempted_action,
            ),
        )

    return _guard


__all__ = ["make_lifecycle_guard"]
