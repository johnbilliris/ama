from uuid import uuid4

from app.services.preparedness_analysis_service import PreparednessAnalysisService

from packages.domain.src.domain.models.scenario_run import ScenarioRun


class RehearsalOrchestrator:
    def run(
        self, scenario_name: str, scenario_type: str, jurisdiction_ids: list[str]
    ) -> ScenarioRun:
        from apps.agents.evacuation.agent import EvacuationAgent

        analysis = PreparednessAnalysisService().analyse(scenario_type, jurisdiction_ids)
        evacuation_review = EvacuationAgent().review(scenario_type, jurisdiction_ids)
        organisation_ids = [
            organisation["organisation_id"] for organisation in analysis["organisations"]
        ]
        framework_ids = [framework["framework_id"] for framework in analysis["frameworks"]]
        findings = list(analysis["findings"])
        findings.append(evacuation_review["recommendation"])

        return ScenarioRun(
            scenario_run_id=f"scenario-{uuid4().hex[:8]}",
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            jurisdiction_ids=jurisdiction_ids,
            organisation_ids=organisation_ids,
            framework_ids=framework_ids,
            coordination_gap_summary=list(analysis["coordinationGaps"]),
            generated_findings=findings,
        )
