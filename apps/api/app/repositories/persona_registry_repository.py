"""Persona registry repository (spec-035 T024b dependency).

Provides ``persona_id → AIIMS function`` lookup for the RBAC stage-(b) check.
Backed by the canonical seed file
[`packages/domain/src/domain/seed/identities_australia.json`](../../../../../packages/domain/src/domain/seed/identities_australia.json).

The repository is a thin in-memory cache; callers obtain the singleton via
``get_persona_registry_repository()``. Reload on test by calling
``reset_persona_registry_repository()``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_SEED_RELATIVE: tuple[str, ...] = (
    "packages",
    "domain",
    "src",
    "domain",
    "seed",
    "identities_australia.json",
)


def _resolve_seed_path() -> Path:
    """Locate ``identities_australia.json`` for both repo and container layouts.

    Host layout: ``<repo>/apps/api/app/repositories/...`` → repo root is ``parents[4]``.
    Container layout: ``/app/app/repositories/...`` → ``/app`` is ``parents[2]`` and
    holds ``packages/`` directly. Walking parents handles both without crashing.
    """
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor.joinpath(*_SEED_RELATIVE)
        if candidate.exists():
            return candidate
    return here.parents[0] / "_missing_identities_australia.json"


@dataclass(frozen=True)
class Persona:
    persona_id: str
    aiims_function: str | None
    organisation_id: str | None = None
    jurisdiction_id: str | None = None
    display_name: str | None = None
    role: str | None = None
    decision_rights: list[str] = field(default_factory=list)
    information_needs: list[str] = field(default_factory=list)
    communication_pathways: list[str] = field(default_factory=list)


def _canonical_role(label: str | None, aiims_function: str | None, persona_id: str) -> str:
    value = (label or "").strip().lower().replace("/", "_").replace("-", " ")
    if "incident commander" in value:
        return "incident_commander"
    if "operations" in value:
        return "operations_officer"
    if "planning" in value:
        return "planning_officer"
    if "logistics" in value:
        return "logistics_officer"
    if "public information" in value:
        return "public_information_officer"
    if "field coordinator" in value:
        return "field_coordinator"
    if "observer" in value or "auditor" in value:
        return "observer_auditor"
    if "executive" in value:
        return "executive_leader"
    if "risk" in value:
        return "risk_manager"
    if "liaison" in value:
        return "liaison_officer"

    if aiims_function == "control":
        return "incident_commander"
    if aiims_function == "operations":
        return "operations_officer"
    if aiims_function == "planning":
        return "planning_officer"
    if aiims_function == "logistics":
        return "logistics_officer"
    if aiims_function == "public-information":
        return "public_information_officer"
    if "field" in persona_id:
        return "field_coordinator"
    return "operations_officer"


@dataclass
class PersonaRegistryRepository:
    _index: dict[str, Persona] = field(default_factory=dict)

    @classmethod
    def from_seed(cls, seed_path: Path | None = None) -> PersonaRegistryRepository:
        path = seed_path if seed_path is not None else _resolve_seed_path()
        index: dict[str, Persona] = {}
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            for raw in payload:
                pid = raw.get("persona_id")
                if not pid:
                    continue
                index[pid] = Persona(
                    persona_id=pid,
                    aiims_function=raw.get("aiims_function"),
                    organisation_id=raw.get("organisation_id"),
                    jurisdiction_id=raw.get("jurisdiction_id"),
                    display_name=raw.get("display_name"),
                    role=_canonical_role(raw.get("role"), raw.get("aiims_function"), pid),
                    decision_rights=list(raw.get("permissions", [])),
                    information_needs=["incident_summary", "task_dependency_status"],
                    communication_pathways=["agency_channel", "incident_channel"],
                )
        return cls(_index=index)

    def find_by_id(self, persona_id: str) -> Persona | None:
        return self._index.get(persona_id)


@lru_cache(maxsize=1)
def get_persona_registry_repository() -> PersonaRegistryRepository:
    return PersonaRegistryRepository.from_seed()


def reset_persona_registry_repository() -> None:
    get_persona_registry_repository.cache_clear()


__all__ = [
    "Persona",
    "PersonaRegistryRepository",
    "get_persona_registry_repository",
    "reset_persona_registry_repository",
]
