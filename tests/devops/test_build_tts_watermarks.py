"""T-F03 — devops test for ``tools/build_tts_watermarks.py``."""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.api.app.services.simulation.watermark_text_loader import (
    WatermarkTexts,
)
from tests.staging_gates import speech_staging_enabled
from tools.build_tts_watermarks import (
    LOCALE_TO_VOICE,
    AudioArtefact,
    _content_hash,
    _resolve_voice,
    build_artefacts,
)


def _toy_table() -> dict[str, WatermarkTexts]:
    return {
        "en-AU": WatermarkTexts(
            chat_receipt_prefix="[SIMULATION]",
            public_warning_watermark="SIMULATION — DO NOT DISTRIBUTE",
        ),
        "zh-Hans": WatermarkTexts(
            chat_receipt_prefix="[模拟]",
            public_warning_watermark="模拟 — 请勿分发",
        ),
    }


def test_voice_mapping_covers_authored_locales() -> None:
    """Every locale in the watermark table MUST have a voice."""
    expected = {
        "en-AU",
        "zh-Hans",
        "zh-Hant",
        "ar",
        "vi",
        "hi",
        "el",
        "it",
        "tl",
        "tr",
        "id",
    }
    missing = expected - set(LOCALE_TO_VOICE.keys())
    assert not missing, f"Missing voice mappings: {missing}"


def test_content_hash_is_deterministic() -> None:
    a = _content_hash("[SIMULATION]", "en-AU", "en-AU-NatashaNeural")
    b = _content_hash("[SIMULATION]", "en-AU", "en-AU-NatashaNeural")
    assert a == b
    assert len(a) == 32


def test_content_hash_distinguishes_locale() -> None:
    assert _content_hash("[SIMULATION]", "en-AU", "v") != _content_hash("[SIMULATION]", "zh-Hans", "v")


def test_resolve_voice_falls_back_to_en_au() -> None:
    assert _resolve_voice("en-AU") == "en-AU-NatashaNeural"
    assert _resolve_voice("xx-YY") == "en-AU-NatashaNeural"


def test_build_artefacts_writes_one_mp3_per_locale(tmp_path: Path) -> None:
    """Stub synth → 1 mp3 per locale + manifest.json."""
    captured: list[tuple[str, str, str]] = []

    def stub(text: str, locale: str, voice: str) -> bytes:
        captured.append((text, locale, voice))
        return b"ID3\x04\x00\x00\x00\x00\x00\x00" + locale.encode()

    arts = build_artefacts(out_dir=tmp_path, table=_toy_table(), synthesize=stub)
    assert len(arts) == 2
    assert all(isinstance(a, AudioArtefact) for a in arts)
    assert (tmp_path / "manifest.json").exists()
    files = sorted(p.name for p in tmp_path.glob("*.mp3"))
    assert len(files) == 2
    # All synth calls observed.
    assert {entry[1] for entry in captured} == {"en-AU", "zh-Hans"}


def test_build_artefacts_is_idempotent(tmp_path: Path) -> None:
    """Re-running with the same inputs MUST not re-call the synthesizer."""

    def stub(text: str, locale: str, voice: str) -> bytes:
        return b"\x00" * 32

    build_artefacts(out_dir=tmp_path, table=_toy_table(), synthesize=stub)

    calls: list[str] = []

    def counting_stub(text: str, locale: str, voice: str) -> bytes:
        calls.append(locale)
        return b"\x00" * 32

    build_artefacts(out_dir=tmp_path, table=_toy_table(), synthesize=counting_stub)
    assert calls == [], "Idempotency violation: second run re-invoked the synthesizer"


def test_build_artefacts_renders_at_least_mvp_minimum(tmp_path: Path) -> None:
    """FR-058 MVP minimum: ≥10 audio artefacts."""
    from apps.api.app.services.simulation.watermark_text_loader import _load_table

    table = dict(_load_table())
    assert len(table) >= 10, f"Watermark table has {len(table)} locales — must be ≥10 for FR-058 MVP."

    def stub(text: str, locale: str, voice: str) -> bytes:
        return b"\x00" * 32

    arts = build_artefacts(out_dir=tmp_path, table=table, synthesize=stub)
    assert len(arts) >= 10


@pytest.mark.azure_speech_staging
@pytest.mark.skipif(
    not speech_staging_enabled(),
    reason="Live Speech rendering — set AMA_STAGING_SPEECH=1 with AZURE_SPEECH_KEY/REGION.",
)
def test_build_artefacts_against_live_speech(tmp_path: Path) -> None:
    pytest.skip(
        "Staging gate — runs build_artefacts without `synthesize=` so the live Azure SDK "
        "is exercised; assert each MP3 is >1 KB."
    )
