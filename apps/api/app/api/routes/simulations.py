from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.dependencies.rbac import (
    require_simulation_participant,
    require_simulation_role,
)
from app.core.auth import extract_principal_from_claims
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.signal_repository import SignalRepository
from app.services.simulation_audit_writer import SimulationAuditWriter
from app.services.simulation_service import SimulationService
from app.services.scenario_seeding_service import ScenarioSeedingService
from app.services.exercise_report_service import ExerciseReportService

router = APIRouter(prefix="/simulations", tags=["simulation"])

_repo = SimulationRepository()
_signal_repo = SignalRepository()
_audit = SimulationAuditWriter()
_service = SimulationService(simulation_repository=_repo, audit_writer=_audit)
_seeding = ScenarioSeedingService(signal_repository=_signal_repo, audit_writer=_audit)
_report_service = ExerciseReportService(simulation_repository=_repo, signal_repository=_signal_repo)


class CreateSimulationRequest(BaseModel):
    scenario_type: str
    jurisdictions: list[str] = Field(default_factory=list)
    scenario_template_id: str | None = None
    participants: list[str] = Field(default_factory=list)
    resource_limits: dict | None = None


@router.post("", status_code=201)
async def create_simulation(body: CreateSimulationRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    tenant = await _service.create_tenant(
        scenario_type=body.scenario_type,
        jurisdictions=body.jurisdictions,
        participants=body.participants,
        creator_oid=principal.subject,
        scenario_template_id=body.scenario_template_id,
        resource_limits=body.resource_limits,
    )
    return {
        "tenant_id": tenant.tenant_id,
        "scenario_run_id": tenant.scenario_run_id,
        "status": tenant.status,
        "created_at": tenant.created_at.isoformat(),
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
    return tenant.model_dump(mode="json")


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
    if tenant.status != "active":
        raise HTTPException(status_code=409, detail="Simulation must be active to seed")

    result = await _seeding.seed_from_template(tenant_id, body.template_id)
    return {"status": "accepted", **result}


@router.post("/{tenant_id}/seed/replay", status_code=202)
async def seed_replay(tenant_id: str, body: SeedReplayRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status != "active":
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
    if tenant.status == "active":
        raise HTTPException(status_code=409, detail="Cannot generate report while simulation is active")

    report = await _report_service.get_report(tenant_id)
    if report is None:
        report = await _report_service.generate_report(tenant_id)

    return report.model_dump(mode="json")


@router.post("/{tenant_id}/pause")
async def pause_simulation(tenant_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if not tenant.can_transition_to("paused"):
        raise HTTPException(status_code=409, detail=f"Cannot pause simulation in '{tenant.status}' status")

    tenant = tenant.transition_to("paused")
    tenant = await _repo.update(tenant)
    return {"tenant_id": tenant.tenant_id, "status": tenant.status}


@router.post("/{tenant_id}/resume")
async def resume_simulation(tenant_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if not tenant.can_transition_to("active"):
        raise HTTPException(status_code=409, detail=f"Cannot resume simulation in '{tenant.status}' status")

    tenant = tenant.transition_to("active")
    tenant = await _repo.update(tenant)
    return {"tenant_id": tenant.tenant_id, "status": tenant.status}


@router.post("/{tenant_id}/archive", status_code=202)
async def archive_simulation(tenant_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if not tenant.can_transition_to("archiving"):
        raise HTTPException(status_code=409, detail=f"Cannot archive simulation in '{tenant.status}' status")

    tenant = tenant.transition_to("archiving")
    tenant = await _repo.update(tenant)
    return {"tenant_id": tenant.tenant_id, "status": tenant.status}


@router.delete("/{tenant_id}", status_code=204)
async def delete_simulation(tenant_id: str, request: Request) -> None:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status != "archived":
        raise HTTPException(status_code=409, detail="Simulation must be archived before deletion")

    tenant = tenant.transition_to("deleted")
    await _repo.update(tenant)
