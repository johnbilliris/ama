from __future__ import annotations

import base64
import json
from collections.abc import Callable

import pytest
from app.api.dependencies import governance_composition as governance_composition_module
from app.api.dependencies.governance_composition import ensure_governance_seed_loaded
from app.main import create_app
from app.services.public_alert_service import compute_alert_binding_sha256, stamp_alert_content_version
from app.services.state_store import ALERTS, APPROVALS, RECOMMENDATIONS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.approval_decision import ApprovalDecision
from packages.domain.src.domain.models.public_alert import PublicAlert
from packages.domain.src.domain.models.recommendation import Recommendation


@pytest.fixture(autouse=True)
def _reset_governance_composition(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(governance_composition_module, "_DEFAULT_COMPOSITION", None)


@pytest.fixture
def production_auth_headers(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, object]], dict[str, str]]:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "tenant-test")
    monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://ama-test")
    monkeypatch.setenv("API_PROXY_UPSTREAM", "https://api.internal.example")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)

    from app.middleware import entra_auth

    principal: dict[str, object] = {
        "sub": "principal-default",
        "roles": ["incident-commander"],
        "app_role": "incident-commander",
        "persona_id": "persona-default",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
    }

    def _fake_validate(_token: str) -> dict[str, object]:
        return dict(principal)

    monkeypatch.setattr(entra_auth, "_validate_jwt", _fake_validate)

    def _set_principal(overrides: dict[str, object]) -> dict[str, str]:
        principal.update(overrides)
        return {"Authorization": "Bearer synthetic"}

    return _set_principal


