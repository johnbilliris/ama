"""Contract test: `/api/agents/risk-assessment/recommend` bridges the Risk Matrix UI.

Regression for the deployed-app bug where the Risk Matrix panel
[`apps/web/src/app/workspaces/[personaId]/_panels/risk-matrix.tsx`](../../apps/web/src/app/workspaces/[personaId]/_panels/risk-matrix.tsx)
displayed "risk-fetch-failed:404" because no `/agents/risk-assessment/recommend`
route existed on the main API. The route now returns a deterministic, schema-stable
recommendation so the UI panel always has a defensible matrix cell to render.
"""

from app.main import create_app
from app.services.state_store import reset_state
from fastapi.testclient import TestClient

LIKELIHOOD_VALUES = {"Rare", "Unlikely", "Possible", "Likely", "Almost Certain"}
CONSEQUENCE_VALUES = {"Insignificant", "Minor", "Moderate", "Major", "Catastrophic"}


def _client() -> TestClient:
    reset_state()
    return TestClient(create_app())


def test_recommend_returns_full_payload_for_known_scenario() -> None:
    client = _client()

    response = client.get(
        "/api/agents/risk-assessment/recommend",
        params={"scenario_id": "sa-pol-state-control"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["scenario_id"] == "sa-pol-state-control"
    assert payload["likelihood"] in LIKELIHOOD_VALUES
    assert payload["consequence"] in CONSEQUENCE_VALUES
    assert isinstance(payload["rationale"], str) and payload["rationale"]
    assert isinstance(payload["recommended_controls"], list)
    assert payload["recommended_controls"]
    assert all(isinstance(c, str) and c for c in payload["recommended_controls"])


def test_recommend_unknown_scenario_returns_default_not_404() -> None:
    client = _client()

    response = client.get(
        "/api/agents/risk-assessment/recommend",
        params={"scenario_id": "totally-unknown-xyz-001"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["scenario_id"] == "totally-unknown-xyz-001"
    assert payload["likelihood"] == "Possible"
    assert payload["consequence"] == "Moderate"


def test_recommend_bushfire_classification_is_high_severity() -> None:
    client = _client()

    response = client.get(
        "/api/agents/risk-assessment/recommend",
        params={"scenario_id": "vic-bushfire-2026"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["likelihood"] == "Likely"
    assert payload["consequence"] == "Major"


def test_recommend_requires_scenario_id() -> None:
    client = _client()
    response = client.get("/api/agents/risk-assessment/recommend")
    assert response.status_code == 422
