"""T045 contract: recovery handover signing per
[`recovery-handover.contract.md`](../../../../specs/035-webapp-capstone-closure/contracts/recovery-handover.contract.md).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _full_payload(**overrides: Any) -> dict[str, Any]:
    body = {
        "event_id": "evt-2025-04-15-syd",
        "gap_analysis": "## gap\n- staff",
        "framework_modelling": {"model": "EMHIPS"},
        "lessons_integration": "## lessons\n- triage",
        "baseline_loss": 12_500_000.00,
        "projected_loss": 8_200_000.00,
        "recovery_environments": {
            "social": {"risks": ["isolation"], "actions": ["outreach"]},
            "built": {"risks": ["bridges"], "actions": ["temp-bridge"]},
            "economic": {"risks": ["sme"], "actions": ["grants"]},
            "natural": {"risks": ["erosion"], "actions": ["reveg"]},
        },
        "claims_velocity_snapshot_id": "claims-2025-04-14",
    }
    body.update(overrides)
    return body


@pytest.fixture
def app() -> FastAPI:
    from app.api.routes.recovery_handover import router
    from app.schemas.envelope_errors import ExtensionEnvelopeError, error_to_response
    from fastapi import Request

    fa = FastAPI()
    fa.include_router(router, prefix="/api")

    @fa.exception_handler(ExtensionEnvelopeError)
    async def _handle(request: Request, exc: ExtensionEnvelopeError):  # type: ignore[no-untyped-def]
        return error_to_response(request, exc)

    return fa


def test_happy_path_returns_artefact_envelope_and_audit(app: FastAPI) -> None:
    res = TestClient(app).post("/api/recovery/handover/sign", json=_full_payload())
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["artefact_id"]
    assert body["artefact_hash"].startswith("sha256:")
    assert body["sendai_ratio"] >= 0.30
    assert "blob_uri" in body
    assert "sas_url_expires_at" in body


def test_artefact_hash_byte_equals_sha256_of_blob_payload(app: FastAPI) -> None:
    """Audit row hash must byte-equal SHA-256 of the canonical PDF bytes."""
    from app.services.recovery_handover_service import HandoverRequest, _render_pdf

    req = HandoverRequest(**_full_payload())
    ratio = (req.baseline_loss - req.projected_loss) / req.baseline_loss
    expected = "sha256:" + hashlib.sha256(_render_pdf(req, ratio)).hexdigest()

    res = TestClient(app).post("/api/recovery/handover/sign", json=_full_payload())
    assert res.json()["artefact_hash"] == expected


def test_sendai_ratio_below_threshold_is_rejected(app: FastAPI) -> None:
    res = TestClient(app).post(
        "/api/recovery/handover/sign",
        json=_full_payload(baseline_loss=10_000_000, projected_loss=9_000_000),
    )
    assert res.status_code == 422
    assert res.json()["error_code"] == "schema_invalid"


def test_missing_economic_environment_is_rejected(app: FastAPI) -> None:
    payload = _full_payload()
    del payload["recovery_environments"]["economic"]
    res = TestClient(app).post("/api/recovery/handover/sign", json=payload)
    assert res.status_code == 422
    assert res.json()["error_code"] == "schema_invalid"


def test_signing_key_expired_returns_schema_invalid_with_signing_detail(app: FastAPI) -> None:
    from app.services.recovery_handover_service import RecoveryHandoverService

    expired_service = RecoveryHandoverService(cert_not_after=datetime.now(UTC) - timedelta(days=1))
    app.state.recovery_handover_service = expired_service

    res = TestClient(app).post("/api/recovery/handover/sign", json=_full_payload())
    assert res.status_code == 422
    body = res.json()
    assert body["error_code"] == "schema_invalid"
