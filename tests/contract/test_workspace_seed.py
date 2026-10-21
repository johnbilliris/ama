"""Unit + contract tests for the workspace coordination-task seeder.

Regression for the deployed-app DEGRADED lineage where every persona
workspace surfaced empty Assigned-Tasks / Dependencies columns because
``state_store.TASKS`` is process-local memory that is never seeded at
startup.
"""

from __future__ import annotations

from app.main import create_app
from app.services.state_store import TASKS, reset_state
from app.services.workspace_seed import (
    reset_seed_cache,
    seed_workspace_tasks,
)
from fastapi.testclient import TestClient


def test_seed_workspace_tasks_is_idempotent() -> None:
    reset_state()
    reset_seed_cache()
    first = seed_workspace_tasks()
    snapshot = dict(TASKS)
    second = seed_workspace_tasks()
    assert first > 0
    assert first == second
    assert TASKS.keys() == snapshot.keys()


def test_seed_includes_panel_routing_personas() -> None:
    reset_state()
    reset_seed_cache()
    seed_workspace_tasks()
    seeded_personas = {task.assigned_persona_id for task in TASKS.values()}
    panel_personas = {
        "incident-commander",
        "operations-officer",
        "planning-officer",
        "public-information-officer",
        "observer-auditor",
        "risk-manager",
        "field-coordinator",
        "resilience-planner",
    }
    missing = panel_personas - seeded_personas
    assert not missing, f"Seed missing tasks for panel personas: {missing}"


def test_workspace_route_returns_seeded_tasks_when_lifespan_runs(monkeypatch) -> None:
    reset_state()
    reset_seed_cache()
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "1")
    # Using ``with TestClient(create_app())`` triggers the FastAPI lifespan
    # which in turn invokes the workspace seeder.
    with TestClient(create_app()) as client:
        incident_id = next(
            task.incident_id for task in TASKS.values() if task.assigned_persona_id == "incident-commander"
        )
        response = client.get(f"/api/personas/incident-commander/workspace?incidentId={incident_id}")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["persona"]["persona_id"] == "incident-commander"
        # IC has tasks of their own AND dependencies from PIO and Planning.
        assert len(payload["tasks"]) >= 1
        # dependency chain is non-empty because task-ic-002 depends on
        # task-pio-001 and task-ic-003 depends on task-plan-001.
        assert len(payload["dependencies"]) >= 1
