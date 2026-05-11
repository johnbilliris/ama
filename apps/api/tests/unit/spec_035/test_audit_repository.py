"""Unit tests for the AuditRepository (spec-035 T015)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def _no_cosmos_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    yield


def _run(coro):
    if asyncio.iscoroutinefunction(coro):
        return asyncio.run(coro)
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.asyncio
async def test_append_assigns_audit_id_and_keeps_correlation():
    from app.repositories.audit_repository import AuditRepository

    repo = AuditRepository()
    persisted = await repo.append(
        {
            "outcome": "approved",
            "appRole": "incident-commander",
            "personaId": "ic_au_east",
            "operatorIdentity": "oid-1",
            "route": "/api/outcomes/sc-001/evaluate",
            "requestHash": "abc",
        },
        correlation_id="cid-1",
    )

    assert persisted["auditId"]
    assert persisted["id"] == persisted["auditId"]
    assert persisted["correlationId"] == "cid-1"
    assert persisted["timestamp"].endswith("Z")


@pytest.mark.asyncio
async def test_append_paired_requires_admin_override_outcome():
    from app.repositories.audit_repository import AuditRepository

    repo = AuditRepository()
    bad_op = {"outcome": "approved", "appRole": "system-administrator", "operatorIdentity": "admin"}
    target = {"outcome": "approved", "appRole": "incident-commander", "operatorIdentity": "admin"}

    with pytest.raises(ValueError):
        await repo.append_paired(bad_op, target, correlation_id="cid-2")


@pytest.mark.asyncio
async def test_append_paired_writes_two_rows_same_correlation():
    from app.repositories.audit_repository import AuditRepository

    repo = AuditRepository()

    op_row = {
        "outcome": "admin_override",
        "appRole": "system-administrator",
        "personaId": "*",
        "operatorIdentity": "admin",
        "route": "/api/outcomes/sc-001/evaluate",
        "requestHash": "h",
        "impersonatedPersonaId": "ic_au_east",
    }
    target_row = {
        "outcome": "approved",
        "appRole": "system-administrator",
        "personaId": "ic_au_east",
        "operatorIdentity": "admin",
        "impersonatedBy": "admin",
        "route": "/api/outcomes/sc-001/evaluate",
        "requestHash": "h",
    }
    op, tgt = await repo.append_paired(op_row, target_row, correlation_id="cid-paired")

    assert op["correlationId"] == "cid-paired"
    assert tgt["correlationId"] == "cid-paired"
    assert op["auditId"] != tgt["auditId"]
    assert op["outcome"] == "admin_override"
    assert tgt["impersonatedBy"] == "admin"
    assert len(repo.in_memory_rows) == 2


@pytest.mark.asyncio
async def test_append_paired_rejects_empty_correlation():
    from app.repositories.audit_repository import AuditRepository

    repo = AuditRepository()
    with pytest.raises(ValueError):
        await repo.append_paired(
            {"outcome": "admin_override"},
            {"outcome": "approved"},
            correlation_id="",
        )


@pytest.mark.asyncio
async def test_append_default_correlation_uuid_when_omitted():
    from app.repositories.audit_repository import AuditRepository

    repo = AuditRepository()
    row = await repo.append({"outcome": "approved"})
    assert row["correlationId"]
    assert "-" in row["correlationId"]
