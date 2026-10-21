"""Planning Agent — AIDR emergency planning with 9-step process and plan lifecycle.

Implements the AIIMS Planning function with a ``create_app()`` factory
returning a FastAPI application. Follows the established agent pattern.

FRs: FR-001–007 | Research: R-001, R-002, R-008, R-012
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from planning import telemetry
from planning.audit import build_section_edit_audit, build_transition_audit
from planning.config import PlanningConfig
from planning.models import (
    CreatePlanRequest,
    PlanActivationHandoff,
    PlanActivationHandoffResult,
    PlanActivationRecord,
    PlanActivationRequest,
    PlanCompleteness,
    PlanDocument,
    PlanHierarchy,
    PlanSection,
    PlanSummary,
    PlanTransitionRequest,
    PlanTransitionResult,
    ProcessStep,
    UpdateSectionRequest,
    UpdateStepRequest,
)
from planning.pipeline import compute_completeness
from planning.plan_lifecycle import is_editable_state, validate_plan_transition
from planning.telemetry import update_section_completeness
from pydantic import BaseModel

from packages.domain.src.domain.models.emergency_plan import PLAN_SECTION_SLUGS
from packages.domain.src.domain.models.planning_process_record import PLANNING_STEPS

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    agent: str
    agent_version: str
    timestamp: str


class PlanningAgent:
    """Core planning agent with emergency plan lifecycle management."""

    def __init__(self, config: PlanningConfig | None = None):
        self._config = config or PlanningConfig()
        self._plans: dict[str, PlanDocument] = {}
        self._audit_log: list[dict[str, str | bool]] = []

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def create_plan(self, request: CreatePlanRequest) -> PlanDocument:
        plan_id = uuid4().hex
        now = datetime.now(UTC).isoformat()

        # Build initial plan sections (empty)
        plan_sections: dict[str, PlanSection] = {}
        for slug in PLAN_SECTION_SLUGS:
            plan_sections[slug] = {
                "section_slug": slug,
                "title": slug.replace("_", " ").title(),
                "content": "",
                "is_complete": False,
                "last_edited_at": None,
                "last_edited_by": None,
            }

        # Build initial 9-step process tracking
        process_steps: dict[int, ProcessStep] = {}
        for step_num, step_name in PLANNING_STEPS.items():
            process_steps[step_num] = {
                "step_number": step_num,
                "step_name": step_name,
                "is_complete": False,
                "completed_at": None,
                "completed_by": None,
                "notes": "",
            }

        plan_doc: PlanDocument = {
            "plan_id": plan_id,
            "title": request.title,
            "region_id": request.region_id,
            "hazard_types": request.hazard_types,
            "hierarchy_level": request.hierarchy_level,
            "parent_plan_id": request.parent_plan_id,
            "lifecycle_state": "draft",
            "version": 1,
            "security_rating": request.security_rating,
            "authority": request.authority,
            "created_by": request.created_by,
            "created_at": now,
            "updated_at": None,
            "plan_sections": plan_sections,
            "planning_principles_checklist": {},
            "process_steps": process_steps,
        }

        self._plans[plan_id] = plan_doc
        logger.info("Created plan %s: %s", plan_id, request.title)
        return plan_doc

    def get_plan(self, plan_id: str) -> PlanDocument | None:
        return self._plans.get(plan_id)

    def list_plans(self) -> list[PlanDocument]:
        return list(self._plans.values())

    def update_section(self, plan_id: str, section_slug: str, title: str, content: str) -> PlanDocument:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")
        if not is_editable_state(plan["lifecycle_state"]):
            raise ValueError(f"Plan is in '{plan['lifecycle_state']}' state and cannot be edited")
        if section_slug not in PLAN_SECTION_SLUGS:
            raise ValueError(f"Unknown section slug: '{section_slug}'")

        now = datetime.now(UTC).isoformat()
        section = plan["plan_sections"].get(section_slug, {})
        section.update(
            {
                "section_slug": section_slug,
                "title": title or section.get("title", section_slug.replace("_", " ").title()),
                "content": content,
                "is_complete": bool(content),
                "last_edited_at": now,
            }
        )
        plan["plan_sections"][section_slug] = section
        plan["updated_at"] = now

        audit = build_section_edit_audit(plan_id=plan_id, section_slug=section_slug, user_id="system")
        self._audit_log.append(audit)

        # Update telemetry
        completeness = compute_completeness(plan)
        update_section_completeness(completeness["section_completeness"])

        return plan

    def transition_plan(
        self, plan_id: str, target_state: str, user_role: str, reason: str = ""
    ) -> PlanTransitionResult:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")

        current_state = plan["lifecycle_state"]
        is_valid, error_msg = validate_plan_transition(current_state, target_state, user_role)
        if not is_valid:
            raise ValueError(error_msg)

        previous_state = current_state
        plan["lifecycle_state"] = target_state
        plan["updated_at"] = datetime.now(UTC).isoformat()

        audit = build_transition_audit(
            plan_id=plan_id,
            from_state=previous_state,
            to_state=target_state,
            user_id=user_role,
            user_role=user_role,
            reason=reason,
        )
        self._audit_log.append(audit)
        logger.info("Transitioned plan %s: %s → %s", plan_id, previous_state, target_state)

        return {
            "plan_id": plan_id,
            "previous_state": previous_state,
            "new_state": target_state,
            "transitioned_by": user_role,
        }

    def get_completeness(self, plan_id: str) -> PlanCompleteness:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")
        completeness = compute_completeness(plan)
        completeness["plan_id"] = plan_id
        return completeness

    def get_hierarchy(self, region_id: str) -> list[PlanDocument]:
        return [p for p in self._plans.values() if p.get("region_id") == region_id]

    def update_process_step(
        self, plan_id: str, step_number: int, is_complete: bool, notes: str, completed_by: str
    ) -> PlanDocument:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")
        if step_number not in PLANNING_STEPS:
            raise ValueError(f"Invalid step number: {step_number}. Must be 1–9.")

        now = datetime.now(UTC).isoformat()
        step: ProcessStep = plan["process_steps"].get(step_number, {})
        step.update(
            {
                "step_number": step_number,
                "step_name": PLANNING_STEPS[step_number],
                "is_complete": is_complete,
                "completed_at": now if is_complete else None,
                "completed_by": completed_by if is_complete else None,
                "notes": notes,
            }
        )
        plan["process_steps"][step_number] = step
        plan["updated_at"] = now

        return plan

    async def handle_plan_activation_handoff(self, handoff_event: PlanActivationHandoff) -> PlanActivationHandoffResult:
        """Process a plan activation handoff from incident management."""
        plan_id = handoff_event.get("payload", {}).get("plan_id")
        activated_by = handoff_event.get("payload", {}).get("activated_by", "system")
        # Would look up and activate the plan
        return {"status": "processed", "plan_id": plan_id, "activated_by": activated_by}


def _to_summary(plan_doc: PlanDocument) -> PlanSummary:
    """Convert a full plan document to a summary response dict."""
    return {
        "plan_id": plan_doc["plan_id"],
        "title": plan_doc["title"],
        "region_id": plan_doc["region_id"],
        "lifecycle_state": plan_doc["lifecycle_state"],
        "hierarchy_level": plan_doc["hierarchy_level"],
        "version": plan_doc["version"],
        "hazard_types": plan_doc["hazard_types"],
        "created_at": plan_doc["created_at"],
        "updated_at": plan_doc.get("updated_at"),
    }


def create_app(
    agent: PlanningAgent | None = None,
    config: PlanningConfig | None = None,
) -> FastAPI:
    """Factory function returning a configured FastAPI application."""
    _config = config or PlanningConfig()
    _agent = agent or PlanningAgent(config=_config)

    app = FastAPI(title="Planning Agent", version=_config.agent_version)

    # Store dependencies on app.state
    app.state.agent = _agent
    app.state.config = _config

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            agent="planning",
            agent_version=_config.agent_version,
            timestamp=datetime.now(UTC).isoformat(),
        )

    # ------------------------------------------------------------------
    # Plan CRUD
    # ------------------------------------------------------------------

    @app.post("/plans", status_code=201)
    async def create_plan(request: CreatePlanRequest) -> PlanSummary:
        plan_doc = _agent.create_plan(request)
        return _to_summary(plan_doc)

    @app.get("/plans")
    async def list_plans() -> list[PlanSummary]:
        return [_to_summary(p) for p in _agent.list_plans()]

    @app.get("/plans/by-region/{region_id}/hierarchy")
    async def get_hierarchy(region_id: str) -> PlanHierarchy:
        plans = _agent.get_hierarchy(region_id)
        return {
            "region_id": region_id,
            "plans": [_to_summary(p) for p in plans],
        }

    @app.get("/plans/{plan_id}")
    async def get_plan(plan_id: str) -> PlanSummary:
        plan = _agent.get_plan(plan_id)
        if plan is None:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found")
        return _to_summary(plan)

    @app.put("/plans/{plan_id}/sections/{section_slug}")
    async def update_section(plan_id: str, section_slug: str, request: UpdateSectionRequest) -> PlanSummary:
        try:
            plan = _agent.update_section(plan_id, section_slug, request.title, request.content)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _to_summary(plan)

    @app.post("/plans/{plan_id}/transition")
    async def transition_plan(plan_id: str, request: PlanTransitionRequest) -> PlanTransitionResult:
        try:
            result = _agent.transition_plan(plan_id, request.target_state, request.user_role, request.reason)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result

    @app.get("/plans/{plan_id}/completeness")
    async def get_completeness(plan_id: str) -> PlanCompleteness:
        try:
            return _agent.get_completeness(plan_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.put("/plans/{plan_id}/process/steps/{step_number}")
    async def update_process_step(plan_id: str, step_number: int, request: UpdateStepRequest) -> PlanSummary:
        try:
            plan = _agent.update_process_step(
                plan_id, step_number, request.is_complete, request.notes, request.completed_by
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return _to_summary(plan)

    # ------------------------------------------------------------------
    # Plan Activation & Post-Event Review (FRs: FR-007, FR-029)
    # ------------------------------------------------------------------

    plans_store = _agent._plans

    @app.post("/plans/{plan_id}/activate", status_code=200)
    async def activate_plan(plan_id: str, request: PlanActivationRequest) -> dict[str, object]:
        plan = plans_store.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        # Must be in endorsed state
        if plan["lifecycle_state"] != "endorsed":
            raise HTTPException(
                status_code=400,
                detail=f"Plan must be in 'endorsed' state to activate, currently '{plan['lifecycle_state']}'",
            )
        # Transition to activated
        plan["lifecycle_state"] = "activated"
        plan["updated_at"] = datetime.now(UTC).isoformat()
        activation_record: PlanActivationRecord = {
            "incident_id": request.incident_id,
            "activated_at": datetime.now(UTC).isoformat(),
            "activated_by": request.activated_by,
            "deactivated_at": None,
            "deactivation_reason": None,
        }
        plan.setdefault("activation_records", []).append(activation_record)
        telemetry.increment_activation_count()
        return {
            "plan_id": plan_id,
            "incident_id": request.incident_id,
            "activated_at": activation_record["activated_at"],
            "response_arrangements": plan.get("plan_sections", {}).get("response_arrangements"),
        }

    @app.post("/plans/{plan_id}/post-event-review", status_code=200)
    async def trigger_post_event_review(plan_id: str) -> dict[str, str]:
        plan = plans_store.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan["lifecycle_state"] != "activated":
            raise HTTPException(status_code=400, detail="Plan must be activated to trigger post-event review")
        plan["lifecycle_state"] = "post_event_review"
        plan["updated_at"] = datetime.now(UTC).isoformat()
        return {"plan_id": plan_id, "new_state": "post_event_review", "message": "Plan flagged for post-event review"}

    return app
