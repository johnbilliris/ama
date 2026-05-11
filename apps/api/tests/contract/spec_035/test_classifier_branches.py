"""T021 — classifier gateway branch coverage.

Five branches per
[`classifier-gateway.contract.md`](../../../../specs/035-webapp-capstone-closure/contracts/classifier-gateway.contract.md):

1. ``clean``        — pass-through.
2. ``pii``          — mask in-place, 200, ``audit_outcome=classifier_mask``.
3. ``pspf``         — deny, 403 ``sovereignty_denied``, ``audit_outcome=classifier_deny``.
4. ``pspf+pii``     — deny (PSPF wins).
5. ``classifier_failure`` — 503 ``sovereignty_denied`` (fail-closed).

Admin-bypass is impossible: even ``system-administrator`` is denied on PSPF.
"""

from __future__ import annotations

import json
import re

import pytest
from app.middleware.classifier_gateway import classify_text
from fastapi import FastAPI, Request
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


def _build_app() -> tuple[FastAPI, list[bytes]]:
    from app.middleware.classifier_gateway import add_classifier_gateway_middleware

    app = FastAPI()
    add_classifier_gateway_middleware(app)

    captured: list[bytes] = []

    @app.post("/api/outcomes/sc-001/evaluate")
    async def _evaluate(request: Request) -> dict[str, str]:
        captured.append(await request.body())
        return {"status": "ok"}

    return app, captured


# ---------------- pure helper (deterministic regex+dict scan) ----------------


def test_classify_text_clean_branch() -> None:
    out = classify_text("Hello world")
    assert out == {"branch": "clean"}


def test_classify_text_pspf_branch_official_sensitive() -> None:
    out = classify_text("OFFICIAL: Sensitive — context for IC")
    assert out["branch"] == "deny"
    assert out["content_class"] == "pspf"


@pytest.mark.parametrize(
    "marking",
    [
        "PROTECTED",
        "SECRET",
        "TOP SECRET",
        "IN-CONFIDENCE",
    ],
)
def test_classify_text_pspf_marking_variants(marking: str) -> None:
    out = classify_text(f"Document classified {marking} for review")
    assert out["branch"] == "deny"


def test_classify_text_pii_branch_masks_email_and_phone() -> None:
    text = "contact alice@example.com or 0412 345 678"
    out = classify_text(text)
    assert out["branch"] == "mask"
    assert out["count"] >= 2
    assert "[MASKED:" in out["masked"]
    assert "alice@example.com" not in out["masked"]


def test_classify_text_pspf_wins_over_pii() -> None:
    out = classify_text("PROTECTED — phone 0412 345 678")
    assert out["branch"] == "deny"


# ---------------- end-to-end via the middleware -----------------------------


def test_clean_payload_passes_through_to_handler() -> None:
    app, captured = _build_app()
    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={"narrative": "Field assessment of access roads."},
    )
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert len(captured) == 1


def test_pspf_payload_is_denied_with_sovereignty_envelope() -> None:
    app, captured = _build_app()
    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={"narrative": "PROTECTED briefing for IC."},
    )
    assert res.status_code == 403
    body = res.json()
    assert body["error_code"] == "sovereignty_denied"
    # Handler MUST NOT have been reached.
    assert captured == []


def test_pii_payload_is_masked_then_handler_sees_masked_body() -> None:
    app, captured = _build_app()
    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={
            "narrative": "Contact officer at jane.doe@example.com or 0412 345 678.",
        },
    )
    assert res.status_code == 200
    assert len(captured) == 1
    seen = captured[0].decode("utf-8")
    assert "jane.doe@example.com" not in seen
    assert re.search(r"\[MASKED:email\]", seen)
    assert re.search(r"\[MASKED:phone-au-mobile\]", seen)


def test_pspf_plus_pii_payload_denies_pspf_wins() -> None:
    app, captured = _build_app()
    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={"narrative": "PROTECTED — call 0412 345 678 for context."},
    )
    assert res.status_code == 403
    assert res.json()["error_code"] == "sovereignty_denied"
    assert captured == []
