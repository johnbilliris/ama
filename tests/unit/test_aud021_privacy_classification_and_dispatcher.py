from __future__ import annotations

from datetime import UTC, datetime

from app.services.privacy_classification import classify_payload
from common.foundry_chat_client import FoundryGatewayDenied
from dispatcher.agent import create_app
from fastapi.testclient import TestClient


def test_classify_payload_rejects_unclassifiable_label() -> None:
    received_at = datetime(2026, 1, 1, tzinfo=UTC)
    try:
        classify_payload({"classification": "secret"}, received_at)
    except ValueError as exc:
        assert "classification" in str(exc)
    else:
        raise AssertionError("expected classification failure")


def test_classify_payload_rejects_pspf_secret_markings() -> None:
    received_at = datetime(2026, 1, 1, tzinfo=UTC)
    try:
        classify_payload({"note": "TOP SECRET evacuation route"}, received_at)
    except ValueError as exc:
        assert "PSPF" in str(exc)
    else:
        raise AssertionError("expected PSPF failure")


def test_dispatcher_non_au_gateway_denial_has_no_outbound(monkeypatch) -> None:
    calls = {"chat_complete": 0}

    class _FakeFoundryClient:
        def chat_complete(self, **_: object):
            calls["chat_complete"] += 1
            raise FoundryGatewayDenied("PSPF marking detected")

    monkeypatch.setattr("dispatcher.agent._build_foundry_client", lambda: _FakeFoundryClient())
    monkeypatch.setattr("dispatcher.agent._resolve_model_key", lambda: "simulation")

    client = TestClient(create_app())
    response = client.post(
        "/risk-assessment/invoke",
        json={"tenant_id": "sim-tenant-1", "question": "TOP SECRET details"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "classification-denied" in payload["summary"]
    assert calls["chat_complete"] == 1
