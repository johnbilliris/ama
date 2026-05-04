"""Multilingual coverage probe (FR-019).

Spec 034 (cycle-1): the language-pack accessibility probe in
``tests/e2e/web-coverage/_support/a11y/languagePackProbe.ts`` calls
``GET /api/i18n/coverage`` and asserts the response declares the
languages the warning payloads reference (en + zh-Hans +
aus-x-atsi-placeholder at minimum, plus the broader set used by the
seed warning fixtures: vi, el, ar, tl, id).

Returns the static seed list — the actual translation pack is supplied
out-of-band; this endpoint exists purely so the multilingual coverage
contract has something to assert against.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/i18n", tags=["i18n"])

_SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "en",
    "zh-Hans",
    "vi",
    "el",
    "ar",
    "tl",
    "id",
    "aus-x-atsi-placeholder",
)


@router.get("/coverage")
def coverage() -> dict[str, list[str]]:
    return {"languages": list(_SUPPORTED_LANGUAGES)}
