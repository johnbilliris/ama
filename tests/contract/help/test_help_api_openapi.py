"""spec-038 T-AA182 — verify FastAPI surface matches OpenAPI contract."""

from __future__ import annotations

from pathlib import Path

import yaml
from app.api.routes.help_articles import router as articles_router
from app.api.routes.help_chat import router as chat_router
from app.api.routes.help_screenshots import router as screenshots_router
from app.api.routes.help_search import router as search_router
from app.api.routes.help_snapshots import router as snapshots_router
from app.api.routes.help_support_handoff import router as handoff_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

CONTRACT = Path(__file__).resolve().parents[3] / "specs/038-help-docs-chat/contracts/help-api.openapi.yaml"


def _app() -> FastAPI:
    a = FastAPI()
    for r in (chat_router, articles_router, snapshots_router, screenshots_router, search_router, handoff_router):
        a.include_router(r)
    return a


def test_every_contract_path_has_a_route() -> None:
    spec = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    expected = set(spec.get("paths", {}).keys())
    actual = set(_app().openapi()["paths"].keys())
    # paths in contract are listed without the /api/v1 prefix
    missing = []
    for ep in expected:
        # screenshot signed URL is `/help/screenshots/{screenId}/url`; FastAPI uses `{screen_id}` etc.
        # normalise braces
        norm = (
            ep.replace("{screenId}", "{screen_id}")
            .replace("{sessionId}", "{session_id}")
            .replace("{snapshotId}", "{snapshot_id}")
            .replace("{flagId}", "{flag_id}")
        )
        if norm not in actual:
            missing.append(ep)
    assert not missing, f"OpenAPI paths missing from FastAPI app: {missing}"


def test_app_openapi_generates() -> None:
    c = TestClient(_app())
    j = c.get("/openapi.json")
    assert j.status_code == 200
    schema = j.json()
    assert any(p.startswith("/help/") for p in schema["paths"]), "no /help paths in app openapi"
