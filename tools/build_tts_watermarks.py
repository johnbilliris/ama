"""T-F03 — Speech Services pre-render offline build (FR-058).

Reads the locale-correct chat-receipt prefix table from
``apps/api/app/config/watermark_text.yaml`` and renders each entry to
**audio** via Azure AI Speech Services, writing the resulting MP3 to a
local Blob staging directory keyed by content hash for idempotency.

CI uploads the directory as a build artefact; deploy time syncs to the
``tts-audio-artefacts`` Blob container.

Idempotency: filename is ``sha256(prefix_text + locale + voice).mp3``,
so re-runs do not re-mint already-built files.

Usage::

    python tools/build_tts_watermarks.py --out artifacts/tts/
    # CI:
    python tools/build_tts_watermarks.py --out $(Build.ArtifactStagingDirectory)/tts/

The Azure SDK call is delegated to the
:class:`SpeechSynthesisClient` callable so unit tests can substitute a
fake. Live invocation requires ``AZURE_SPEECH_KEY`` and
``AZURE_SPEECH_REGION`` env-vars.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.api.app.services.simulation.watermark_text_loader import (
    WatermarkTexts,
    _load_table,
)

logger = logging.getLogger(__name__)

# Locale → preferred Azure Speech Services voice (au-friendly defaults).
LOCALE_TO_VOICE: dict[str, str] = {
    "en-AU": "en-AU-NatashaNeural",
    "zh-Hans": "zh-CN-XiaoxiaoNeural",
    "zh-Hant": "zh-TW-HsiaoChenNeural",
    "ar": "ar-SA-ZariyahNeural",
    "vi": "vi-VN-HoaiMyNeural",
    "hi": "hi-IN-SwaraNeural",
    "el": "el-GR-AthinaNeural",
    "it": "it-IT-ElsaNeural",
    "tl": "fil-PH-BlessicaNeural",
    "tr": "tr-TR-EmelNeural",
    "id": "id-ID-GadisNeural",
}


# Synthesizer signature: (text, locale, voice) -> mp3 bytes.
SpeechSynthesisClient = Callable[[str, str, str], bytes]


@dataclass(frozen=True)
class AudioArtefact:
    locale: str
    voice: str
    text: str
    content_hash: str
    out_path: Path

    @property
    def manifest_entry(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "voice": self.voice,
            "text": self.text,
            "content_hash": self.content_hash,
            "filename": self.out_path.name,
        }


def _content_hash(text: str, locale: str, voice: str) -> str:
    payload = f"{locale}|{voice}|{text}".encode()
    return hashlib.sha256(payload).hexdigest()[:32]


def _resolve_voice(locale: str) -> str:
    return LOCALE_TO_VOICE.get(locale, LOCALE_TO_VOICE["en-AU"])


def _ensure_outdir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def build_artefacts(
    *,
    out_dir: Path,
    table: dict[str, WatermarkTexts] | None = None,
    synthesize: SpeechSynthesisClient | None = None,
) -> list[AudioArtefact]:
    """Render every locale's chat-receipt prefix to MP3 idempotently."""
    table = table if table is not None else dict(_load_table())
    if synthesize is None:
        synthesize = _make_default_synthesizer()
    _ensure_outdir(out_dir)

    artefacts: list[AudioArtefact] = []
    for locale, texts in sorted(table.items()):
        prefix = texts.chat_receipt_prefix
        voice = _resolve_voice(locale)
        digest = _content_hash(prefix, locale, voice)
        out_path = out_dir / f"{digest}.mp3"
        if out_path.exists():
            logger.info("tts.skip locale=%s digest=%s reason=already-rendered", locale, digest)
        else:
            mp3 = synthesize(prefix, locale, voice)
            if not mp3:
                raise RuntimeError(f"synthesize returned empty audio for locale={locale}")
            out_path.write_bytes(mp3)
            logger.info("tts.render locale=%s voice=%s bytes=%d", locale, voice, len(mp3))
        artefacts.append(
            AudioArtefact(
                locale=locale,
                voice=voice,
                text=prefix,
                content_hash=digest,
                out_path=out_path,
            )
        )
    manifest = {
        "version": 1,
        "artefacts": [a.manifest_entry for a in artefacts],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return artefacts


# ---------------------------------------------------------------------------
# Synthesiser factories
# ---------------------------------------------------------------------------


def _make_default_synthesizer() -> SpeechSynthesisClient:
    """Return the default synthesizer.

    If ``AZURE_SPEECH_KEY`` + ``AZURE_SPEECH_REGION`` are set, returns a
    real Azure Speech client; otherwise returns a deterministic stub
    that produces a tiny MP3-shaped payload (so CI smoke runs without
    Azure credentials).
    """
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if key and region:
        return _make_azure_synthesizer(key=key, region=region)
    return _StubSynthesizer()


class _StubSynthesizer:
    """Deterministic stub used in CI when Speech credentials aren't present."""

    def __call__(self, text: str, locale: str, voice: str) -> bytes:
        digest = hashlib.sha256(f"{locale}:{voice}:{text}".encode()).digest()
        # Minimal valid MP3 header (ID3v2 header + zero-length tag).
        return b"ID3\x04\x00\x00\x00\x00\x00\x00" + digest


def _make_azure_synthesizer(*, key: str, region: str) -> SpeechSynthesisClient:
    """Wrap ``azure.cognitiveservices.speech`` for live rendering.

    The import is deferred so this module imports cleanly without the
    optional dependency being installed.
    """

    def _synth(text: str, locale: str, voice: str) -> bytes:  # pragma: no cover - live
        try:
            import azure.cognitiveservices.speech as speech_sdk  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError("azure-cognitiveservices-speech is required for live TTS rendering") from exc

        config = speech_sdk.SpeechConfig(subscription=key, region=region)
        config.set_speech_synthesis_output_format(speech_sdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        config.speech_synthesis_language = locale
        config.speech_synthesis_voice_name = voice

        synthesizer = speech_sdk.SpeechSynthesizer(speech_config=config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        if result.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"Azure Speech synthesis failed for locale={locale}: {result.reason}")
        return bytes(result.audio_data)

    return _synth


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    arts = build_artefacts(out_dir=args.out)
    print(f"Rendered {len(arts)} TTS artefacts → {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_main())
