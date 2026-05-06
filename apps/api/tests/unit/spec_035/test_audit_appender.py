"""Unit tests for the audit-row-emission middleware (spec-035 T016)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


class _RecordingRepository:
    def __init__(self) -> None:
        self.appended: list[dict[str, Any]] = []
        self.paired: list[tuple[dict[str, Any], dict[str, Any], str]] = []

    async def append(self, row: dict[str, Any], correlation_id: str | None = None) -> dict[str, Any]:
        row = {**row, "correlationId": correlation_id, "auditId": f"id-{len(self.appended)}"}
        self.appended.append(row)
        return row

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


def _build_app(repo: _RecordingRepository) -> FastAPI:
    from app.middleware.audit_appender import add_audit_appender_middleware

    app = FastAPI()
    add_audit_appender_middleware(app, repository=repo)

    @app.middleware("http")
    async def _claims_injector(request: Request, call_next):
        request.state.claims = {
            "oid": "oid-admin" if request.headers.get("X-Persona-Role") == "admin" else "oid-user",
            "app_role": "system-administrator"
            if request.headers.get("X-Persona-Role") == "admin"
            else "incident-commander",
            "persona_id": "ic_au_east",
        }
        return await call_next(request)

    @app.post("/api/outcomes/sc-001/evaluate")
    async def _evaluate() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/health")
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_get_request_does_not_emit_audit_row():
    repo = _RecordingRepository()
    client = TestClient(_build_app(repo))
    res = client.get("/api/health")
    assert res.status_code == 200
    assert repo.appended == []
    assert repo.paired == []


def test_post_emits_single_audit_row_for_normal_user():
    repo = _RecordingRepository()
    client = TestClient(_build_app(repo))
    res = client.post("/api/outcomes/sc-001/evaluate", json={"input": "x"})
    assert res.status_code == 200

    assert len(repo.appended) == 1
    row = repo.appended[0]
    assert row["outcome"] == "approved"
    assert row["appRole"] == "incident-commander"
    assert row["personaId"] == "ic_au_east"
    assert row["impersonatedBy"] is None
    assert row["impersonatedPersonaId"] is None
    assert row["correlationId"]


def test_post_admin_direct_emits_admin_override_single_row():
    repo = _RecordingRepository()
    client = TestClient(_build_app(repo))
    res = client.post(
        "/api/outcomes/sc-001/evaluate",
        json={},
        headers={"X-Persona-Role": "admin"},
    )
    assert res.status_code == 200
    assert len(repo.appended) == 1
    assert repo.paired == []
    row = repo.appended[0]
    assert row["outcome"] == "admin_override"
    assert row["personaId"] == "*"
    assert row["impersonatedPersonaId"] is None


def test_post_with_impersonate_header_emits_paired_rows():
    repo = _RecordingRepository()
    client = TestClient(_build_app(repo))
    res = client.post(
        "/api/outcomes/sc-001/evaluate",
        json={},
        headers={
            "X-Persona-Role": "admin",
            "X-Impersonate-Persona": "logistics_au_east",
            "X-Correlation-Id": "cid-q9",
        },
    )
    assert res.status_code == 200
    assert repo.appended == []
    assert len(repo.paired) == 1
    op, tgt, cid = repo.paired[0]
    assert cid == "cid-q9"
    assert op["outcome"] == "admin_override"
    assert op["personaId"] == "*"
    assert op["impersonatedPersonaId"] == "logistics_au_east"
    assert tgt["personaId"] == "logistics_au_east"
    assert tgt["impersonatedBy"] == "oid-admin"


def test_request_hash_is_sha256_of_body():
    import hashlib

    repo = _RecordingRepository()
    client = TestClient(_build_app(repo))
    payload = b'{"x":1}'
    expected = hashlib.sha256(payload).hexdigest()
    res = client.post(
        "/api/outcomes/sc-001/evaluate",
        content=payload,
        headers={"content-type": "application/json"},
    )
    assert res.status_code == 200
    assert repo.appended[0]["requestHash"] == expected


def test_correlation_id_falls_back_to_uuid_when_header_absent():
    repo = _RecordingRepository()
    client = TestClient(_build_app(repo))
    client.post("/api/outcomes/sc-001/evaluate", json={})
    cid = repo.appended[0]["correlationId"]
    assert cid and "-" in cid
