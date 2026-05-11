"""Loader for the locale-correct watermark/chat-receipt-prefix table (T-F01).

Pure-Python YAML loader (used by both watermark guards and the
audio-watermark service). Tests can override the search path.

The table covers the MVP minimum + ~30 CALD backlog (per Assumption A11);
locales NOT yet authored emit ``audit.watermark.locale_missing`` (T-F05)
and fall back to en-AU.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "watermark_text.yaml"

DEFAULT_LOCALE = "en-AU"


@dataclass(frozen=True)
class WatermarkTexts:
    chat_receipt_prefix: str
    public_warning_watermark: str


def _parse(text: str) -> dict[str, dict[str, str]]:
    """Tiny YAML subset parser for the watermark table."""
    out: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0]
        stripped = line.lstrip()
        if not stripped.strip():
            continue
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.endswith(":"):
            current = stripped[:-1].strip()
            out[current] = {}
            continue
        if indent > 0 and current is not None and ":" in stripped:
            key, _, value = stripped.partition(":")
            v = value.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            out[current][key.strip()] = v
    return out


@lru_cache(maxsize=1)
def _load_table() -> Mapping[str, WatermarkTexts]:
    if not DEFAULT_PATH.exists():
        return {
            DEFAULT_LOCALE: WatermarkTexts(
                chat_receipt_prefix="[SIMULATION]",
                public_warning_watermark="SIMULATION — DO NOT DISTRIBUTE",
            )
        }
    raw = _parse(DEFAULT_PATH.read_text(encoding="utf-8"))
    out: dict[str, WatermarkTexts] = {}
    for locale, fields in raw.items():
        chat = fields.get("chat_receipt_prefix")
        warn = fields.get("public_warning_watermark")
        if not chat or not warn:
            continue
        out[locale] = WatermarkTexts(chat_receipt_prefix=chat, public_warning_watermark=warn)
    return out


def reset_cache_for_tests() -> None:
    _load_table.cache_clear()


def get_table() -> Mapping[str, WatermarkTexts]:
    return _load_table()


def lookup(locale: str) -> tuple[WatermarkTexts, bool]:
    """Return ``(texts, fell_back)`` — ``fell_back=True`` triggers T-F05 audit."""
    table = _load_table()
    if locale in table:
        return table[locale], False
    return table[DEFAULT_LOCALE], True


__all__ = [
    "DEFAULT_LOCALE",
    "WatermarkTexts",
    "get_table",
    "lookup",
    "reset_cache_for_tests",
]
