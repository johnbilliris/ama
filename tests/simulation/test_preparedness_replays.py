import pytest

from app.services.rehearsal_orchestrator import RehearsalOrchestrator


@pytest.mark.parametrize(
    ("scenario_name", "scenario_type", "jurisdiction_ids"),
    [
        ("Bushfire State Drill", "bushfire", ["vic"]),
        ("Flood Corridor Exercise", "flood", ["nsw"]),
        ("Cyclone Multi-Agency Review", "cyclone", ["commonwealth"]),
    ],
)
def test_preparedness_replays_cover_australian_hazard_types(
    scenario_name: str,
    scenario_type: str,
    jurisdiction_ids: list[str],
) -> None:
    scenario_run = RehearsalOrchestrator().run(scenario_name, scenario_type, jurisdiction_ids)

    assert scenario_run.scenario_type == scenario_type
    assert scenario_run.jurisdiction_ids == jurisdiction_ids
    assert scenario_run.generated_findings
