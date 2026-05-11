"""Unit tests for spec-036 T-W01 — ``sim_locale_table.json`` ≥30 locales.

Per tasks.md §16 (Phase W) and FR-039 / Amendment L:

* The locale table MUST contain at least 30 locales.
* Each row carries ``bcp47``, ``display_name``, ``fallback_chain[]``,
  ``jurisdictions[]``.
* Every fallback chain ends in ``en-AU`` (NSW EM-default).
* NT/Aboriginal locales must include the doctrinal floor:
  Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte, Kriol, Torres Strait Creole.
* Migrant-language floor: Vietnamese, Mandarin, Cantonese, Arabic, Greek,
  Italian, Tagalog, Punjabi, Korean, Spanish, Hindi, Bengali.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

LOCALE_TABLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "app"
    / "services"
    / "simulation"
    / "data"
    / "sim_locale_table.json"
)


@pytest.fixture(scope="module")
def locale_table() -> list[dict]:
    assert LOCALE_TABLE_PATH.is_file(), (
        f"sim_locale_table.json missing at {LOCALE_TABLE_PATH}"
    )
    payload = json.loads(LOCALE_TABLE_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, list), "Locale table must be a JSON array."
    return payload


def test_locale_table_has_at_least_30_entries(locale_table: list[dict]) -> None:
    assert len(locale_table) >= 30, (
        f"FR-039 / Amendment L requires ≥30 locales; got {len(locale_table)}."
    )


def test_every_entry_has_required_fields(locale_table: list[dict]) -> None:
    required = {"bcp47", "display_name", "fallback_chain", "jurisdictions"}
    for row in locale_table:
        missing = required - set(row.keys())
        assert not missing, f"Row {row.get('bcp47')!r} missing fields: {missing!r}"


def test_bcp47_codes_are_unique(locale_table: list[dict]) -> None:
    codes = [row["bcp47"] for row in locale_table]
    duplicates = {c for c in codes if codes.count(c) > 1}
    assert not duplicates, f"Duplicate BCP-47 codes: {duplicates!r}"


def test_every_fallback_chain_terminates_in_en_au(locale_table: list[dict]) -> None:
    for row in locale_table:
        chain = row["fallback_chain"]
        assert isinstance(chain, list) and chain, (
            f"{row['bcp47']!r}: fallback_chain must be a non-empty list."
        )
        assert chain[-1] == "en-AU", (
            f"{row['bcp47']!r}: fallback_chain must end in 'en-AU'; got {chain[-1]!r}"
        )


def test_nt_aboriginal_locales_present(locale_table: list[dict]) -> None:
    """Doctrinal floor — NT/Aboriginal locales MUST be represented."""

    codes = {row["bcp47"] for row in locale_table}
    required = {
        "yij",  # Yolŋu Matha
        "wbp",  # Warlpiri
        "pjt",  # Pitjantjatjara
        "aer",  # Arrernte (Eastern)
        "rop",  # Kriol (Roper River)
        "tcs",  # Torres Strait Creole
    }
    missing = required - codes
    assert not missing, f"NT/Aboriginal floor missing locales: {missing!r}"


def test_migrant_language_floor_present(locale_table: list[dict]) -> None:
    """Migrant-language floor per FR-039 (community-language coverage)."""

    codes = {row["bcp47"] for row in locale_table}
    required = {
        "vi",  # Vietnamese
        "zh-Hans",  # Mandarin (simplified)
        "zh-Hant",  # Cantonese (traditional)
        "ar",  # Arabic
        "el",  # Greek
        "it",  # Italian
        "tl",  # Tagalog
        "pa",  # Punjabi
        "ko",  # Korean
        "es",  # Spanish
        "hi",  # Hindi
        "bn",  # Bengali
    }
    missing = required - codes
    assert not missing, f"Migrant-language floor missing locales: {missing!r}"


def test_jurisdictions_field_uses_known_codes(locale_table: list[dict]) -> None:
    """Jurisdictions are AU state/territory codes plus 'AU' for federal."""

    allowed = {"AU", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"}
    for row in locale_table:
        for j in row["jurisdictions"]:
            assert j in allowed, (
                f"{row['bcp47']!r}: unknown jurisdiction code {j!r} (allowed={allowed!r})"
            )


def test_en_au_is_anchor_locale(locale_table: list[dict]) -> None:
    """``en-AU`` itself MUST be present and MUST be self-fallback."""

    en_au = next((row for row in locale_table if row["bcp47"] == "en-AU"), None)
    assert en_au is not None, "en-AU anchor locale missing from table."
    assert en_au["fallback_chain"] == ["en-AU"], (
        "en-AU's fallback chain must be self-contained."
    )
