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
