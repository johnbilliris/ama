"""Public-warning watermark guard (T-F02b / FR-039 / T-P04).

Embeds the bilingual ``SIMULATION — DO NOT DISTRIBUTE`` watermark on
every public-warning artefact (PDFs, SMS bodies, banner overlays).

This module is text-only — PDF/Speech rendering pipelines wrap the
returned watermark string into the appropriate output format. The LLM
cannot translate or remove the text — table lookup only.

Wave 4 (T-P04) added :func:`embed_with_audit` which emits the canonical
``audit.watermark.applied`` envelope (audit-envelope.md §3.14a) in
addition to returning the watermarked text. Per Q6 the same locale
table services both the text-live-log and audio-prefix delivery
channels.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Literal

from app.services.simulation.watermark_text_loader import lookup

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WatermarkResult:
    watermark: str
    locale_fell_back: bool


def get_watermark(*, locale: str) -> WatermarkResult:
    texts, fell_back = lookup(locale)
    return WatermarkResult(
        watermark=texts.public_warning_watermark,
        locale_fell_back=fell_back,
    )


def is_watermarked(text: str, *, locale: str) -> bool:
    """Return ``True`` if *text* already contains the locale-correct watermark."""
    res = get_watermark(locale=locale)
    return res.watermark in text


def embed(text: str, *, locale: str) -> WatermarkResult:
    """Return *text* with the locale-correct watermark prepended (idempotent)."""
    res = get_watermark(locale=locale)
    if res.watermark in text:
        return res
    return WatermarkResult(
        watermark=f"{res.watermark}\n\n{text}",
        locale_fell_back=res.locale_fell_back,
    )


DeliveryChannel = Literal["audio", "text-live-log", "both"]


@dataclass(frozen=True)
class WatermarkAuditResult:
    """Outcome of :func:`embed_with_audit` — text + audit envelope id."""

    watermark: str
    locale_fell_back: bool
    resolved_locale: str
    watermark_text_hash: str
    audit_emitted: bool


async def embed_with_audit(
    text: str,
    *,
    locale: str,
    artefact_id: str,
    delivery_channel: DeliveryChannel,
    simulation_id: str,
    actor: str = "watermark_guard",
    audio_prefix_table_version: str | None = None,
    live_log_sse_event_id: str | None = None,
) -> WatermarkAuditResult:
    """Embed the watermark and emit the ``audit.watermark.applied`` envelope.

    Per T-P04 / Amendment Q / pass-2 Q6 every watermark application MUST
    be auditable so reviewers can correlate FR-058 audio-prefix
    renderings to FR-064 accessible live-log emissions. The audit entry
    is best-effort — guard failures here MUST NOT prevent the
    deliverable from being rendered (Primacy of Life invariant).
    """

    res = embed(text, locale=locale)
    resolved_locale = "en-AU" if res.locale_fell_back else locale
    watermark_hash = hashlib.sha256(res.watermark.encode("utf-8")).hexdigest()

    audit_emitted = False
    try:  # pragma: no branch - linear path
        from app.services.simulation.audit_writer import get_audit_writer

        details: dict[str, object] = {
            "artefact_id": artefact_id,
            "delivery_channel": delivery_channel,
            "resolved_locale": resolved_locale,
            "watermark_text_hash": watermark_hash,
        }
        if audio_prefix_table_version is not None:
            details["audio_prefix_table_version"] = audio_prefix_table_version
        if live_log_sse_event_id is not None:
            details["live_log_sse_event_id"] = live_log_sse_event_id

        await get_audit_writer().write(
            "audit.watermark.applied",
            simulation_id=simulation_id,
            actor=actor,
            details=details,
        )
        audit_emitted = True
    except Exception:  # pragma: no cover - best-effort audit
        logger.exception(
            "sim.watermark_audit_failed sim=%s artefact=%s",
            simulation_id,
            artefact_id,
        )

    return WatermarkAuditResult(
        watermark=res.watermark,
        locale_fell_back=res.locale_fell_back,
        resolved_locale=resolved_locale,
        watermark_text_hash=watermark_hash,
        audit_emitted=audit_emitted,
    )


__all__ = [
    "WatermarkAuditResult",
    "WatermarkResult",
    "embed",
    "embed_with_audit",
    "get_watermark",
    "is_watermarked",
]
