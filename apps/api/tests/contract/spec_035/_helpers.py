"""Shared test helpers for spec-035 production-auth contract tests.

These tests run with ``AMA_ENABLE_PRODUCTION_AUTH=1`` and use the test-principal
escape hatch (``AMA_ENTRA_TEST_PRINCIPAL``) so we can exercise the middleware
stack without hitting Entra/JWKS in CI.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI


def make_test_principal(
    *,
    role: str = "incident-commander",
    persona_id: str = "incident-commander",
    oid: str = "00000000-0000-0000-0000-000000000001",
) -> dict[str, Any]:
    return {
        "oid": oid,
        "sub": oid,
        "app_role": role,
        "roles": [role],
        "persona_id": persona_id,
    }


@contextmanager
def production_auth_env(
    monkeypatch: Any,
    principal: dict[str, Any] | None = None,
) -> Iterator[None]:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")
    if principal is None:
        principal = make_test_principal()
    monkeypatch.setenv("AMA_ENTRA_TEST_PRINCIPAL", json.dumps(principal))
    yield


def build_test_app(principal: dict[str, Any]) -> FastAPI:
    """Compose the production-auth middleware stack onto a minimal FastAPI app.

    Mirrors the stack wired in [`apps/api/app/main.py`](../../../app/main.py)
    but without lifespan dependencies.
    """
    os.environ["AMA_ENABLE_PRODUCTION_AUTH"] = "1"
    os.environ["AMA_ENTRA_TEST_PRINCIPAL"] = json.dumps(principal)

    from app.middleware.audit_appender import add_audit_appender_middleware
    from app.middleware.classifier_gateway import (
        add_classifier_gateway_middleware,
    )
    from app.middleware.entra_auth import add_entra_auth_middleware
    from app.middleware.rate_limit_audit import add_rate_limit_audit_middleware
    from app.middleware.rbac_check import add_rbac_check_middleware

    app = FastAPI()
    add_audit_appender_middleware(app)
    add_rate_limit_audit_middleware(app)
    add_rbac_check_middleware(app)
    add_entra_auth_middleware(app)
    add_classifier_gateway_middleware(app)

    @app.post("/api/outcomes/sc-001/evaluate")
    async def _evaluate() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/audit/list")
    async def _audit_list() -> dict[str, Any]:
        return {"items": []}

    @app.get("/api/auth/whoami")
    async def _whoami() -> dict[str, str]:
        return {"persona_id": principal.get("persona_id", "")}

    return app


__all__ = ["make_test_principal", "production_auth_env", "build_test_app"]
