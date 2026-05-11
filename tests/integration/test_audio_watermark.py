"""T-F04 — audio watermark integration test."""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.audio_watermark_service import (
    AudioPrefix,
    AudioPrefixCatalog,
    AudioWatermarkService,
    starts_with_prefix,
)
from tests.staging_gates import speech_staging_enabled


def _catalog() -> AudioPrefixCatalog:
    return AudioPrefixCatalog(
        prefixes={
            "en-AU": AudioPrefix(
                locale="en-AU",
                content_hash="abc123",
                audio_bytes=b"AUDIO_PREFIX_EN_AU__",
            ),
            "zh-Hans": AudioPrefix(
                locale="zh-Hans",
                content_hash="def456",
                audio_bytes=b"AUDIO_PREFIX_ZH_HANS__",
            ),
        }
    )


@pytest.mark.asyncio
async def test_audio_starts_with_locale_correct_prefix() -> None:
    svc = AudioWatermarkService(catalog=_catalog())
    body = b"BODY_AUDIO_BYTES"
    result = await svc.apply(body_audio=body, locale="zh-Hans", simulation_id="sim-x")

    assert result.prefix_locale == "zh-Hans"
    assert result.fallback_applied is False
    assert result.audio_bytes.startswith(b"AUDIO_PREFIX_ZH_HANS__")
    assert result.audio_bytes.endswith(b"BODY_AUDIO_BYTES")
    assert starts_with_prefix(result.audio_bytes, _catalog().prefixes["zh-Hans"])


@pytest.mark.asyncio
async def test_missing_locale_falls_back_and_emits_audit() -> None:
    audits: list[dict] = []

    async def writer(**kwargs):
        audits.append(kwargs)

    svc = AudioWatermarkService(catalog=_catalog(), audit_writer=writer)
    result = await svc.apply(body_audio=b"BODY", locale="xx-YY", simulation_id="sim-y")

    assert result.fallback_applied is True
    assert result.prefix_locale == "en-AU"
    assert audits == [
        {
            "locale": "xx-YY",
            "pathway": "audio",
            "fallback_applied": "en-AU",
            "simulation_id": "sim-y",
        }
    ]


@pytest.mark.asyncio
async def test_audio_watermark_byte_deterministic() -> None:
    """Same inputs MUST produce byte-identical output (concatenation invariant)."""
    svc = AudioWatermarkService(catalog=_catalog())
    a = await svc.apply(body_audio=b"X", locale="en-AU")
    b = await svc.apply(body_audio=b"X", locale="en-AU")
    assert a.audio_bytes == b.audio_bytes


@pytest.mark.asyncio
async def test_completely_empty_catalog_raises() -> None:
    svc = AudioWatermarkService(catalog=AudioPrefixCatalog(prefixes={}))
    with pytest.raises(RuntimeError, match="default locale missing"):
        await svc.apply(body_audio=b"X", locale="ar")


@pytest.mark.azure_speech_staging
@pytest.mark.skipif(
    not speech_staging_enabled(),
    reason="Live Speech — set AMA_STAGING_SPEECH=1 to run end-to-end against staging.",
)
def test_audio_watermark_against_live_tts_rendering() -> None:
    pytest.skip("Staging gate — invoke against live Speech-rendered prefixes.")
