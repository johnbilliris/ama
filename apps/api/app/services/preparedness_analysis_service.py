from pathlib import Path

from app.services.seed_service import SeedService

from packages.domain.src.domain.models.framework_assignment import FrameworkAssignment
from packages.domain.src.domain.models.jurisdiction import Jurisdiction
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
    ) -> dict[str, list[Jurisdiction | OperatingFramework | Organisation | FrameworkAssignment]]:
        seeds = SeedService().load(self.seed_root)
        return {
            "jurisdictions": [Jurisdiction(**item) for item in seeds["jurisdictions"]],
            "frameworks": [OperatingFramework(**item) for item in seeds["frameworks"]],
            "organisations": [Organisation(**item) for item in seeds["organisations"]],
            "framework_assignments": [
                FrameworkAssignment(**item) for item in seeds.get("framework_assignments", [])
            ],
        }

    def list_frameworks_by_jurisdictions(self, jurisdiction_ids: list[str]) -> list[OperatingFramework]:
        if not jurisdiction_ids:
            return []
        context = self.get_context()
        assignments = context["framework_assignments"]
        matching_framework_ids: set[str] = set()
        for assignment in assignments:
            if (
                assignment.jurisdiction_id in jurisdiction_ids
                and assignment.effective_to is None
            ):
                matching_framework_ids.add(assignment.framework_id)
        frameworks = context["frameworks"]
        return [fw for fw in frameworks if fw.framework_id in matching_framework_ids]

    def analyse(self, scenario_type: str, jurisdiction_ids: list[str]) -> dict[str, object]:
        context = self.get_context()
        organisations = [
            organisation
            for organisation in context["organisations"]
            if any(
                jurisdiction_id in organisation.jurisdiction_ids
                for jurisdiction_id in jurisdiction_ids
            )
        ]
        all_assignments = context["framework_assignments"]
        assignments = [
            a for a in all_assignments
            if a.jurisdiction_id in jurisdiction_ids and a.effective_to is None
        ]
        matched_framework_ids = {a.framework_id for a in assignments}
        frameworks = [
            fw for fw in context["frameworks"] if fw.framework_id in matched_framework_ids
        ]
        gaps = []
        if len(organisations) < 2:
            gaps.append("Insufficient multi-agency coverage for cross-organisational rehearsal.")
        if not any(framework.framework_type == "communications" for framework in frameworks):
            gaps.append("No communications framework assigned for public messaging rehearsal.")
        if scenario_type == "cyclone" and not any(
            "commonwealth" in organisation.jurisdiction_ids
            for organisation in organisations
        ):
            gaps.append("Cyclone scenario lacks commonwealth meteorology support.")

        findings = [
            f"{len(organisations)} organisations available"
            f" across {len(jurisdiction_ids)} jurisdictions.",
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
            "coordinationGaps": gaps,
            "findings": findings,
        }
