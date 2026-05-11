"""spec-038 T-AA058 — persona resolver (FR-027/FR-028)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ama_domain import authority_rank, is_known_persona, sort_personas_by_authority

PersonaSource = Literal["idp_default", "user_override"]


@dataclass(frozen=True)
class ResolvedPersona:
    persona_id: str
    persona_source: PersonaSource


def resolve_persona(
    *,
    idp_persona_claims: list[str],
    user_override: str | None = None,
    entitled_personas: list[str] | None = None,
) -> ResolvedPersona:
    """Pick the active persona per FR-027 / FR-027-AMEND.

    - If ``user_override`` is provided AND entitled, returns it with source
      ``user_override``.
    - Otherwise returns the highest-authority operational persona from
      ``idp_persona_claims``, with source ``idp_default``.
    - Raises ``ValueError`` if no persona resolves (caller should return 403).
    """
    entitled = (
        set(entitled_personas)
        if entitled_personas
        else set(idp_persona_claims) | ({user_override} if user_override else set())
    )
    if user_override:
        if user_override not in entitled or not is_known_persona(user_override):
            raise ValueError(f"persona {user_override!r} not entitled or unknown")
        return ResolvedPersona(persona_id=user_override, persona_source="user_override")
    candidates = [p for p in idp_persona_claims if is_known_persona(p) and p in entitled]
    if not candidates:
        raise ValueError("no entitled persona for user")
    return ResolvedPersona(persona_id=sort_personas_by_authority(candidates)[0], persona_source="idp_default")


def union_for_landing(idp_persona_claims: list[str]) -> list[str]:
    """Return personas ordered by authority for the landing tile union (FR-028)."""
    return [p for p in sort_personas_by_authority(idp_persona_claims) if is_known_persona(p)]


__all__ = ["ResolvedPersona", "resolve_persona", "union_for_landing", "authority_rank"]
