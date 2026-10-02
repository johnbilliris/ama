from datetime import UTC, datetime
from pathlib import Path

from app.services.seed_service import SeedService

from packages.domain.src.domain.models.framework_assignment import FrameworkAssignment, is_effective
from packages.domain.src.domain.models.jurisdiction import Jurisdiction
from packages.domain.src.domain.models.jurisdiction_policy import JurisdictionPolicy
from packages.domain.src.domain.models.operating_framework import OperatingFramework
from packages.domain.src.domain.models.organisation import Organisation


class PreparednessAnalysisService:
    def __init__(self, seed_root: Path | None = None) -> None:
        if seed_root is None:
            from packages.domain.src.domain.seed import bootstrap as _seed_mod

            seed_root = Path(_seed_mod.__file__).resolve().parent
        self.seed_root = seed_root

    def get_context(
        self,
    ) -> dict[str, list[Jurisdiction | OperatingFramework | Organisation | FrameworkAssignment | JurisdictionPolicy]]:
        seeds = SeedService().load(self.seed_root)
        return {
            "jurisdictions": [Jurisdiction(**item) for item in seeds["jurisdictions"]],
            "frameworks": [OperatingFramework(**item) for item in seeds["frameworks"]],
            "organisations": [Organisation(**item) for item in seeds["organisations"]],
            "framework_assignments": [FrameworkAssignment(**item) for item in seeds.get("framework_assignments", [])],
            "jurisdiction_policies": [JurisdictionPolicy(**item) for item in seeds.get("jurisdiction_policies", [])],
        }

    def list_frameworks_by_jurisdictions(
        self,
        jurisdiction_ids: list[str],
        as_of: datetime | None = None,
    ) -> list[OperatingFramework]:
        if not jurisdiction_ids:
            return []
        context = self.get_context()
        now = as_of or datetime.now(UTC)
        assignments = context["framework_assignments"]
        matching_framework_ids: set[str] = set()
        for assignment in assignments:
            if assignment.jurisdiction_id in jurisdiction_ids and is_effective(assignment, now):
                matching_framework_ids.add(assignment.framework_id)
        frameworks = context["frameworks"]
        return [fw for fw in frameworks if fw.framework_id in matching_framework_ids]

    def analyse(
        self, scenario_type: str, jurisdiction_ids: list[str], as_of: datetime | None = None
    ) -> dict[str, object]:
        context = self.get_context()
        now = as_of or datetime.now(UTC)
        organisations = [
            organisation
            for organisation in context["organisations"]
            if any(jurisdiction_id in organisation.jurisdiction_ids for jurisdiction_id in jurisdiction_ids)
        ]
        organisation_ids = {organisation.organisation_id for organisation in organisations}
        all_assignments = context["framework_assignments"]

        candidate_assignments = [
            assignment
            for assignment in all_assignments
            if is_effective(assignment, now)
            and (
                assignment.jurisdiction_id in jurisdiction_ids
                or (assignment.organisation_id is not None and assignment.organisation_id in organisation_ids)
            )
        ]

        selected_by_framework: dict[str, FrameworkAssignment] = {}
        for assignment in candidate_assignments:
            current = selected_by_framework.get(assignment.framework_id)
            if current is None:
                selected_by_framework[assignment.framework_id] = assignment
                continue
            if current.organisation_id is None and assignment.organisation_id is not None:
                selected_by_framework[assignment.framework_id] = assignment

        assignments = list(selected_by_framework.values())
        matched_framework_ids = {a.framework_id for a in assignments}
        frameworks = [fw for fw in context["frameworks"] if fw.framework_id in matched_framework_ids]
        gaps = []
        if len(organisations) < 2:
            gaps.append("Insufficient multi-agency coverage for cross-organisational rehearsal.")
        if not any(framework.framework_type == "communications" for framework in frameworks):
            gaps.append("No communications framework assigned for public messaging rehearsal.")
        if scenario_type == "cyclone" and not any(
            "commonwealth" in organisation.jurisdiction_ids for organisation in organisations
        ):
            gaps.append("Cyclone scenario lacks commonwealth meteorology support.")

        findings = [
            f"{len(organisations)} organisations available across {len(jurisdiction_ids)} jurisdictions.",
            f"{len(assignments)} framework assignments active for the selected jurisdictions.",
        ]

        return {
            "jurisdictions": [
                item.model_dump(mode="json")
                for item in context["jurisdictions"]
                if item.jurisdiction_id in jurisdiction_ids
            ],
            "organisations": [item.model_dump(mode="json") for item in organisations],
            "frameworks": [item.model_dump(mode="json") for item in frameworks],
            "assignments": [item.model_dump(mode="json") for item in assignments],
            "policies": [
                item.model_dump(mode="json")
                for item in context["jurisdiction_policies"]
                if any(
                    jurisdiction.policy_set_id == item.policy_set_id
                    for jurisdiction in context["jurisdictions"]
                    if jurisdiction.jurisdiction_id in jurisdiction_ids
                )
            ],
            "coordinationGaps": gaps,
            "findings": findings,
        }
