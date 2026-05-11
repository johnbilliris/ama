"""Shared fixtures for spec-037 API contract tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def api_client():
    """FastAPI TestClient against the spec-037 evidence-pack router.

    Skips if the router has not yet been wired (T036).
    """
    pytest.importorskip("fastapi")
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.api.routes.governance import evidence_pack as evidence_pack_router  # type: ignore
    except ImportError:
        pytest.skip("evidence_pack router not yet wired (T036)")
        return None

    app = FastAPI()
    app.include_router(evidence_pack_router.router)
    return TestClient(app)
