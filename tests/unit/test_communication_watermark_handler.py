"""T-F06 — handler unit tests."""

from __future__ import annotations

import pytest

from apps.agents.communication.handler import (
    WatermarkContext,
    apply_audio_watermark,
    apply_text_watermarks,
)
from apps.api.app.services.simulation.audio_watermark_service import (
    AudioPrefix,
    AudioPrefixCatalog,
)


def test_text_handler_applies_chat_receipt_prefix_when_missing() -> None:
    ctx = WatermarkContext(locale="en-AU", simulation_id="sim-1", is_public_warning=False)
    result = apply_text_watermarks("hello", context=ctx)
    assert result.chat_receipt_prefix_applied is True
    assert result.text.startswith("[SIMULATION]")


def test_text_handler_idempotent_when_prefix_present() -> None:
    ctx = WatermarkContext(locale="en-AU", simulation_id="sim-1", is_public_warning=False)
    result = apply_text_watermarks("[SIMULATION] hello", context=ctx)
    assert result.chat_receipt_prefix_applied is False
    assert result.text == "[SIMULATION] hello"


def test_text_handler_adds_public_warning_watermark() -> None:
    ctx = WatermarkContext(locale="en-AU", simulation_id="sim-1", is_public_warning=True)
    result = apply_text_watermarks("Bushfire warning issued", context=ctx)
    assert result.public_warning_watermark_applied is True
    assert "SIMULATION — DO NOT DISTRIBUTE" in result.text


def test_text_handler_passthrough_for_non_simulation() -> None:
    ctx = WatermarkContext(locale="en-AU", is_simulation=False, is_public_warning=True)
    result = apply_text_watermarks("Real warning", context=ctx)
    assert result.text == "Real warning"
    assert result.chat_receipt_prefix_applied is False
    assert result.public_warning_watermark_applied is False


@pytest.mark.asyncio
async def test_audio_handler_applies_locale_correct_prefix() -> None:
    catalog = AudioPrefixCatalog(
        prefixes={
            "en-AU": AudioPrefix("en-AU", "abc", b"PREFIX_AU__"),
            "zh-Hans": AudioPrefix("zh-Hans", "def", b"PREFIX_ZH__"),
        }
    )
    ctx = WatermarkContext(locale="zh-Hans", simulation_id="sim-1")
    result = await apply_audio_watermark(b"BODY", context=ctx, catalog=catalog)
    assert result.prefix_applied is True
    assert result.audio_bytes.startswith(b"PREFIX_ZH__")
    assert result.fallback_locale is None


@pytest.mark.asyncio
async def test_audio_handler_falls_back_for_unknown_locale() -> None:
    catalog = AudioPrefixCatalog(
        prefixes={"en-AU": AudioPrefix("en-AU", "abc", b"PREFIX_AU__")}
    )
    ctx = WatermarkContext(locale="ar", simulation_id="sim-2")
    result = await apply_audio_watermark(b"BODY", context=ctx, catalog=catalog)
    assert result.prefix_applied is True
    assert result.audio_bytes.startswith(b"PREFIX_AU__")
    assert result.fallback_locale == "en-AU"
