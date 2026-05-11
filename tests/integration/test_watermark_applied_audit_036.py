"""Spec-036 Wave 4 — T-P04 watermark audit envelope integration.

Verifies that :func:`embed_with_audit` emits the canonical
``audit.watermark.applied`` envelope (audit-envelope.md §3.14a)
alongside the watermarked text, with all required fields populated:

* ``artefact_id``
* ``delivery_channel`` ∈ {audio, text-live-log, both}
* ``resolved_locale`` (post-fallback)
* ``watermark_text_hash`` (64-char hex SHA-256 of the embedded text)

Per Q6 the same locale table services both the text-live-log and
audio-prefix delivery channels, so the audit entry MUST capture the
discriminator so the two pathways can be correlated.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from apps.api.app.services.simulation.public_warning_watermark_guard import (
    WatermarkAuditResult,
    embed_with_audit,
)

SIM_ID = "11111111-2222-3333-4444-aaaaaaaaaaaa"


@pytest.mark.parametrize("channel", ["audio", "text-live-log", "both"])
def test_embed_with_audit_emits_canonical_envelope(channel: str) -> None:
    captured: dict[str, Any] = {}

    async def _fake_write(entry_type: str, **kwargs: Any) -> None:
        captured["entry_type"] = entry_type
        captured.update(kwargs)

    fake_writer = AsyncMock()
    fake_writer.write = _fake_write

    async def _run() -> WatermarkAuditResult:
        with patch(
            "apps.api.app.services.simulation.audit_writer.get_audit_writer",
            return_value=fake_writer,
        ):
            return await embed_with_audit(
                "Bushfire warning — leave now.",
                locale="en-AU",
                artefact_id="art-warn-1",
                delivery_channel=channel,  # type: ignore[arg-type]
                simulation_id=SIM_ID,
            )

    result = asyncio.new_event_loop().run_until_complete(_run())
    assert result.audit_emitted is True
    assert captured["entry_type"] == "audit.watermark.applied"
    assert captured["simulation_id"] == SIM_ID
    details = captured["details"]
    assert details["artefact_id"] == "art-warn-1"
    assert details["delivery_channel"] == channel
    assert details["resolved_locale"] == "en-AU"
    # 64-hex SHA-256 hash invariant.
    assert len(details["watermark_text_hash"]) == 64
    assert all(c in "0123456789abcdef" for c in details["watermark_text_hash"])


def test_embed_with_audit_records_locale_fallback() -> None:
    captured: dict[str, Any] = {}

    async def _fake_write(entry_type: str, **kwargs: Any) -> None:
        captured["entry_type"] = entry_type
        captured.update(kwargs)

    fake_writer = AsyncMock()
    fake_writer.write = _fake_write

    async def _run() -> WatermarkAuditResult:
        with patch(
            "apps.api.app.services.simulation.audit_writer.get_audit_writer",
            return_value=fake_writer,
        ):
            return await embed_with_audit(
                "Storm tide — move to higher ground.",
                locale="zz-XX",  # unknown locale → falls back to en-AU
                artefact_id="art-warn-2",
                delivery_channel="both",
                simulation_id=SIM_ID,
            )

    result = asyncio.new_event_loop().run_until_complete(_run())
    assert result.locale_fell_back is True
    # Resolved locale MUST be the fallback (not the requested one).
    assert captured["details"]["resolved_locale"] == "en-AU"


def test_embed_with_audit_does_not_block_on_audit_failure() -> None:
    """Per Primacy of Life — audit failure MUST NOT prevent rendering."""

    async def _exploding_write(*_: Any, **__: Any) -> None:
        raise RuntimeError("audit channel down")

    fake_writer = AsyncMock()
    fake_writer.write = _exploding_write

    async def _run() -> WatermarkAuditResult:
        with patch(
            "apps.api.app.services.simulation.audit_writer.get_audit_writer",
            return_value=fake_writer,
        ):
            return await embed_with_audit(
                "Earthquake — drop, cover, hold.",
                locale="en-AU",
                artefact_id="art-warn-3",
                delivery_channel="text-live-log",
                simulation_id=SIM_ID,
            )

    result = asyncio.new_event_loop().run_until_complete(_run())
    # Caller still gets the watermark.
    assert "DO NOT DISTRIBUTE" in result.watermark
    # But audit was best-effort and failed — flag is False.
    assert result.audit_emitted is False
