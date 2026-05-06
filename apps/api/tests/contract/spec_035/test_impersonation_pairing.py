"""T020 — admin impersonation produces paired audit rows under one correlation_id.

When an admin token is paired with ``X-Impersonate-Persona``, the audit appender
emits exactly two rows (operator + target) sharing one correlation_id:
* operator row: ``personaId="*"``, ``outcome="admin_override"``, ``impersonatedPersonaId=<target>``.
* target row:   ``personaId=<target>``, ``impersonatedBy=<admin oid>``.

Non-admin callers presenting the header are rejected by the RBAC stack with 403.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


class _RecordingRepository:
    def __init__(self) -> None:
        self.appended: list[dict[str, Any]] = []
        self.paired: list[tuple[dict[str, Any], dict[str, Any], str]] = []

    async def append(self, row: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
        record = {**row, "correlationId": correlation_id, "auditId": f"id-{len(self.appended)}"}
        self.appended.append(record)
        return record

    async def append_paired(
        self,
        operator_row: dict[str, Any],
        target_row: dict[str, Any],
        correlation_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        op = {**operator_row, "correlationId": correlation_id, "auditId": "op"}
        tgt = {**target_row, "correlationId": correlation_id, "auditId": "tgt"}
        self.paired.append((op, tgt, correlation_id))
        return op, tgt


@pytest.fixture(autouse=True)
def _enable_production_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENABLE_PRODUCTION_AUTH", "1")


def _build_app(repo: _RecordingRepository, principal: dict[str, Any]) -> FastAPI:
    import os

    os.environ["AMA_ENTRA_TEST_PRINCIPAL"] = json.dumps(principal)

    from app.middleware.audit_appender import add_audit_appender_middleware
    from app.middleware.entra_auth import add_entra_auth_middleware
    from app.middleware.rbac_check import add_rbac_check_middleware

    app = FastAPI()
    # Innermost first.
    add_rbac_check_middleware(app)
    add_entra_auth_middleware(app)
    add_audit_appender_middleware(app, repository=repo)

    @app.post("/api/outcomes/sc-001/evaluate")
    async def _evaluate(_request: Request) -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_admin_impersonation_emits_paired_rows_in_one_correlation_id() -> None:
    repo = _RecordingRepository()
    app = _build_app(
        repo,
        {
            "oid": "admin-oid",
            "sub": "admin-oid",
            "app_role": "system-administrator",
            "roles": ["system-administrator"],
            "persona_id": "system-administrator",
        },
    )

    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={},
        headers={
            "Authorization": "Bearer test",
            "X-Impersonate-Persona": "incident-commander",
            "X-Correlation-Id": "cid-impersonation-1",
        },
    )

    assert res.status_code == 200, res.text
    assert repo.appended == []
    assert len(repo.paired) == 1, f"expected one paired write, got {len(repo.paired)}"

    operator_row, target_row, cid = repo.paired[0]
    assert cid == "cid-impersonation-1"

    assert operator_row["outcome"] == "admin_override"
    assert operator_row["personaId"] == "*"
    assert operator_row["impersonatedPersonaId"] == "incident-commander"
    assert operator_row["impersonatedBy"] is None

    assert target_row["personaId"] == "incident-commander"
    assert target_row["impersonatedBy"] == "admin-oid"
    assert target_row["impersonatedPersonaId"] is None


def test_non_admin_with_impersonation_header_is_rejected_403() -> None:
    repo = _RecordingRepository()
    app = _build_app(
        repo,
        {
            "oid": "user-oid",
            "sub": "user-oid",
            "app_role": "incident-commander",
            "roles": ["incident-commander"],
            "persona_id": "incident-commander",
        },
    )

    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={},
        headers={
            "Authorization": "Bearer test",
            "X-Impersonate-Persona": "logistics-officer",
        },
    )

    assert res.status_code == 403, res.text
    body = res.json()
    assert body["error_code"] == "forbidden"


def test_admin_direct_call_no_impersonation_emits_single_admin_override_row() -> None:
    repo = _RecordingRepository()
    app = _build_app(
        repo,
        {
            "oid": "admin-oid",
            "sub": "admin-oid",
            "app_role": "system-administrator",
            "roles": ["system-administrator"],
            "persona_id": "system-administrator",
        },
    )

    res = TestClient(app).post(
        "/api/outcomes/sc-001/evaluate",
        json={},
        headers={"Authorization": "Bearer test"},
    )

    assert res.status_code == 200
    assert repo.paired == []
    assert len(repo.appended) == 1
    row = repo.appended[0]
    assert row["outcome"] == "admin_override"
    assert row["personaId"] == "*"
    assert row["impersonatedPersonaId"] is None
