from __future__ import annotations

from app.main import create_app
from fastapi.testclient import TestClient


def _client() -> TestClient:
    return TestClient(create_app())


def test_au_export_policy_allows_default_country() -> None:
    client = _client()
    response = client.post(
        "/api/governance/dashboard/audit/export",
        json={
            "format": "json",
            "filter_params": {"country_code": "AU", "include_history": False, "legal_hold": False},
            "record_ids": [],
        },
    )
    assert response.status_code == 202


def test_non_au_country_activation_is_rejected() -> None:
    client = _client()
    response = client.post(
        "/api/governance/dashboard/audit/export",
        json={
            "format": "json",
            "filter_params": {"country_code": "PH", "include_history": False, "legal_hold": False},
            "record_ids": [],
        },
    )
    assert response.status_code == 403
    assert response.json()["message"] == "You are not authorized to perform this action"


def test_mixed_scope_export_is_rejected() -> None:
    client = _client()
    response = client.post(
        "/api/governance/dashboard/audit/export",
        json={
            "format": "json",
            "filter_params": {
                "country_code": "AU",
                "scope": "mixed",
                "include_history": False,
                "legal_hold": False,
            },
            "record_ids": [],
        },
    )
    assert response.status_code == 403
    assert response.json()["message"] == "You are not authorized to perform this action"


def test_history_export_requires_legal_hold() -> None:
    client = _client()
    response = client.post(
        "/api/governance/dashboard/audit/export",
        json={
            "format": "json",
            "filter_params": {"country_code": "AU", "include_history": True, "legal_hold": False},
            "record_ids": [],
        },
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Request conflicts with current resource state"


def test_history_export_with_legal_hold_is_allowed() -> None:
    client = _client()
    response = client.post(
        "/api/governance/dashboard/audit/export",
        json={
            "format": "json",
            "filter_params": {"country_code": "AU", "include_history": True, "legal_hold": True},
            "record_ids": [],
        },
    )
    assert response.status_code == 202
