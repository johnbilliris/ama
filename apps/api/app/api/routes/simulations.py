from app.api.dependencies.rbac import (
    require_simulation_participant,
    require_simulation_role,
)
from app.core.auth import extract_principal_from_claims
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.exercise_report_service import ExerciseReportService
from app.services.scenario_seeding_service import ScenarioSeedingService
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_clock_service import SimulationClockService
from app.services.simulation_event_recorder import SimulationEventRecorder
from app.services.simulation_service import SimulationService
from app.services.warp_scheduler import WarpScheduler
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from packages.domain.src.domain.models.warp_constants import (
    ALLOWED_WARP_SPEEDS,
    DEFAULT_WARP_SPEED,
    DELIVERY_LAG_WARNING_SECONDS,
    validate_warp_speed,
)

router = APIRouter(prefix="/simulations", tags=["simulation"])

_repo = SimulationRepository()
_signal_repo = SignalRepository()
_audit = SimulationAuditWriter()
_event_repo = SimulationEventRepository()
_clock = SimulationClockService()
_recorder = SimulationEventRecorder(_event_repo)
_service = SimulationService(
    simulation_repository=_repo,
    audit_writer=_audit,
    clock_service=_clock,
    event_recorder=_recorder,
)
_scheduler = WarpScheduler(
    signal_repository=_signal_repo,
    event_repository=_event_repo,
    simulation_repository=_repo,
    clock_service=_clock,
    event_recorder=_recorder,
)
_seeding = ScenarioSeedingService(
    signal_repository=_signal_repo,
    audit_writer=_audit,
    warp_scheduler=_scheduler,
    event_recorder=_recorder,
)
_report_service = ExerciseReportService(simulation_repository=_repo, signal_repository=_signal_repo)


def _tenant_public_view(tenant) -> dict:
    data = tenant.model_dump(mode="json")
    current = _clock.get_current_sim_seconds(tenant)
    data["current_sim_seconds"] = current
    data["accumulated_sim_seconds"] = tenant.accumulated_sim_seconds
    data["current_warp_speed"] = tenant.current_warp_speed
    data["clock_paused"] = tenant.clock_paused
    data["playback_status"] = tenant.playback_status
    # Backward-compat: mirror accumulated time into the legacy field.
    data["elapsed_seconds"] = current
    return data


class CreateSimulationRequest(BaseModel):
    scenario_type: str
    jurisdictions: list[str] = Field(default_factory=list)
    scenario_template_id: str | None = None
    participants: list[str] = Field(default_factory=list)
    resource_limits: dict | None = None
    warp_speed: float = Field(default=DEFAULT_WARP_SPEED)

    @classmethod
    def _validate(cls, v):
        return validate_warp_speed(v)


