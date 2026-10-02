import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from app.api.dependencies.rbac import (
    require_simulation_admin,
    require_simulation_participant,
    require_simulation_role,
)
from app.api.dependencies.simulation_composition import get_resource_governor, simulation_repository_proxy
from app.core.async_io import run_blocking
from app.core.auth import extract_principal_from_claims
from app.repositories.persona_registry_repository import get_persona_registry_repository
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.services.exercise_report_service import ExerciseReportService
from app.services.operational_store import OperationalStore
from app.services.scenario_seeding_service import ScenarioSeedingService
from app.services.simulation_audit_writer import build_simulation_blob_service_client, get_simulation_audit_writer
from app.services.simulation_clock_service import SimulationClockService
from app.services.simulation_event_recorder import SimulationEventRecorder
from app.services.simulation_service import SimulationService
from app.services.warp_scheduler import WarpScheduler
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from packages.domain.src.domain.models.simulation_run import SimulationRun as ScenarioRunModel
from packages.domain.src.domain.models.simulation_scenario import EventPhase, SimulationScenario
from packages.domain.src.domain.models.simulation_tenant import SimulationParticipant
from packages.domain.src.domain.models.warp_constants import (
    ALLOWED_WARP_SPEEDS,
    DEFAULT_WARP_SPEED,
    DELIVERY_LAG_WARNING_SECONDS,
    validate_warp_speed,
)

router = APIRouter(prefix="/simulations", tags=["simulation"])

_repo = simulation_repository_proxy()
_resource_governor = get_resource_governor()
_signal_repo = SignalRepository(write_guard=_resource_governor)
_live_signal_repo = _signal_repo.bind("live")
_audit = get_simulation_audit_writer()
_event_repo = SimulationEventRepository()
_clock = SimulationClockService()
_blob_service_client = build_simulation_blob_service_client()
_recorder = SimulationEventRecorder(_event_repo)
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
    cosmos_client=getattr(_repo, "_client", None),
    simulation_repository=_repo,
    replay_source_repository=_live_signal_repo,
    warp_scheduler=_scheduler,
    event_recorder=_recorder,
)
_report_service = ExerciseReportService(
    simulation_repository=_repo,
    signal_repository=_signal_repo,
    event_repository=_event_repo,
    blob_service_client=_blob_service_client,
    audit_writer=_audit,
)
_service = SimulationService(
    simulation_repository=_repo,
    audit_writer=_audit,
    clock_service=_clock,
    event_recorder=_recorder,
    report_service=_report_service,
    signal_repository=_signal_repo,
    event_repository=_event_repo,
    resource_governor=_resource_governor,
)

_seed_catalogue = json.loads(
    Path("packages/domain/src/domain/seed/data_sources_australia.json").read_text(encoding="utf-8")
)
_registered_source_ids = {
    str(entry.get("data_source_id"))
    for entry in _seed_catalogue
    if isinstance(entry, dict) and str(entry.get("data_source_id", "")).strip()
}


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


class SimulationScenarioInputCompat(BaseModel):
    name: str
    scenarioType: str
    targetRegion: dict
    targetJurisdictionIds: list[str]
    activatedDataSourceIds: list[str]
    timeCompressionRatio: float = Field(default=1.0, gt=0)
    misinformationRatio: float = Field(default=0.15, ge=0.0, le=1.0)
    historicalOverlayPath: str | None = None


class StartRunInputCompat(BaseModel):
    scenarioId: str
    requestedByPersonaId: str
    timeCompressionRatio: float | None = Field(default=None, gt=0)
    misinformationRatio: float | None = Field(default=None, ge=0.0, le=1.0)


