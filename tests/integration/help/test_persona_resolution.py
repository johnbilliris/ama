"""spec-038 T-AA196 — persona resolution ordering + persona_source recording."""

from __future__ import annotations

from app.services.help.persona_resolver import resolve_persona, union_for_landing


def test_idp_default_resolves_highest_authority() -> None:
    # incident-commander rank 10 (higher authority) vs operations-officer rank 20.
    r = resolve_persona(
        idp_persona_claims=["operations-officer", "incident-commander", "observer-auditor"],
        user_override=None,
    )
    assert r.persona_id == "incident-commander"
    assert r.persona_source == "idp_default"


def test_user_override_recorded() -> None:
    r = resolve_persona(
        idp_persona_claims=["operations-officer", "incident-commander"],
        user_override="operations-officer",
    )
    assert r.persona_id == "operations-officer"
    assert r.persona_source == "user_override"


def test_union_ordered_by_authority() -> None:
    union = union_for_landing(["operations-officer", "incident-commander", "observer-auditor"])
    assert union[0] == "incident-commander"
