"""Lessons management service — capture, assign, resolve, and trend analysis.

Supports AIIMS/PPRR categorisation, contradictory-lesson handling,
PR quality gate verification, and SC-007 closure rate tracking.

FRs: FR-038–042, FR-052 | Research: R-007
"""

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.services.state_store import LESSONS

from packages.domain.src.domain.models.lesson import AIIMSFunction, Lesson, LessonSeverity, PPRRPhase


class LessonsService:
    def capture(
        self,
        incident_id: str | None = None,
        scenario_run_id: str | None = None,
        title: str = "",
        description: str = "",
        aiims_function: AIIMSFunction | None = None,
        pprr_phase: PPRRPhase | None = None,
        severity: LessonSeverity = "medium",
        created_by: str = "",
        tags: list[str] | None = None,
        originating_event_id: str | None = None,
    ) -> Lesson:
        """Create a new lesson. Must have incident_id or scenario_run_id."""
        lesson = Lesson(
            lesson_id=str(uuid4()),
            incident_id=incident_id,
            scenario_run_id=scenario_run_id,
            title=title,
            description=description,
            aiims_function=aiims_function,
            pprr_phase=pprr_phase,
            severity=severity,
            created_by=created_by,
            tags=tags or [],
            originating_event_id=originating_event_id,
        )
        LESSONS[lesson.lesson_id] = lesson
        return lesson

    def get(self, lesson_id: str) -> Lesson | None:
        return LESSONS.get(lesson_id)

    def list_lessons(
        self,
        incident_id: str | None = None,
        status: str | None = None,
        aiims_function: str | None = None,
        pprr_phase: str | None = None,
        severity: str | None = None,
    ) -> list[Lesson]:
        """Filter lessons by various criteria."""
        results = list(LESSONS.values())
        if incident_id:
            results = [ls for ls in results if ls.incident_id == incident_id]
        if status:
            results = [ls for ls in results if ls.status == status]
        if aiims_function:
            results = [ls for ls in results if ls.aiims_function == aiims_function]
        if pprr_phase:
            results = [ls for ls in results if ls.pprr_phase == pprr_phase]
        if severity:
            results = [ls for ls in results if ls.severity == severity]
        return results

    def assign(
        self,
        lesson_id: str,
        assigned_to: str,
        target_resolution_date: datetime | None = None,
    ) -> Lesson:
        """Assign a lesson to someone with optional target date."""
        lesson = LESSONS.get(lesson_id)
        if not lesson:
            raise KeyError(f"Lesson '{lesson_id}' not found")
        updated = lesson.model_copy(
            update={
                "assigned_to": assigned_to,
                "target_resolution_date": target_resolution_date,
                "status": "in_progress",
            },
        )
        LESSONS[lesson_id] = updated
        return updated

    def resolve(
        self,
        lesson_id: str,
        resolution_reference: str,
        resolution_notes: str = "",
        escalation_approved_by: str | None = None,
    ) -> Lesson:
        """Mark lesson as resolved with a reference (e.g., PR URL)."""
        lesson = LESSONS.get(lesson_id)
        if not lesson:
            raise KeyError(f"Lesson '{lesson_id}' not found")
        update_data: dict[str, object] = {
            "status": "resolved",
            "resolved_at": datetime.now(UTC),
            "resolution_reference": resolution_reference,
            "resolution_notes": resolution_notes,
        }
        if lesson.is_contradictory:
            if not escalation_approved_by:
                raise ValueError(
                    "escalation_approved_by required for contradictory lessons",
                )
            update_data["escalation_approved_by"] = escalation_approved_by
        updated = lesson.model_copy(update=update_data)
        LESSONS[lesson_id] = updated
        return updated

    def flag_contradictory(
        self,
        lesson_id: str,
        contradicts_config_ref: str,
    ) -> Lesson:
        """Flag a lesson as contradicting existing config."""
        lesson = LESSONS.get(lesson_id)
        if not lesson:
            raise KeyError(f"Lesson '{lesson_id}' not found")
        updated = lesson.model_copy(
            update={
                "is_contradictory": True,
                "contradicts_config_ref": contradicts_config_ref,
            },
        )
        LESSONS[lesson_id] = updated
        return updated

    def get_trends(self) -> dict[str, object]:
        """Analyse trends: recurring themes, unresolved items, by-function/by-phase."""
        all_lessons = list(LESSONS.values())
        by_function: dict[str, list[str]] = {}
        by_phase: dict[str, list[str]] = {}
        by_severity: dict[str, list[str]] = {}
        by_status: dict[str, list[str]] = {}
        for lesson in all_lessons:
            if lesson.aiims_function:
                by_function.setdefault(lesson.aiims_function, []).append(lesson.lesson_id)
            if lesson.pprr_phase:
                by_phase.setdefault(lesson.pprr_phase, []).append(lesson.lesson_id)
            by_severity.setdefault(lesson.severity, []).append(lesson.lesson_id)
            by_status.setdefault(lesson.status, []).append(lesson.lesson_id)

        # Tag frequency for recurring themes
        tag_freq: dict[str, int] = {}
        for lesson in all_lessons:
            for tag in lesson.tags:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1
        recurring_tags = {k: v for k, v in sorted(tag_freq.items(), key=lambda x: -x[1]) if v > 1}

        # SC-007 closure rate (90% within 90 days target)
        total = len(all_lessons)
        resolved = len([ls for ls in all_lessons if ls.status == "resolved"])
        closure_rate = resolved / total if total else 0.0

        return {
            "total_lessons": total,
            "closure_rate": closure_rate,
            "by_function": {k: len(v) for k, v in by_function.items()},
            "by_phase": {k: len(v) for k, v in by_phase.items()},
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_status": {k: len(v) for k, v in by_status.items()},
            "recurring_themes": recurring_tags,
            "unresolved_count": total - resolved,
        }

    def verify_pr(self, pr_description: str) -> dict[str, object]:
        """Check if a PR description references valid open lesson IDs."""
        referenced_ids = set(
            re.findall(r"lesson[_-]?([a-f0-9-]+)", pr_description, re.IGNORECASE),
        )
        matched = []
        unmatched = []
        for lid in referenced_ids:
            lesson = LESSONS.get(lid) or LESSONS.get(f"lesson-{lid}")
            if lesson:
                matched.append(
                    {
                        "lesson_id": lesson.lesson_id,
                        "status": lesson.status,
                        "title": lesson.title,
                    }
                )
            else:
                unmatched.append(lid)
        return {
            "referenced_ids": list(referenced_ids),
            "matched_lessons": matched,
            "unmatched_ids": unmatched,
            "all_valid": len(unmatched) == 0 and len(matched) > 0,
        }
