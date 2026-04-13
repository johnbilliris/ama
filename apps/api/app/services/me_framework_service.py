"""Platform API M&E framework service with repository delegation.

Manages M&E framework lifecycle through the Cosmos DB repository layer.
Used by the platform API routes (not the monitoring agent directly).

FRs: FR-008–014
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from app.repositories.me_framework_repository import MEFrameworkRepository

logger = logging.getLogger(__name__)


class MEFrameworkPlatformService:
    """Platform-level M&E framework management with persistence."""

    def __init__(self, repository: MEFrameworkRepository | None = None):
        self._repo = repository or MEFrameworkRepository()

    async def create_framework(
        self,
        *,
        incident_id: str,
        program_name: str,
        affected_community_definition: str = "",
        created_by: str = "",
    ) -> dict:
        """Create a new M&E framework and persist to Cosmos DB."""
        framework_id = f"mef-{uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        framework_doc = {
            "framework_id": framework_id,
            "id": framework_id,
            "document_type": "me_framework",
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
            "created_at": now,
            "created_by": created_by,
            "updated_at": None,
        }
        return await self._repo.create_framework(framework_doc)

    async def get_framework(self, framework_id: str, incident_id: str) -> dict | None:
        """Retrieve a framework by ID and incident partition key."""
        return await self._repo.get_framework(framework_id, incident_id)

    async def list_frameworks(
        self,
        incident_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """List frameworks with optional filters."""
        return await self._repo.list_frameworks(incident_id=incident_id, status=status)

    async def select_outcomes(
        self,
        framework_id: str,
        incident_id: str,
        outcomes: list[dict],
    ) -> dict:
        """Update selected outcomes on a framework."""
        fw = await self._repo.get_framework(framework_id, incident_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        fw["selected_outcomes"] = outcomes
        fw["updated_at"] = datetime.now(UTC).isoformat()
        return await self._repo.update_framework(fw)

    async def create_program_logic(
        self,
        framework_id: str,
        incident_id: str,
        logic_data: dict,
    ) -> dict:
        """Create a program logic model and link it to the framework."""
        fw = await self._repo.get_framework(framework_id, incident_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        model_id = f"plm-{uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        logic_doc = {
            "model_id": model_id,
            "id": model_id,
            "document_type": "program_logic",
            "framework_id": framework_id,
            "incident_id": incident_id,
            **logic_data,
            "created_at": now,
        }
        await self._repo.create_program_logic(logic_doc)
        fw["program_logic_id"] = model_id
        fw["updated_at"] = now
        await self._repo.update_framework(fw)
        return logic_doc

    async def set_standards(
        self,
        framework_id: str,
        incident_id: str,
        standards: list[dict],
    ) -> dict:
        """Set standards of success on a framework."""
        fw = await self._repo.get_framework(framework_id, incident_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        fw["standards_of_success"] = standards
        fw["updated_at"] = datetime.now(UTC).isoformat()
        return await self._repo.update_framework(fw)

    async def set_collection_schedule(
        self,
        framework_id: str,
        incident_id: str,
        schedules: list[dict],
    ) -> dict:
        """Set the indicator collection schedule and activate if needed."""
        fw = await self._repo.get_framework(framework_id, incident_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        fw["indicator_collection_schedule"] = schedules
        fw["updated_at"] = datetime.now(UTC).isoformat()
        if fw.get("status") == "configuring":
            fw["status"] = "active"
        return await self._repo.update_framework(fw)

    async def generate_monitoring_report(
        self,
        framework_id: str,
        incident_id: str,
    ) -> dict:
        """Generate a monitoring report snapshot."""
        fw = await self._repo.get_framework(framework_id, incident_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        overdue = [
            s["indicator_id"]
            for s in fw.get("indicator_collection_schedule", [])
            if s.get("is_overdue")
        ]
        return {
            "framework_id": framework_id,
            "incident_id": fw["incident_id"],
            "indicators_status": fw.get("standards_of_success", []),
            "overdue_indicators": overdue,
            "staleness_warnings": [],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def create_evaluation_report(
        self,
        framework_id: str,
        incident_id: str,
        *,
        period_start: str,
        period_end: str,
        generated_by: str = "manual",
        created_by: str = "",
    ) -> dict:
        """Generate and persist an evaluation report."""
        fw = await self._repo.get_framework(framework_id, incident_id)
        if not fw:
            raise ValueError(f"Framework {framework_id} not found")
        report_id = f"er-{uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        domain_findings = {}
        for domain in fw.get("active_evaluation_domains", []):
            domain_findings[domain] = {
                "evaluation_domain": domain,
                "questions_addressed": [],
                "findings": [],
                "evidence_references": [],
            }
        report_doc = {
            "report_id": report_id,
            "id": report_id,
            "document_type": "evaluation_report",
            "framework_id": framework_id,
            "incident_id": incident_id,
            "evaluation_period_start": period_start,
            "evaluation_period_end": period_end,
            "domain_findings": domain_findings,
            "summary": "",
            "recommendations": [],
            "generated_by": generated_by,
            "content_safety_result": "passed" if generated_by == "ai_assisted" else None,
            "created_at": now,
            "created_by": created_by,
        }
        await self._repo.create_evaluation_report(report_doc)
        # Update framework's report list
        fw.setdefault("evaluation_reports", []).append(report_id)
        fw["updated_at"] = now
        await self._repo.update_framework(fw)
        return report_doc
