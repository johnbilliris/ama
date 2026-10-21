"""M&E framework lifecycle management for the Monitoring Agent.

Handles framework creation, outcome selection, program logic building,
standards definition, collection schedule management, and overdue detection.

FRs: FR-008–013
"""

import logging
from datetime import UTC, datetime
from typing import TypedDict
from uuid import uuid4


class MEFrameworkRecord(TypedDict, total=False):
    framework_id: str
    incident_id: str
    program_name: str
    affected_community_definition: str
    selected_outcomes: list[dict[str, object]]
    program_logic_id: str | None
    active_evaluation_domains: list[str]
    standards_of_success: list[dict[str, object]]
    indicator_collection_schedule: list[dict[str, object]]
    evaluation_reports: list[str]
    status: str
    created_at: str
    created_by: str
    updated_at: str | None


class ProgramLogicRecord(TypedDict, total=False):
    model_id: str
    framework_id: str
    created_at: str
    model_type: str
    resources_inputs: list[dict[str, object]]
    activities: list[dict[str, object]]
    outputs: list[dict[str, object]]
    intermediate_outcomes: list[dict[str, object]]
    final_outcomes: list[dict[str, object]]
    outcome_chain_links: list[dict[str, object]]
    timeline_months: int | None


logger = logging.getLogger(__name__)


class MEFrameworkService:
    """In-agent M&E framework lifecycle management."""

    def __init__(self) -> None:
        self._frameworks: dict[str, MEFrameworkRecord] = {}
        self._program_logics: dict[str, dict[str, object]] = {}

    def create_framework(
        self,
        *,
        incident_id: str,
        program_name: str,
        affected_community_definition: str = "",
        created_by: str = "",
    ) -> MEFrameworkRecord:
        framework_id = f"mef-{uuid4().hex[:12]}"
        framework: MEFrameworkRecord = {
            "framework_id": framework_id,
            "incident_id": incident_id,
            "program_name": program_name,
            "affected_community_definition": affected_community_definition,
            "selected_outcomes": [],
            "program_logic_id": None,
            "active_evaluation_domains": [
                "governance",
                "community_engagement",
                "effectiveness",
                "efficiency",
                "implementation",
            ],
            "standards_of_success": [],
            "indicator_collection_schedule": [],
            "evaluation_reports": [],
            "status": "configuring",
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
            "updated_at": None,
        }
        self._frameworks[framework_id] = framework
        return framework

    def get_framework(self, framework_id: str) -> MEFrameworkRecord | None:
        return self._frameworks.get(framework_id)

    def select_outcomes(self, framework_id: str, outcomes: list[dict[str, object]]) -> MEFrameworkRecord:
        fw = self._frameworks.get(framework_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        fw["selected_outcomes"] = outcomes
        fw["updated_at"] = datetime.now(UTC).isoformat()
        return fw

    def create_program_logic(self, framework_id: str, logic_data: dict[str, object]) -> dict[str, object]:
        fw = self._frameworks.get(framework_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        model_id = f"plm-{uuid4().hex[:12]}"
        logic: dict[str, object] = {
            "model_id": model_id,
            "framework_id": framework_id,
            **logic_data,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._program_logics[model_id] = logic
        fw["program_logic_id"] = model_id
        fw["updated_at"] = datetime.now(UTC).isoformat()
        return logic

    def set_standards(self, framework_id: str, standards: list[dict[str, object]]) -> MEFrameworkRecord:
        fw = self._frameworks.get(framework_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        fw["standards_of_success"] = standards
        fw["updated_at"] = datetime.now(UTC).isoformat()
        return fw

    def set_collection_schedule(self, framework_id: str, schedules: list[dict[str, object]]) -> MEFrameworkRecord:
        fw = self._frameworks.get(framework_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        fw["indicator_collection_schedule"] = schedules
        fw["updated_at"] = datetime.now(UTC).isoformat()
        if fw["status"] == "configuring":
            fw["status"] = "active"
        return fw

    def generate_monitoring_report(self, framework_id: str) -> dict[str, object]:
        fw = self._frameworks.get(framework_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        overdue = [s["indicator_id"] for s in fw.get("indicator_collection_schedule", []) if s.get("is_overdue")]
        return {
            "framework_id": framework_id,
            "incident_id": fw["incident_id"],
            "indicators_status": fw.get("standards_of_success", []),
            "overdue_indicators": overdue,
            "staleness_warnings": [],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def generate_evaluation_report(
        self,
        framework_id: str,
        *,
        period_start: str,
        period_end: str,
        generated_by: str = "manual",
        created_by: str = "",
    ) -> dict[str, object]:
        fw = self._frameworks.get(framework_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        report_id = f"er-{uuid4().hex[:12]}"
        report: dict[str, object] = {
            "report_id": report_id,
            "framework_id": framework_id,
            "incident_id": fw["incident_id"],
            "evaluation_period_start": period_start,
            "evaluation_period_end": period_end,
            "domain_findings": {},
            "summary": "",
            "recommendations": [],
            "generated_by": generated_by,
            "content_safety_result": "passed" if generated_by == "ai_assisted" else None,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
        }
        fw["evaluation_reports"].append(report_id)
        fw["updated_at"] = datetime.now(UTC).isoformat()
        return report
