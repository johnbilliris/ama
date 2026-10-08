import asyncio
import os
from datetime import UTC, datetime, timedelta

from app.api.dependencies.rbac import require_simulation_admin
from app.api.dependencies.simulation_composition import get_resource_governor, simulation_repository_proxy
from app.core.auth import extract_principal_from_claims
from app.repositories.signal_repository import SignalRepository
from app.services.dashboard_service import DashboardService
from app.services.ingestion.incident_association import IncidentAssociationService
from app.services.state_store import INCIDENTS
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/incidents", tags=["incidents"])

_sim_repo = simulation_repository_proxy()
_governor = get_resource_governor()
_signal_repository = SignalRepository(write_guard=_governor)
_declaration_lock = asyncio.Lock()
_declaration_results: dict[str, dict[str, object]] = {}


class DeclareIncidentRequest(BaseModel):
    incident_id: str | None = None
    jurisdiction_id: str | None = None
    lookback_hours: int | None = None
    declaration_event_id: str | None = None
    tenant_id: str = "live"


def _default_lookback_hours() -> int:
    raw = os.environ.get("AMA_RETROSPECTIVE_LOOKBACK_HOURS", "24").strip()
    try:
        value = int(raw)
    except ValueError:
        return 24
    return value if value > 0 else 24


async def _run_retrospective_association(request: DeclareIncidentRequest) -> dict[str, object]:
    if not request.incident_id:
        return {"status": "skipped", "reason": "incident_id_not_provided", "signals_associated": 0}

    tenant_id = request.tenant_id.strip() or "live"
    incident = INCIDENTS.bucket_for(tenant_id).get(request.incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found in requested tenant scope")

    jurisdiction_id = (request.jurisdiction_id or "").strip().lower() or (
        incident.affected_jurisdiction_ids[0].lower() if incident.affected_jurisdiction_ids else "national"
    )
    lookback_hours = request.lookback_hours if request.lookback_hours is not None else _default_lookback_hours()
    if lookback_hours <= 0:
        raise HTTPException(status_code=422, detail="lookback_hours must be greater than zero")

    declaration_event_id = request.declaration_event_id or f"declare:{tenant_id}:{request.incident_id}"
    replay_key = f"{tenant_id}:{declaration_event_id}"

    async with _declaration_lock:
        if replay_key in _declaration_results:
            replay = dict(_declaration_results[replay_key])
            replay["replayed"] = True
            return replay

    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
    candidates = await _signal_repository.query_unassociated(
        jurisdiction_id=jurisdiction_id,
        since=cutoff,
        scope=tenant_id,
        include_all_jurisdictions=jurisdiction_id == "national",
    )

    scoped_matcher = IncidentAssociationService(incident_reader=lambda _scope: [(request.incident_id, incident)])

    associated = 0
    skipped = 0
    failed = 0
    outcomes: list[dict[str, str]] = []
    for signal in candidates:
        envelope = {
            "jurisdictionId": signal.jurisdiction_id,
            "location": signal.location,
            "provenance": {
                "collectionMethod": "retrospective_association",
                "sourceUri": "internal://incidents/declare",
            },
        }
        matched = await scoped_matcher.associate(envelope, scope=tenant_id)
        if matched.get("incidentId") != request.incident_id:
            skipped += 1
            outcomes.append({"signal_id": signal.signal_id, "outcome": "skipped_geometry_or_scope"})
            continue
        try:
            updated = await _signal_repository.update_incident_id(
                signal.signal_id,
                request.incident_id,
                scope=tenant_id,
                expected_incident_id=None,
            )
            if updated:
                associated += 1
                outcomes.append({"signal_id": signal.signal_id, "outcome": "associated"})
            else:
                skipped += 1
                outcomes.append({"signal_id": signal.signal_id, "outcome": "already_associated_or_conflict"})
        except Exception:
            failed += 1
            outcomes.append({"signal_id": signal.signal_id, "outcome": "update_failed"})

    result = {
        "status": "completed",
        "declaration_event_id": declaration_event_id,
        "tenant_id": tenant_id,
        "incident_id": request.incident_id,
        "jurisdiction_id": jurisdiction_id,
        "lookback_hours": lookback_hours,
        "signals_considered": len(candidates),
        "signals_associated": associated,
        "signals_skipped": skipped,
        "signals_failed": failed,
        "outcomes": outcomes,
        "replayed": False,
    }

    async with _declaration_lock:
        _declaration_results[replay_key] = dict(result)
    return result


@router.get("/{incident_id}/dashboard")
async def get_dashboard(incident_id: str, request: Request) -> dict[str, object]:
    try:
        claims = getattr(request.state, "claims", {}) or {}
        roles = tuple(str(role) for role in claims.get("roles", []))
        persona_id = claims.get("persona_id") or claims.get("personaId")
        return DashboardService().get_dashboard(
            incident_id,
            actor_roles=roles,
            actor_persona_id=str(persona_id) if persona_id else None,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/declare")
async def declare_incident(http_request: Request, request: DeclareIncidentRequest | None = None) -> dict[str, object]:
    principal = extract_principal_from_claims(http_request.state.claims)
    require_simulation_admin(principal)
    transition = await _governor.declare_incident_with_status(principal.subject)
    retrospective = await _run_retrospective_association(request or DeclareIncidentRequest())
    return {
        "status": transition["status"],
        "converged": transition["converged"],
        "simulations_throttled": transition["simulations_throttled"],
        "pending_tenant_ids": transition["pending_tenant_ids"],
        "mode_version": transition["mode_version"],
        "retrospective": retrospective,
    }


@router.post("/resolve")
async def resolve_incident(request: Request) -> dict[str, object]:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_admin(principal)
    transition = await _governor.resolve_incident_with_status(principal.subject)
    return {
        "status": transition["status"],
        "converged": transition["converged"],
        "simulations_restored": transition["simulations_restored"],
        "pending_tenant_ids": transition["pending_tenant_ids"],
        "mode_version": transition["mode_version"],
    }
