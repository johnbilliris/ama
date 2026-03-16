from pathlib import Path

from app.services.seed_service import SeedService

from packages.domain.src.domain.models.framework_assignment import FrameworkAssignment
from packages.domain.src.domain.models.jurisdiction import Jurisdiction
from packages.domain.src.domain.models.operating_framework import OperatingFramework
from packages.domain.src.domain.models.organisation import Organisation


class PreparednessAnalysisService:
    def __init__(self, seed_root: Path | None = None) -> None:
        self.seed_root = (
            seed_root
            or Path(__file__).resolve().parents[4]
            / "packages" / "domain" / "src" / "domain" / "seed"
        )

    def get_context(self) -> dict[str, list[object]]:
        seeds = SeedService().load(self.seed_root)
        return {
            "jurisdictions": [Jurisdiction(**item) for item in seeds["jurisdictions"]],
            "frameworks": [OperatingFramework(**item) for item in seeds["frameworks"]],
            "organisations": [Organisation(**item) for item in seeds["organisations"]],
        }

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
        frameworks = context["frameworks"]
        assignments = [
            FrameworkAssignment(
                assignment_id=f"assign-{framework.framework_id}-{jurisdiction_id}",
                framework_id=framework.framework_id,
                jurisdiction_id=jurisdiction_id,
            )
            for jurisdiction_id in jurisdiction_ids
            for framework in frameworks
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
            f"{len(assignments)} framework assignments synthesized for rehearsal analysis.",
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
