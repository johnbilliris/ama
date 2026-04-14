"""Emergency plan service — Platform API business logic for emergency plans.

Delegates persistence to ``EmergencyPlanRepository`` and applies plan lifecycle
rules from the planning agent's lifecycle module.

FRs: FR-001–007 | Research: R-002
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from app.repositories.emergency_plan_repository import EmergencyPlanRepository

from packages.domain.src.domain.models.emergency_plan import PLAN_SECTION_SLUGS, PLANNING_PRINCIPLES
from packages.domain.src.domain.models.planning_process_record import PLANNING_STEPS

logger = logging.getLogger(__name__)


class EmergencyPlanService:
    """Platform API service for emergency plan CRUD and lifecycle management."""

    def __init__(self, repository: EmergencyPlanRepository | None = None):
        self._repo = repository or EmergencyPlanRepository()

    async def create_plan(
        self,
        *,
        title: str,
        region_id: str,
        hazard_types: list[str],
        hierarchy_level: str = "local",
        parent_plan_id: str | None = None,
        security_rating: str = "official",
        authority: str = "",
        created_by: str = "",
    ) -> dict:
        """Create a new emergency plan in draft state."""
        plan_id = uuid4().hex
        now = datetime.now(UTC).isoformat()

        plan_sections: dict[str, dict] = {}
        for slug in PLAN_SECTION_SLUGS:
            plan_sections[slug] = {
                "section_slug": slug,
                "title": slug.replace("_", " ").title(),
                "content": "",
                "is_complete": False,
            }

        process_steps: dict[str, dict] = {}
        for step_num, step_name in PLANNING_STEPS.items():
            process_steps[str(step_num)] = {
                "step_number": step_num,
                "step_name": step_name,
                "is_complete": False,
            }

        plan_doc = {
            "plan_id": plan_id,
            "title": title,
            "region_id": region_id,
            "hazard_types": hazard_types,
            "hierarchy_level": hierarchy_level,
            "parent_plan_id": parent_plan_id,
            "lifecycle_state": "draft",
            "version": 1,
            "security_rating": security_rating,
            "authority": authority,
            "created_by": created_by,
            "created_at": now,
            "updated_at": None,
            "plan_sections": plan_sections,
            "planning_principles_checklist": {},
            "process_steps": process_steps,
        }

        return await self._repo.create_plan(plan_doc)

    async def get_plan(self, plan_id: str, region_id: str) -> dict | None:
        """Retrieve a plan by ID and region."""
        return await self._repo.get_plan(plan_id, region_id)

    async def list_plans(
        self,
        region_id: str | None = None,
        lifecycle_state: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List plans with optional filters."""
        return await self._repo.list_plans(region_id=region_id, lifecycle_state=lifecycle_state, limit=limit)

    async def update_section(
        self,
        plan_id: str,
        region_id: str,
        section_slug: str,
        title: str = "",
        content: str = "",
    ) -> dict:
        """Update a section of a plan."""
        plan = await self._repo.get_plan(plan_id, region_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")

        if plan["lifecycle_state"] not in ("draft", "in_consultation"):
            raise ValueError(f"Plan in '{plan['lifecycle_state']}' state cannot be edited")

        if section_slug not in PLAN_SECTION_SLUGS:
            raise ValueError(f"Unknown section slug: '{section_slug}'")

        sections = plan.get("plan_sections", {})
        section = sections.get(section_slug, {"section_slug": section_slug})
        section["content"] = content
        section["title"] = title or section.get("title", section_slug.replace("_", " ").title())
        section["is_complete"] = bool(content)
        section["last_edited_at"] = datetime.now(UTC).isoformat()
        sections[section_slug] = section
        plan["plan_sections"] = sections
        plan["updated_at"] = datetime.now(UTC).isoformat()

        return await self._repo.update_plan(plan)

    async def transition_plan(
        self,
        plan_id: str,
        region_id: str,
        target_state: str,
        user_role: str,
    ) -> dict:
        """Transition a plan to a new lifecycle state."""
        from planning.plan_lifecycle import validate_plan_transition

        plan = await self._repo.get_plan(plan_id, region_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")

        current_state = plan["lifecycle_state"]
        is_valid, error_msg = validate_plan_transition(current_state, target_state, user_role)
        if not is_valid:
            raise ValueError(error_msg)

        plan["lifecycle_state"] = target_state
        plan["updated_at"] = datetime.now(UTC).isoformat()
        await self._repo.update_plan(plan)

        return {
            "plan_id": plan_id,
            "previous_state": current_state,
            "new_state": target_state,
            "transitioned_by": user_role,
        }

    async def get_completeness(self, plan_id: str, region_id: str) -> dict:
        """Compute completeness metrics for a plan."""
        plan = await self._repo.get_plan(plan_id, region_id)
        if plan is None:
            raise KeyError(f"Plan '{plan_id}' not found")

        sections = plan.get("plan_sections", {})
        completed_sections = sum(1 for s in sections.values() if isinstance(s, dict) and s.get("is_complete", False))
        total_sections = len(PLAN_SECTION_SLUGS)

        principles = plan.get("planning_principles_checklist", {})
        checked_principles = sum(1 for v in principles.values() if v is True)
        total_principles = len(PLANNING_PRINCIPLES)

        missing_sections = [
            slug for slug in PLAN_SECTION_SLUGS
            if slug not in sections or not sections.get(slug, {}).get("is_complete", False)
        ]
        unchecked_principles = [p for p in PLANNING_PRINCIPLES if not principles.get(p, False)]

        return {
            "plan_id": plan_id,
            "section_completeness": completed_sections / total_sections if total_sections > 0 else 0.0,
            "principles_completeness": checked_principles / total_principles if total_principles > 0 else 0.0,
            "total_sections": total_sections,
            "completed_sections": completed_sections,
            "total_principles": total_principles,
            "checked_principles": checked_principles,
            "missing_sections": missing_sections,
            "unchecked_principles": unchecked_principles,
        }

    async def get_hierarchy(self, region_id: str) -> list[dict]:
        """Get plans for a region, ordered by hierarchy."""
        return await self._repo.get_hierarchy(region_id)
