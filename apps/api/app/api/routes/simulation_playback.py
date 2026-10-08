"""Playback API routes (feature 026 — US3 / US5).

Exposes read-only endpoints for after-action review:

* ``GET  /simulations/{tenant_id}/playback/events``
* ``GET  /simulations/{tenant_id}/playback/snapshots``
* ``POST /simulations/{tenant_id}/playback/annotations``  (US5)
* ``PUT  /simulations/{tenant_id}/playback/annotations/{annotation_id}``  (US5)
* ``DELETE /simulations/{tenant_id}/playback/annotations/{annotation_id}``  (US5)
"""

from __future__ import annotations

from app.api.dependencies.rbac import require_simulation_role
from app.api.routes.simulations import _event_repo, _recorder, _repo
from app.core.auth import extract_principal_from_claims
from app.services.annotation_service import AnnotationService
from app.services.playback_service import PlaybackService
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/simulations/{tenant_id}/playback",
    tags=["simulation-playback"],
)

_playback = PlaybackService(event_repository=_event_repo, simulation_repository=_repo)
_annotations = AnnotationService(event_repository=_event_repo, simulation_repository=_repo)


def _principal(request: Request) -> str:
    principal = extract_principal_from_claims(request.state.claims)
    try:
        require_simulation_role(principal)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return principal.subject


def _access_error_to_http(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail="simulation_not_found")
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    return HTTPException(status_code=500, detail="internal_error")


# ── events ────────────────────────────────────────────────────────────


@router.get("/events")
async def list_playback_events(
    tenant_id: str,
    request: Request,
    after_seq: int = 0,
    limit: int = 200,
    include_annotations: bool = True,
) -> dict[str, object]:
    user_oid = _principal(request)
    try:
        return await _playback.get_events(
            tenant_id,
            requesting_user_oid=user_oid,
            after_seq=after_seq,
            limit=min(limit, 1000),
            include_annotations=include_annotations,
        )
    except (LookupError, PermissionError) as exc:
        raise _access_error_to_http(exc) from exc


@router.get("/snapshots")
async def list_playback_snapshots(
    tenant_id: str,
    request: Request,
    before_sim_time: float | None = None,
) -> dict[str, object]:
    user_oid = _principal(request)
    try:
        return await _playback.get_snapshots(
            tenant_id,
            requesting_user_oid=user_oid,
            before_sim_time=before_sim_time,
        )
    except (LookupError, PermissionError) as exc:
        raise _access_error_to_http(exc) from exc


# ── annotations (US5) ─────────────────────────────────────────────────


class CreateLogEntryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    sim_time_offset: float | None = Field(default=None, ge=0)
    category: str | None = Field(default=None, max_length=64)


@router.post("/log-entries", status_code=201)
async def create_log_entry(
    tenant_id: str,
    body: CreateLogEntryRequest,
    request: Request,
) -> dict[str, object]:
    """Persist a UI-emitted Event Log line to the ``sim-events`` container.

    The right-hand Event Log on the simulation dashboard previously held
    optimistic, in-memory only entries (Deploy / SITREP commands, sub-agent
    reply previews, scenario-seed banners) which vanished on refresh and
    were pruned by the polling reconciler the moment a newer durable event
    arrived. This endpoint gives the client a permanent home for those
    lines so post-exercise review reflects exactly what controllers saw.
    """
    user_oid = _principal(request)
    tenant = await _repo.get_by_tenant_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="simulation_not_found")
    if not (tenant.created_by == user_oid or user_oid in tenant.participants):
        raise HTTPException(status_code=403, detail="log_entry_access_denied")
    sim_time = body.sim_time_offset if body.sim_time_offset is not None else 0.0
    event = _recorder.record_ui_log(
        tenant_id,
        sim_time,
        text=body.text,
        author_oid=user_oid,
        category=body.category,
    )
    if event is None:
        raise HTTPException(status_code=503, detail="event_recorder_unhealthy")
    return event.model_dump(mode="json")


# ── annotations (US5) ─────────────────────────────────────────────────


class CreateAnnotationRequest(BaseModel):
    sim_time_offset: float = Field(..., ge=0)
    text: str = Field(..., min_length=1, max_length=2000)


class UpdateAnnotationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


@router.post("/annotations", status_code=201)
async def create_annotation(
    tenant_id: str,
    body: CreateAnnotationRequest,
    request: Request,
) -> dict[str, object]:
    user_oid = _principal(request)
    try:
        ann = await _annotations.create(
            tenant_id,
            author_oid=user_oid,
            sim_time_offset=body.sim_time_offset,
            text=body.text,
        )
        return ann.model_dump(mode="json")
    except (LookupError, PermissionError) as exc:
        raise _access_error_to_http(exc) from exc


@router.put("/annotations/{annotation_id}")
async def update_annotation(
    tenant_id: str,
    annotation_id: str,
    body: UpdateAnnotationRequest,
    request: Request,
) -> dict[str, object]:
    user_oid = _principal(request)
    try:
        ann = await _annotations.update(
            tenant_id,
            annotation_id=annotation_id,
            requesting_user_oid=user_oid,
            text=body.text,
        )
        return ann.model_dump(mode="json")
    except (LookupError, PermissionError) as exc:
        raise _access_error_to_http(exc) from exc


@router.delete("/annotations/{annotation_id}", status_code=204)
async def delete_annotation(
    tenant_id: str,
    annotation_id: str,
    request: Request,
) -> Response:
    user_oid = _principal(request)
    try:
        await _annotations.delete(
            tenant_id,
            annotation_id=annotation_id,
            requesting_user_oid=user_oid,
        )
    except (LookupError, PermissionError) as exc:
        raise _access_error_to_http(exc) from exc
    return Response(status_code=204)
