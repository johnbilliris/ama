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
    assert scenario_run.event_trace
    assert scenario_run.mode == "rehearsal"
    assert scenario_run.status == "completed"


def test_rehearsal_orchestrator_supports_severe_storm() -> None:
    scenario_run = RehearsalOrchestrator().run("NSW Severe Storm Drill", "severe_storm", ["nsw"])
    assert scenario_run.scenario_type == "severe_storm"
    assert scenario_run.generated_findings


def test_rehearsal_orchestrator_is_deterministic_for_same_inputs() -> None:
    orchestrator = RehearsalOrchestrator()
    run1 = orchestrator.run("Deterministic Flood", "flood", ["nsw"])
    run2 = orchestrator.run("Deterministic Flood", "flood", ["nsw"])

    assert run1.generated_findings == run2.generated_findings
    assert [event.offset_seconds for event in run1.event_trace] == [event.offset_seconds for event in run2.event_trace]
