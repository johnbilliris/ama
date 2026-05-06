"""Contract test: persona workspace resolves from seed registry in production.

Regression for the deployed-app bug where ``/workspaces/{persona_id}`` showed
"Loading workspace…" indefinitely because ``state_store.PERSONAS`` is empty
at startup. ``PersonaWorkspaceService`` now falls back to
``PersonaRegistryRepository`` (loaded from
``packages/domain/src/domain/seed/identities_australia.json``).
"""

from app.main import create_app
from app.services.state_store import reset_state
from fastapi.testclient import TestClient


def test_workspace_resolves_from_seed_registry_without_state_store_seed() -> None:
    reset_state()

    client = TestClient(create_app())

    response = client.get("/api/personas/incident-commander/workspace")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["persona"]["persona_id"] == "incident-commander"
    # role mirrors persona_id so the frontend's role-based panel routing
    # (e.g. role === "incident-commander") fires correctly.
    assert payload["persona"]["role"] == "incident-commander"
    assert payload["tasks"] == []
    assert payload["dependencies"] == []


def test_workspace_returns_404_for_unknown_persona() -> None:
    reset_state()

    client = TestClient(create_app())

    response = client.get("/api/personas/incident_commander_au_east/workspace")

    assert response.status_code == 404
    assert response.json()["message"] == "Persona not found"
