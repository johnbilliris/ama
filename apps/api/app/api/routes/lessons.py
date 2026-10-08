"""Lessons management API routes.

Provides endpoints for capturing lessons, assignment, resolution,
contradictory-lesson flagging, trend analysis, and PR quality gates.

FRs: FR-038–042, FR-052 | Research: R-007
"""

from datetime import datetime

from app.services.lessons_service import LessonsService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.domain.src.domain.models.lesson import AIIMSFunction, LessonSeverity, PPRRPhase

router = APIRouter(prefix="/lessons", tags=["lessons"])

_svc = LessonsService()


# --- Request models ---


class CaptureInput(BaseModel):
    incident_id: str | None = None
    scenario_run_id: str | None = None
    title: str
    description: str
    aiims_function: AIIMSFunction | None = None
    pprr_phase: PPRRPhase | None = None
    severity: LessonSeverity = "medium"
    created_by: str = ""
    tags: list[str] = []
    originating_event_id: str | None = None


class AssignInput(BaseModel):
    assigned_to: str
    target_resolution_date: datetime | None = None


class ResolveInput(BaseModel):
    resolution_reference: str
    resolution_notes: str = ""
    escalation_approved_by: str | None = None


class FlagContradictoryInput(BaseModel):
    contradicts_config_ref: str


# --- Routes ---


@router.post("/")
async def capture_lesson(payload: CaptureInput) -> dict[str, object]:
    try:
        lesson = _svc.capture(
            incident_id=payload.incident_id,
            scenario_run_id=payload.scenario_run_id,
            title=payload.title,
            description=payload.description,
            aiims_function=payload.aiims_function,
            pprr_phase=payload.pprr_phase,
            severity=payload.severity,
            created_by=payload.created_by,
            tags=payload.tags,
            originating_event_id=payload.originating_event_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return lesson.model_dump(mode="json")


@router.get("/")
async def list_lessons(
    incident_id: str | None = None,
    status: str | None = None,
    aiims_function: str | None = None,
    pprr_phase: str | None = None,
    severity: str | None = None,
) -> list[dict[str, object]]:
    results = _svc.list_lessons(
        incident_id=incident_id,
        status=status,
        aiims_function=aiims_function,
        pprr_phase=pprr_phase,
        severity=severity,
    )
    return [ls.model_dump(mode="json") for ls in results]


@router.get("/trends")
async def get_trends() -> dict[str, object]:
    return _svc.get_trends()


@router.get("/verify-pr")
async def verify_pr(pr_description: str) -> dict[str, object]:
    return _svc.verify_pr(pr_description)


@router.get("/{lesson_id}")
async def get_lesson(lesson_id: str) -> dict[str, object]:
    lesson = _svc.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found")
    return lesson.model_dump(mode="json")


@router.put("/{lesson_id}/assign")
async def assign_lesson(lesson_id: str, payload: AssignInput) -> dict[str, object]:
    try:
        updated = _svc.assign(
            lesson_id=lesson_id,
            assigned_to=payload.assigned_to,
            target_resolution_date=payload.target_resolution_date,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return updated.model_dump(mode="json")


@router.put("/{lesson_id}/resolve")
async def resolve_lesson(lesson_id: str, payload: ResolveInput) -> dict[str, object]:
    try:
        updated = _svc.resolve(
            lesson_id=lesson_id,
            resolution_reference=payload.resolution_reference,
            resolution_notes=payload.resolution_notes,
            escalation_approved_by=payload.escalation_approved_by,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return updated.model_dump(mode="json")


@router.put("/{lesson_id}/flag-contradictory")
async def flag_contradictory(lesson_id: str, payload: FlagContradictoryInput) -> dict[str, object]:
    try:
        updated = _svc.flag_contradictory(
            lesson_id=lesson_id,
            contradicts_config_ref=payload.contradicts_config_ref,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return updated.model_dump(mode="json")
