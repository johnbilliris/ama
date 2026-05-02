"""Test-support endpoints for the spec-034 web coverage Playwright suite.

Read-only facade over ``bootstrap_seed_data().identities`` and
``hazard_scenarios``. Used **exclusively** by the Playwright fixtures in
``tests/e2e/web-coverage/_support/fixtures/`` to resolve persona IDs to
real seed identities (ASM-011).

Activation is dual-guarded by ``app.middleware.test_support_guard.is_enabled``;
the router is registered in ``app.api.router`` only when that returns True.

Contract: ``specs/034-webapp-capstone-coverage/contracts/persona-fixture.contract.md``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter(prefix="/test-support", tags=["test-support"])

# Resolved at module import — keeps tests deterministic across requests.
_SEED_ROOT = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src" / "domain" / "seed"


def _seed_root() -> Path:
    """Allow tests to monkey-patch the seed root for isolation."""

    return _SEED_ROOT


def _load_identities() -> list[dict[str, Any]]:
    from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data

    payload = bootstrap_seed_data(_seed_root())
    identities = payload.get("identities") or []
    if not isinstance(identities, list):  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="bootstrap_seed_data().identities is not a list",
        )
    return identities  # type: ignore[return-value]


def _load_hazard_scenarios() -> list[dict[str, Any]]:
    from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data

    payload = bootstrap_seed_data(_seed_root())
    scenarios = payload.get("hazard_scenarios") or []
    return scenarios if isinstance(scenarios, list) else []  # type: ignore[return-value]


def _audit_log(request: Request, audit_type: str, persona_id: str | None) -> None:
    """Best-effort audit log; the test-support endpoint is read-only.

    We attempt to use the standard audit writer when available so the
    contract's "audit_type=test-support.persona-resolved" obligation is met.
    Falls back to structured logging if the writer is not wired up yet.
    """

    correlation_id = request.headers.get("x-correlation-id", "unknown")
    try:  # pragma: no cover - depends on optional pipeline component
        from app.services.ingestion.audit_writer import write_audit  # type: ignore[import-not-found]

        write_audit(
            audit_type=audit_type,
            payload={"persona_id": persona_id},
            correlation_id=correlation_id,
        )
    except Exception:
        import logging

        logging.getLogger(__name__).info(
            "test-support audit_type=%s persona_id=%s correlation_id=%s",
            audit_type,
            persona_id,
            correlation_id,
        )


@router.get("/personas")
def list_personas(request: Request) -> dict[str, Any]:
    items = _load_identities()
    _audit_log(request, "test-support.personas-listed", None)
    return {"count": len(items), "items": items}


@router.get("/personas/{persona_id}")
def get_persona(persona_id: str, request: Request) -> dict[str, Any]:
    for item in _load_identities():
        if item.get("persona_id") == persona_id:
            _audit_log(request, "test-support.persona-resolved", persona_id)
            return item
    _audit_log(request, "test-support.persona-miss", persona_id)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"persona '{persona_id}' not found in seed registry",
    )


@router.post("/seed/scenario", status_code=status.HTTP_200_OK)
def resolve_scenario(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    """Resolve a hazard scenario fixture by id; **read-only** (no mutation).

    Per contract acceptance criteria: "Refuses to mutate seed data on any verb".
    The POST verb is used because the request includes a body (scenario_id +
    hazard filter), but the handler MUST treat it as a lookup.
    """

    scenario_id = payload.get("scenario_id")
    if not scenario_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scenario_id is required",
        )
    for scenario in _load_hazard_scenarios():
        if scenario.get("scenario_id") == scenario_id:
            _audit_log(request, "test-support.scenario-resolved", None)
            return {"scenario": scenario}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"hazard scenario '{scenario_id}' not found",
    )
