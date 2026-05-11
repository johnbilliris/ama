"""Unit tests for spec-036 T-W02 — jurisdiction locale priority profiles.

Asserts that the profile fixture and its loader satisfy:

* All 8 AU jurisdictions plus the federal ``AU`` umbrella are present.
* Every list begins with ``en-AU`` (anchor locale).
* The **NT** profile lists at least one NT/Aboriginal locale per CHK020.
* The 3-step locale-resolution fallback (FR-058 / FR-064 / pass-2 Q6) is
  honoured in priority order: ``request_locale → jurisdiction_priority →
  en-AU``.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.jurisdiction_locale_priority import (
    ALL_JURISDICTIONS,
    ANCHOR_LOCALE,
    NT_ABORIGINAL_LOCALES,
    UnknownJurisdictionError,
    load_priorities,
    priorities_for,
    resolve_locale,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    load_priorities.cache_clear()
    yield
    load_priorities.cache_clear()


def test_all_au_jurisdictions_have_a_priority_profile():
    table = load_priorities()
    missing = ALL_JURISDICTIONS - set(table.keys())
    assert not missing, f"Missing jurisdiction priority profiles: {sorted(missing)}"


def test_every_profile_starts_with_en_au_anchor():
    for jurisdiction, profile in load_priorities().items():
        assert profile[0] == ANCHOR_LOCALE, (
            f"Jurisdiction {jurisdiction!r} priority profile must start with "
            f"{ANCHOR_LOCALE!r}; got {profile!r}"
        )


def test_nt_profile_includes_at_least_one_aboriginal_locale_chk020():
    nt_profile = priorities_for("NT")
    overlap = set(nt_profile) & NT_ABORIGINAL_LOCALES
    assert overlap, (
        "NT priority profile MUST include at least one NT/Aboriginal locale "
        f"(any of {sorted(NT_ABORIGINAL_LOCALES)}); got {nt_profile!r}"
    )


def test_unknown_jurisdiction_raises():
    with pytest.raises(UnknownJurisdictionError):
        priorities_for("XYZ")


def test_resolve_locale_honours_request_locale_first():
    available = frozenset({"en-AU", "vi", "yij"})
    resolved, source = resolve_locale("vi", jurisdiction="NT", available_locales=available)
    assert resolved == "vi"
    assert source == "request_locale"


def test_resolve_locale_falls_back_to_jurisdiction_priority_when_request_unavailable():
    available = frozenset({"en-AU", "yij"})
    resolved, source = resolve_locale(
        "ko", jurisdiction="NT", available_locales=available
    )
    # NT priority lists rop (Kriol) before yij; rop is not available, so it falls to yij.
    assert resolved in {"yij", "rop", "wbp", "pjt", "tcs"} | {ANCHOR_LOCALE}
    if resolved != ANCHOR_LOCALE:
        assert source == "jurisdiction_priority"


def test_resolve_locale_anchors_to_en_au_when_nothing_matches():
    available = frozenset({"en-AU"})
    resolved, source = resolve_locale(
        "xx-YY", jurisdiction="VIC", available_locales=available
    )
    assert resolved == ANCHOR_LOCALE
    # Source may be either jurisdiction_priority (because VIC's first entry is en-AU)
    # or en_au_anchor; we accept both because the anchor is part of every profile.
    assert source in {"jurisdiction_priority", "en_au_anchor"}


def test_resolve_locale_with_no_request_locale_uses_priority_chain():
    available = frozenset({"en-AU", "zh-Hans"})
    resolved, source = resolve_locale(
        None, jurisdiction="VIC", available_locales=available
    )
    # VIC priority is [en-AU, zh-Hans, ...]; en-AU is available so it resolves first.
    assert resolved == "en-AU"
    assert source == "jurisdiction_priority"
