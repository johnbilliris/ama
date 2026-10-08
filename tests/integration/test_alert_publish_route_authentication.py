from __future__ import annotations

from app.api.routes.alerts import router
from app.services.public_alert_service import compute_alert_binding_sha256, stamp_alert_content_version
from app.services.state_store import ALERTS, APPROVALS, reset_state
from fastapi import FastAPI
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.public_alert import PublicAlert


def _seed_publishable_alert() -> None:
    alert = PublicAlert(
        alert_id="alert-auth",
        incident_id="incident-1",
        status="approved",
        audience_segments=["affected-community"],
        languages=["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
        channel_set=["sms"],
        content_blocks={
            "headline": "Act now",
            "body": "Leave now.",
            "en-AU": "Act now",
            "zh-Hans": "立即行动",
            "ar": "تحرك الآن",
            "vi": "Hanh dong ngay",
            "el": "Energiste tora",
            "it": "Agisci ora",
        },
        content_safety_result="passed",
    )
    stamp_alert_content_version(alert)
    ALERTS["alert-auth"] = alert
    APPROVALS["decision-auth"] = ApprovalDecision(
        approval_decision_id="decision-auth",
        public_alert_id="alert-auth",
        approver_persona_id="persona-approver",
        outcome="approved",
        rationale="approved",
        conditions=[
            f"contentVersion={alert.content_blocks['contentVersion']}",
            f"bindingSha256={compute_alert_binding_sha256(alert)}",
        ],
    )


def _client(claims: dict | None) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")

    @app.middleware("http")
    async def _inject_claims(request, call_next):  # type: ignore[no-untyped-def]
        request.state.claims = claims or {}
        return await call_next(request)

    return TestClient(app)


def test_publish_requires_authenticated_persona_claim() -> None:
    reset_state()
    _seed_publishable_alert()
    client = _client(claims={"sub": "user-1"})

    response = client.post("/api/alerts/alert-auth/publish", json={})

    assert response.status_code == 401


def test_publish_rejects_body_actor_mismatch() -> None:
    reset_state()
    _seed_publishable_alert()
    client = _client(claims={"sub": "user-1", "persona_id": "persona-live"})

    response = client.post(
        "/api/alerts/alert-auth/publish",
        json={"publishedByPersonaId": "spoofed-persona"},
    )

    assert response.status_code == 403


def test_publish_uses_authenticated_actor_identity() -> None:
    reset_state()
    _seed_publishable_alert()
    client = _client(claims={"sub": "user-1", "personaId": "persona-live"})

    response = client.post("/api/alerts/alert-auth/publish", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["content_blocks"]["publishedBy"] == "persona-live"
    assert body["content_blocks"]["approvalDecisionId"] == "decision-auth"
