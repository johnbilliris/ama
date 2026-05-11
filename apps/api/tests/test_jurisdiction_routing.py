"""Phase G — jurisdiction ladder + agent-routing-table tests."""

from __future__ import annotations

from apps.api.app.services.simulation.agent_routing_table import (
    combat_for,
    control_for,
    is_ic_eligible,
    medical_brand_for,
    police_for,
    reset_cache_for_tests,
)
from apps.api.app.services.simulation.jurisdiction_ladder import (
    LadderInput,
    resolve,
)


def test_ladder_step1_explicit_payload_wins() -> None:
    res = resolve(
        request=LadderInput(explicit_jurisdiction_code="AU-NSW"),
    )
    assert res.jurisdiction_code == "AU-NSW"
    assert res.ladder_step == "explicit_payload"
    assert res.confidence == "high"


def test_ladder_step2_operator_asserted_runs_when_no_explicit() -> None:
    res = resolve(
        request=LadderInput(operator_asserted_code="AU-VIC"),
    )
    assert res.jurisdiction_code == "AU-VIC"
    assert res.ladder_step == "operator_asserted"


def test_ladder_step3_viewport_hint_match_promotes_to_high_confidence() -> None:
    def lookup(lat: float, lng: float) -> str | None:
        return "AU-NSW"

    res = resolve(
        request=LadderInput(
            client_jurisdiction_hint="AU-NSW",
            viewport_centroid_lat=-33.0,
            viewport_centroid_lng=151.0,
            signal_lat=-33.0,
            signal_lng=151.0,
        ),
        polygon_lookup=lookup,
    )
    assert res.ladder_step == "viewport_hint_revalidated"
    assert res.viewport_hint_match is True


def test_ladder_step4_polygon_lookup_when_viewport_hint_mismatches() -> None:
    def lookup(lat: float, lng: float) -> str | None:
        return "AU-VIC"

    res = resolve(
        request=LadderInput(
            client_jurisdiction_hint="AU-NSW",  # mismatch
            viewport_centroid_lat=-37.0,
            viewport_centroid_lng=145.0,
            signal_lat=-37.0,
            signal_lng=145.0,
        ),
        polygon_lookup=lookup,
    )
    assert res.ladder_step == "strtree_polygon"
    assert res.jurisdiction_code == "AU-VIC"
    assert res.viewport_hint_match is False
    assert any("viewport_hint_mismatch" in n for n in res.notes)


def test_ladder_step5_sa4_fallback_when_polygon_lookup_returns_none() -> None:
    def polygon(lat: float, lng: float) -> str | None:
        return None

    def sa4(lat: float, lng: float) -> str | None:
        return "AU-SA4-110"

    res = resolve(
        request=LadderInput(signal_lat=-26.5, signal_lng=153.0),
        polygon_lookup=polygon,
        sa4_lookup=sa4,
    )
    assert res.ladder_step == "abs_sa4_fallback"
    assert res.jurisdiction_code == "AU-SA4-110"


def test_ladder_au_national_when_all_lookups_fail() -> None:
    res = resolve(request=LadderInput(signal_lat=-26.5, signal_lng=153.0))
    assert res.ladder_step == "abs_sa4_fallback"
    assert res.jurisdiction_code == "AU"
    assert res.confidence == "ambiguous"


# --- Agent routing table -------------------------------------------------


def test_combat_for_nsw_lists_rfs_ses_fr() -> None:
    reset_cache_for_tests()
    agencies = combat_for("NSW")
    assert "NSW RFS" in agencies
    assert "NSW SES" in agencies
    assert "NSW Fire and Rescue" in agencies


def test_control_for_act_routes_to_afp() -> None:
    reset_cache_for_tests()
    assert police_for("ACT") == "Australian Federal Police"
    assert police_for("NSW") == "NSW Police Force"


def test_medical_brand_per_state() -> None:
    reset_cache_for_tests()
    assert medical_brand_for("NSW") == "NSW Ambulance"
    assert medical_brand_for("VIC") == "Ambulance Victoria"
    assert medical_brand_for("WA") == "St John WA"
    assert medical_brand_for("UNKNOWN") is None


def test_nsw_ic_restriction_enforced() -> None:
    reset_cache_for_tests()
    assert is_ic_eligible("NSW", "NSW RFS Incident Controller") is True
    assert is_ic_eligible("NSW", "Random Civilian") is False
    # Non-NSW unaffected
    assert is_ic_eligible("VIC", "Random Person") is True


def test_control_for_returns_empty_for_unknown_jurisdiction() -> None:
    reset_cache_for_tests()
    assert control_for("XX") == ()