def _seed_operational_records() -> None:
    RECOMMENDATIONS["rec-authz"] = Recommendation(
        recommendation_id="rec-authz",
        incident_id="incident-authz",
        type="public_alert",
        summary="Issue warning",
        explanation="risk",
        supporting_signal_ids=[],
        required_approval_level="incident_commander",
    )
    alert = PublicAlert(
        alert_id="alert-authz",
        incident_id="incident-authz",
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
    ALERTS["alert-authz"] = alert
    APPROVALS["approval-authz"] = ApprovalDecision(
        approval_decision_id="approval-authz",
        public_alert_id="alert-authz",
        approver_persona_id="persona-incident-commander",
        outcome="approved",
        rationale="approved",
        conditions=[
            f"contentVersion={alert.content_blocks['contentVersion']}",
            f"bindingSha256={compute_alert_binding_sha256(alert)}",
        ],
    )


def _forwarded_claims_header(role: str = "incident-commander") -> dict[str, str]:
    claims = {
        "sub": "user-001",
        "agency_id": "ses-nsw",
        "jurisdiction_ids": ["nsw"],
        "roles": [role],
        "persona_id": "persona-incident-commander",
    }
    encoded = base64.b64encode(json.dumps(claims).encode("utf-8")).decode("utf-8")
    return {"X-MS-CLIENT-PRINCIPAL": encoded}


def test_forged_forwarded_principal_is_rejected_in_production(monkeypatch) -> None:
    reset_state()
    _seed_operational_records()
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv("AMA_TRUST_FORWARDED_PRINCIPAL", "1")
    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")

    client = TestClient(create_app())
    response = client.post(
        "/api/alerts/alert-authz/publish",
        json={"publishedByPersonaId": "persona-incident-commander"},
        headers=_forwarded_claims_header(),
    )

    assert response.status_code == 401
    assert ALERTS["alert-authz"].status == "approved"


def test_production_ignores_test_principal_fallback(monkeypatch) -> None:
    reset_state()
    _seed_operational_records()
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv(
        "AMA_ENTRA_TEST_PRINCIPAL",
        json.dumps(
            {
                "sub": "user-001",
                "roles": ["incident-commander"],
                "persona_id": "persona-incident-commander",
                "agency_id": "ses-nsw",
                "jurisdiction_ids": ["nsw"],
            }
        ),
    )

    client = TestClient(create_app())
    response = client.post(
        "/api/alerts/alert-authz/publish",
        json={"publishedByPersonaId": "persona-incident-commander"},
    )

    assert response.status_code == 401
    assert ALERTS["alert-authz"].status == "approved"


def test_wrong_role_cannot_approve_recommendation(monkeypatch) -> None:
    reset_state()
    _seed_operational_records()
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")

    from app.middleware import entra_auth

    def _fake_validate_jwt(_token: str) -> dict[str, object]:
        return {
            "sub": "user-002",
            "roles": ["public-information-officer"],
            "persona_id": "persona-public-info",
            "agency_id": "ses-nsw",
            "jurisdiction_ids": ["nsw"],
        }

    monkeypatch.setattr(entra_auth, "_validate_jwt", _fake_validate_jwt)

    client = TestClient(create_app())
    response = client.post(
        "/api/recommendations/rec-authz/approvals",
        json={
            "approverPersonaId": "persona-public-info",
            "outcome": "approved",
            "rationale": "attempt",
        },
        headers={"Authorization": "Bearer synthetic"},
    )

    assert response.status_code == 403
    assert RECOMMENDATIONS["rec-authz"].status == "proposed"


def test_aud001_anonymous_governance_dashboard_is_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv("AMA_ENTRA_TENANT_ID", "tenant-test")
    monkeypatch.setenv("AMA_ENTRA_AUDIENCE", "api://ama-test")
    monkeypatch.setenv("API_PROXY_UPSTREAM", "https://api.internal.example")

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/governance/dashboard")
    assert response.status_code == 401


def test_aud001_governance_read_write_roles_and_no_side_effects(
    production_auth_headers: Callable[[dict[str, object]], dict[str, str]],
) -> None:
    app = create_app()
    with TestClient(app) as client:
        read_headers = production_auth_headers(
            {
                "sub": "reader-1",
                "roles": ["incident-commander"],
                "app_role": "incident-commander",
            }
        )
        baseline = client.get("/api/governance/dashboard", headers=read_headers)
        assert baseline.status_code == 200
        baseline_total = baseline.json()["summary"]["total_sources"]

        denied = client.post(
            "/api/data-sources",
            headers=read_headers,
            json={
                "name": "Denied Source",
                "kind": "authoritative",
                "sub_category": "weather_climate",
                "provider": "BoM",
                "collection_method": "api_pull",
                "data_type": "geojson",
                "update_frequency": "5_minutes",
                "geographic_coverage": "nsw",
                "trust_tier": "tier_1_authoritative_government",
            },
        )
        assert denied.status_code == 403

        after = client.get("/api/governance/dashboard", headers=read_headers)
        assert after.status_code == 200
        assert after.json()["summary"]["total_sources"] == baseline_total


def test_aud001_forged_header_and_body_actor_are_ignored(
    production_auth_headers: Callable[[dict[str, object]], dict[str, str]],
) -> None:
    app = create_app()
    with TestClient(app) as client:
        write_headers = production_auth_headers(
            {
                "sub": "governance-author",
                "roles": ["incident-commander", "governance_lead"],
                "app_role": "incident-commander",
            }
        )
        create = client.post(
            "/api/data-sources",
            headers=write_headers,
            json={
                "name": "Attributed Source",
                "kind": "authoritative",
                "sub_category": "weather_climate",
                "provider": "BoM",
                "collection_method": "api_pull",
                "data_type": "geojson",
                "update_frequency": "5_minutes",
                "geographic_coverage": "nsw",
                "trust_tier": "tier_1_authoritative_government",
            },
        )
        assert create.status_code == 201
        source_id = create.json()["data_source_id"]

        forged = dict(write_headers)
        forged["X-User-Role"] = "governance_lead"
        assessment = client.post(
            f"/api/data-sources/{source_id}/compliance",
            headers=forged,
            json={
                "principle": "life_safety_first",
                "compliance_status": "compliant",
                "explanation": "Verified by authenticated principal.",
                "assessor_id": "forged-body-actor",
                "conditions": [],
                "gaps": [],
                "triggered_by": "initial_review",
            },
        )
        assert assessment.status_code == 201
        assert assessment.json()["assessor_id"] == "governance-author"

        trail = client.get(f"/api/data-sources/{source_id}/audit", headers=write_headers)
        assert trail.status_code == 200
        created_entries = [entry for entry in trail.json() if entry["action"] == "assessment_created"]
        assert created_entries
        assert created_entries[0]["actor_id"] == "governance-author"


def test_aud001_wrong_role_and_forged_header_do_not_bypass_write(
    production_auth_headers: Callable[[dict[str, object]], dict[str, str]],
) -> None:
    app = create_app()
    with TestClient(app) as client:
        headers = production_auth_headers(
            {
                "sub": "reader-2",
                "roles": ["incident-commander"],
                "app_role": "incident-commander",
            }
        )
        forged = dict(headers)
        forged["X-User-Role"] = "governance_lead"
        response = client.post(
            "/api/data-sources",
            headers=forged,
            json={
                "name": "Blocked Source",
                "kind": "authoritative",
                "sub_category": "weather_climate",
                "provider": "BoM",
                "collection_method": "api_pull",
                "data_type": "geojson",
                "update_frequency": "5_minutes",
                "geographic_coverage": "nsw",
                "trust_tier": "tier_1_authoritative_government",
            },
        )
        assert response.status_code == 403


def test_aud010_cross_router_shared_registry_and_signal_ingestion(
    production_auth_headers: Callable[[dict[str, object]], dict[str, str]],
) -> None:
    app = create_app()
    with TestClient(app) as client:
        write_headers = production_auth_headers(
            {
                "sub": "governance-author-2",
                "roles": ["incident-commander", "governance_lead"],
                "app_role": "incident-commander",
            }
        )
        create = client.post(
            "/api/data-sources",
            headers=write_headers,
            json={
                "name": "Shared Runtime Source",
                "kind": "authoritative",
                "sub_category": "weather_climate",
                "provider": "BoM",
                "collection_method": "api_pull",
                "data_type": "geojson",
                "update_frequency": "5_minutes",
                "geographic_coverage": "nsw",
                "trust_tier": "tier_1_authoritative_government",
            },
        )
        assert create.status_code == 201
        source_id = create.json()["data_source_id"]

        compliance = client.get(f"/api/data-sources/{source_id}/compliance", headers=write_headers)
        assert compliance.status_code == 200

        governance = client.get(f"/api/data-sources/{source_id}/governance", headers=write_headers)
        assert governance.status_code == 200

        ingest = client.post(
            "/api/signals",
            headers=write_headers,
            json={
                "source": {
                    "dataSourceId": source_id,
                    "name": "BoM",
                    "kind": "authoritative",
                },
                "incidentId": "incident-aud010",
                "category": "weather",
                "occurredAt": "2026-03-09T00:00:00Z",
                "receivedAt": "2026-03-09T00:05:00Z",
                "jurisdictionId": "nsw",
                "location": {
                    "type": "Point",
                    "coordinates": [151.2, -33.8],
                    "precisionMeters": 100,
                },
                "payload": {"warning": "Major flood warning"},
                "confidenceScore": 0.95,
                "freshnessScore": 0.9,
                "validationStatus": "validated",
                "provenance": {
                    "sourceUri": "https://example.gov.au",
                    "collectionMethod": "api",
                },
            },
        )
        assert ingest.status_code == 202


def test_aud010_seed_is_idempotent_and_preserves_user_edits() -> None:
    app = create_app()

    def _seed_loader() -> list[dict[str, object]]:
        return [
            {
                "data_source_id": "seed-custom-001",
                "name": "Seed Custom",
                "kind": "authoritative",
                "sub_category": "weather_climate",
                "provider": "Original Provider",
                "collection_method": "api_pull",
                "trust_tier": "tier_1_authoritative_government",
            }
        ]

    app.state.governance_seed_loader = _seed_loader
    with TestClient(app):
        composition = app.state.governance_composition
        assert composition.seed_status.successful is True
        source = composition.registry.get_source("seed-custom-001")
        assert source.provider == "Original Provider"

        composition.registry.update_source(
            "seed-custom-001",
            {"provider": "Edited Provider"},
            actor_id="editor-user",
        )

        ensure_governance_seed_loaded(composition, seed_loader=_seed_loader)
        updated = composition.registry.get_source("seed-custom-001")
        assert updated.provider == "Edited Provider"


def test_aud010_seed_failure_retries_on_next_lifespan() -> None:
    app = create_app()
    attempts = {"count": 0}

    def _flaky_loader() -> list[dict[str, object]]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("seed loader failed")
        return [
            {
                "data_source_id": "seed-retry-001",
                "name": "Seed Retry",
                "kind": "authoritative",
                "sub_category": "weather_climate",
                "provider": "Retry Provider",
                "collection_method": "api_pull",
                "trust_tier": "tier_1_authoritative_government",
            }
        ]

    app.state.governance_seed_loader = _flaky_loader

    with TestClient(app):
        composition = app.state.governance_composition
        assert composition.seed_status.successful is False
        assert composition.seed_status.attempts == 1

    with TestClient(app):
        composition = app.state.governance_composition
        assert composition.seed_status.successful is True
        assert composition.seed_status.attempts == 2
        source = composition.registry.get_source("seed-retry-001")
        assert source.name == "Seed Retry"


def test_aud010_production_requires_durable_backend_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_GOVERNANCE_BACKEND_MODE", "durable")
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    with pytest.raises(RuntimeError, match="durable governance backend mode requires COSMOS_ENDPOINT"):
        create_app()
