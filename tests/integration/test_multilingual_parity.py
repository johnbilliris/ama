"""Spec-039 T150 — multilingual alert-template parity (FR-070, SC-014).

Asserts every locale file under
``packages/domain/src/domain/seed/alert-templates/`` exposes the same
``template_id`` set as the canonical ``en-AU`` file, and that the two
accessibility-placeholder files (Indigenous + Auslan) are present and
have ``placeholder=true`` rows.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
DIR = _REPO / "packages" / "domain" / "src" / "domain" / "seed" / "alert-templates"

MUST_LOCALES = ("en-AU", "ar", "el", "it", "vi", "zh-Hans")
PLACEHOLDER_LOCALES = ("indigenous-placeholder", "auslan-placeholder")


def _records(locale: str) -> list[dict]:
    return json.loads((DIR / f"{locale}.json").read_text(encoding="utf-8"))["records"]


def test_must_locale_files_present() -> None:
    for loc in MUST_LOCALES + PLACEHOLDER_LOCALES:
        assert (DIR / f"{loc}.json").exists(), loc


def test_template_ids_match_across_locales() -> None:
    base_ids = {r["template_id"] for r in _records("en-AU")}
    assert base_ids, "en-AU has no templates"
    for loc in MUST_LOCALES + PLACEHOLDER_LOCALES:
        if loc == "en-AU":
            continue
        ids = {r["template_id"] for r in _records(loc)}
        assert ids == base_ids, f"{loc} template_ids drift: missing={base_ids-ids} extra={ids-base_ids}"


def test_placeholder_locales_marked() -> None:
    for loc in PLACEHOLDER_LOCALES:
        for r in _records(loc):
            assert r.get("placeholder") is True, (
                f"{loc} record {r.get('id')} must declare placeholder=true (FR-044/A-9/A-10)"
            )


def test_every_record_has_audio_description_field() -> None:
    """T151 — WCAG 2.1 AA placeholder presence (FR-071)."""
    for loc in MUST_LOCALES + PLACEHOLDER_LOCALES:
        for r in _records(loc):
            assert "wcag_audio_description" in r, (
                f"{loc} record {r.get('id')} missing wcag_audio_description (FR-071)"
            )


def test_parity_matrix_doc_present() -> None:
    p = _REPO / "docs" / "test-data" / "MULTILINGUAL-PARITY.md"
    assert p.exists(), "docs/test-data/MULTILINGUAL-PARITY.md missing (T150)"
    text = p.read_text(encoding="utf-8")
    for loc in MUST_LOCALES:
        assert loc in text, f"parity doc missing {loc}"
