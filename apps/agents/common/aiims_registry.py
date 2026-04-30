"""Typed AIIMS role-to-agent registry (spec 032 FR-P05).

Replaces the constants in ``aiims_mapping.py`` with a typed, declarative
registry that supports per-jurisdiction overrides driven by JurisdictionPolicy
(``aiims_role_overrides``). Existing callers continue to work via re-export.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from common.aiims_mapping import (
    DEFAULT_AGENT_AIIMS_MAP,
    INCIDENT_LEVEL_DESCRIPTIONS,
    get_default_function,
    is_full_coverage_required,
    validate_coverage,
)

from packages.domain.src.domain.models.aiims_role_assignment import AiimsFunction


@dataclass(frozen=True)
class AiimsRoleEntry:
    """One row in the registry: function -> agent + optional jurisdiction overrides."""

    function: AiimsFunction
    default_agent: str
    description: str
    jurisdiction_overrides: dict[str, str] = field(default_factory=dict)

    def agent_for(self, jurisdiction_code: str | None) -> str:
        """Return the agent assigned to the given jurisdiction (falls back to default)."""
        if jurisdiction_code:
            return self.jurisdiction_overrides.get(jurisdiction_code, self.default_agent)
        return self.default_agent


@dataclass
class AiimsRegistry:
    """Typed registry of AIIMS roles.

    Defaults are seeded from the existing ``DEFAULT_AGENT_AIIMS_MAP`` so the
    refactor is safe for all existing callers. Per-jurisdiction overrides may
    be applied via :py:meth:`override`.
    """

    entries: dict[AiimsFunction, AiimsRoleEntry] = field(default_factory=dict)

    @classmethod
    def from_defaults(cls) -> AiimsRegistry:
        out = cls()
        for agent, function in DEFAULT_AGENT_AIIMS_MAP.items():
            out.entries[function] = AiimsRoleEntry(
                function=function,
                default_agent=agent,
                description=f"Default AIIMS {function} → {agent}",
            )
        return out

    def get(self, function: AiimsFunction) -> AiimsRoleEntry | None:
        return self.entries.get(function)

    def agent_for(self, function: AiimsFunction, jurisdiction_code: str | None = None) -> str | None:
        entry = self.get(function)
        return entry.agent_for(jurisdiction_code) if entry else None

    def override(self, function: AiimsFunction, jurisdiction_code: str, agent: str) -> None:
        """Apply a per-jurisdiction override (mutates in place)."""
        entry = self.entries.get(function)
        if entry is None:
            entry = AiimsRoleEntry(
                function=function, default_agent=agent, description=f"AIIMS {function} → {agent}"
            )
        new_overrides = {**entry.jurisdiction_overrides, jurisdiction_code: agent}
        self.entries[function] = AiimsRoleEntry(
            function=entry.function,
            default_agent=entry.default_agent,
            description=entry.description,
            jurisdiction_overrides=new_overrides,
        )

    def coverage(
        self, assigned_functions: list[str], incident_level: int
    ) -> tuple[float, list[str]]:
        """Convenience wrapper around the existing validate_coverage helper."""
        return validate_coverage(assigned_functions, incident_level)

    def level_description(self, level: int) -> str:
        return INCIDENT_LEVEL_DESCRIPTIONS.get(level, f"Unknown level {level}")

    def is_full_coverage_required(self, level: int) -> bool:
        return is_full_coverage_required(level)


# Module-level singleton (lazy-built); call sites can import directly.
_REGISTRY: AiimsRegistry | None = None


def registry() -> AiimsRegistry:
    """Return the process-wide registry, building it on first call."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AiimsRegistry.from_defaults()
    return _REGISTRY


def reset_for_tests() -> None:
    """Clear the singleton; for unit tests only."""
    global _REGISTRY
    _REGISTRY = None


# Re-exports for backward compatibility.
__all__ = [
    "AiimsRoleEntry",
    "AiimsRegistry",
    "registry",
    "reset_for_tests",
    "get_default_function",
    "validate_coverage",
    "is_full_coverage_required",
    "INCIDENT_LEVEL_DESCRIPTIONS",
    "DEFAULT_AGENT_AIIMS_MAP",
]


# Mark literal types unused to satisfy lint
_ = Literal
