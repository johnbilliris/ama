"""T019 — APIM-fronted rate-limit triggers Q10 envelope with Retry-After.

The contract:
* APIM signals rate-limit on the response with header ``X-Rate-Limit-Triggered: 1``.
* Middleware rewrites the response body to a Q10 ``rate_limited`` envelope.
* HTTP status is 429.
* ``Retry-After`` header equals the envelope's ``retry_after_seconds`` field.
* The audit row records ``outcome=rate_limited``.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _enable_production_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    monkeypatch.setenv(
        "AMA_ENTRA_TEST_PRINCIPAL",
        json.dumps(
            {
                "oid": "00000000-0000-0000-0000-000000000001",
                "sub": "00000000-0000-0000-0000-000000000001",
                "app_role": "incident-commander",
                "roles": ["incident-commander"],
                "persona_id": "incident-commander",
            }
        ),
    )


def _build_app(retry_after_seconds: int = 30) -> FastAPI:
    from app.middleware.rate_limit_audit import add_rate_limit_audit_middleware

    app = FastAPI()
    add_rate_limit_audit_middleware(app)

    @app.post("/api/outcomes/sc-001/evaluate")
    async def _evaluate(request: Request) -> JSONResponse:
        return JSONResponse(
            content={"status": "ok"},
            status_code=200,
            headers={"X-Rate-Limit-Triggered": "1", "Retry-After": str(retry_after_seconds)},
        )

    return app


def test_rate_limit_triggers_q10_envelope_with_correct_status_and_retry_after() -> None:
    app = _build_app(retry_after_seconds=42)
    client = TestClient(app)

    res = client.post("/api/outcomes/sc-001/evaluate", json={})

    assert res.status_code == 429
    assert res.headers.get("Retry-After") == "42"

    body = res.json()
    assert body["error_code"] == "rate_limited"
    assert body["retry_after_seconds"] == 42
    assert body["audit_id"]
    assert body["correlation_id"]


def test_rate_limit_envelope_body_is_byte_equal_to_serialised_extension_envelope() -> None:
    from app.schemas.extension_envelope import ExtensionEnvelope

    app = _build_app(retry_after_seconds=15)
    res = TestClient(app).post("/api/outcomes/sc-001/evaluate", json={})

    body = res.json()
    parsed = ExtensionEnvelope.model_validate(body)
    assert parsed.error_code.value == "rate_limited"
    assert parsed.retry_after_seconds == 15
    # Round-trip equality.
    assert json.loads(parsed.model_dump_json()) == body


def test_clean_response_passes_through_unchanged_when_header_absent() -> None:
    from app.middleware.rate_limit_audit import add_rate_limit_audit_middleware

    app = FastAPI()
    add_rate_limit_audit_middleware(app)

    @app.get("/api/health")
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    res = TestClient(app).get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert "Retry-After" not in res.headers
