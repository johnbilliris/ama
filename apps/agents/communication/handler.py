"""T-F06 — communication-agent simulation watermark handler (FR-035, FR-039, FR-058).

Centralises the **pre-emit** application of the three FR-watermarks for
simulation tenants:

* **Chat receipt prefix** (FR-035 / FR-040) — text reply MUST begin with
  the locale-correct ``[SIMULATION]`` prefix; the LLM cannot remove it.
* **Public-warning watermark** (FR-039) — public-warning artefacts MUST
  carry the bilingual ``SIMULATION — DO NOT DISTRIBUTE`` watermark.
* **Audio prefix** (FR-058) — TTS output MUST begin with the
  locale-correct spoken simulation prefix.

This module is the thin glue between the existing pipeline and the
guard services in ``apps/api/app/services/simulation/``. It accepts
already-rendered output bytes, applies the guards, and returns the
post-watermark output ready for delivery.

The handler is intentionally synchronous-friendly for chat/text and
async for audio (since the audio watermark service emits an audit
event). Callers can opt in/out of any pathway.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.services.simulation.audio_watermark_service import (
    AudioPrefixCatalog,
    AudioWatermarkResult,
    AudioWatermarkService,
)
from app.services.simulation.chat_receipt_prefix_guard import (
    enforce as enforce_chat_receipt_prefix,
)
from app.services.simulation.public_warning_watermark_guard import (
    get_watermark,
    is_watermarked,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WatermarkContext:
    locale: str
    simulation_id: str | None = None
    is_public_warning: bool = False
    is_simulation: bool = True


@dataclass
class HandledTextResult:
    text: str
    chat_receipt_prefix_applied: bool
    public_warning_watermark_applied: bool


def apply_text_watermarks(
    text: str,
    *,
    context: WatermarkContext,
) -> HandledTextResult:
    """Apply both text-pathway watermarks pre-emit.

    For non-simulation tenants this is a passthrough.
    """
    if not context.is_simulation:
        return HandledTextResult(text=text, chat_receipt_prefix_applied=False, public_warning_watermark_applied=False)

    chat_applied = False
    out = text
    guard = enforce_chat_receipt_prefix(out, locale=context.locale)
    if guard.prefix_was_missing:
        chat_applied = True
        out = guard.text

    public_applied = False
    if context.is_public_warning:
        if not is_watermarked(out, locale=context.locale):
            wm = get_watermark(locale=context.locale)
            out = f"{wm.watermark}\n{out}"
            public_applied = True

    return HandledTextResult(
        text=out,
        chat_receipt_prefix_applied=chat_applied,
        public_warning_watermark_applied=public_applied,
    )


@dataclass
class HandledAudioResult:
    audio_bytes: bytes
    prefix_applied: bool
    fallback_locale: str | None
    prefix_content_hash: str


async def apply_audio_watermark(
    audio_bytes: bytes,
    *,
    context: WatermarkContext,
    catalog: AudioPrefixCatalog,
    audit_writer: Any | None = None,
) -> HandledAudioResult:
    """Apply the locale-correct spoken simulation prefix pre-emit."""
    if not context.is_simulation:
        return HandledAudioResult(
            audio_bytes=audio_bytes,
            prefix_applied=False,
            fallback_locale=None,
            prefix_content_hash="",
        )
    svc = AudioWatermarkService(catalog=catalog, audit_writer=audit_writer)
    result: AudioWatermarkResult = await svc.apply(
        body_audio=audio_bytes,
        locale=context.locale,
        simulation_id=context.simulation_id,
    )
    return HandledAudioResult(
        audio_bytes=result.audio_bytes,
        prefix_applied=True,
        fallback_locale=result.prefix_locale if result.fallback_applied else None,
        prefix_content_hash=result.prefix_content_hash,
    )


__all__ = [
    "HandledAudioResult",
    "HandledTextResult",
    "WatermarkContext",
    "apply_audio_watermark",
    "apply_text_watermarks",
]
