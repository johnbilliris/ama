from app.services.preparedness_analysis_service import PreparednessAnalysisService
from app.services.rehearsal_orchestrator import RehearsalOrchestrator


def test_preparedness_analysis_returns_frameworks_and_findings() -> None:
    analysis = PreparednessAnalysisService().analyse("flood", ["nsw"])

    assert any(item["framework_id"] == "aiims-national" for item in analysis["frameworks"])
    assert analysis["findings"]


def test_rehearsal_orchestrator_produces_gap_summary_and_findings() -> None:
    scenario_run = RehearsalOrchestrator().run("Victorian Bushfire Drill", "bushfire", ["vic"])

    assert scenario_run.framework_ids
    assert scenario_run.generated_findings
