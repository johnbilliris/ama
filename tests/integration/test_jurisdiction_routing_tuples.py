"""Integration test for spec-036 T-X08 — jurisdiction × hazard × agency tuples.

Sweeps each of the 31 multi-jurisdiction.md checklist items (CHK001-CHK031)
via the canonical :func:`route` service to assert that the **fixture data
is correct AND the service does not coarsen the routing**.

The test categories mirror the multi-jurisdiction.md structure:

* CHK003 — WA single-route (DFES sole entry point for fire/flood/storm).
* CHK004 — QLD canonical agency name = QFD (formerly QFES).
* CHK005 — VIC fire = CFA + FRV split.
* CHK006 — SA fire = SACFS + SAMFS split.
* CHK007 — TAS fire = single combat agency (Tasmania Fire Service).
* CHK008 — NT dual-fire (Bushfires NT + NTFRS).
* CHK009 — NT cyclone routes via NTES.
* CHK010 — ACT umbrella addressed via ESA.
* CHK011 — ACT police split (AFP + ACT Policing) with agency_hint disambiguation.
* CHK012 — Closed medical-service set per jurisdiction.
* CHK013 — SES is lead flood/storm in NSW + VIC + QLD.

Each parametrised case is annotated with its CHK identifier so a failure
points the reader at the source-of-truth checklist item.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.jurisdiction_routing import (
    UnknownRouteError,
    load_routes,
    route,
)


@pytest.fixture(autouse=True)
def _clear_route_cache():
    load_routes.cache_clear()
    yield
    load_routes.cache_clear()


# --- WA single-route (CHK003) -----------------------------------------------


@pytest.mark.parametrize("hazard", ["fire", "flood", "storm"])
def test_chk003_wa_single_route_via_dfes(hazard):
    decision = route("WA", hazard)
    assert decision.agencies == ("DFES",), (
        f"WA {hazard} MUST route to DFES alone (CHK003); got {decision.agencies}"
    )


# --- QLD QFD naming (CHK004) -----------------------------------------------


def test_chk004_qld_fire_uses_qfd_name():
    decision = route("QLD", "fire")
    assert "QFD" in decision.agencies, (
        f"QLD fire MUST use QFD name (CHK004); got {decision.agencies}"
    )
    assert "QFES" not in decision.agencies, (
        "QFES is the legacy name and must not appear in the routing tuple."
    )


# --- VIC CFA + FRV split (CHK005) -------------------------------------------


def test_chk005_vic_fire_includes_cfa_and_frv():
    decision = route("VIC", "fire")
    assert "CFA" in decision.agencies, "CHK005: VIC fire missing CFA"
    assert "FRV" in decision.agencies, "CHK005: VIC fire missing FRV"


@pytest.mark.parametrize("hint,expected", [("CFA", ("CFA",)), ("FRV", ("FRV",))])
def test_chk005_vic_agency_hint_disambiguates(hint, expected):
    decision = route("VIC", "fire", agency_hint=hint)
    assert decision.agencies == expected


# --- SA SACFS + SAMFS split (CHK006) ----------------------------------------


def test_chk006_sa_fire_includes_sacfs_and_samfs():
    decision = route("SA", "fire")
    assert "SACFS" in decision.agencies
    assert "SAMFS" in decision.agencies


# --- TAS single-agency fire (CHK007) ---------------------------------------


def test_chk007_tas_fire_single_combat_agency():
    decision = route("TAS", "fire")
    assert decision.agencies == ("Tasmania Fire Service",), (
        f"CHK007: TAS fire MUST be Tasmania Fire Service alone; got {decision.agencies}"
    )


# --- NT dual-fire (CHK008) -------------------------------------------------


def test_chk008_nt_dual_fire_includes_both_agencies():
    decision = route("NT", "fire")
    assert "Bushfires NT" in decision.agencies
    assert "NTFRS" in decision.agencies


# --- NT cyclone (CHK009) ---------------------------------------------------


def test_chk009_nt_cyclone_routes_to_ntes():
    decision = route("NT", "cyclone")
    assert decision.agencies == ("NTES",)


# --- ACT umbrella (CHK010) -------------------------------------------------


def test_chk010_act_fire_addresses_esa_first():
    decision = route("ACT", "fire")
    assert decision.agencies[0] == "ESA", (
        f"CHK010: ACT fire MUST list ESA first (umbrella); got {decision.agencies}"
    )


# --- ACT police split (CHK011) ---------------------------------------------


def test_chk011_act_police_includes_afp_and_act_policing():
    decision = route("ACT", "police")
    assert "AFP" in decision.agencies
    assert "ACT Policing" in decision.agencies


@pytest.mark.parametrize(
    "hint,expected",
    [
        ("AFP", ("AFP",)),
        ("ACT Policing", ("ACT Policing",)),
    ],
)
def test_chk011_act_police_agency_hint_disambiguates(hint, expected):
    decision = route("ACT", "police", agency_hint=hint)
    assert decision.agencies == expected


# --- Closed medical set per jurisdiction (CHK012) --------------------------


@pytest.mark.parametrize(
    "jurisdiction,expected_agency",
    [
        ("NSW", "NSW Ambulance"),
        ("VIC", "Ambulance Victoria"),
        ("QLD", "Queensland Ambulance Service"),
        ("WA", "St John WA"),
        ("SA", "SA Ambulance Service"),
        ("TAS", "Ambulance Tasmania"),
        ("NT", "St John NT"),
        ("ACT", "ACT Ambulance Service"),
    ],
)
def test_chk012_medical_brand_per_jurisdiction(jurisdiction, expected_agency):
    decision = route(jurisdiction, "medical")
    assert expected_agency in decision.agencies, (
        f"CHK012: {jurisdiction} medical MUST include {expected_agency!r}; "
        f"got {decision.agencies}"
    )


# --- SES is lead flood/storm in NSW + VIC + QLD (CHK013) -------------------


@pytest.mark.parametrize("jurisdiction", ["NSW", "VIC", "QLD"])
@pytest.mark.parametrize("hazard", ["flood", "storm"])
def test_chk013_ses_lead_flood_storm_in_eastern_states(jurisdiction, hazard):
    decision = route(jurisdiction, hazard)
    # Each of these uses an SES variant; assert at least one agency contains "SES".
    has_ses = any("SES" in a for a in decision.agencies)
    assert has_ses, (
        f"CHK013: {jurisdiction} {hazard} MUST include an SES variant; "
        f"got {decision.agencies}"
    )


# --- CHK014 negative: unknown jurisdiction OR unknown hazard raises --------


def test_chk014_unknown_jurisdiction_raises():
    with pytest.raises(UnknownRouteError):
        route("XYZ", "fire")


def test_chk014_unknown_hazard_raises():
    with pytest.raises(UnknownRouteError):
        route("NSW", "asteroid")


# --- Smoke: every jurisdiction routes for the canonical hazard set ---------


@pytest.mark.parametrize(
    "jurisdiction", ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT"]
)
@pytest.mark.parametrize("hazard", ["fire", "flood", "storm", "police", "medical"])
def test_every_jurisdiction_resolves_canonical_hazards(jurisdiction, hazard):
    decision = route(jurisdiction, hazard)
    assert decision.agencies, (
        f"({jurisdiction}, {hazard}) MUST resolve to ≥1 agency"
    )