class AbortRunInputCompat(BaseModel):
    requestedByPersonaId: str


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

    try:
        tenant = await _service.create_tenant(
            scenario_type=body.scenario_type,
            jurisdictions=body.jurisdictions,
            participants=participants,
            creator_oid=principal.subject,
            scenario_template_id=body.scenario_template_id,
            resource_limits=body.resource_limits,
            warp_speed=warp_speed,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
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

    tenants, total = await _service.list_tenants(
        status=status,
        limit=limit,
        offset=offset,
        participant_oid=principal.subject,
    )
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


@router.get("/scenarios")
async def list_compat_scenarios(request: Request) -> list[dict]:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    rows = await _repo.list_documents(
        document_type="spec006_simulation_scenario",
        owner_agency_id=principal.agency_id,
        limit=500,
    )
    return [
        {
            "scenarioId": row.get("scenario_id"),
            "name": row.get("name"),
            "scenarioType": row.get("scenario_type"),
            "targetRegion": row.get("target_region"),
            "targetJurisdictionIds": row.get("target_jurisdiction_ids", []),
            "activatedDataSourceIds": row.get("activated_data_source_ids", []),
            "timeCompressionRatio": row.get("time_compression_ratio"),
            "misinformationRatio": row.get("misinformation_ratio"),
            "historicalOverlayPath": row.get("historical_overlay_path"),
            "createdBy": row.get("created_by"),
            "createdAt": row.get("created_at"),
        }
        for row in rows
    ]


@router.post("/scenarios", status_code=201)
async def create_compat_scenario(body: SimulationScenarioInputCompat, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    if body.targetRegion.get("type") != "Polygon":
        raise HTTPException(status_code=400, detail="targetRegion must be a GeoJSON Polygon")

    unknown_sources = [
        source_id for source_id in body.activatedDataSourceIds if source_id not in _registered_source_ids
    ]
    if unknown_sources:
        raise HTTPException(status_code=400, detail=f"Unknown data source ids: {sorted(unknown_sources)}")

    scenario_id = f"scn-{uuid4().hex[:12]}"
    phases = [
        EventPhase(
            phase_name="phase-1",
            phase_order=1,
            duration_minutes=5,
            data_sources_active=body.activatedDataSourceIds,
            escalation_triggers=[],
            signal_generation_params={},
        )
    ]
    scenario = SimulationScenario(
        scenario_id=scenario_id,
        name=body.name,
        scenario_type=body.scenarioType,  # type: ignore[arg-type]
        target_region=body.targetRegion,
        target_jurisdiction_ids=body.targetJurisdictionIds,
        activated_data_source_ids=body.activatedDataSourceIds,
        time_compression_ratio=body.timeCompressionRatio,
        event_phases=phases,
        misinformation_ratio=body.misinformationRatio,
        historical_overlay_path=body.historicalOverlayPath,
        created_by=principal.subject,
    )
    doc = scenario.model_dump(mode="json")
    doc["id"] = scenario_id
    doc["document_type"] = "spec006_simulation_scenario"
    doc["owner_agency_id"] = principal.agency_id
    await _repo.upsert_document(doc)

    return {
        "scenarioId": scenario.scenario_id,
        "name": scenario.name,
        "scenarioType": scenario.scenario_type,
        "targetRegion": scenario.target_region,
        "targetJurisdictionIds": scenario.target_jurisdiction_ids,
        "activatedDataSourceIds": scenario.activated_data_source_ids,
        "timeCompressionRatio": scenario.time_compression_ratio,
        "misinformationRatio": scenario.misinformation_ratio,
        "historicalOverlayPath": scenario.historical_overlay_path,
        "createdBy": scenario.created_by,
        "createdAt": scenario.created_at.isoformat(),
    }


@router.post("/runs", status_code=202)
async def start_compat_run(body: StartRunInputCompat, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    scenario_doc = await _repo.get_document(
        document_type="spec006_simulation_scenario",
        document_id=body.scenarioId,
    )
    if scenario_doc is None or str(scenario_doc.get("owner_agency_id", "")) != principal.agency_id:
        raise HTTPException(status_code=404, detail="Scenario not found")

    ratio = (
        body.timeCompressionRatio
        if body.timeCompressionRatio is not None
        else float(scenario_doc.get("time_compression_ratio", 1.0))
    )
    misinfo = (
        body.misinformationRatio
        if body.misinformationRatio is not None
        else float(scenario_doc.get("misinformation_ratio", 0.15))
    )

    run = ScenarioRunModel(
        run_id=uuid4().hex[:12],
        scenario_id=body.scenarioId,
        status="configuring",
        current_phase="",
        signals_generated={},
        total_signals=0,
        time_compression_ratio=ratio,
        misinformation_ratio=misinfo,
        created_by=principal.subject,
    )
    run = run.transition_to("running")
    doc = run.model_dump(mode="json")
    doc["id"] = run.run_id
    doc["document_type"] = "spec006_simulation_run"
    doc["owner_agency_id"] = principal.agency_id
    doc["requested_by_persona_id"] = body.requestedByPersonaId
    await _repo.upsert_document(doc)

    return _to_compat_run_response(doc)


@router.get("/runs/{run_id}")
async def get_compat_run(run_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    doc = await _repo.get_document(document_type="spec006_simulation_run", document_id=run_id)
    if doc is None or str(doc.get("owner_agency_id", "")) != principal.agency_id:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return _to_compat_run_response(doc)


@router.post("/runs/{run_id}/abort")
async def abort_compat_run(run_id: str, body: AbortRunInputCompat, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    doc = await _repo.get_document(document_type="spec006_simulation_run", document_id=run_id)
    if doc is None or str(doc.get("owner_agency_id", "")) != principal.agency_id:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    run = ScenarioRunModel.model_validate(doc)
    if run.status in ("completed", "aborted"):
        raise HTTPException(status_code=409, detail="Simulation run is already in a terminal state")
    run = run.transition_to("aborted")
    updated = run.model_dump(mode="json")
    updated["id"] = run.run_id
    updated["document_type"] = "spec006_simulation_run"
    updated["owner_agency_id"] = principal.agency_id
    updated["requested_by_persona_id"] = body.requestedByPersonaId
    await _repo.upsert_document(updated)
    return _to_compat_run_response(updated)


@router.get("/{tenant_id}")
async def get_simulation(tenant_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")

    await require_simulation_participant(principal, tenant_id, _repo)
    return _tenant_public_view(tenant)


def _to_compat_run_response(document: dict) -> dict:
    return {
        "runId": document.get("run_id"),
        "scenarioId": document.get("scenario_id"),
        "status": document.get("status"),
        "startedAt": document.get("started_at"),
        "completedAt": document.get("completed_at"),
        "currentPhase": document.get("current_phase"),
        "signalsGenerated": document.get("signals_generated", {}),
        "totalSignals": document.get("total_signals", 0),
        "timeCompressionRatio": document.get("time_compression_ratio"),
        "misinformationRatio": document.get("misinformation_ratio"),
        "createdBy": document.get("created_by"),
        "createdAt": document.get("created_at"),
    }


@router.get("/{tenant_id}/clock")
async def get_simulation_clock(tenant_id: str, request: Request) -> dict:
    """Lightweight polling endpoint for the server-owned clock."""
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")

    state = await run_blocking(_event_repo.get_scheduler_state, tenant_id)
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

    result = await _seeding.seed_from_template(tenant_id, body.template_id, warp_speed=tenant.current_warp_speed)
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

    source_incident = OperationalStore("live").incidents.get(body.incident_id)
    if source_incident is None:
        raise HTTPException(status_code=404, detail="Source incident not found")
    allowed = {jurisdiction.lower() for jurisdiction in principal.jurisdiction_ids}
    affected = {jurisdiction.lower() for jurisdiction in source_incident.affected_jurisdiction_ids}
    if allowed and not allowed.intersection(affected):
        raise HTTPException(status_code=403, detail="Source incident jurisdiction is not authorized")

    result = await _seeding.seed_from_replay(tenant_id, body.incident_id, body.start, body.end, body.time_compression)
    return {"status": "accepted", **result}


class ParticipantAssignmentInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    oid: str = Field(min_length=1)
    persona_id: str | None = Field(default=None, alias="persona")
    organisation_id: str | None = None
    jurisdiction_id: str | None = None
    role: Literal["coordinator", "participant", "observer", "administrator"] = "participant"


class AddParticipantsRequest(BaseModel):
    participants: list[ParticipantAssignmentInput] = Field(default_factory=list)


@router.post("/{tenant_id}/participants")
async def add_participants(tenant_id: str, body: AddParticipantsRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")

    coordinator_roles = {"simulation.coordinator", "simulation.admin", "system-administrator"}
    if principal.subject != tenant.created_by and not coordinator_roles.intersection(principal.roles):
        raise HTTPException(status_code=403, detail="Simulation coordinator role required")

    request_oids = [participant.oid for participant in body.participants]
    if len(request_oids) != len(set(request_oids)):
        raise HTTPException(status_code=422, detail="Participant OIDs must be unique within the request")

    persona_registry = get_persona_registry_repository()
    tenant_jurisdictions = {jurisdiction.lower() for jurisdiction in tenant.jurisdictions}
    for participant in body.participants:
        if participant.persona_id is None:
            continue
        persona = persona_registry.find_by_id(participant.persona_id)
        if persona is None:
            raise HTTPException(status_code=422, detail=f"Unknown persona: {participant.persona_id}")
        if participant.organisation_id and persona.organisation_id != participant.organisation_id:
            raise HTTPException(status_code=422, detail="Participant organisation does not match persona catalogue")
        if participant.jurisdiction_id and persona.jurisdiction_id != participant.jurisdiction_id:
            raise HTTPException(status_code=422, detail="Participant jurisdiction does not match persona catalogue")
        resolved_jurisdiction = (participant.jurisdiction_id or persona.jurisdiction_id or "").lower()
        if resolved_jurisdiction and tenant_jurisdictions and resolved_jurisdiction not in tenant_jurisdictions:
            raise HTTPException(status_code=422, detail="Participant jurisdiction is outside the simulation")

    new_assignments = [
        SimulationParticipant(
            oid=participant.oid,
            persona_id=participant.persona_id,
            organisation_id=(
                participant.organisation_id
                or (
                    get_persona_registry_repository().find_by_id(participant.persona_id).organisation_id
                    if participant.persona_id
                    else None
                )
            ),
            jurisdiction_id=(
                participant.jurisdiction_id
                or (
                    get_persona_registry_repository().find_by_id(participant.persona_id).jurisdiction_id
                    if participant.persona_id
                    else None
                )
            ),
            role=participant.role,
        )
        for participant in body.participants
    ]
    existing = set(tenant.participants)
    existing_assignments = {assignment.oid: assignment for assignment in tenant.participant_assignments}
    for assignment in new_assignments:
        if assignment.oid not in existing:
            tenant.participants.append(assignment.oid)
        existing_assignments[assignment.oid] = assignment
    tenant.participant_assignments = list(existing_assignments.values())

    tenant = await _repo.update(tenant)
    return {
        "tenant_id": tenant.tenant_id,
        "participants": tenant.participants,
        "participant_assignments": [
            assignment.model_dump(mode="json") for assignment in tenant.participant_assignments
        ],
    }


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
        raise HTTPException(status_code=404, detail="Exercise report not found")

    return report.model_dump(mode="json")


@router.get("/reports/{report_id}")
async def get_report_by_id(report_id: str, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    report = await _report_service.get_report_by_id(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Exercise report not found")
    await require_simulation_participant(principal, report.tenant_id, _repo)
    return report.model_dump(mode="json")


class PauseResumeRequest(BaseModel):
    # Retained for backward compatibility with pre-feature-026 clients;
    # the server now owns the clock and ignores any supplied value.
    elapsed_seconds: float | None = Field(default=None, ge=0.0)


@router.post("/{tenant_id}/pause")
async def pause_simulation(tenant_id: str, request: Request, body: PauseResumeRequest | None = None) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    try:
        tenant = await _service.pause_tenant(tenant_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message else 409
        raise HTTPException(status_code=status_code, detail=message)

    await _scheduler.stop_delivery_loop(tenant_id)

    return {
        "tenant_id": tenant.tenant_id,
        "status": tenant.status,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "elapsed_seconds": tenant.accumulated_sim_seconds,
    }


@router.post("/{tenant_id}/resume")
async def resume_simulation(tenant_id: str, request: Request, body: PauseResumeRequest | None = None) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    try:
        tenant = await _service.resume_tenant(tenant_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message else 409
        raise HTTPException(status_code=status_code, detail=message)

    await _scheduler.start_delivery_loop_async(tenant_id)

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
    tenant_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    body: ArchiveRequest | None = None,
) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    tenant = await _service.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Simulation tenant not found")
    if tenant.status != "Archiving" and not tenant.can_transition_to("Archiving"):
        raise HTTPException(status_code=409, detail=f"Cannot archive simulation in '{tenant.status}' status")

    await _scheduler.stop_delivery_loop(tenant_id)
    tenant = await _service.begin_archive(tenant_id)
    background_tasks.add_task(_service.archive_tenant, tenant_id)
    return {
        "tenant_id": tenant.tenant_id,
        "status": tenant.status,
        "accumulated_sim_seconds": tenant.accumulated_sim_seconds,
        "elapsed_seconds": tenant.accumulated_sim_seconds,
    }


class ChangeWarpSpeedRequest(BaseModel):
    warp_speed: float


@router.post("/{tenant_id}/warp-speed")
async def change_warp_speed(tenant_id: str, body: ChangeWarpSpeedRequest, request: Request) -> dict:
    principal = extract_principal_from_claims(request.state.claims)
    require_simulation_role(principal)
    await require_simulation_participant(principal, tenant_id, _repo)

    try:
        validate_warp_speed(body.warp_speed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        tenant, previous = await _service.change_warp_speed(tenant_id, body.warp_speed, actor_oid=principal.subject)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message else 409
        raise HTTPException(status_code=status_code, detail=message)

    await _scheduler.update_speed_async(tenant_id, tenant.current_warp_speed)
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
    # Retention-governed deletion is an administrator action; membership is not required.
    require_simulation_admin(principal)

    try:
        await _service.delete_archived_tenant(tenant_id, actor_id=principal.subject)
    except (PermissionError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Metadata endpoint used by the UI warp-speed picker.
# ---------------------------------------------------------------------------


@router.get("/meta/warp-speeds")
async def get_allowed_warp_speeds() -> dict:
    return {"allowed": list(ALLOWED_WARP_SPEEDS), "default": DEFAULT_WARP_SPEED}
