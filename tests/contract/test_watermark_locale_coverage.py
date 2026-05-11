"""Contract test for spec-036 T-W04 — locale coverage.

Asserts that the watermark/audio locale surface satisfies FR-039,
Amendment L, multi-jurisdiction.md CHK018-CHK023 and the §16 Phase-W
floor:

* The locale table (T-W01) lists ≥30 locales.
* Every NT/Aboriginal locale has a fallback chain that terminates in
  ``en-AU`` (CHK020 + CHK021).
* Every locale has either a reachable MP3 pointer in the pre-render
  catalog (T-W03) **or** a fallback locale on its chain that does, so the
  FR-058 audio-prefix path is never silent.
* Every backlog NT/Aboriginal locale is recorded in the catalog with
  ``staging_promotion_blocker: true`` so the spec target is not silently
  degraded (CHK023).
* All eight AU jurisdictions plus the federal ``AU`` umbrella have a
  priority profile (T-W02).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.api.app.services.simulation.jurisdiction_locale_priority import (
    ALL_JURISDICTIONS,
    NT_ABORIGINAL_LOCALES,
    load_priorities,
)
from apps.api.app.services.simulation.speech_prerender_catalog import (
    load_catalog,
    reachable,
)

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
    return json.loads(LOCALE_TABLE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _clear_caches():
    load_catalog.cache_clear()
    load_priorities.cache_clear()
    yield
    load_catalog.cache_clear()
    load_priorities.cache_clear()


def test_locale_table_meets_thirty_floor(locale_table):
    assert len(locale_table) >= 30, (
        f"FR-039 requires ≥30 locales; got {len(locale_table)}"
    )


def test_every_locale_chain_terminates_in_en_au(locale_table):
    for row in locale_table:
        chain = row["fallback_chain"]
        assert chain, f"Locale {row['bcp47']!r} has empty fallback chain"
        assert chain[-1] == "en-AU", (
            f"Locale {row['bcp47']!r} fallback chain MUST end in en-AU; got {chain!r}"
        )


def test_nt_aboriginal_locales_present_in_table(locale_table):
    """CHK018-CHK020: Yolŋu, Warlpiri, Pitjantjatjara, Arrernte, Kriol, Torres Strait Creole."""
    table_locales = {row["bcp47"] for row in locale_table}
    for required in NT_ABORIGINAL_LOCALES:
        assert required in table_locales, (
            f"NT/Aboriginal locale {required!r} missing from sim_locale_table.json"
        )


def test_every_locale_has_reachable_mp3_or_fallback(locale_table):
    """FR-058: every locale must resolve to an MP3 via its fallback chain."""
    for row in locale_table:
        bcp47 = row["bcp47"]
        chain = tuple(row["fallback_chain"])
        pointer, source = reachable(bcp47, fallback_chain=chain)
        # en-AU is in every chain and MUST always have an MP3.
        assert pointer is not None, (
            f"Locale {bcp47!r} cannot reach any MP3 via chain {chain!r}; "
            f"FR-058 requires audio-prefix coverage."
        )
        assert source in {bcp47, *chain}, (
            f"Reachable source {source!r} not in chain for {bcp47!r}"
        )


def test_nt_aboriginal_backlog_flagged_chk023():
    """CHK023: each NT/Aboriginal locale must be present in the catalog with explicit blocker flag."""
    catalog = load_catalog()
    for locale in NT_ABORIGINAL_LOCALES:
        assert locale in catalog, (
            f"NT/Aboriginal locale {locale!r} missing from speech_prerender_catalog.json"
        )
        # When a backlog locale lacks an MP3 it MUST be flagged so promotion is gated.
        entry = catalog[locale]
        if entry.mp3_pointer is None:
            assert entry.staging_promotion_blocker is True, (
                f"Locale {locale!r} has no MP3 pointer but is not flagged as a "
                f"staging_promotion_blocker; CHK023 violated."
            )


def test_all_jurisdictions_have_priority_profile():
    table = load_priorities()
    missing = ALL_JURISDICTIONS - set(table.keys())
    assert not missing, f"Missing jurisdiction priority profiles: {sorted(missing)}"


def test_priority_profiles_only_reference_known_locales(locale_table):
    """A priority list must only reference locales in the table or en-AU."""
    known = {row["bcp47"] for row in locale_table}
    for jurisdiction, profile in load_priorities().items():
        for locale in profile:
            assert locale in known, (
                f"Jurisdiction {jurisdiction!r} priority profile references "
                f"unknown locale {locale!r} (not in sim_locale_table.json)"
            )
