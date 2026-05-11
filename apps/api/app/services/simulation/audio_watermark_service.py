"""T-F04 — audio watermark service (FR-058).

Resolves the locale-correct pre-rendered audio prefix and prepends it to
TTS-bound communications. Lookup goes through Blob signed URLs in
production; in tests a synchronous in-memory `AudioPrefixCatalog` is
used.

The FR-058 contract:

* Audio output MUST start with a locale-correct spoken simulation prefix.
* If the locale prefix is missing, the service falls back to **en-AU**
  and emits ``audit.watermark.locale_missing`` with ``pathway=audio``.
* The injection is byte-deterministic: ``prefix_bytes + body_bytes``.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_LOCALE = "en-AU"


@dataclass(frozen=True)
class AudioPrefix:
    locale: str
    content_hash: str
    audio_bytes: bytes


@dataclass
class AudioPrefixCatalog:
    """Lookup table for pre-rendered audio prefixes."""

    prefixes: Mapping[str, AudioPrefix] = field(default_factory=dict)

    def get(self, locale: str) -> AudioPrefix | None:
        return self.prefixes.get(locale)


class LocaleMissingAuditWriter:
    """Async callable interface for the audit writer (T-F05 contract)."""

    async def __call__(  # pragma: no cover - protocol shim
        self,
        *,
        locale: str,
        pathway: str,
        fallback_applied: str,
        simulation_id: str | None,
    ) -> None: ...


@dataclass
class AudioWatermarkResult:
    audio_bytes: bytes
    prefix_locale: str
    prefix_content_hash: str
    fallback_applied: bool


class AudioWatermarkService:
    """Prepend locale-correct simulation prefix to TTS output."""

    def __init__(
        self,
        *,
        catalog: AudioPrefixCatalog,
        audit_writer: Callable[..., Awaitable[None]] | None = None,
        default_locale: str = DEFAULT_LOCALE,
    ) -> None:
        self.catalog = catalog
        self.audit_writer = audit_writer
        self.default_locale = default_locale

    async def apply(
        self,
        *,
        body_audio: bytes,
        locale: str,
        simulation_id: str | None = None,
    ) -> AudioWatermarkResult:
        prefix = self.catalog.get(locale)
        fallback = False
        if prefix is None:
            fallback = True
            prefix = self.catalog.get(self.default_locale)
            if prefix is None:
                raise RuntimeError("audio_watermark: no audio prefix available; default locale missing")
            await self._emit_locale_missing(
                requested=locale,
                resolved=self.default_locale,
                simulation_id=simulation_id,
            )
        merged = prefix.audio_bytes + body_audio
        logger.info(
            "audio_watermark.applied locale=%s fallback=%s digest=%s sim=%s",
            prefix.locale,
            fallback,
            prefix.content_hash,
            simulation_id,
        )
        return AudioWatermarkResult(
            audio_bytes=merged,
            prefix_locale=prefix.locale,
            prefix_content_hash=prefix.content_hash,
            fallback_applied=fallback,
        )

    async def _emit_locale_missing(
        self,
        *,
        requested: str,
        resolved: str,
        simulation_id: str | None,
    ) -> None:
        if self.audit_writer is None:
            return
        try:
            await self.audit_writer(
                locale=requested,
                pathway="audio",
                fallback_applied=resolved,
                simulation_id=simulation_id,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "audio_watermark.audit_write_failed locale=%s sim=%s",
                requested,
                simulation_id,
            )


def starts_with_prefix(audio: bytes, prefix: AudioPrefix) -> bool:
    """Convenience predicate: does *audio* start with the prefix bytes?"""
    return audio.startswith(prefix.audio_bytes)


__all__ = [
    "AudioPrefix",
    "AudioPrefixCatalog",
    "AudioWatermarkResult",
    "AudioWatermarkService",
    "DEFAULT_LOCALE",
    "starts_with_prefix",
]
