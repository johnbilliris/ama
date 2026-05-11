"""Jurisdiction locale priority — spec-036 T-W02 / FR-039 / FR-058 / FR-064.

Maps each AU jurisdiction to an ordered priority list of BCP-47 locale tags
that is consulted as the **second** step of the 3-step locale-resolution
fallback chain mandated by FR-058 (audio prefix) and FR-064 (live-log):

    request_locale → jurisdiction_priority_locale → en-AU

The default for **every** jurisdiction is `en-AU`; jurisdictions list their
most-spoken CALD locales next so that CALD-listener pathways still receive a
locale-correct watermark even when the requesting client did not pin a
locale.

Per CHK020 the **NT** list MUST include at least one NT/Aboriginal locale
(Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte, or Kriol) because the
sectors cohort flagged NT routing as the canonical surface where remote
Aboriginal locales would otherwise be silently dropped.

The fixture lives at
``apps/api/app/services/simulation/data/jurisdiction_locale_priority.json``
and is loaded once via :func:`load_priorities` (LRU-cached). All eight AU
jurisdictions PLUS the federal ``AU`` umbrella are present.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Final

DEFAULT_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "data" / "jurisdiction_locale_priority.json"
)

#: Closed AU+8 set (federal umbrella + 8 states/territories).
ALL_JURISDICTIONS: Final[frozenset[str]] = frozenset(
    {"AU", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT"}
)

#: NT/Aboriginal locale floor per FR-039 / Amendment L / CHK018-CHK020.
NT_ABORIGINAL_LOCALES: Final[frozenset[str]] = frozenset(
    {"yij", "wbp", "pjt", "aer", "rop", "tcs"}
)

ANCHOR_LOCALE: Final[str] = "en-AU"


class UnknownJurisdictionError(LookupError):
    """The requested jurisdiction is not in the closed AU+8 set."""


@lru_cache(maxsize=1)
def load_priorities(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    """Load and cache the jurisdiction → priority locales fixture."""

    target = path or DEFAULT_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(
            f"jurisdiction_locale_priority.json at {target} must be a JSON object."
        )
    out: dict[str, tuple[str, ...]] = {}
    for key, value in payload.items():
        if key.startswith("_"):
            continue  # skip _meta etc.
        if not isinstance(value, list) or not value:
            raise ValueError(
                f"Priority list for jurisdiction {key!r} must be a non-empty list."
            )
        out[key] = tuple(str(v) for v in value)
    return out


def priorities_for(jurisdiction: str) -> tuple[str, ...]:
    """Return the priority locale tuple for *jurisdiction*.

    Raises :class:`UnknownJurisdictionError` when the jurisdiction is not
    one of the AU+8 set.
    """

    if jurisdiction not in ALL_JURISDICTIONS:
        raise UnknownJurisdictionError(
            f"Unknown AU jurisdiction {jurisdiction!r}; expected one of {sorted(ALL_JURISDICTIONS)}"
        )
    return load_priorities().get(jurisdiction, (ANCHOR_LOCALE,))


def resolve_locale(
    request_locale: str | None,
    *,
    jurisdiction: str,
    available_locales: frozenset[str],
) -> tuple[str, str]:
    """Resolve a request locale via the FR-058 / FR-064 3-step fallback chain.

    Returns ``(resolved_locale, source)`` where ``source`` is one of
    ``request_locale | jurisdiction_priority | en_au_anchor``.
    """

    if request_locale and request_locale in available_locales:
        return (request_locale, "request_locale")
    for candidate in priorities_for(jurisdiction):
        if candidate in available_locales:
            return (candidate, "jurisdiction_priority")
    return (ANCHOR_LOCALE, "en_au_anchor")


__all__ = [
    "ALL_JURISDICTIONS",
    "ANCHOR_LOCALE",
    "DEFAULT_PATH",
    "NT_ABORIGINAL_LOCALES",
    "UnknownJurisdictionError",
    "load_priorities",
    "priorities_for",
    "resolve_locale",
]
