"""Unit tests for spec-036 T-X01 — jurisdiction × hazard × agency routing tuples.

Per tasks.md §17 (Phase X) and FR-021:

* New service signature: ``route(jurisdiction, hazard, agency_hint=None) -> RoutingDecision``.
* Backing data is a list of tuple keys; replaces the prior coarse
  jurisdiction-only routing.
* Wave 2 establishes the **service shape and a representative fixture
  set** covering at least the eight jurisdictions; Wave 3+ tasks T-X02..X07
  will tighten WA/QLD/VIC/SA/NT/ACT details and the integration test will
  cover the full multi-jurisdiction.md J01–J31 matrix in T-X08.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.jurisdiction_routing import (
    RoutingDecision,
    UnknownRouteError,
    route,
)


def test_returns_routing_decision_for_known_tuple() -> None:
    decision = route("NSW", "fire")
    assert isinstance(decision, RoutingDecision)
    assert decision.jurisdiction == "NSW"
    assert decision.hazard == "fire"
    assert decision.agencies, "RoutingDecision must list at least one agency."


def test_nsw_fire_routes_to_rfs() -> None:
    decision = route("NSW", "fire")
    # NSW RFS is the lead combat agency for rural fire.
    assert "NSW RFS" in decision.agencies


def test_wa_fire_collapses_to_dfes() -> None:
    """WA single-route per multi-jurisdiction.md (DFES merged fire+SES)."""

    decision = route("WA", "fire")
    assert decision.agencies == ("DFES",)


def test_vic_fire_includes_both_cfa_and_frv() -> None:
    """VIC fire is split CFA (rural) + FRV (urban) per multi-jurisdiction.md."""

    decision = route("VIC", "fire")
    assert "CFA" in decision.agencies
    assert "FRV" in decision.agencies


def test_qld_fire_uses_qfd_naming() -> None:
    """QLD fire agency renamed to QFD (was QFES) per multi-jurisdiction.md."""

    decision = route("QLD", "fire")
    assert "QFD" in decision.agencies


def test_act_default_routes_to_esa() -> None:
    """ACT defaults to ESA umbrella (ESA-first); AFP is fallback for police."""

    decision = route("ACT", "fire")
    assert "ESA" in decision.agencies


def test_act_police_falls_back_to_afp() -> None:
    """ACT police events fallback to AFP / ACT-policing per FR-023 + Phase X."""

    decision = route("ACT", "police")
    assert "AFP" in decision.agencies or "ACT Policing" in decision.agencies


def test_agency_hint_disambiguates_when_multiple_match() -> None:
    """``agency_hint`` selects a single agency when several would qualify."""

    decision = route("VIC", "fire", agency_hint="FRV")
    assert decision.agencies == ("FRV",)


def test_unknown_jurisdiction_raises() -> None:
    with pytest.raises(UnknownRouteError):
        route("XX", "fire")


def test_unknown_hazard_raises() -> None:
    with pytest.raises(UnknownRouteError):
        route("NSW", "unknown-hazard-kind")


def test_routing_decision_is_frozen() -> None:
    """``RoutingDecision`` instances are immutable (Pydantic frozen=True)."""

    decision = route("NSW", "fire")
    with pytest.raises((TypeError, ValueError)):
        decision.jurisdiction = "VIC"  # type: ignore[misc]


def test_every_australian_jurisdiction_has_at_least_one_route() -> None:
    """Smoke check — all 8 AU jurisdictions are routable for at least one hazard."""

    from apps.api.app.services.simulation.jurisdiction_routing import (
        load_routes,
    )

    routes = load_routes()
    jurisdictions = {entry.jurisdiction for entry in routes}
    assert {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"} <= jurisdictions
