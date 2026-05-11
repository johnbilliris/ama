"""Spec-036 Wave 4 — T-AA05 public_artefact_guard decorator tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from apps.api.app.services.simulation.public_artefact_guard import guarded_public

SIM_ID = "11111111-2222-3333-4444-aaaaaaaaaaaa"


@dataclass
class _Subject:
    user_id: str
    tenant_id: str


@guarded_public(scope="lessons_draft", audit_kind="lessons.draft.read")
async def _example_route(*, simulation_id: str, rbac_subject: Any) -> dict[str, Any]:
    return {"sim": simulation_id, "user": rbac_subject.user_id}


def test_decorator_records_metadata() -> None:
    """The decorator must annotate the wrapped function for introspection."""
    assert _example_route.__public_artefact_scope__ == "lessons_draft"  # type: ignore[attr-defined]
    assert _example_route.__public_artefact_audit_kind__ == "lessons.draft.read"  # type: ignore[attr-defined]


def test_guarded_public_emits_audit_on_success() -> None:
    captured: dict[str, Any] = {}

    async def _fake_write(entry_type: str, **kwargs: Any) -> None:
        captured["entry_type"] = entry_type
        captured.update(kwargs)

    fake_writer = AsyncMock()
    fake_writer.write = _fake_write

    async def _run() -> dict[str, Any]:
        with patch(
            "apps.api.app.services.simulation.audit_writer.get_audit_writer",
            return_value=fake_writer,
        ):
            return await _example_route(
                simulation_id=SIM_ID,
                rbac_subject=_Subject(user_id="alice", tenant_id="tenant-1"),
            )

    result = asyncio.new_event_loop().run_until_complete(_run())
    assert result == {"sim": SIM_ID, "user": "alice"}
    assert captured["entry_type"] == "lessons.draft.read"
    assert captured["simulation_id"] == SIM_ID
    assert captured["actor"].startswith("public_artefact:lessons_draft:")
    details = captured["details"]
    assert details["scope"] == "lessons_draft"
    assert details["outcome"] == "allowed"
    assert details["subject"]["user_id"] == "alice"


def test_guarded_public_requires_simulation_id_kwarg() -> None:
    @guarded_public(scope="audit_log_export", audit_kind="audit.export")
    async def _bad_route(rbac_subject: Any) -> str:
        return "ok"

    with pytest.raises(TypeError, match="simulation_id"):
        asyncio.new_event_loop().run_until_complete(
            _bad_route(rbac_subject=_Subject(user_id="alice", tenant_id="t1"))  # type: ignore[call-arg]
        )


def test_guarded_public_requires_rbac_subject_kwarg() -> None:
    @guarded_public(scope="overlay_manifest", audit_kind="overlay.manifest.read")
    async def _bad_route(*, simulation_id: str) -> str:
        return "ok"

    with pytest.raises(TypeError, match="rbac_subject"):
        asyncio.new_event_loop().run_until_complete(_bad_route(simulation_id=SIM_ID))


def test_guarded_public_accepts_sim_id_alias() -> None:
    """Routes that use ``sim_id`` (FastAPI path-param convention) work too."""

    captured: dict[str, Any] = {}

    async def _fake_write(entry_type: str, **kwargs: Any) -> None:
        captured["entry_type"] = entry_type
        captured.update(kwargs)

    fake_writer = AsyncMock()
    fake_writer.write = _fake_write

    @guarded_public(scope="overlay_manifest", audit_kind="overlay.manifest.read")
    async def _alias_route(*, sim_id: str, rbac_subject: Any) -> str:
        return sim_id

    async def _run() -> str:
        with patch(
            "apps.api.app.services.simulation.audit_writer.get_audit_writer",
            return_value=fake_writer,
        ):
            return await _alias_route(
                sim_id=SIM_ID,
                rbac_subject=_Subject(user_id="bob", tenant_id="tenant-1"),
            )

    result = asyncio.new_event_loop().run_until_complete(_run())
    assert result == SIM_ID
    assert captured["simulation_id"] == SIM_ID
    assert captured["entry_type"] == "overlay.manifest.read"