@router.post("", status_code=201)
async def create_simulation(body: CreateSimulationRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    try:
        warp_speed = validate_warp_speed(body.warp_speed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    participants = list(body.participants)
    if principal.subject not in participants:
        participants.insert(0, principal.subject)

    tenant = await _service.create_tenant(
        scenario_type=body.scenario_type,
        jurisdictions=body.jurisdictions,
        participants=participants,
        creator_oid=principal.subject,
        scenario_template_id=body.scenario_template_id,
        resource_limits=body.resource_limits,
        warp_speed=warp_speed,
    )
    return {
        "tenant_id": tenant.tenant_id,
        "scenario_run_id": tenant.scenario_run_id,
        "status": tenant.status,
        "created_at": tenant.created_at.isoformat(),
        "warp_speed": tenant.current_warp_speed,
        "current_warp_speed": tenant.current_warp_speed,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "clock_paused": tenant.clock_paused,
        "playback_status": tenant.playback_status,
    }


@router.get("")
async def list_simulations(
    request: Request,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    if limit > 100:
        limit = 100

    tenants, total = await _service.list_tenants(status=status, limit=limit, offset=offset)
    return {
        "simulations": [
            {
                "tenant_id": t.tenant_id,
                "scenario_type": t.scenario_type,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "participant_count": len(t.participants),
                "signal_count": t.resource_consumption.signal_count,
                "storage_bytes": t.resource_consumption.storage_bytes,
                "current_warp_speed": t.current_warp_speed,
                "playback_status": t.playback_status,
            }
            for t in tenants
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{tenant_id}")
async def get_simulation(tenant_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")

    await require_simulation_participant(principal, tenant_id, _repo)
    return _tenant_public_view(tenant)


@router.get("/{tenant_id}/clock")
async def get_simulation_clock(tenant_id: str, request: Request) -> dict:
    """Lightweight polling endpoint for the server-owned clock."""
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")

    state = _event_repo.get_scheduler_state(tenant_id)
    lag = state.delivery_lag_seconds if state is not None else 0.0
    current = _clock.get_current_sim_seconds(tenant)
    return {
        "current_sim_seconds": current,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "current_warp_speed": tenant.current_warp_speed,
        "clock_paused": tenant.clock_paused,
        "delivery_lag_seconds": lag,
        "delivery_lag_warning": lag > DELIVERY_LAG_WARNING_SECONDS,
        "delivery_lag_threshold_seconds": DELIVERY_LAG_WARNING_SECONDS,
    }


class SeedTemplateRequest(BaseModel):
    template_id: str


class SeedReplayRequest(BaseModel):
    incident_id: str
    start: str
    end: str
    time_compression: float = 1.0


@router.post("/{tenant_id}/seed", status_code=202)
async def seed_simulation(tenant_id: str, body: SeedTemplateRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status != "Active":
        raise HTTPException(status_code=409, detail="Simulation must be active to seed")

    result = await _seeding.seed_from_template(
        tenant_id, body.template_id, warp_speed=tenant.current_warp_speed
    )
    return {"status": "accepted", **result}


@router.post("/{tenant_id}/seed/replay", status_code=202)
async def seed_replay(tenant_id: str, body: SeedReplayRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status != "Active":
        raise HTTPException(status_code=409, detail="Simulation must be active to seed")

    result = await _seeding.seed_from_replay(
        tenant_id, body.incident_id, body.start, body.end, body.time_compression
    )
    return {"status": "accepted", **result}


class AddParticipantsRequest(BaseModel):
    participants: list[dict] = Field(default_factory=list)


@router.post("/{tenant_id}/participants")
async def add_participants(tenant_id: str, body: AddParticipantsRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")

    new_oids = [p["oid"] for p in body.participants if "oid" in p]
    existing = set(tenant.participants)
    for oid in new_oids:
        if oid not in existing:
            tenant.participants.append(oid)

    tenant = await _repo.update(tenant)
    return {"tenant_id": tenant.tenant_id, "participants": tenant.participants}


@router.get("/{tenant_id}/report")
async def get_report(tenant_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status == "Active":
        raise HTTPException(status_code=409, detail="Cannot generate report while simulation is active")

    report = await _report_service.get_report(tenant_id)
    if report is None:
        report = await _report_service.generate_report(tenant_id)

    return report.model_dump(mode="json")


class PauseResumeRequest(BaseModel):
    # Retained for backward compatibility with pre-feature-026 clients;
    # the server now owns the clock and ignores any supplied value.
    elapsed_seconds: float | None = Field(default=None, ge=0.0)


@router.post("/{tenant_id}/pause")
async def pause_simulation(
    tenant_id: str, request: Request, body: PauseResumeRequest | None = None
) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    try:
        tenant = await _service.pause_tenant(tenant_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message else 409
        raise HTTPException(status_code=status_code, detail=message)

    return {
        "tenant_id": tenant.tenant_id,
        "status": tenant.status,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "elapsed_seconds": tenant.accumulated_sim_seconds,
    }


@router.post("/{tenant_id}/resume")
async def resume_simulation(
    tenant_id: str, request: Request, body: PauseResumeRequest | None = None
) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    try:
        tenant = await _service.resume_tenant(tenant_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message else 409
        raise HTTPException(status_code=status_code, detail=message)

    return {
        "tenant_id": tenant.tenant_id,
        "status": tenant.status,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "current_warp_speed": tenant.current_warp_speed,
        "elapsed_seconds": tenant.accumulated_sim_seconds,
    }


class ArchiveRequest(BaseModel):
    elapsed_seconds: float | None = Field(default=None, ge=0.0)


@router.post("/{tenant_id}/archive", status_code=202)
async def archive_simulation(
    tenant_id: str, request: Request, body: ArchiveRequest | None = None
) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if not tenant.can_transition_to("Archiving"):
        raise HTTPException(status_code=409, detail=f"Cannot archive simulation in '{tenant.status}' status")

    tenant = await _service.archive_tenant(tenant_id)
    return {
        "tenant_id": tenant.tenant_id,
        "status": tenant.status,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "elapsed_seconds": tenant.accumulated_sim_seconds,
    }


class ChangeWarpSpeedRequest(BaseModel):
    warp_speed: float


@router.post("/{tenant_id}/warp-speed")
async def change_warp_speed(
    tenant_id: str, body: ChangeWarpSpeedRequest, request: Request
) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    try:
        validate_warp_speed(body.warp_speed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        tenant, previous = await _service.change_warp_speed(
            tenant_id, body.warp_speed, actor_oid=principal.subject
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message else 409
        raise HTTPException(status_code=status_code, detail=message)

    _scheduler.update_speed(tenant_id, tenant.current_warp_speed)
    return {
        "tenant_id": tenant.tenant_id,
        "previous_speed": previous,
        "current_warp_speed": tenant.current_warp_speed,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
    }


@router.delete("/{tenant_id}", status_code=204)
async def delete_simulation(tenant_id: str, request: Request) -> None:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status != "Archived":
        raise HTTPException(status_code=409, detail="Simulation must be archived before deletion")

    tenant = tenant.transition_to("Deleted")
    await _repo.update(tenant)


# ---------------------------------------------------------------------------
# Metadata endpoint used by the UI warp-speed picker.
# ---------------------------------------------------------------------------


@router.get("/meta/warp-speeds")
async def get_allowed_warp_speeds() -> dict:
    return {"allowed": list(ALLOWED_WARP_SPEEDS), "default": DEFAULT_WARP_SPEED}
