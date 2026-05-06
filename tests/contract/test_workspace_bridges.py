"""Contract tests for the spec-035 follow-up workspace bridge routes.

These pin the schema-stable shapes the persona-workspace UI panels expect.
Each test is a regression for one of the BROKEN / DEGRADED lineages
identified in plan.md "Investigation #6" and remediated in fix #7.

These tests reload the API modules with both feature gates explicitly OFF
so they're robust to running after other contract tests (e.g.
``test_outcome_evaluator.py`` and ``test_test_support_router.py``) that
import + reload the same modules with ``AMA_TEST_SUPPORT=1``.
"""

from __future__ import annotations

import importlib
import os

import pytest
from app.services.state_store import reset_state
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch) -> TestClient:
    """Rebuild the FastAPI app with both feature gates explicitly OFF.

    Mirrors the reload pattern in ``test_outcome_evaluator.py`` so previous
    test files' module-state mutations cannot leak in.
    """
    monkeypatch.delenv("AMA_TEST_SUPPORT", raising=False)
    monkeypatch.delenv("AMA_ENABLE_PRODUCTION_AUTH", raising=False)
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")

    import app.core.settings as settings_module

    importlib.reload(settings_module)
    settings_module.get_settings.cache_clear()

    import app.middleware.test_support_guard as guard_module

    importlib.reload(guard_module)

    import app.api.router as router_module

    importlib.reload(router_module)

    import app.main as main_module

    importlib.reload(main_module)

    reset_state()
    return TestClient(main_module.create_app())


@pytest.fixture(autouse=True)
def _restore_env():
    """Belt-and-braces: never leak AMA_TEST_SUPPORT / AMA_ENABLE_PRODUCTION_AUTH."""
    original_test = os.environ.get("AMA_TEST_SUPPORT")
    original_prod = os.environ.get("AMA_ENABLE_PRODUCTION_AUTH")
    yield
    for name, value in (
        ("AMA_TEST_SUPPORT", original_test),
        ("AMA_ENABLE_PRODUCTION_AUTH", original_prod),
    ):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


# ---------------------------------------------------------------------------
# Communication agent bridge — POST /api/agents/communication/draft-aws
# ---------------------------------------------------------------------------


def test_communication_draft_aws_returns_per_language_variants(client: TestClient) -> None:
    response = client.post(
        "/api/agents/communication/draft-aws",
        json={
            "level": "Watch and Act",
            "hazard": "bushfire",
            "location": "Wimmera",
            "action": "leave now via the Western Highway",
            "languages": ["en", "zh-Hans", "warlpiri"],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "variants" in body
    variants = body["variants"]
    assert isinstance(variants, list)
    assert len(variants) == 3
    by_lang = {v["language"]: v for v in variants}
    assert by_lang["en"]["reviewer_required"] is False
    assert by_lang["zh-Hans"]["reviewer_required"] is False
    assert by_lang["warlpiri"]["reviewer_required"] is True
    assert "Wimmera" in by_lang["en"]["text"]


def test_communication_draft_aws_rejects_invalid_level(client: TestClient) -> None:
    response = client.post(
        "/api/agents/communication/draft-aws",
        json={
            "level": "Mostly Harmless",
            "hazard": "bushfire",
            "location": "",
            "action": "",
            "languages": ["en"],
        },
    )
    assert response.status_code == 422


def test_communication_draft_aws_defaults_languages_to_english(client: TestClient) -> None:
    response = client.post(
        "/api/agents/communication/draft-aws",
        json={"level": "Advice", "hazard": "flood", "location": "Lismore", "action": ""},
    )
    assert response.status_code == 200, response.text
    variants = response.json()["variants"]
    assert len(variants) == 1
    assert variants[0]["language"] == "en"


# ---------------------------------------------------------------------------
# Audit denied-mutation — POST /api/audit/denied-mutation
# ---------------------------------------------------------------------------


def test_audit_denied_mutation_records_the_attempt(client: TestClient) -> None:
    response = client.post(
        "/api/audit/denied-mutation",
        headers={"x-correlation-id": "11111111-1111-4111-8111-111111111111"},
        json={
            "attempted_action": "edit",
            "target_audit_id": "audit-abc-123",
            "rationale": "append-only-policy",
        },
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["recorded"] is True
    assert body["outcome"] == "denied"
    assert "audit_id" in body and body["audit_id"]


def test_audit_denied_mutation_rejects_missing_target(client: TestClient) -> None:
    response = client.post(
        "/api/audit/denied-mutation",
        json={"attempted_action": "delete", "rationale": "append-only-policy"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Planning agent bridge — GET /api/agents/planning/draft-iap
# ---------------------------------------------------------------------------


def test_planning_draft_iap_returns_full_payload(client: TestClient) -> None:
    response = client.get(
        "/api/agents/planning/draft-iap",
        params={"scenario_id": "vic-bushfire-2026"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body["iap_draft_markdown"], str) and body["iap_draft_markdown"]
    forecast = body["forecast"]
    assert forecast["horizon_hours"] == 24
    assert 0.0 <= forecast["confidence"] <= 1.0
    assert isinstance(forecast["bullets"], list) and forecast["bullets"]


def test_planning_draft_iap_unknown_scenario_falls_back(client: TestClient) -> None:
    response = client.get(
        "/api/agents/planning/draft-iap",
        params={"scenario_id": "totally-unknown"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["forecast"]["horizon_hours"] == 24
    assert body["forecast"]["confidence"] == 0.6


def test_planning_draft_iap_requires_scenario_id(client: TestClient) -> None:
    response = client.get("/api/agents/planning/draft-iap")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Workspace IC approval bridge — POST /outcomes/sc-{id}/evaluate + GET /audit/list
# ---------------------------------------------------------------------------


def test_workspace_outcome_evaluate_then_audit_list_round_trip(client: TestClient) -> None:
    correlation_id = "22222222-2222-4222-8222-222222222222"
    eval_response = client.post(
        "/api/outcomes/sc-task-ic-001/evaluate",
        headers={"x-correlation-id": correlation_id},
        json={
            "rationale": "Approving the IAP for the next operational period.",
            "sources": [{"doc_id": "ev-001", "excerpt": "Catchment saturation"}],
            "confidence": 0.82,
            "approver_identity": "incident-commander",
        },
    )
    assert eval_response.status_code == 200, eval_response.text
    eval_body = eval_response.json()
    assert eval_body["status"] == "approved"
    assert eval_body["correlation_id"] == correlation_id

    list_response = client.get(
        "/api/audit/list",
        params={"correlation_id": correlation_id},
    )
    assert list_response.status_code == 200, list_response.text
    rows = list_response.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["correlation_id"] == correlation_id
    assert rows[0]["outcome"] == "approved"
    assert rows[0]["audit_id"] == eval_body["audit_id"]


def test_workspace_audit_list_returns_empty_for_unknown_correlation_id(client: TestClient) -> None:
    response = client.get(
        "/api/audit/list",
        params={"correlation_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["rows"] == []
    assert body["count"] == 0
