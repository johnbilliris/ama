from fastapi.testclient import TestClient

from app.main import create_app


def test_preparedness_catalog_and_replay_contract() -> None:
    client = TestClient(create_app())

    organisations_response = client.get("/api/organisations?jurisdictionId=nsw")
    assert organisations_response.status_code == 200
    assert any(item["organisation_id"] == "ses-nsw" for item in organisations_response.json())

    frameworks_response = client.get("/api/frameworks?jurisdictionId=nsw")
    assert frameworks_response.status_code == 200
    assert any(item["framework_id"] == "aiims-national" for item in frameworks_response.json())

    scenario_response = client.post(
        "/api/scenarios/replay",
        json={
            "scenarioName": "NSW Flood Rehearsal",
            "scenarioType": "flood",
            "jurisdictionIds": ["nsw"],
        },
    )
    assert scenario_response.status_code == 200
    scenario_run = scenario_response.json()
    assert scenario_run["scenario_type"] == "flood"
    assert scenario_run["jurisdiction_ids"] == ["nsw"]
