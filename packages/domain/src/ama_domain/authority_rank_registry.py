"""spec-038 T-AA044 — Shared AIIMS authority-rank registry.

Single source of truth for persona authority ranking, mirroring spec-021
FR-025 (AIIMS Controller > Operations Officer > Planning > …). Used by
:class:`PersonaHelpProfile` and the runtime persona resolver
(``apps/api/app/services/help/persona_resolver.py``).

Per FR-027-AMEND the registry MUST be the only place where these ranks live;
do NOT inline the table elsewhere.
"""

from __future__ import annotations

from typing import Final

# Lower number = higher authority. Operational personas come from AIIMS;
# sector cluster personas (frontline / commonwealth / cross-sector) are ranked
# below operational coordinators by convention.
AUTHORITY_RANK: Final[dict[str, int]] = {
    # Operational (AIIMS — spec-021 FR-025)
    "incident-commander": 10,
    "operations-officer": 20,
    "planning-officer": 30,
    "logistics-officer": 40,
    "public-information-officer": 50,
    "field-coordinator": 60,
    "resilience-planner": 70,
    "executive-leader": 5,  # strategic; ranked above tactical roles
    "observer-auditor": 90,  # read-only — explicit lower priority
    "risk-manager": 65,
    # Sector clusters
    "frontline-fire": 100,
    "frontline-medical": 100,
    "frontline-police": 100,
    "frontline-ses-marine": 100,
    "commonwealth": 80,
    "cross-sector": 110,
}

OPERATIONAL_PERSONAS: Final[frozenset[str]] = frozenset(
    {
        "incident-commander",
        "operations-officer",
        "planning-officer",
        "logistics-officer",
        "public-information-officer",
        "field-coordinator",
        "resilience-planner",
        "executive-leader",
        "observer-auditor",
        "risk-manager",
    }
)

SECTOR_PERSONAS: Final[frozenset[str]] = frozenset(
    {
        "frontline-fire",
        "frontline-medical",
        "frontline-police",
        "frontline-ses-marine",
        "commonwealth",
        "cross-sector",
    }
)


def authority_rank(persona_id: str) -> int:
    """Return the rank for ``persona_id`` (raises KeyError on unknown)."""
    return AUTHORITY_RANK[persona_id]


def is_known_persona(persona_id: str) -> bool:
    return persona_id in AUTHORITY_RANK


def sort_personas_by_authority(persona_ids: list[str]) -> list[str]:
    """Sort persona ids by authority (highest first); unknown ids sort last."""
    return sorted(
        persona_ids,
        key=lambda p: AUTHORITY_RANK.get(p, 10_000),
    )


__all__ = [
    "AUTHORITY_RANK",
    "OPERATIONAL_PERSONAS",
    "SECTOR_PERSONAS",
    "authority_rank",
    "is_known_persona",
    "sort_personas_by_authority",
]
